# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# Plugin for download and watch videos of youtube
# -----------------------------------------------------------------------
# $Id$
#
# Notes:
#    You need to install:
#    youtube-dl from http://www.arrakis.es/~rggi3/youtube-dl/
#    and
#    gdata from http://code.google.com/p/gdata-python-client/
#
#    thanks to Sylvain Fabre (cinemovies_trailers.py)
#    and David Sotelo (universal_newlines=1)
#
#    To activate, put the following line in local_conf.py:
#       plugin.activate('video.youtube')
#       YOUTUBE_VIDEOS = [
#           ('user1', 'description1'),
#           ('user2', 'description2'),
#           ...
#       ]
#       YOUTUBE_DIR = '/tmp/'
#
# ToDo:
#
# -----------------------------------------------------------------------
#
# Freevo - A Home Theater PC framework
# Copyright (C) 2002 Krister Lagerstrom, et al.
# Please see the file freevo/Docs/CREDITS for a complete list of authors.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MER-
# CHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# -----------------------------------------------------------------------

__author__           = 'Author Alberto Gonz�lez'
__author_email__     = 'alberto@pesadilla.org'
__maintainer__       = __author__
__maintainer_email__ = __author_email__
__version__          = '0.1b'

import os
import plugin
import gdata.service
import urllib2
import re
import traceback
import menu
import video
import config
import string, os, subprocess, util

from video.videoitem import VideoItem
from subprocess import Popen
from item import Item
from gui.PopupBox import PopupBox

try:
    from xml.etree import cElementTree as ElementTree
except ImportError:
    try:
        import cElementTree as ElementTree
    except ImportError:
        from elementtree import ElementTree


class PluginInterface(plugin.MainMenuPlugin):
    """
    Download and watch youtube video

    prerequisites are:
    U(youtube-dl <http://www.arrakis.es/~rggi3/youtube-dl/>
    U(gdata <http://code.google.com/p/gdata-python-client/>

    Activate:
    | plugin.activate('video.youtube')
    |
    | YOUTUBE_VIDEOS = [
    |     ('user1', 'description1'),
    |     ('user2', 'description2'),
    |     ...
    | ]
    | YOUTUBE_DIR = '/tmp/'
    """
    def __init__(self):
        if not config.USE_NETWORK:
            self.reason = 'USE_NETWORK not enabled'
            return
        if not config.YOUTUBE_VIDEOS:
            self.reason = 'YOUTUBE_VIDEOS not defined'
            return
        plugin.MainMenuPlugin.__init__(self)

        if not os.path.isdir(config.YOUTUBE_DIR):
            os.mkdir(config.YOUTUBE_DIR, stat.S_IMODE(os.stat(config.FREEVO_CACHEDIR)[stat.ST_MODE]))


    def config(self):
        """returns the config variables used by this plugin"""
        return [
            ('YOUTUBE_VIDEOS', None, 'id and description to get/watch videos of youtube'),
            ('YOUTUBE_DIR', config.FREEVO_CACHEDIR + '/youtube', 'directory to save youtube videos'),
            ('YOUTUBE-DL', 'youtube-dl', 'The you tube downloader'),
        ]


    def items(self, parent):
        return [ YoutubeVideo(parent) ]



class YoutubeVideoItem(VideoItem):
    """Create a VideoItem for play"""

    def __init__(self, name, url, parent):
        VideoItem.__init__(self, url, parent)
        self.name = name
        self.type = 'youtube'



class YoutubeVideo(Item):
    """Main Class"""

    def __init__(self, parent):
        # look for a default player
        for p in plugin.getbyname(plugin.VIDEO_PLAYER, True):
            if config.VIDEO_PREFERED_PLAYER == p.name:
                self.player = p
        Item.__init__(self, parent)
        self.name = _('Youtube videos')
        self.type = 'youtube'


    def actions(self):
        """Only one action, return user list"""
        return [ (self.userlist, 'Video youtube') ]


    def userlist(self, arg=None, menuw=None):
        """Menu for choose user"""
        users = []
        for user, description in config.YOUTUBE_VIDEOS:
            users.append(menu.MenuItem(description, self.videolist, (user, description)))
        menuw.pushmenu(menu.Menu(_('Choose please'), users))


    def videolist(self, arg=None, menuw=None):
        """Menu for video"""
        items = video_list(self, _('Retrieving video list'), arg[0])
        menuw.pushmenu(menu.Menu(_('Videos available'), items))


    def downloadvideo(self, arg=None, menuw=None):
        """Download video (if necessary) and watch it"""
        filename =  config.YOUTUBE_DIR + '/' + arg[1].replace('-', '_') + '.flv'
        if not os.path.exists(filename):
            box = PopupBox(text=_('Downloading video'), width=950)
            cmd = config.YOUTUBE_DL + ' -o ' + config.YOUTUBE_DIR + '/' + arg[1].replace('-', '_')
            cmd += '.flv "http://www.youtube.com/watch?v=' + arg[1] + '"'
            proceso = Popen(cmd, shell=True, bufsize=1024, stdout=subprocess.PIPE, universal_newlines=1)
            follow = proceso.stdout
            while proceso.poll() == None:
                mess = follow.readline()
                if mess:
                    if len(mess.strip()) > 0:
                        box.label.text=mess.strip()
                        box.show()
            box.destroy()

        # Create a fake VideoItem
        playvideo2 = YoutubeVideoItem(_('bla'), filename, self)
        playvideo2.player = self.player
        playvideo2.player_rating = 10
        playvideo2.menuw = menuw
        playvideo2.play()


def video_list(parent, title, user):
    """Get the video list for a specific user"""
    items = []
    feed = 'http://gdata.youtube.com/feeds/users/' + user + '/uploads?orderby=updated'

    service = gdata.service.GDataService(server='gdata.youtube.com')
    box = PopupBox(text=_('Loading video list'))
    box.show()
    for video in service.GetFeed(feed).entry:
        date = video.published.text.split("T")
        id = video.link[1].href.split("watch?v=");
        mi = menu.MenuItem(date[0] + " " + video.title.text, parent.downloadvideo, id[1])
        mi.arg = (video.title.text, id[1])
        text = util.htmlenties2txt(video.content)
        mi.description = re.search('<span>([^\<]*)<',text).group(1)
        tempimage = re.search('src="([^\"]*)"',text).group(1)
        file = config.YOUTUBE_DIR + "/" + id[1].replace("-","_") + ".jpg"
        if not os.path.exists(file):
            aimage = urllib.urlretrieve(tempimage,file)
        mi.image = file
        items.append(mi)
    box.destroy()
    return items