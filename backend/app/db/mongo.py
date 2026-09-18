from typing import Any
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import get_settings

_client: AsyncIOMotorClient | None = None
_memory: Any = None
_use_memory = False


def using_memory() -> bool:
    return _use_memory


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(get_settings().mongodb_url, serverSelectionTimeoutMS=1500)
    return _client


def get_db() -> Any:
    if _use_memory:
        return _memory
    return get_client()[get_settings().mongodb_database]


async def ping_db() -> bool:
    if _use_memory:
        return True
    try:
        await get_client().admin.command("ping")
        return True
    except Exception:
        return False


async def enable_memory() -> None:
    global _memory, _use_memory
    from app.db.memory import FakeDB

    _memory = FakeDB()
    _use_memory = True


async def close_db() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
