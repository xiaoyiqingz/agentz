import asyncio
import unittest

from core.shell_approval import ShellApprovalManager, ShellApprovalRegistry


class TestShellApprovalManager(unittest.IsolatedAsyncioTestCase):
    async def test_approved_request_resolves_true(self):
        manager = ShellApprovalManager("session-1")
        request = manager.create_request(
            command="make generate",
            working_directory="/workspace",
            is_background=False,
        )
        waiting = asyncio.create_task(manager.wait_for_decision(request.approval_id))

        self.assertEqual(await manager.next_request(), request)

        self.assertTrue(manager.resolve(request.approval_id, True))
        self.assertTrue(await waiting)
        self.assertFalse(manager.resolve(request.approval_id, True))

    async def test_rejected_request_resolves_false(self):
        manager = ShellApprovalManager("session-1")
        request = manager.create_request(
            command="go test ./...",
            working_directory="/workspace",
            is_background=False,
        )
        waiting = asyncio.create_task(manager.wait_for_decision(request.approval_id))

        self.assertEqual(await manager.next_request(), request)

        self.assertTrue(manager.resolve(request.approval_id, False))
        self.assertFalse(await waiting)

    async def test_registry_only_resolves_the_registered_session(self):
        registry = ShellApprovalRegistry()
        manager = ShellApprovalManager("session-1")
        registry.register(manager)
        request = manager.create_request(
            command="make generate",
            working_directory="/workspace",
            is_background=False,
        )
        waiting = asyncio.create_task(manager.wait_for_decision(request.approval_id))

        self.assertFalse(registry.resolve("session-2", request.approval_id, True))
        self.assertTrue(registry.resolve("session-1", request.approval_id, True))
        self.assertTrue(await waiting)

    async def test_unregister_rejects_pending_requests(self):
        registry = ShellApprovalRegistry()
        manager = ShellApprovalManager("session-1")
        registry.register(manager)
        request = manager.create_request(
            command="make generate",
            working_directory="/workspace",
            is_background=False,
        )
        waiting = asyncio.create_task(manager.wait_for_decision(request.approval_id))

        registry.unregister(manager)

        self.assertFalse(await waiting)
        self.assertFalse(registry.resolve("session-1", request.approval_id, True))
