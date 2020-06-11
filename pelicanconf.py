#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = "Jim Pudar"
SITENAME = "pudar.net"
# SITESUBTITLE = "Jim Pudar's personal weblog"
SITEURL = ""

# THEME = "../pelican-themes/pelican-simplegrey"
# THEME = "simple"

PATH = "content"

TIMEZONE = "America/Detroit"

DEFAULT_LANG = "en"

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

STATIC_PATHS = ["favicon"]
EXTRA_PATH_METADATA = {
    "favicon/android-chrome-192x192.png": {"path": "android-chrome-192x192.png"},
    "favicon/android-chrome-512x512.png": {"path": "android-chrome-512x512.png"},
    "favicon/apple-touch-icon.png": {"path": "apple-touch-icon.png"},
    "favicon/favicon.ico": {"path": "favicon.ico"},
    "favicon/favicon-16x16.png": {"path": "favicon-16x16.png"},
    "favicon/favicon-32x32.png": {"path": "favicon-32x32.png"},
    "favicon/site.webmanifest": {"path": "site.webmanifest"},
}

# Blogroll
# LINKS = (
#     ("Pelican", "http://getpelican.com/"),
#     ("Python.org", "http://python.org/"),
#     ("Jinja2", "http://jinja.pocoo.org/"),
#     ("You can modify those links in your config file", "#"),
# )

# Social widget
# SOCIAL = (("You can add links in your config file", "#"), ("Another social link", "#"))

DEFAULT_PAGINATION = 10

# Uncomment following line if you want document-relative URLs when developing
# RELATIVE_URLS = True

DISPLAY_PAGES_ON_MENU = True

PLUGIN_PATHS = ["../pelican-plugins"]
PLUGINS = ["photos"]

PHOTO_LIBRARY = "./content/images"
PHOTO_GALLERY = (1024, 786, 80)
PHOTO_ARTICLE = (760, 506, 80)
PHOTO_THUMB = (192, 144, 60)
PHOTO_SQUARE_THUMB = False
PHOTO_RESIZE_JOBS = -1
PHOTO_WATERMARK = True
PHOTO_WATERMARK_TEXT = "pudar.net"
# PHOTO_WATERMARK_IMG = ''
PHOTO_EXIF_KEEP = False
PHOTO_EXIF_REMOVE_GPS = True
PHOTO_EXIF_COPYRIGHT = "CC-BY-NC-ND"
PHOTO_EXIF_COPYRIGHT_AUTHOR = "Jim Pudar"
