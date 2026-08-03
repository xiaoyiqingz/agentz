"""User approval state for shell commands.

The shell capability executes a command only after the active UI has resolved
the matching approval request.  This is deliberately application state rather
than an instruction for the model, so a model cannot bypass it.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from uuid import uuid4


class ShellApprovalRejected(RuntimeError):
    """Raised when the user declines a shell command."""


@dataclass(frozen=True)
class ShellApprovalRequest:
    approval_id: str
    session_id: str
    command: str
    working_directory: str
    is_background: bool


class ShellApprovalManager:
    """Coordinate pending approvals for one open Agent session."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self._pending: dict[str, asyncio.Future[bool]] = {}
        self._requests: asyncio.Queue[ShellApprovalRequest] = asyncio.Queue()

    def create_request(
        self,
        *,
        command: str,
        working_directory: str,
        is_background: bool,
    ) -> ShellApprovalRequest:
        approval_id = str(uuid4())
        self._pending[approval_id] = asyncio.get_running_loop().create_future()
        request = ShellApprovalRequest(
            approval_id=approval_id,
            session_id=self.session_id,
            command=command,
            working_directory=working_directory,
            is_background=is_background,
        )
        self._requests.put_nowait(request)
        return request

    async def next_request(self) -> ShellApprovalRequest:
        """Wait until a deferred Shell tool call needs a UI decision."""
        return await self._requests.get()

    async def wait_for_decision(self, approval_id: str) -> bool:
        future = self._pending.get(approval_id)
        if future is None:
            raise ShellApprovalRejected("Shell 命令审批已失效")
        try:
            return await future
        finally:
            self._pending.pop(approval_id, None)

    def resolve(self, approval_id: str, approved: bool) -> bool:
        future = self._pending.get(approval_id)
        if future is None or future.done():
            return False
        future.set_result(approved)
        return True

    def reject_all(self) -> None:
        for future in self._pending.values():
            if not future.done():
                future.set_result(False)


class ShellApprovalRegistry:
    """Expose approvals to the Web request that submits a user's choice."""

    def __init__(self) -> None:
        self._sessions: dict[str, ShellApprovalManager] = {}

    def register(self, manager: ShellApprovalManager) -> None:
        self._sessions[manager.session_id] = manager

    def unregister(self, manager: ShellApprovalManager) -> None:
        if self._sessions.get(manager.session_id) is manager:
            self._sessions.pop(manager.session_id, None)
        manager.reject_all()

    def resolve(self, session_id: str, approval_id: str, approved: bool) -> bool:
        manager = self._sessions.get(session_id)
        return manager is not None and manager.resolve(approval_id, approved)


shell_approval_registry = ShellApprovalRegistry()
