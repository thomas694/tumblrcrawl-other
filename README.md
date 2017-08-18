# tumblrcrawl
Download images and videos from  Tumblr sites. It will also grab embedded video from YouTube, Vimeo and Instagram. Requires aria2c and youtube-dl.
## Installation
Copy tumblrcrawl.py into your $PATH and set it executable (chmod -v 755 tumblrcrawl.py)
## Usage

```
tumblrcrawl.py tumblrname [months] [p] [v]
```

tumblrname (required) is the site you want to crawl. Optional arguments are:
1. months (number) - only grab the most recent number of months
2. p - only grab photos
3. v - only grab videos

Files will be written to a sub-directory named from the Tumblr site.
