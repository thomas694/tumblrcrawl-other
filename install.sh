#!/bin/sh

/usr/bin/python3 -c "import bs4" 2>/dev/null

if [ $? == 1 ]; then
    echo "TumblrCrawl requires Python3 BeautifulSoup."
    echo "Install from your Package Manager or try running 'pip install beautifulsoup4' as super user."
    exit 1
fi

/usr/bin/python3 -c "from PyQt5.QtCore import QCoreApplication"

if [ $? == 1 ]; then
    echo "TumblrCrawl requires Python Qt5."
    echo "Check your package manager."
    exit 1
fi

which aria2c 2>/dev/null >/dev/null

if [ $? == 1 ]; then
    echo "TumblrCrawl requires aria2c to download from Tumblr."
    echo "Check your package manager or look here:"
    echo "https://aria2.github.io/"
    exit 1
fi

which youtube-dl 2>/dev/null >/dev/null

if [ $? == 1 ]; then
    echo "TumblrCrawl requires youtube-dl to download external videos."
    echo "Install from your Package Manager or try running 'pip install youtube-dl' as super user."
    exit 1
fi

FLAG=0

cp -v --remove-destination tumblrcrawl_2.py /usr/bin
if [ $? == 1 ]; then FLAG=1; fi
cp -v --remove-destination TumblrCrawler /usr/bin
if [ $? == 1 ]; then FLAG=1; fi
cp -v --remove-destination tumblrcrawl.png /usr/share/icons/hicolor/256x256/apps
if [ $? == 1 ]; then FLAG=1; fi
cp -v --remove-destination tumblrcrawl.desktop /usr/share/applications
if [ $? == 1 ]; then FLAG=1; fi

if [ $FLAG == 1 ]; then
    echo -e "\033[31mSomething's not quite right. Did you run me as sudo?\033[0m"
    exit 1
fi

echo -e "\033[32mThat went well, didn't it.\033[0m"
