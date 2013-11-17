#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       rabbitmq.py
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
from wishbone.errors import QueueLocked
from gevent import monkey;monkey.patch_time()
from time import time
import json

class RabbitMQ(Actor):
    '''**Decode RabbitMQ metrics.**

    This module takes a JSON formatted coming from a RabbitMQ
    clusternode and converts the metrics into the common format.

    The name of the metric will be point delimited.

    Parameters:

        - name (str):           The instance name.
        - source(str):          Allows to set the source manually.
                                Default: rabbitmq

    Queues:

        - inbox:    Incoming events.
        - outbox:   Outgoing events.

    It's possible to process metrics coming from following resources:

        - /api/nodes
        - /api/queues
    '''

    def __init__(self, name, source="rabbitmq"):
        Actor.__init__(self, name, setupbasic=True)
        self.logging.info("Initialized")
        self.source=source

    def consume(self, event):

        try:
            data=json.loads(event["data"])
            for metric in self.extractMetrics(data):
                self.queuepool.outbox.put({"header":event["header"], "data":metric})
        except ValueError as err:
            self.logging.error("Problem reading JSON data.  Reason: %s"%(err))
        except QueueLocked:
            self.queuepool.inbox.rescue(event)
            self.queuepool.outbox.waitUntillPutAllowed()

    def extractMetrics(self, data):
        #(time, type, source, name, value, unit, (tag1, tag2))
        #(1381002603.726132, 'wishbone', 'hostname', 'queue.outbox.in_rate', 0, '', ())
        timestamp=time()
        if "os_pid" in data[0]:
            #Got metrics from /api/nodes
            for node in data:
                for metric in [ "fd_used","fd_total","sockets_used","sockets_total","mem_used","mem_limit","disk_free_limit","disk_free","proc_used","proc_total","uptime","run_queue","processors" ]:
                    yield (time(),
                        "rabbitmq",
                        self.source,
                        "%s.%s"%(node["name"].split("@")[1], metric),
                            node[metric],
                            '',
                            ())
