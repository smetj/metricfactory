#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       jsonflatten.py
#
#       Copyright 2015 Jelle Smet development@smetj.net
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
from wishbone.event import Metric
from gevent import monkey
monkey.patch_time()
from time import time
import json


class JSONFlatten(Actor):

    '''**Flattens JSON metrics of arbitrary depth into a flat metric names.**

    This module takes a JSON structure and recursively travels the structure
    flattening the namespace into a dotted format untill a numeric value is
    encountered.  For each metric a <wishbone.event.Metric> datastructure is
    created.

    Non-numeric values are ignored.

    For example:

        {"server": {"host01": {"memory": {"free": 10, "consumed": 90}}}}

        Would generate following metrics:

        server.host01.memory.free
        server.host01.memory.consumed

    These metrics are converted to the Wishbone metric data format:

        http://wishbone.readthedocs.org/en/latest/logs%20and%20metrics.html#format

    The module is expecting a Python <dict> type.  That means you should have
    already decoded the incoming data using a module like wishbone.decode.json.


    Parameters:

        - type(str)("wishbone")
           |  An arbitrary string to assign to the "type" field of the Metric
           |  datastructure.

        - source(str)("wishbone")
           |  An arbitrary string to assign to the "source" field of the Metric
           |  datastructure.

        - tags(set)()
           |  An arbitrary set of tags assign to the "tags" field of the Metric
           |  datastructure.


    Queues:

        - inbox:    Incoming events.

        - outbox:   Outgoing events in wishbone.event.Metric format.
    '''

    def __init__(self, actor_config, type="wishbone", source="wishbone", tags=()):
        Actor.__init__(self, actor_config)

        self.pool.createQueue("inbox")
        self.registerConsumer(self.consume, "inbox")
        self.pool.createQueue("outbox")

    def consume(self, event):

        if isinstance(event.data, dict) or isinstance(event.data, list):
            for name, value in self.recurseData(event.data):
                e = self.createEvent()
                e.setData(Metric(time(), self.kwargs.type, self.kwargs.source, name, value, "", self.kwargs.tags))
                self.submit(e, self.pool.queue.outbox)
        else:
            raise Exception("Dropped incoming data because not of type <dict>. Perhaps you forgot to feed the data through wishbone.decode.json first?")

    def recurseData(self, data, breadcrumbs=""):

        if isinstance(data, list):
            for item in data:
                for a, b in self.recurseData(item, breadcrumbs):
                    yield a, b
        elif isinstance(data, dict):
            for key, value in data.iteritems():
                name = self.__concatBreadCrumbs(breadcrumbs, key)
                for a, b in self.recurseData(value, name):
                    yield a, b
        elif isinstance(data, bool):
            pass
        elif isinstance(data, (int, long, float)):
            yield breadcrumbs, data

    def __concatBreadCrumbs(self, breadcrumbs, element_name):

        if element_name.startswith('.'):
            element_name = "_%s" % (element_name[1:])
        if element_name.startswith('_'):
            element_name = "_%s" % (element_name)

        name = "%s.%s" % (breadcrumbs, element_name)

        if name.startswith('.'):
            return name[1:]
        else:
            return name
