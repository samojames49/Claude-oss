import unittest

from pytgcalls.ffmpeg import build_command
from pytgcalls.types.raw import AudioParameters, VideoParameters

from player.core.calls import build_stream
from player.core.track import Track


def audio_command(track: Track) -> list[str]:
    params = build_stream(track)._ffmpeg_parameters
    return build_command("ffmpeg", params, track.file_path or track.source, AudioParameters(48000, 2))


def video_command(track: Track) -> list[str]:
    params = build_stream(track)._ffmpeg_parameters
    return build_command(
        "ffmpeg", params, track.file_path or track.source, VideoParameters(1280, 720, 30)
    )


def option_values(command: list[str], flag: str) -> list[str]:
    return [command[index + 1] for index, item in enumerate(command) if item == flag]


class TestStreamParameters(unittest.TestCase):
    def track(self, **kwargs) -> Track:
        defaults = dict(title="نمونه", source="/tmp/sample.mp4", duration=120)
        defaults.update(kwargs)
        return Track(**defaults)

    def test_plain_track_has_no_filters(self):
        command = audio_command(self.track())
        self.assertNotIn("-af", command)
        self.assertNotIn("-ss", command)

    def test_seek_is_applied_before_input(self):
        command = audio_command(self.track(seek=42))
        self.assertLess(command.index("-ss"), command.index("-i"))
        self.assertEqual(option_values(command, "-ss"), ["42"])

    def test_speed_and_media_volume_share_one_audio_filter(self):
        """ffmpeg تنها آخرین ‎-af را می‌بیند، پس هر دو فیلتر باید در یکی جمع شوند."""
        command = audio_command(self.track(speed=1.5, media_volume=150))
        filters = option_values(command, "-af")
        self.assertEqual(filters, ["atempo=1.5,volume=1.5"])

    def test_audio_filter_comes_after_input(self):
        command = audio_command(self.track(media_volume=50))
        self.assertGreater(command.index("-af"), command.index("-i"))
        self.assertEqual(option_values(command, "-af"), ["volume=0.5"])

    def test_default_media_volume_adds_no_filter(self):
        self.assertNotIn("-af", audio_command(self.track(media_volume=100)))

    def test_subtitles_are_ignored_for_audio_only_tracks(self):
        command = audio_command(self.track(subtitle_path="/tmp/sub.srt"))
        self.assertNotIn("-vf", command)

    def test_subtitle_filter_wins_and_keeps_scaling(self):
        """فیلتر ما باید آخرین ‎-vf باشد و مقیاس تصویر را هم نگه دارد."""
        command = video_command(self.track(video=True, subtitle_path="/tmp/subs/movie.srt"))
        filters = option_values(command, "-vf")
        self.assertEqual(len(filters), 2)
        self.assertEqual(filters[-1], "subtitles=/tmp/subs/movie.srt,scale=1280:720")

    def test_subtitle_path_special_characters_survive_shlex(self):
        """`:` و `'` برای ffmpeg فرار می‌خورند و باید بعد از پارس شدن سالم بمانند."""
        track = self.track(video=True, subtitle_path="/tmp/a:b/movie's.srt")
        filters = option_values(video_command(track), "-vf")
        self.assertEqual(filters[-1], "subtitles=/tmp/a\\:b/movie\\'s.srt,scale=1280:720")

    def test_subtitle_path_with_spaces_stays_one_argument(self):
        track = self.track(video=True, subtitle_path="/tmp/my subs/movie.srt")
        filters = option_values(video_command(track), "-vf")
        self.assertEqual(filters[-1], "subtitles=/tmp/my subs/movie.srt,scale=1280:720")

    def test_video_track_without_subtitle_only_has_library_scaling(self):
        command = video_command(self.track(video=True))
        self.assertEqual(option_values(command, "-vf"), ["scale=1280:720"])

    def test_downloaded_file_is_preferred_over_remote_source(self):
        track = self.track(source="https://example.com/x.mp4", file_path="/tmp/x.mp4")
        stream = build_stream(track)
        self.assertEqual(stream._media_path, "/tmp/x.mp4")

    def test_clone_keeps_new_fields(self):
        track = self.track(media_volume=140, subtitle_path="/tmp/s.srt")
        clone = track.clone()
        self.assertEqual(clone.media_volume, 140)
        self.assertEqual(clone.subtitle_path, "/tmp/s.srt")


if __name__ == "__main__":
    unittest.main()
