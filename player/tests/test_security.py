import asyncio
import tempfile
import unittest
from dataclasses import dataclass, field
from pathlib import Path

from player.core import security as security_module
from player.core.db import Database
from player.core.security import (
    EVENT_MULTI_ENDPOINT,
    EVENT_MULTI_SOURCE,
    EVENT_REJOIN,
    EVENT_TIME_GAP,
    EVENT_UNMUTED_JOIN,
    EVENT_VIDEO_REJOIN,
    CallSecurityService,
)
from player.strings import Strings


@dataclass
class FakePeer:
    user_id: int


@dataclass
class FakeVideo:
    endpoint: str


@dataclass
class FakeParticipant:
    """شکل سادهٔ raw.types.GroupCallParticipant برای تست."""

    user_id: int
    muted: bool | None = True
    left: bool = False
    date: int = 1_700_000_000
    source: int = 111
    video_joined: bool = False
    video: FakeVideo | None = None
    presentation: FakeVideo | None = None
    is_self: bool = False
    peer: FakePeer = field(init=False)

    def __post_init__(self):
        self.peer = FakePeer(self.user_id)


def run(coro):
    return asyncio.run(coro)


class TestCallSecurity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "db.json")
        self.db.load()
        self.db.set_chat_setting(-100, "call_security", True)

        self._db_backup = security_module.db
        self._admins_backup = security_module.load_admins
        security_module.db = self.db

        async def no_admins(_chat_id, force=False):
            return set()

        security_module.load_admins = no_admins
        self.service = CallSecurityService()
        self.service.start_session(-100)

    def tearDown(self):
        security_module.db = self._db_backup
        security_module.load_admins = self._admins_backup
        self.tmp.cleanup()

    def keys(self, events):
        return [event.key for event in events]

    def test_disabled_security_reports_nothing(self):
        self.db.set_chat_setting(-100, "call_security", False)
        events = run(self.service.analyze(-100, [FakeParticipant(1, muted=False)]))
        self.assertEqual(events, [])

    def test_quiet_participant_is_not_reported(self):
        events = run(self.service.analyze(-100, [FakeParticipant(1)]))
        self.assertEqual(events, [])

    def test_unmuted_join_is_reported(self):
        events = run(self.service.analyze(-100, [FakeParticipant(1, muted=False)]))
        self.assertIn(EVENT_UNMUTED_JOIN, self.keys(events))

    def test_privileged_user_may_join_unmuted(self):
        async def only_admin(_chat_id, force=False):
            return {1}

        security_module.load_admins = only_admin
        events = run(self.service.analyze(-100, [FakeParticipant(1, muted=False)]))
        self.assertEqual(events, [])

    def test_repeated_joins_are_reported(self):
        for _ in range(6):
            run(self.service.analyze(-100, [FakeParticipant(1)]))
            run(self.service.analyze(-100, []))  # لفت داد
        keys = self.keys(self.service.events(-100))
        self.assertIn(EVENT_REJOIN, keys)

    def test_multiple_sources_are_reported(self):
        run(self.service.analyze(-100, [FakeParticipant(1, source=1)]))
        events = run(self.service.analyze(-100, [FakeParticipant(1, source=2)]))
        self.assertIn(EVENT_MULTI_SOURCE, self.keys(events))

    def test_multiple_endpoints_are_reported(self):
        run(self.service.analyze(-100, [FakeParticipant(1, video=FakeVideo("a"))]))
        events = run(self.service.analyze(-100, [FakeParticipant(1, video=FakeVideo("b"))]))
        self.assertIn(EVENT_MULTI_ENDPOINT, self.keys(events))

    def test_changed_join_date_is_a_time_gap(self):
        run(self.service.analyze(-100, [FakeParticipant(1, date=1000)]))
        events = run(self.service.analyze(-100, [FakeParticipant(1, date=2000)]))
        self.assertIn(EVENT_TIME_GAP, self.keys(events))

    def test_second_video_join_without_leaving_is_reported(self):
        run(self.service.analyze(-100, [FakeParticipant(1, video_joined=True)]))
        run(self.service.analyze(-100, [FakeParticipant(1, video_joined=False)]))
        events = run(self.service.analyze(-100, [FakeParticipant(1, video_joined=True)]))
        self.assertIn(EVENT_VIDEO_REJOIN, self.keys(events))

    def test_video_join_after_leaving_is_allowed(self):
        run(self.service.analyze(-100, [FakeParticipant(1, video_joined=True)]))
        run(self.service.analyze(-100, []))  # لفت داد
        events = run(self.service.analyze(-100, [FakeParticipant(1, video_joined=True)]))
        self.assertNotIn(EVENT_VIDEO_REJOIN, self.keys(events))

    def test_each_behaviour_is_reported_once_per_member(self):
        first = run(self.service.analyze(-100, [FakeParticipant(1, muted=False)]))
        run(self.service.analyze(-100, []))
        second = run(self.service.analyze(-100, [FakeParticipant(1, muted=False)]))
        self.assertEqual(self.keys(first), [EVENT_UNMUTED_JOIN])
        self.assertNotIn(EVENT_UNMUTED_JOIN, self.keys(second))

    def test_left_participants_are_skipped(self):
        events = run(self.service.analyze(-100, [FakeParticipant(1, muted=False, left=True)]))
        self.assertEqual(events, [])

    def test_summary_is_none_without_events(self):
        self.assertIsNone(self.service.summary_text(-100, Strings("fa")))

    def test_summary_lists_events_and_totals(self):
        run(self.service.analyze(-100, [FakeParticipant(1, muted=False)]))
        summary = self.service.summary_text(-100, Strings("fa"))
        self.assertIn("1", summary)
        self.assertIn(Strings("fa")("security_event_unmuted_join"), summary)
        self.assertIn(Strings("fa")("security_summary_totals"), summary)

    def test_report_lines_mention_users(self):
        events = run(self.service.analyze(-100, [FakeParticipant(42, muted=False)]))
        lines = self.service.report_lines(Strings("fa"), events)
        self.assertEqual(len(lines), 1)
        self.assertIn("tg://user?id=42", lines[0])

    def test_end_session_clears_state(self):
        run(self.service.analyze(-100, [FakeParticipant(1, muted=False)]))
        self.service.end_session(-100)
        self.assertEqual(self.service.events(-100), [])

    def test_min_age_days_falls_back_to_config(self):
        from player import config

        self.assertEqual(security_module.min_age_days(-100), config.CALL_SECURITY_MIN_AGE_DAYS)
        self.db.set_chat_setting(-100, "security_min_age_days", 3)
        self.assertEqual(security_module.min_age_days(-100), 3)


if __name__ == "__main__":
    unittest.main()
