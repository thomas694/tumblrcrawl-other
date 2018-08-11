#!/usr/bin/python3

import sys

from urllib.request import urlopen
from bs4 import BeautifulSoup

def get_photo_urls(posts):

    photos = posts.find_all("photo-url", {"max-width" : "1280"})
#    print(photos)
    photo_url_list = []

    for i in photos:
        tmp = i.get_text()
        
        if not tmp.endswith("gif"):
            photo_url_list.append(tmp)

    photo_url_set = set(photo_url_list)

    for photo_url in photo_url_set:
        print(photo_url)


url = "https://pupaegis.tumblr.com/api/read?type=photo&num=60&start=0"

try:
    tumblr_doc = urlopen(url)
except:
    print("Failed to load")
    sys.exit(1)

soup = BeautifulSoup(tumblr_doc, 'lxml')


photo_posts = []

posts = soup.find_all("post")

for i in posts:
    tmp = i.attrs.get("date-gmt")
    post_date = tmp[:10]

    if post_date >= "2018-08-01":
        tmp_string = str(i)
        photo_posts.append(tmp_string)

photo_posts_list = BeautifulSoup(''.join(photo_posts), 'lxml')

get_photo_urls(photo_posts_list)
