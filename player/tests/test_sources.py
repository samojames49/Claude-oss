import unittest

from player.platforms import live, spotify, youtube


class TestYoutubeHelpers(unittest.TestCase):
    def test_is_youtube_url(self):
        self.assertTrue(youtube.is_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
        self.assertTrue(youtube.is_youtube_url("https://youtu.be/dQw4w9WgXcQ"))
        self.assertTrue(youtube.is_youtube_url("https://music.youtube.com/watch?v=dQw4w9WgXcQ"))
        self.assertFalse(youtube.is_youtube_url("https://soundcloud.com/artist/track"))
        self.assertFalse(youtube.is_youtube_url("شادمهر عقیلی"))

    def test_video_id(self):
        self.assertEqual(
            youtube.video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ"), "dQw4w9WgXcQ"
        )
        self.assertEqual(youtube.video_id("https://youtu.be/dQw4w9WgXcQ"), "dQw4w9WgXcQ")
        self.assertEqual(
            youtube.video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ"), "dQw4w9WgXcQ"
        )
        self.assertIsNone(youtube.video_id("just a song name"))

    def test_is_url(self):
        self.assertTrue(youtube.is_url("https://example.com/a.mp3"))
        self.assertFalse(youtube.is_url("music please"))

    def test_playlist_detection(self):
        self.assertTrue(youtube.is_playlist_url("https://www.youtube.com/playlist?list=PL123"))
        self.assertFalse(
            youtube.is_playlist_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PL123")
        )

    def test_thumbnail_url(self):
        self.assertIn("dQw4w9WgXcQ", youtube.thumbnail_url("dQw4w9WgXcQ"))
        self.assertIsNone(youtube.thumbnail_url(None))

    def test_watch_url(self):
        self.assertEqual(
            youtube.watch_url("dQw4w9WgXcQ"), "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )


class TestLiveHelpers(unittest.TestCase):
    def test_live_urls(self):
        self.assertTrue(live.is_live_url("https://radio.example/stream.m3u8"))
        self.assertTrue(live.is_live_url("https://radio.example/live.mpd"))
        self.assertFalse(live.is_live_url("https://cdn.example/song.mp3"))

    def test_direct_media(self):
        self.assertTrue(live.is_direct_media_url("https://cdn.example/song.mp3"))
        self.assertTrue(live.is_direct_media_url("https://cdn.example/clip.mp4"))
        self.assertFalse(live.is_direct_media_url("https://example.com/page.html"))

    def test_streamable(self):
        self.assertTrue(live.is_streamable_url("https://cdn.example/a.flac"))
        self.assertFalse(live.is_streamable_url("https://example.com/"))

    def test_title_from_url(self):
        self.assertEqual(live.title_from_url("https://cdn.example/my_song-name.mp3"), "my song name")
        self.assertEqual(live.title_from_url("https://radio.example"), "radio.example")


class TestSpotifyHelpers(unittest.TestCase):
    def test_detection(self):
        self.assertTrue(spotify.is_spotify_url("https://open.spotify.com/track/abc123"))
        self.assertTrue(
            spotify.is_spotify_url("https://open.spotify.com/intl-de/track/abc123?si=1")
        )
        self.assertFalse(spotify.is_spotify_url("https://youtube.com/watch?v=x"))

    def test_kind(self):
        self.assertEqual(spotify.link_kind("https://open.spotify.com/album/abc"), "album")
        self.assertIsNone(spotify.link_kind("nope"))


if __name__ == "__main__":
    unittest.main()
