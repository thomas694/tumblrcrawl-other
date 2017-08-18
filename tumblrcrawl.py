#!/usr/bin/python

'''
    tumblrcrawl.py - download images and video from tumblr sites
    Copyright (C) 2017 Mark Whittaker

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
import urllib.request
import urllib.error
import xmltodict
import datetime
import datedelta
import subprocess
import re

# Containers to hold filenames
PHOTO_LIST = []
ARIA2C_VIDEO = []
YOUTUBE_DL_VIDEO = []
EXTERNAL_VIDEO = []

# Number of posts to retrieve on each call to Tumblr (default is 20, max is 50)
NUMBER = 50

# Photos, videos or both? 0 = both, 1 = photos, 2 = videos
WANTED = 2

# Regex to filter video filenames
pattern = re.compile(r'.*src="(\S*)" ', re.DOTALL)

def add_to_list(xmldata, beginning, medium):
    flag = True
    
    # Are we prior to our end date
    if medium == "photo":
        # Reply now a dictionary. Look down into <Post> fot the date tag
        try:
            for posts in xmldata['tumblr']['posts']['post']:
                date_of_post = posts['@date-gmt'].split()[0]
                
                if date_of_post > beginning:
                    try:
                        for sets in posts['photoset']['photo']:
                            PHOTO_LIST.append(sets['photo-url'][0]['#text'])
                    except:
                        PHOTO_LIST.append(posts['photo-url'][0]['#text'])
                else:
                    flag = False
        except:
            flag = False
        
    if medium == "video":
        try:
            for posts in xmldata['tumblr']['posts']['post']:
                date_of_post = posts['@date-gmt'].split()[0]
                
                if date_of_post > beginning:
                    try:
                        video_match = pattern.match(posts['video-player'][1]['#text'])
                        video_url = video_match.group(1)
                        
                        if video_url.endswith(("/480", "/720")):
                            video_url = video_url[:-4]
                        
                        if "youtube" in video_url:
                            YOUTUBE_DL_VIDEO.append(video_url)
                        elif "vimeo" in video_url:
                            YOUTUBE_DL_VIDEO.append(video_url)
                        else:
                            ARIA2C_VIDEO.append(video_url)
                    except:
                        EXTERNAL_VIDEO.append(posts['video-source'])
                        #if "instagram" in video_url:
                            #print("DEBUG " + video_url)
                else:
                    flag=False
                
        except:
            flag = False
    
    xmldata = []
    return flag

def parse_instagram(embedded):
    print("Parsing instagram link")
    if embedded.startswith('<iframe'):
        for segment in embedded.split('"'):
            if segment.startswith('//www'):
                insta_page = ("https:" + segment[:-6])
                break
            elif segment.startswith('//instagram'):
                insta_page = ("https://www." + segment[2:-6])
                break
    else:
        insta_page = embedded
    
    try:
        response = urllib.request.urlopen(insta_page)
    except urllib.error.URLError as e:
        sys.stderr.write(e.reason + '\n')
        return
    
    data = response.read().decode("UTF-8")
    m = re.search('og:video" (.+?)>', data, re.DOTALL)
    n = m.group(0).split('"')
    ARIA2C_VIDEO.append(n[2])

def process_external_sites():
    for links in EXTERNAL_VIDEO:
        if "youtube" in links:
            YOUTUBE_DL_VIDEO.append(links)
        elif "instagram" in links:
            parse_instagram(links)

def collect_posts(NUMBER, medium):
    backdate = 0
    proceed = True
    offset = 0
    counter = 0
    data = []
    
    # How far back (in months) to go. 0 is no limit.
    if len(sys.argv) == 3:
        backdate = int(sys.argv[2])
    
    # Only crawl last number of months
    if backdate > 0:
        d = datetime.datetime.today()
        r = d - datedelta.datedelta(months=int(backdate))
        beginning = r.strftime("%Y-%m-%d")
    else:
        beginning = "2012-01-01"
    
    while proceed:
        counter += 1
        print("Getting " + medium +"s page " + str(counter))
        # Get site info from Tumblr
        tumblr_url = "http://{0}.tumblr.com/api/read?type={1}&num={2}&start={3}"
        site_url = tumblr_url.format(sys.argv[1], medium, NUMBER, offset)
        
        try:
            response = urllib.request.urlopen(site_url)
        except urllib.error.URLError as e:
            sys.stderr.write(e.reason + '\n')
            sys.exit(1)
        
        data = xmltodict.parse(response.read())
        proceed = add_to_list(data, beginning, medium)
        offset += NUMBER
    
    
def aria_photo_job(url_list):
    # Not interested in GIFs
    newlist = [ x for x in url_list if x.find(".gif") == -1]
    # Remove duplicates
    newlist = list(set(newlist))
    
    # Write a manifest for aria2c
    with open("manifest", 'w') as f:
        for s in newlist:
            f.write(s + '\n')
    
    # Run aria2c to do the work
    subprocess.call(["aria2c", "-j6", "-i", "manifest", "-s1", "-c", "-d", sys.argv[1]])
    
    # Cleanup
    os.remove("manifest")

def aria_video_job(url_list):
    # Write a manifest for aria2c
    with open("manifest", 'w') as f:
        for s in url_list:
            f.write(s + '\n')
    
    # Run aria2c to do the work
    subprocess.call(["aria2c", "-j4", "-i", "manifest", "-s1", "-c", "-d", sys.argv[1]])
    
    # Cleanup
    os.remove("manifest")

def ytdl_video_job(url_list):
    # Write a manifest for aria2c
    with open("manifest", 'w') as f:
        for s in url_list:
            f.write(s + '\n')
    
    # Output format string to save in sub-directory
    outstring = sys.argv[1] + "/%(title)s-%(id)s.%(ext)s"
    # Run ytdl to do the work
    subprocess.call(["youtube-dl", "-a", "manifest", "-i", "-o", outstring])
    
    # Cleanup
    os.remove("manifest")


if __name__ == "__main__":
    sites = None
    
    if len(sys.argv) < 2:
        sys.stderr.write("I need a tumblr name to crawl\n")
    
    if WANTED != 2:
        collect_posts(NUMBER, "photo")
    
    if WANTED != 1:
        collect_posts(NUMBER, "video")
    
    
    if EXTERNAL_VIDEO:
        process_external_sites()
    
    for i in ARIA2C_VIDEO:
        print(i)
    #for i in YOUTUBE_DL_VIDEO:
        #print("YTDL")
        #print(i)
    
    
    if PHOTO_LIST:
        aria_photo_job(PHOTO_LIST)
    
    #if ARIA2C_VIDEO:
        #aria_video_job(ARIA2C_VIDEO)
    
    #if YOUTUBE_DL_VIDEO:
        #ytdl_video_job(YOUTUBE_DL_VIDEO)
    print(len(ARIA2C_VIDEO))
    print(len(YOUTUBE_DL_VIDEO))
