from typing import Protocol


class NotificationProvider(Protocol):
    async def send(self, to: str, title: str, body: str) -> None: ...


class InAppProvider:
    def __init__(self, notify_service):
        self.notify_service = notify_service

    async def send(self, to: str, title: str, body: str) -> None:
        return None


class EmailProvider:
    async def send(self, to: str, title: str, body: str) -> None:
        return None
