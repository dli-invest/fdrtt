import unittest
from yt_utils import get_video_metadata, get_youtube_meta_data



# Our test case class
class YTUtils(unittest.TestCase):
    def test_get_video_metadata(self):
        metadata = get_video_metadata("https://www.youtube.com/watch?v=KWMqeJiIiMo&ab_channel=EpicEconomist")
        formats = metadata.get("formats", [])
        # ensure url is available
        assert "url" in formats[0]
        # ensure title is available
        assert "title" in metadata

    def test_get_youtube_meta_data(self):
        metadata = get_youtube_meta_data("https://www.youtube.com/watch?v=KWMqeJiIiMo&ab_channel=EpicEconomist")
        formats = metadata.get("formats", [])
        # ensure url is available
        assert "url" in formats[0]
        # ensure title is available
        assert "title" in metadata

if __name__ == '__main__':
    unittest.main()