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
from dispatch_another_event import dispatch_github_event
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
        livestream_data = []
        first_section = soup.find("ytd-item-section-renderer")

        title_wrapper = first_section.find("ytd-channel-video-player-renderer")
        if title_wrapper == None:
            watch_link = first_section.find("a", {"class": "yt-simple-endpoint style-scope ytd-video-renderer"})
            watch_url = watch_link.get("href")
        else:
            channel_title = title_wrapper.find("yt-formatted-string")
            watch_link = channel_title.find("a")
            watch_url = watch_link.get("href")
        # get video_id <a id="thumbnail" class="yt-simple-endpoint inline-block style-scope ytd-thumbnail" aria-hidden="true" tabindex="-1" rel="null" href="/watch?v=wl1p_H6ckt4">
        # https://www.youtube.com/BloombergTV style-scope ytd-thumbnail-overlay-time-status-renderer
        ytd_thumbnail_overlay_time_status_renderer = first_section.find("ytd-thumbnail-overlay-time-status-renderer")
        # try to find ytd-video-renderer and get href

        if ytd_thumbnail_overlay_time_status_renderer is None:
            # try to grab upcoming livestream
            scheduled_text = first_section.find("ytd-video-meta-block")
            run_time = scheduled_text.get_text()
            # parse strings like August 22 at 6:00 AM
            # remove words like at
            run_str = run_time.replace("Scheduled for", "").strip()
            parsed_date =  dateparser.parse(run_str)
            # save to sql table and/or check if date exists
            # channel, date, status /upcoming
            # todo return channel data + status
            # get watch url 
            # find element
            livestream_data.append({"date": parsed_date, "status": "UPCOMING", "watch_url": watch_url})
        else:
            livestream_label = ytd_thumbnail_overlay_time_status_renderer.get_text()
            if livestream_label is not None:
                livestream_data.append({"date": None, "status": livestream_label.strip(), "watch_url": watch_url})
        return livestream_data
    except Exception as e:
        print(e)
        print("Error getting data from url")
        return []


def get_webdriver():
    remote_url = os.environ.get("REMOTE_SELENIUM_URL")
    if remote_url is None:
        raise Exception("Missing REMOTE_SELENIUM_URL in env vars")
    return webdriver.Remote(
        command_executor=remote_url,
    )

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
    # TODO expand this to get all channels from config file, probably ini file
    # html = get_html_from_url("https://www.youtube.com/c/YahooFinance")
    html = get_html_from_url("https://www.youtube.com/c/YahooFinance")
    # html = get_html_from_url("https://www.youtube.com/BloombergTV")
    # TODO fix code so it works for upcoming livestreams that arent periodic
    livestream_data = get_livestreams_from_html(html)

    base_url = "https://www.youtube.com"
    # check if LIVE or UPCOMING
    for livestream in livestream_data:
        if livestream["status"] == "LIVE":
            print("LIVE")
            youtube_url = base_url + livestream["watch_url"]
            data = {"youtube_url": youtube_url, "iteration": -1, "table_name": "YahooFinance"}
            print(data)
            dispatch_github_event(data)
        elif livestream["status"] == "UPCOMING":
            print("UPCOMING")
            print("NO UPCOMING STUFF")
            exit(0)
        else:
            print("NONE")
            exit(1)
