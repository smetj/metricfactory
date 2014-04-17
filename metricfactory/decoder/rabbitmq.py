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
        except Exception as err:
            self.logging.error("Unexpected error encountered possibly due to the event format. Event dropped.  Reason: %s"%(err))

    def extractMetrics(self, data):
        #(time, type, source, name, value, unit, (tag1, tag2))
        #(1381002603.726132, 'wishbone', 'hostname', 'queue.outbox.in_rate', 0, '', ())
        if len(data) == 0:
            return

        timestamp=time()
        if "os_pid" in data[0]:
            #Got metrics from /api/nodes
            for node in data:
                for metric in [ "fd_used","fd_total","sockets_used","sockets_total","mem_used","mem_limit","disk_free_limit","disk_free","proc_used","proc_total","uptime","run_queue","processors" ]:
                    yield (timestamp,
                        "rabbitmq",
                        self.source,
                        "node.%s.%s"%(node["name"].split("@")[1], metric),
                        node.get(metric,0),
                        '',
                        ())

        elif "backing_queue_status" in data[0]:
            #Got metrics from /api/queues
            for queue in data:
                for metric in self.__crawlDictionary(timestamp, queue, "%s.queue.%s"%(queue["vhost"],queue["name"])):
                        yield metric

        elif data[1]["name"] == "amq.direct":
            #got metrics from /api/exchanges
            for exchange in data:
                if exchange["name"] == "":
                    exchange["name"] = "_AMQP_default_"
                for metric in self.__crawlDictionary(timestamp, exchange, "%s.exchange.%s"%(exchange["vhost"],exchange["name"])):
                    yield metric


    def __formatMetric(self, timestamp, name, value):
        return (timestamp, "elasticsearch", self.source, name, value, '', ())

    def __crawlDictionary(self, timestamp, dictionary,  breadcrumbs=""):

        for k, v in dictionary.iteritems():
            b = "%s.%s"%(breadcrumbs, k)
            if isinstance(v, dict):
                 for metric in self.__crawlDictionary(timestamp, v, b):
                    yield metric
            elif isinstance(v, list):
                continue
            elif isinstance(v, (int, long, float, complex)):
                yield self.__formatMetric(timestamp, b, v)