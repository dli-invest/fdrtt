"""
author: David Li
description: grab livestream data from url using selenium, (need a browser for youtube)
create database entries to track livestreams, check if livestream is live or upcoming and exclude certain channels with never ending livestreams.
"""

import bs4
import time
from selenium import webdriver
import os
import dateparser
# requirements.livestream.txt for requirements


def get_livestreams_from_html(data: str):
    """
        gets livestream from html from youtube channel and determines if it is live or upcoming.

        Returns dict:
          time: time of livestream
          channel: channel name
          status: LIVE or UPCOMING or none
    """
    # get text data from url using requests
    try:
        # data = requests.get(channel_url, timeout=(15.05, 15)).text
        # # data to html file
        # with open("data.html", "w") as f:
        #     f.write(data)
        #     f.close()
        soup = bs4.BeautifulSoup(data, "html.parser")
        # find html tag named <ytd-channel-featured-content-renderer>
        # style-scope ytd-thumbnail-overlay-time-status-renderer
        # #contents //*[@id="contents"]
        #   yt-simple-endpoint inline-block style-scope ytd-thumbnail
        # featured_content = soup.find("div", {"id": "ytd-channel-featured-content-renderer" })
        # if featured_content == None:
        #     return None
        # find section-list-renderer
        first_section = soup.find("ytd-item-section-renderer")
        # https://www.youtube.com/BloombergTV style-scope ytd-thumbnail-overlay-time-status-renderer
        ytd_thumbnail_overlay_time_status_renderer = first_section.find("ytd-thumbnail-overlay-time-status-renderer")
        if ytd_thumbnail_overlay_time_status_renderer == None:
            # try to grab upcoming livestream
            scheduled_text = first_section.find("ytd-video-meta-block")
            run_time = scheduled_text.get_text()
            # parse strings like August 22 at 6:00 AM
            # remove words like at
            run_str = run_time.replace("Scheduled for", "").strip()
            parsed_date =  dateparser.parse(run_str)
            print(parsed_date)
            # save to sql table and/or check if date exists
            # channel, date, status /upcoming
            # todo return channel data + status
        else:
            livestream_label = ytd_thumbnail_overlay_time_status_renderer.get_text()
            if livestream_label is not None:
                print(livestream_label.strip())
                return livestream_label.strip()
    except Exception as e:
        print(e)
        print("Error getting data from url")
        return None
    # //*[@id="overlays"]/ytd-thumbnail-overlay-time-status-renderer


def get_webdriver():
    remote_url = os.environ.get("REMOTE_SELENIUM_URL")
    if remote_url == None:
        raise Exception("Missing REMOTE_SELENIUM_URL in env vars")
    driver = webdriver.Remote(
        command_executor=remote_url,
    )
    return driver

def get_html_from_url(url: str):
    """
        gets html from url
    """
    # get text data from url using requests
    driver = get_webdriver()
    driver.get(url)
    time.sleep(10)
    # return html from page source
    return driver.page_source

if __name__ == "__main__":
    # html = get_html_from_url("https://www.youtube.com/c/YahooFinance")
    html = get_html_from_url("https://www.youtube.com/BloombergTV")
    get_livestreams_from_html(html)