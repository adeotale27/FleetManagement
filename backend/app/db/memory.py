from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


def _get(doc: dict, path: str) -> Any:
    cur: Any = doc
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def matches(doc: dict, query: dict) -> bool:
    for key, expected in query.items():
        if key == "$or":
            if not any(matches(doc, q) for q in expected):
                return False
            continue
        if key == "$and":
            if not all(matches(doc, q) for q in expected):
                return False
            continue
        actual = _get(doc, key)
        if isinstance(expected, dict) and any(k.startswith("$") for k in expected):
            if "$ne" in expected and actual == expected["$ne"]:
                return False
            if "$in" in expected and actual not in expected["$in"]:
                return False
            if "$gte" in expected and (actual is None or actual < expected["$gte"]):
                return False
            if "$lte" in expected and (actual is None or actual > expected["$lte"]):
                return False
            if "$gt" in expected and (actual is None or actual <= expected["$gt"]):
                return False
            if "$regex" in expected:
                import re

                if actual is None or not re.search(expected["$regex"], str(actual), re.I if expected.get("$options") == "i" else 0):
                    return False
            continue
        if actual != expected:
            return False
    return True


class Cursor:
    def __init__(self, items: list[dict]):
        self.items = items

    def sort(self, key, direction=1):
        if isinstance(key, list):
            for k, d in reversed(key):
                self.items.sort(key=lambda x: x.get(k) or "", reverse=d < 0)
        else:
            self.items.sort(key=lambda x: x.get(key) or "", reverse=direction < 0)
        return self

    def skip(self, n: int):
        self.items = self.items[n:]
        return self

    def limit(self, n: int):
        self.items = self.items[:n]
        return self

    async def to_list(self, length=None):
        return deepcopy(self.items[:length] if length is not None else self.items)


class Collection:
    def __init__(self):
        self.docs: list[dict] = []

    async def insert_one(self, doc: dict):
        self.docs.append(deepcopy(doc))

    async def insert_many(self, docs: list[dict]):
        self.docs.extend(deepcopy(d) for d in docs)

    async def find_one(self, query: dict):
        for d in self.docs:
            if matches(d, query):
                return deepcopy(d)
        return None

    def find(self, query: dict | None = None):
        query = query or {}
        return Cursor([deepcopy(d) for d in self.docs if matches(d, query)])

    async def count_documents(self, query: dict):
        return len([d for d in self.docs if matches(d, query)])

    async def update_one(self, query: dict, update: dict):
        class R:
            modified_count = 0

        r = R()
        for i, d in enumerate(self.docs):
            if matches(d, query):
                self.docs[i] = apply_update(d, update)
                r.modified_count = 1
                break
        return r

    async def find_one_and_update(self, query: dict, update: dict, upsert=False, return_document=None):
        for i, d in enumerate(self.docs):
            if matches(d, query):
                self.docs[i] = apply_update(d, update)
                return deepcopy(self.docs[i])
        if upsert:
            base = dict(query)
            base = {k: v for k, v in base.items() if not str(k).startswith("$")}
            new_doc = apply_update(base, update)
            if "_id" not in new_doc:
                from app.repositories.base import oid

                new_doc["_id"] = oid()
            self.docs.append(new_doc)
            return deepcopy(new_doc)
        return None

    def aggregate(self, pipeline: list[dict]):
        items = deepcopy(self.docs)
        for stage in pipeline:
            if "$match" in stage:
                items = [d for d in items if matches(d, stage["$match"])]
            elif "$group" in stage:
                spec = stage["$group"]
                groups: dict[Any, dict] = {}
                for d in items:
                    gid = d.get(spec["_id"][1:]) if isinstance(spec["_id"], str) and spec["_id"].startswith("$") else spec["_id"]
                    if isinstance(spec["_id"], str) and spec["_id"].startswith("$"):
                        gid = d.get(spec["_id"][1:])
                    g = groups.setdefault(gid, {"_id": gid})
                    for k, v in spec.items():
                        if k == "_id":
                            continue
                        if "$sum" in v:
                            field = v["$sum"]
                            if field == 1:
                                g[k] = g.get(k, 0) + 1
                            elif isinstance(field, str) and field.startswith("$"):
                                g[k] = g.get(k, 0) + (d.get(field[1:]) or 0)
                            else:
                                g[k] = g.get(k, 0) + field
                        if "$last" in v:
                            field = v["$last"]
                            g[k] = d.get(field[1:]) if isinstance(field, str) and field.startswith("$") else field
                        if "$subtract" in v:
                            pass
                    groups[gid] = g
                items = list(groups.values())
            elif "$project" in stage:
                projected = []
                for d in items:
                    row = {}
                    for k, v in stage["$project"].items():
                        if v == 1:
                            row[k] = d.get(k)
                        elif isinstance(v, str):
                            row[k] = d.get(v[1:] if v.startswith("$") else v)
                        elif isinstance(v, dict) and "$subtract" in v:
                            a, b = v["$subtract"]
                            row[k] = (d.get(a[1:]) if isinstance(a, str) and a.startswith("$") else d.get(a, 0) if isinstance(a, str) else a) - (
                                d.get(b[1:]) if isinstance(b, str) and b.startswith("$") else d.get(b, 0) if isinstance(b, str) else b
                            )
                    projected.append(row)
                items = projected
            elif "$sort" in stage:
                for k, direction in reversed(list(stage["$sort"].items())):
                    items.sort(key=lambda x: x.get(k) or 0, reverse=direction < 0)
        return Cursor(items)

    async def create_index(self, *args, **kwargs):
        return "ok"


def apply_update(doc: dict, update: dict) -> dict:
    out = deepcopy(doc)
    if "$set" in update:
        out.update(update["$set"])
    if "$inc" in update:
        for k, v in update["$inc"].items():
            out[k] = (out.get(k) or 0) + v
    if "$setOnInsert" in update and not doc.get("_id"):
        for k, v in update["$setOnInsert"].items():
            out.setdefault(k, v)
    if "$setOnInsert" in update:
        for k, v in update["$setOnInsert"].items():
            if k not in out:
                out[k] = v
    return out


class FakeDB(dict):
    def __getitem__(self, key: str) -> Collection:
        if key not in self:
            super().__setitem__(key, Collection())
        return super().__getitem__(key)

    def __getattr__(self, key: str) -> Collection:
        return self[key]
