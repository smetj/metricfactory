#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       graphite.py
#
#       Copyright 2013 Jelle Smet development@smetj.net
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#
#

from wishbone import Actor

class Graphite(Actor):
    '''**Encodes the data field into a Graphite format.**

    Encodes the event["data"] field into a Graphite formatted string ready to dump
    into Graphite.

    Parameters:

        - name (str):       The instance name when initiated.
        - prefix (str):     A prefix to assign to all metrics.
        - template (str):   A template which shapes the metric name.

    Queues:

        - inbox:    Incoming MetricFactory formatted events.
        - outbox:   Outgoing Graphite formatted events.
    '''

    def __init__(self, name, prefix=''):
        Actor.__init__(self, name)
        self.name=name
        self.prefix=prefix

    def consume(self,event):
        #system.loadavg_1min 1.05 1257715746
        if event["data"]["type"] == "nagios":
            if event["data"]["tags"][1] == "hostcheck":
                event["data"]="%s.%s.hostcheck.%s %s %s\n"%(self.prefix,event["data"]["source"],event["data"]["name"],event["data"]["value"],event["data"]["time"])
            else:
                event["data"]="%s.%s.%s.%s %s %s\n"%(self.prefix,event["data"]["source"],event["data"]["tags"][1],event["data"]["name"],event["data"]["value"],event["data"]["time"])

        else:
            event["data"]="%s.%s.%s %s %s\n"%(self.prefix,event["data"]["source"],event["data"]["name"],event["data"]["value"],event["data"]["time"])
        self.queuepool.outbox.put(event)