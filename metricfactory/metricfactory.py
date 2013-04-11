#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  metricfactory
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

from wishbone.server import BootStrap

def main():
    BootStrap(name="MetricFactory",
        description="Accept, process and submit metrics.",
        version="0.1",
        author="Jelle Smet",
        support="",
        groups=["metricfactory.encoder","metricfactory.decoder","metricfactory.filter"]
    )

if __name__ == '__main__':
    main()
