#if 0 /*
# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# main.py - This is the Freevo main application code
# -----------------------------------------------------------------------
# $Id$
#
# Notes:
# Todo:        
#
# -----------------------------------------------------------------------
# $Log$
# Revision 1.91  2003/11/22 16:06:06  dischi
# use drawstringframed to center shutdown message
#
# Revision 1.90  2003/11/16 17:41:04  dischi
# i18n patch from David Sagnol
#
# Revision 1.89  2003/11/16 14:35:08  dischi
# better help doc when deps are missing
#
# Revision 1.88  2003/11/16 10:18:10  dischi
# add -dpms for xset
#
# Revision 1.87  2003/11/02 09:01:28  dischi
# check for missing libs on startup
#
# Revision 1.86  2003/10/27 20:38:30  dischi
# cleaner shutdown
#
# Revision 1.85  2003/10/23 17:58:14  dischi
# kill/stop threads before exit
#
# Revision 1.84  2003/10/23 17:28:41  dischi
# correct shutdown
#
# Revision 1.83  2003/10/20 19:32:33  dischi
# catch exception caused by eventhandlers
#
# Revision 1.82  2003/10/19 11:17:38  dischi
# move gettext into config so that everything has _()
#
# -----------------------------------------------------------------------
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
# ----------------------------------------------------------------------- */
#endif

# Must do this here to make sure no os.system() calls generated by module init
# code gets LD_PRELOADed
import os
os.environ['LD_PRELOAD'] = ''

import sys, time
import traceback


# i18n support

# First load the xml module. It's not needed here but it will mess
# up with the domain we set (set it from freevo 4Suite). By loading it
# first, Freevo will override the 4Suite setting to freevo

try:
    from xml.utils import qp_xml
    from xml.dom import minidom
    
    # now load other modules to check if all requirements are installed
    import mmpython
    import Image
    import pygame
    import twisted
    
except ImportError, i:
    print 'Can\'t find all Python dependencies:'
    print i
    print
    print 'Not all requirements of Freevo are installed on your system.'
    print 'Please check the INSTALL file for more informations.'
    print
    print 'A quick solution is to install the Freevo runtime. This contains'
    print 'all Python dependencies to run Freevo. Get the current runtime at'
    print 'http://sourceforge.net/project/showfiles.php?group_id=46652&release_id=194955'
    print 'After downloading, run \'./freevo install path-to-runtime.tgz\'.'
    print
    print 'The runtime doesn\'t contain external applications like mplayer, xine'
    print 'or tvtime. You need to download and install them, too (all except'
    print 'mplayer are optional).'
    print
    sys.exit(0)

    
import config

import util    # Various utilities
import osd     # The OSD class, used to communicate with the OSD daemon
import menu    # The menu widget class
import skin    # The skin class
import rc      # The RemoteControl class.

import signal

from item import Item
from event import *

skin    = skin.get_singleton()


# Create the remote control object
rc_object = rc.get_singleton()

# Create the OSD object
osd = osd.get_singleton()

# Create the MenuWidget object
menuwidget = menu.get_singleton()


def shutdown(menuw=None, arg=None, allow_sys_shutdown=True, exit=False):
    """
    function to shut down freevo or the whole system
    """

    if not osd.active:
        # this function is called from the signal handler, but
        # we are dead already.
        sys.exit(0)

    import plugin
    import childapp
    osd.clearscreen(color=osd.COL_BLACK)
    osd.drawstringframed(_('shutting down...'), 0, 0, osd.width, osd.height,
                         osd.getfont(config.OSD_DEFAULT_FONTNAME,
                                     config.OSD_DEFAULT_FONTSIZE),
                         fgcolor=osd.COL_ORANGE, align_h='center', align_v='center')
    osd.update()

    time.sleep(0.5)

    if arg == None:
        sys_shutdown = allow_sys_shutdown and 'ENABLE_SHUTDOWN_SYS' in dir(config)
    else:
        sys_shutdown = arg

    # XXX temporary kludge so it won't break on old config files
    if sys_shutdown:  
        if config.ENABLE_SHUTDOWN_SYS:
            # shutdown dual head for mga
            if config.CONF.display == 'mga':
                os.system('%s runapp matroxset -f /dev/fb1 -m 0' % \
                          os.environ['FREEVO_SCRIPT'])
                time.sleep(1)
                os.system('%s runapp matroxset -f /dev/fb0 -m 1' % \
                          os.environ['FREEVO_SCRIPT'])
                time.sleep(1)

            plugin.shutdown()
            childapp.shutdown()
            osd.shutdown()

            os.system(config.SHUTDOWN_SYS_CMD)
            # let freevo be killed by init, looks nicer for mga
            while 1:
                time.sleep(1)
            return

    #
    # Exit Freevo
    #
    
    # Shutdown any daemon plugins that need it.
    plugin.shutdown()

    # Shutdown all children still running
    childapp.shutdown()

    # SDL must be shutdown to restore video modes etc
    osd.clearscreen(color=osd.COL_BLACK)
    osd.shutdown()

    if exit:
        # realy exit, we are called by the signal handler
        sys.exit(0)

    os.system('%s stop' % os.environ['FREEVO_SCRIPT'])

    # Just wait until we're dead. SDL cannot be polled here anyway.
    while 1:
        time.sleep(1)
        


def get_main_menu(parent):
    """
    function to get the items on the main menu based on the settings
    in the skin
    """

    import plugin

    items = []
    for p in plugin.get('mainmenu'):
        items += p.items(parent)
        
    return items
    

class SkinSelectItem(Item):
    """
    Item for the skin selector
    """
    def __init__(self, parent, name, image, skin):
        Item.__init__(self, parent)
        self.name  = name
        self.image = image
        self.skin  = skin
        
    def actions(self):
        return [ ( self.select, '' ) ]

    def select(self, arg=None, menuw=None):
        """
        Load the new skin and rebuild the main menu
        """
        skin.settings = skin.LoadSettings(self.skin, copy_content = False)
        pos = menuw.menustack[0].choices.index(menuw.menustack[0].selected)
        menuw.menustack[0].choices = get_main_menu(self.parent)
        menuw.menustack[0].selected = menuw.menustack[0].choices[pos]
        menuw.back_one_menu()

        
class MainMenu(Item):
    """
    this class handles the main menu
    """
    
    def getcmd(self):
        """
        Setup the main menu and handle events (remote control, etc)
        """
        
        items = get_main_menu(self)

        mainmenu = menu.Menu(_('Freevo Main Menu'), items, item_types='main', umount_all = 1)
        menuwidget.pushmenu(mainmenu)
        osd.add_app(menuwidget)

    def eventhandler(self, event = None, menuw=None, arg=None):
        """
        Automatically perform actions depending on the event, e.g. play DVD
        """

        # pressing DISPLAY on the main menu will open a skin selector
        # (only for the new skin code)
        if event == MENU_CHANGE_STYLE:
            items = []
            for name, image, skinfile in skin.GetSkins():
                items += [ SkinSelectItem(self, name, image, skinfile) ]

            menuwidget.pushmenu(menu.Menu('SKIN SELECTOR', items))
            return True

        # give the event to the next eventhandler in the list
        return Item.eventhandler(self, event, menuw)
        
    

def signal_handler(sig, frame):
    if sig in (signal.SIGTERM, signal.SIGINT):
        shutdown(allow_sys_shutdown=0, exit=True)

#
# Main init
#
def main_func():
    import plugin

    if hasattr(skin, 'Splashscreen'):
        plugin.init(skin.Splashscreen().progress)
    else:
        plugin.init()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    main = MainMenu()
    main.getcmd()

    poll_plugins = plugin.get('daemon_poll')
    eventhandler_plugins  = []
    eventlistener_plugins = []

    for p in plugin.get('daemon_eventhandler'):
        if hasattr(p, 'event_listener') and p.event_listener:
            eventlistener_plugins.append(p)
        else:
            eventhandler_plugins.append(p)
    
    # Kick off the main menu loop
    _debug_('Main loop starting...',2)

    while 1:

        # Get next command
        while 1:

            event, event_repeat_count = rc_object.poll()
            # OK, now we have a repeat_count... to whom could we give it?
            if event:
                if event == OS_EVENT_POPEN2:
                    _debug_('popen2 %s' % event.arg[1])
                    event.arg[0].child = util.popen3.Popen3(event.arg[1])
                else:
                    _debug_('handling event %s' % str(event), 2)
                    break

            for p in poll_plugins:
                if not (rc_object.app and p.poll_menu_only):
                    p.poll_counter += 1
                    if p.poll_counter == p.poll_interval:
                        p.poll_counter = 0
                        p.poll()
            time.sleep(0.01)

        for p in poll_plugins:
            if not (rc_object.app and p.poll_menu_only):
                p.poll_counter += 1
                if p.poll_counter == p.poll_interval:
                    p.poll_counter = 0
                    p.poll()

        for p in eventlistener_plugins:
            p.eventhandler(event=event)

        if event == FUNCTION_CALL:
            event.arg()

        # Send events to either the current app or the menu handler
        elif rc_object.app:
            if not rc_object.app(event):
                for p in eventhandler_plugins:
                    if p.eventhandler(event=event):
                        break
                else:
                    _debug_('no eventhandler for event %s' % event,2)

        else:
            app = osd.focused_app()
            if app:
                try:
                    app.eventhandler(event)
                except SystemExit:
                    return
                except:
                    if config.FREEVO_EVENTHANDLER_SANDBOX:
                        traceback.print_exc()
                        from gui.AlertBox import AlertBox
                        pop = AlertBox(text=_('Event \'%s\' crashed\n\nPlease take a ' \
                                              'look at the logfile and report the bug to ' \
                                              'the Freevo mailing list. The state of '\
                                              'Freevo may be corrupt now and this error '\
                                              'could cause more errors until you restart '\
                                              'Freevo.\n\nLogfile: %s\n\n') % \
                                       (event, sys.stdout.logfile),
                                       width=osd.width-2*config.OVERSCAN_X-50)
                        pop.show()
                    else:
                        raise 
            else:
                _debug_('no target for events given')
                
#
# Main function
#
if __name__ == "__main__":
    def tracefunc(frame, event, arg, _indent=[0]):
        if event == 'call':
            filename = frame.f_code.co_filename
            funcname = frame.f_code.co_name
            lineno = frame.f_code.co_firstlineno
            if 'self' in frame.f_locals:
                try:
                    classinst = frame.f_locals['self']
                    classname = repr(classinst).split()[0].split('(')[0][1:]
                    funcname = '%s.%s' % (classname, funcname)
                except:
                    pass
            here = '%s:%s:%s()' % (filename, lineno, funcname)
            _indent[0] += 1
            tracefd.write('%4s %s%s\n' % (_indent[0], ' ' * _indent[0], here))
            tracefd.flush()
        elif event == 'return':
            _indent[0] -= 1

        return tracefunc

    if len(sys.argv) >= 2 and sys.argv[1] == '--force-fs':
        os.system('xset -dpms s off')
        config.START_FULLSCREEN_X = 1
        
    if len(sys.argv) >= 2 and sys.argv[1] == '--trace':
        tracefd = open(os.path.join(config.LOGDIR, 'trace.txt'), 'w')
        sys.settrace(tracefunc)

    if len(sys.argv) >= 2 and sys.argv[1] == '--doc':
        import pydoc
        import re
        sys.path.append('src/gui')
        for file in util.match_files_recursively('src/', ['py', ]):
            # doesn't work for everything :-(
            if file not in ( 'src/tv/record_server.py', ) and file.find('src/www'):
                file = re.sub('/', '.', file)
                pydoc.writedoc(file[4:-3])
        # now copy the files to Docs/api
        try:
            os.mkdir('Docs/api')
        except:
            pass
        for file in util.match_files('.', ['html', ]):
            print 'moving %s' % file
            os.rename(file, 'Docs/api/%s' % file)
        shutdown(allow_sys_shutdown=0)

    mmcache = '%s/mmpython' % config.FREEVO_CACHEDIR
    if not os.path.isdir(mmcache):
        os.mkdir(mmcache)

    # setup mmpython
    mmpython.use_cache(mmcache)
    if config.DEBUG > 2:
        mmpython.mediainfo.DEBUG = config.DEBUG
        mmpython.factory.DEBUG   = config.DEBUG
    else:
        mmpython.mediainfo.DEBUG = 0
        mmpython.factory.DEBUG   = 0
        
    mmpython.USE_NETWORK = config.USE_NETWORK
    
    if not os.path.isfile(os.path.join(mmcache, 'VERSION')):
        print '\nWARNING: no pre-cached data'
        print 'Freevo will cache each directory when you first enter it. This can'
        print 'be slow. Start "./freevo cache" to pre-cache all directories to speed'
        print 'up usage of freevo'
        print
    try:
        main_func()
    except KeyboardInterrupt:
        print 'Shutdown by keyboard interrupt'
        # Shutdown the application
        shutdown(allow_sys_shutdown=0)

    except SystemExit:
        sys.exit(0)

    except:
        print 'Crash!'
        try:
            tb = sys.exc_info()[2]
            fname, lineno, funcname, text = traceback.extract_tb(tb)[-1]
            
            for i in range(1, 0, -1):
                osd.clearscreen(color=osd.COL_BLACK)
                osd.drawstring(_('Freevo crashed!'), 70, 70,
                               fgcolor=osd.COL_ORANGE, bgcolor=osd.COL_BLACK)
                osd.drawstring(_('Filename: %s') % fname, 70, 130,
                               fgcolor=osd.COL_ORANGE, bgcolor=osd.COL_BLACK)
                osd.drawstring(_('Lineno: %s') % lineno, 70, 160,
                               fgcolor=osd.COL_ORANGE, bgcolor=osd.COL_BLACK)
                osd.drawstring(_('Function: %s') % funcname, 70, 190,
                               fgcolor=osd.COL_ORANGE, bgcolor=osd.COL_BLACK)
                osd.drawstring(_('Text: %s') % text, 70, 220,
                               fgcolor=osd.COL_ORANGE, bgcolor=osd.COL_BLACK)
                osd.drawstring(_('Please see the logfiles for more info'), 70, 280,
                               fgcolor=osd.COL_ORANGE, bgcolor=osd.COL_BLACK)
                
                osd.drawstring(_('Exit in %s seconds') % i, 70, 340,
                               fgcolor=osd.COL_ORANGE, bgcolor=osd.COL_BLACK)
                osd.update()
                time.sleep(1)

        except:
            pass
        traceback.print_exc()

        # Shutdown the application, but not the system even if that is
        # enabled
        shutdown(allow_sys_shutdown=0)
