import argparse
import requests
import unittest
from dispatch_another_event import dispatch_github_event 
from unittest import mock
from tests.testing_utils import mocked_requests_post

    # return MockResponse(None, 404)

# Our test case class
class DispatchGithubEvents(unittest.TestCase):
    @mock.patch('requests.post', side_effect=mocked_requests_post)
    def test_fetch(self, mock_post):
        dispatch_github_event(vars(argparse.Namespace(youtube_url="https://www.youtube.com/watch?v=KWMqeJiIiMo&ab_channel=EpicEconomist", iteration="0", url="https://api.github.com/repos/dli-invest/fdrtt/actions/workflows/transcribe_video.yml/dispatches")))
        # We patch 'requests.get' with our own method. The mock object is passed in to our test case method.
        # We can even assert that our mocked method was called with the right parameters
        print(mock_post.call_args_list)
        # check for url in mock
        self.assertEqual(mock_post.call_args_list[0][0][0], "https://api.github.com/repos/dli-invest/fdrtt/actions/workflows/transcribe_video.yml/dispatches")
        # check for youtube url
        self.assertEqual(mock_post.call_args_list[0][1]['json']['inputs']['youtube_url'], "https://www.youtube.com/watch?v=KWMqeJiIiMo&ab_channel=EpicEconomist")
        # self.assertIn(mock.call('https://api.github.com/repos/dli-invest/fdrtt/actions/workflows/transcribe_video.yml/dispatches'), mock_post.call_args_list)

        self.assertEqual(len(mock_post.call_args_list), 1)

if __name__ == '__main__':
    unittest.main()