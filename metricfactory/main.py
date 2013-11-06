#!/usr/bin/env python
#
# -*- coding: utf-8 -*-
#
#  main.py
#
#  Copyright 2013 Jelle Smet <development@smetj.net>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

from wishbone.bootstrap import BootStrap
import sys

def main():
    try:
        BootStrap()
    except Exception as err:
        sys.stderr.write("Failed to bootstrap instance.  Reason: %s\n"%(err))
        sys.stderr.flush()
        sys.exit(1)

if __name__ == '__main__':
    main()
