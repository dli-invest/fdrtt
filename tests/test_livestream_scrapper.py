# test cases for DB_MANAGER class in database.py using unittest
from random import random
import unittest

from livestream_scrapper import get_html_from_url, get_livestreams_from_html

class DB_LIVESTREAM_SCRAPPER(unittest.TestCase):
    # def setUp(self):
    #     self.db_manager = DB_MANAGER()

    def test_bloomberg_tv(self):
       html = get_html_from_url("https://www.youtube.com/BloombergTV")
       response = get_livestreams_from_html(html)
       assert response[0].get("status") == "LIVE"

    def test_yahoo_finance_tv(self):
        html = get_html_from_url("https://www.youtube.com/c/YahooFinance")
        response = get_livestreams_from_html(html)
        assert response[0].get("status") in ["UPCOMING", "LIVE"]

if __name__ == '__main__':
    unittest.main()
