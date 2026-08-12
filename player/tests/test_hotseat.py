import asyncio
import unittest
from dataclasses import dataclass, field
from time import time

from player import config
from player.core import hotseat as hotseat_module
from player.core.errors import UserError
from player.core.hotseat import Guest, HotSeatService
from player.strings import Strings

CHAT = -1001


@dataclass
class FakePeer:
    user_id: int


@dataclass
class FakeParticipant:
    user_id: int
    muted: bool = True
    left: bool = False
    peer: FakePeer = field(init=False)

    def __post_init__(self):
        self.peer = FakePeer(self.user_id)


@dataclass
class FakeAssistant:
    id: int = 999


class FakeCalls:
    """جای `calls_service`: تغییر وضعیت مایک‌ها را ثبت می‌کند."""

    def __init__(self, participants=(), allow=True):
        self.participants = list(participants)
        self.allow = allow
        self.mic: list[tuple[int, bool]] = []

    def assistant(self, _chat_id):
        return FakeAssistant()

    async def raw_participants(self, _chat_id, limit=200):
        return list(self.participants)

    async def set_participant_muted(self, _chat_id, user_id, muted):
        self.mic.append((user_id, muted))
        return self.allow


def run(coro):
    return asyncio.run(coro)


def guests(*ids: int) -> list[Guest]:
    return [Guest(user_id=user_id, name=f"user{user_id}") for user_id in ids]


class TestHotSeat(unittest.TestCase):
    def setUp(self):
        self.calls = FakeCalls()
        self._backup = hotseat_module.calls_service
        hotseat_module.calls_service = self.calls
        self.service = HotSeatService()

    def tearDown(self):
        hotseat_module.calls_service = self._backup

    def start(self, *ids: int, seconds: int = 60):
        return run(self.service.start(CHAT, 7, guests(*ids), seconds))

    # ── شروع بازی ────────────────────────────────────────────────────────────
    def test_first_guest_takes_the_seat_and_gets_the_mic(self):
        session = self.start(1, 2)
        self.assertEqual(session.current.user_id, 1)
        self.assertEqual([guest.user_id for guest in session.queue], [2])
        self.assertIn((1, False), self.calls.mic)

    def test_start_without_guests_leaves_the_seat_empty(self):
        session = self.start()
        self.assertIsNone(session.current)
        self.assertEqual(session.size(), 0)
        self.assertEqual(self.calls.mic, [])

    def test_second_game_in_the_same_chat_is_rejected(self):
        self.start(1)
        with self.assertRaises(UserError) as caught:
            self.start(2)
        self.assertEqual(caught.exception.key, "hotseat_already")

    def test_default_turn_length_comes_from_config(self):
        session = run(self.service.start(CHAT, 7, guests(1)))
        self.assertEqual(session.seconds, config.HOTSEAT_TURN_SECONDS)

    def test_duplicate_guests_are_dropped_on_start(self):
        session = run(self.service.start(CHAT, 7, guests(1) + guests(1)))
        self.assertEqual(session.size(), 1)

    # ── مایک‌ها ───────────────────────────────────────────────────────────────
    def test_others_in_the_call_are_muted_for_the_guest(self):
        self.calls.participants = [
            FakeParticipant(1, muted=False),
            FakeParticipant(5, muted=False),
            FakeParticipant(999),  # اسیستنت
        ]
        session = self.start(1)
        self.assertIn((5, True), self.calls.mic)
        self.assertNotIn((999, True), self.calls.mic)
        self.assertNotIn((1, True), self.calls.mic)
        self.assertEqual(session.muted, {5})

    def test_already_muted_members_are_left_alone(self):
        self.calls.participants = [FakeParticipant(5, muted=True)]
        session = self.start(1)
        self.assertEqual(session.muted, set())

    def test_missing_mic_permission_is_flagged(self):
        self.calls.allow = False
        session = self.start(1)
        self.assertTrue(session.mic_failed)

    def test_stop_gives_the_mic_back_to_muted_members(self):
        self.calls.participants = [FakeParticipant(5, muted=False)]
        self.start(1)
        self.calls.mic.clear()
        session = run(self.service.stop(CHAT))
        self.assertIn((5, False), self.calls.mic)
        self.assertIn((1, True), self.calls.mic)
        self.assertEqual(session.muted, set())
        self.assertFalse(self.service.is_active(CHAT))

    # ── مهمان‌ها ──────────────────────────────────────────────────────────────
    def test_guest_added_to_an_empty_seat_starts_playing(self):
        self.start()
        self.assertTrue(run(self.service.add(CHAT, guests(3)[0])))
        self.assertEqual(self.service.session(CHAT).current.user_id, 3)

    def test_guest_added_while_someone_plays_waits_in_the_queue(self):
        session = self.start(1)
        run(self.service.add(CHAT, guests(3)[0]))
        self.assertEqual(session.current.user_id, 1)
        self.assertEqual([guest.user_id for guest in session.waiting()], [3])

    def test_adding_the_same_guest_twice_returns_false(self):
        self.start(1)
        self.assertFalse(run(self.service.add(CHAT, guests(1)[0])))

    def test_guest_limit_is_enforced(self):
        session = self.start(1)
        session.queue = guests(*range(100, 100 + config.HOTSEAT_MAX_GUESTS))
        with self.assertRaises(UserError) as caught:
            run(self.service.add(CHAT, guests(50)[0]))
        self.assertEqual(caught.exception.key, "hotseat_limit")

    def test_removing_the_seated_guest_hands_the_seat_over(self):
        session = self.start(1, 2)
        removed = run(self.service.remove(CHAT, 1))
        self.assertEqual(removed.user_id, 1)
        self.assertEqual(session.current.user_id, 2)
        self.assertIn((1, True), self.calls.mic)

    def test_removing_a_waiting_guest_keeps_the_current_one(self):
        session = self.start(1, 2, 3)
        run(self.service.remove(CHAT, 3))
        self.assertEqual(session.current.user_id, 1)
        self.assertEqual([guest.user_id for guest in session.waiting()], [2])

    def test_removing_an_unknown_user_returns_none(self):
        self.start(1)
        self.assertIsNone(run(self.service.remove(CHAT, 404)))

    # ── نوبت‌ها ───────────────────────────────────────────────────────────────
    def test_advance_moves_to_the_next_guest(self):
        session = self.start(1, 2)
        guest = run(self.service.advance(CHAT))
        self.assertEqual(guest.user_id, 2)
        self.assertEqual(session.served, 2)
        self.assertIn((1, True), self.calls.mic)
        self.assertIn((2, False), self.calls.mic)

    def test_advance_with_an_empty_queue_returns_none(self):
        session = self.start(1)
        self.assertIsNone(run(self.service.advance(CHAT)))
        self.assertIsNone(session.current)

    def test_commands_need_a_running_game(self):
        for coro in (
            self.service.add(CHAT, guests(1)[0]),
            self.service.remove(CHAT, 1),
            self.service.advance(CHAT),
        ):
            with self.assertRaises(UserError) as caught:
                run(coro)
            self.assertEqual(caught.exception.key, "hotseat_not_active")

    def test_stop_without_a_game_returns_none(self):
        self.assertIsNone(run(self.service.stop(CHAT)))

    # ── زمان ─────────────────────────────────────────────────────────────────
    def test_remaining_counts_down(self):
        session = self.start(1, seconds=60)
        session.turn_started = time() - 20
        self.assertEqual(session.remaining(), 40)

    def test_zero_seconds_means_unlimited(self):
        session = self.start(1, seconds=0)
        session.turn_started = time() - 10_000
        self.assertTrue(session.unlimited)
        self.assertEqual(session.remaining(), -1)

    def test_pause_freezes_and_resume_restores_the_timer(self):
        session = self.start(1, seconds=60)
        session.turn_started = time() - 20
        self.service.pause(CHAT)
        self.assertTrue(session.paused)
        self.assertEqual(session.remaining(), 40)
        self.service.resume(CHAT)
        self.assertFalse(session.paused)
        self.assertEqual(session.remaining(), 40)

    def test_paused_turn_does_not_expire(self):
        session = self.start(1, 2, seconds=60)
        session.turn_started = time() - 90
        self.service.pause(CHAT)
        run(self.service.tick(CHAT))
        self.assertEqual(session.current.user_id, 1)

    def test_expired_turn_seats_the_next_guest(self):
        seen: list[int] = []

        async def on_turn(session):
            seen.append(session.current.user_id)

        self.service.on_turn = on_turn
        session = self.start(1, 2, seconds=60)
        session.turn_started = time() - 61
        run(self.service.tick(CHAT))
        self.assertEqual(session.current.user_id, 2)
        self.assertEqual(seen, [2])

    def test_expired_last_turn_finishes_the_game(self):
        finished: list[int] = []

        async def on_finish(session):
            finished.append(session.served)

        self.service.on_finish = on_finish
        session = self.start(1, seconds=60)
        session.turn_started = time() - 61
        run(self.service.tick(CHAT))
        self.assertFalse(self.service.is_active(CHAT))
        self.assertEqual(finished, [1])

    def test_broken_hook_does_not_break_the_game(self):
        async def boom(_session):
            raise RuntimeError("خرابی در ارسال پیام")

        self.service.on_turn = boom
        session = self.start(1, 2, seconds=60)
        session.turn_started = time() - 61
        run(self.service.tick(CHAT))
        self.assertEqual(session.current.user_id, 2)

    def test_unlimited_turn_never_expires(self):
        session = self.start(1, 2, seconds=0)
        run(self.service.tick(CHAT))
        self.assertEqual(session.current.user_id, 1)


class TestHotSeatTexts(unittest.TestCase):
    """متن‌های صندلی داغ در هر دو زبان باید بدون جای‌گذارِ خالی ساخته شوند."""

    def setUp(self):
        self.calls = FakeCalls()
        self._backup = hotseat_module.calls_service
        hotseat_module.calls_service = self.calls
        self.service = HotSeatService()

    def tearDown(self):
        hotseat_module.calls_service = self._backup

    def test_status_and_turn_texts_render(self):
        from player.plugins.hotseat import status_text, turn_text

        session = run(self.service.start(CHAT, 7, guests(1, 2), 60))
        for language in ("fa", "en"):
            s = Strings(language)
            with self.subTest(language=language):
                self.assertIn("user1", turn_text(session, s))
                status = status_text(session, s, "گروه تست")
                self.assertIn("user2", status)
                self.assertNotIn("{", status)

    def test_empty_queue_is_reported_in_the_status(self):
        from player.plugins.hotseat import status_text

        session = run(self.service.start(CHAT, 7, (), 60))
        s = Strings("fa")
        self.assertIn(s("hotseat_no_guests"), status_text(session, s, "-"))
        self.assertIn(s("hotseat_empty_seat"), status_text(session, s, "-"))

    def test_mic_warning_is_appended_when_muting_fails(self):
        from player.plugins.hotseat import turn_text

        self.calls.allow = False
        session = run(self.service.start(CHAT, 7, guests(1), 60))
        s = Strings("fa")
        self.assertIn(s("hotseat_mic_hint").strip(), turn_text(session, s))


if __name__ == "__main__":
    unittest.main()
