import unittest
from tests.testing_utils import mocked_requests_post
from transcript_manager import FD_RTT
from unittest import mock

# Our test case class
class TranscriptManager(unittest.TestCase):

    def setUp(self):
        self.fd_rtt = FD_RTT("https://www.youtube.com/watch?v=KWMqeJiIiMo&ab_channel=EpicEconomist", {})

    @mock.patch('requests.post', side_effect=mocked_requests_post)
    def test_get_youtube_meta_data(self, mock_send_discord_msg):
        self.fd_rtt.send_metadata_embed({"id": "KWMqeJiIiMo"}, {"format_id": "mp4", "url": "https://www.youtube.com/watch?v=KWMqeJiIiMo&ab_channel=EpicEconomist", "is_livestream": False})
        mock_send_discord_msg.assert_called_once()

    def test_process_video(self):
        self.fd_rtt.process_video()
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()