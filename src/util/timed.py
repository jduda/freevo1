# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# This is decorator class to time function calls
# -----------------------------------------------------------------------
# $Id$
#
# Notes:
# Todo:
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
# -----------------------------------------------------------------------


import time

class timed:
    """
    A decorator class to time function calls
    http://wiki.python.org/moin/PythonDecoratorLibrary
    """
    def __init__(self, reset=True):
        """ Contructs the timed class
        @param reset: resets the timer a each call
        """
        self.reset = reset
        self.start = time.time()
        self.level = 0


    def __call__(self, func):
        def newfunc(*args, **kwargs):
            pre = '  ' * self.level
            self.level += 1
            if self.reset:
                self.start = time.time()
            print '%s-> %s' % (pre, func.__name__)
            result = func(*args, **kwargs)
            print '%s<- %s: %.3f' % (pre, func.__name__, time.time() - self.start)
            self.level -= 1
            return result
        newfunc.__name__ = func.__name__
        newfunc.__doc__ = func.__doc__
        return newfunc



if __name__ == '__main__':

    @timed(False)
    def longrunning(n):
        """Wait for n * 100ms"""
        for i in range(n):
            time.sleep(0.1)

    longrunning(12)
    longrunning(2)
    print '__repr__:', longrunning
    print '__name__:', longrunning.__name__
    print '__doc__:', longrunning.__doc__
