import unittest

from pyrogram.handlers.handler import Handler


class TestPluginLoader(unittest.TestCase):
    """بارگذار پلاگین‌ها باید همهٔ هندلرها را قطعی (بدون نیاز به حلقهٔ رویداد) ثبت کند."""

    @classmethod
    def setUpClass(cls):
        from player.core import clients

        cls.clients = clients
        cls.registered = clients.load_plugins()

    def test_handlers_are_registered(self):
        groups = self.clients.bot.dispatcher.groups
        total = sum(len(handlers) for handlers in groups.values())
        self.assertGreater(total, 30)
        self.assertEqual(total, self.registered)

    def test_groups_are_sorted_and_contain_handlers(self):
        groups = self.clients.bot.dispatcher.groups
        self.assertEqual(list(groups), sorted(groups))
        for handlers in groups.values():
            for handler in handlers:
                self.assertIsInstance(handler, Handler)

    def test_loading_twice_does_not_duplicate(self):
        before = sum(len(h) for h in self.clients.bot.dispatcher.groups.values())
        self.assertEqual(self.clients.load_plugins(), before)
        after = sum(len(h) for h in self.clients.bot.dispatcher.groups.values())
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
