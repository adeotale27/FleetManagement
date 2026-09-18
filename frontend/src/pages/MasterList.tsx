import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { PageResult } from "../types";
import { ErrorState, Skeleton } from "../components/ui/primitives";
import { DataTable, StatusBadge } from "../components/tables/DataTable";

export function MasterList({
  title,
  resource,
  columns,
  fields,
  createLabel = "Add new",
  createTo,
}: {
  title: string;
  resource: string;
  columns: { key: string; label: string }[];
  fields: { key: string; label: string }[];
  createLabel?: string;
  createTo?: string;
}) {
  const [tab, setTab] = useState("all");
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<Record<string, string>>({});
  const nav = useNavigate();
  const qc = useQueryClient();
  const status = tab === "all" ? "" : tab;
  const q = useQuery({
    queryKey: [resource, search, status],
    queryFn: () => api<PageResult<Record<string, unknown>>>(`/${resource}?search=${encodeURIComponent(search)}&status=${status}&limit=15`),
  });
  const save = useMutation({
    mutationFn: () => api(`/${resource}`, { method: "POST", body: JSON.stringify({ ...form, status: "active" }) }),
    onSuccess: () => {
      setOpen(false);
      qc.invalidateQueries({ queryKey: [resource] });
    },
  });
  if (q.isLoading) return <Skeleton />;
  if (q.isError) return <ErrorState message={(q.error as Error).message} onRetry={() => q.refetch()} />;
  const rows = q.data?.items || [];
  return (
    <section>
      <div className="page-head">
        <div>
          <h1 className="h1">{title}</h1>
          <p className="muted">{q.data?.total || 0} records · tenant scoped</p>
        </div>
        <button className="btn" onClick={() => (createTo ? nav(createTo) : setOpen(true))}>
          {createLabel}
        </button>
      </div>
      <div className="tabs">
        {["all", "active", "inactive"].map((t) => (
          <button key={t} className={tab === t ? "on" : ""} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
      </div>
      <div className="toolbar">
        <input className="input" placeholder="Search name, mobile, number" value={search} onChange={(e) => setSearch(e.target.value)} aria-label="Search" />
      </div>
      {rows.length === 0 ? (
        <div className="state">Nothing here yet. Add the first record.</div>
      ) : (
        <DataTable
          rows={rows}
          columns={columns.map((c) => (c.key === "status" ? { ...c, render: (r) => <StatusBadge status={String(r.status || "")} /> } : c))}
          onRow={(r) => r.id && nav(`/${resource}/${String(r.id)}`)}
        />
      )}
      <div className="pager">
        <span>Showing {rows.length} of {q.data?.total}</span>
      </div>
      {open ? (
        <form
          className="panel grid"
          style={{ marginTop: 16, display: "grid", gap: 10 }}
          onSubmit={(e) => {
            e.preventDefault();
            save.mutate();
          }}
        >
          <h2 className="h1">{createLabel}</h2>
          {fields.map((f) => (
            <label className="field" key={f.key}>
              {f.label}
              <input className="input" required value={form[f.key] || ""} onChange={(e) => setForm({ ...form, [f.key]: e.target.value })} />
            </label>
          ))}
          {save.isError ? <ErrorState message={(save.error as Error).message} /> : null}
          <div className="toolbar">
            <button className="btn" type="submit">
              Save
            </button>
            <button className="btn secondary" type="button" onClick={() => setOpen(false)}>
              Cancel
            </button>
          </div>
        </form>
      ) : null}
    </section>
  );
}
