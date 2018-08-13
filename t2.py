#!/usr/bin/python3

'''
    tumblrcrawl.py - download images and video from tumblr sites
    Copyright (C) 2018 Mark Whittaker

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''

import sys
import os
import subprocess
import urllib.error
import datetime
import datedelta
import signal
import re
from urllib.request import urlopen
from bs4 import BeautifulSoup
from multiprocessing import Pool


SAVE_PATH = os.getcwd()

# Functions -----------------------------------------------------------------
def get_video_url(video_player):
    video_location = []
    video_player_soup = BeautifulSoup(''.join(video_player), 'lxml')
    tumblr_vid = video_player_soup.find_all("source")

    if tumblr_vid == []:
        external_vid = []
        external_vid = video_player_soup.find_all("iframe")

        if not external_vid:
            print("DB", external_vid)
            return  ["", ""]

        tmp =  external_vid[0].attrs.get("src")

        if 'vimeo' or 'youtu' in tmp:
            tmp = tmp.split('?')[0]

        video_location = ["ytdl", tmp]
    else:
        src = tumblr_vid[0].attrs.get("src")
    
        if src.endswith("/480"):
            src = src[:-4]

        src = "".join((src, "/720"))
        video_location = ["tumblr", src]

    return video_location


def process_videos(posts_list):
    vids_list = []
    video_posts_list = BeautifulSoup(''.join(posts_list), 'lxml')
    videos = video_posts_list.find_all("video-player", {"max-width" : "500"})
    vids_list = [get_video_url(i) for i in videos if videos]

    regular = []
    regular = video_posts_list.find_all("regular-body")
    [vids_list.append(get_video_url(i)) for i in regular if regular]

    for i in vids_list:
        print(i)
#    print(get_video_urls(videos[0]))

def get_photo_urls(posts):
    photos = posts.find_all("photo-url", {"max-width" : "1280"})
    photo_url_list = []

    for i in photos:
        tmp = i.get_text()
        
        if not tmp.endswith("gif"):
            photo_url_list.append(tmp)

    photo_url_set = set(photo_url_list)

    return photo_url_set


def generate_posts_list(tumblr, date_wanted, media):
    flag = True
    posts_list = []
    counter = 1
    offset = 0

    while(flag):
        url = "https://{0}.tumblr.com/api/read?type={1}&num=50&start={2}"
        url = url.format(sys.argv[1], media, offset)
        print("Getting {0}s Page {1}".format(media.capitalize(),counter))

        try:
            tumblr_doc = urlopen(url)
        except urllib.error.URLError as e:
                sys.exit("\033[31m" + str(e.reason) + "\033[0m" + "\n")

        soup = BeautifulSoup(tumblr_doc, 'lxml')
        posts = soup.find_all("post")

        for i in posts:
            tmp = i.attrs.get("date-gmt")
            post_date = tmp[:10]

            if post_date >= date_wanted:
                tmp_string = str(i)
                posts_list.append(tmp_string)
            else:
                flag =False

        offset += 50
        counter += 1

    return posts_list


def process_photos(posts_list):
    photo_posts_list = BeautifulSoup(''.join(posts_list), 'lxml')
    final_set = get_photo_urls(photo_posts_list)
    print("\033[33mCollecting {0} Photos\033[0m".format(len(final_set)))
    photos_save_path = os.path.join(SAVE_PATH, "photos")
    manifest = os.path.join(photos_save_path, "aria_photo_manifest")

    try:
        os.makedirs(photos_save_path, exist_ok = True)
    except OSError as e:
        sys.exit("Terminating: ".format(e))

    with open(manifest, 'wt') as f:
        [f.write(u + '\n') for u in final_set if final_set]

    subprocess.call(["aria2c", "-j8", "-i", manifest,
                     "--console-log-level=warn",
                     "--summary-interval=0",
                     "--download-result=hide",
                     "-c", "-d", photos_save_path])
    print()
    os.remove(manifest)


def sigint_handler(signal, frame):
    cleanup = glob.glob(os.path.join(SAVE_PATH,  "*manifest"))
    for i in cleanup:
        os.remove(i)


def usage():
    print("""\033[33m\nUsage: tumblrcrawl.py TumblrName [v] [p] [{num}]\033[36m\n
Name is required. If only name is given, tumblrcrawl.py will collect
all photos and videos on site. Limit the collection with 
the following options:
   v - videos only
   p - photos only
   {num} - (a number) only collect the last {num} number of months
           e.g. current month is 1\n\033[0m""")



# Begin Here -----------------------------------------------------------------
if len(sys.argv) < 2:
    usage()
    sys.exit(1)

signal.signal(signal.SIGINT, sigint_handler)
signal.signal(signal.SIGQUIT, sigint_handler)

all_args = sys.argv[2:]
media_wanted = 0

for arg in all_args:
    try:
        months_wanted = int(arg)
    except:
        if arg == 'p':
            media_wanted = 1
        elif arg == 'v':
            media_wanted = 2

if months_wanted > 0:
    d = datetime.datetime.today()
    r = d - datedelta.datedelta(months = months_wanted - 1)
    beginning = r.strftime("%Y-%m") + "-01"
else:
    beginning = "2012-01-01"

print(
"\n\033[32m---<Tumblr Crawl>-----<Ctrl+C to abort>---------\033[0m")
check_url = "http://{0}.tumblr.com/api/read?start=0".format(sys.argv[1])
print("\033[33mChecking Tumblr {0}... \033[0m".format(sys.argv[1]),
        end = '', flush = True)

try:
    response = urlopen(check_url)
except urllib.error.URLError as e:
        sys.exit("\033[31m" + e.reason + "\033[0m" + "\n")

print("\033[32mOK \033[0m")
SAVE_PATH = os.path.join(SAVE_PATH, sys.argv[1])

try:
    os.makedirs(SAVE_PATH, exist_ok=True)
    print("\033[33mSaving to: {0}\033[0m".format(SAVE_PATH))
except OSError as e:
    sys.exit("\033[31mTerminating> {0}\033[0m".format(e))

if media_wanted != 2:
    wanted_posts = generate_posts_list(sys.argv[1], beginning, "photo")
    process_photos(wanted_posts)

if media_wanted != 1:
    wanted_posts = generate_posts_list(sys.argv[1], beginning, "video")
    process_videos(wanted_posts)
