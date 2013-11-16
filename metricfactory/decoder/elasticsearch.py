#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       skeleton.py
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

class Elasticsearch(Actor):
    '''**Decode Elasticsearch metrics.**

    This module takes a JSON formatted coming from an Elasticsearch
    clusternode and converts the metrics into the common format.

    The name of the metric will be point delimited.

    Parameters:

        - name (str):           The instance name.
        - source(str):          Allows to set the source manually.
                                Default: elasticsearch

    Queues:

        - inbox:    Incoming events.
        - outbox:   Outgoing events.

    ES can be queried using following resources:

        _cluster/nodes/stats
        _stats

    The _cluster/nodes/stats has a cluster_name value but the _stats
    resource not.  That's why we can override this.  Maybe this can
    be derived automatically if following enhancement request is
    accepted and implemented:
    https://github.com/elasticsearch/elasticsearch/issues/4179
    '''

    def __init__(self, name, source="elasticsearch"):
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
        if "cluster_name" in data:
            #we got metrics from _cluster/nodes/stats
            for node in data["nodes"]:
                for item in data["nodes"][node]["indices"]:
                    for metric in data["nodes"][node]["indices"][item]:
                        yield (data["nodes"][node]["timestamp"]/1000,
                            "elasticsearch",
                            self.source,
                            "%s.indices.%s.%s"%(data["nodes"][node]["hostname"], item, metric),
                            data["nodes"][node]["indices"][item][metric],
                            '',
                            ())
        elif "ok" in data:
            timestamp=time()
            #We got metrics from /_stats
            for metric in data["_shards"]:
                yield (timestamp,
                        "elasticsearch",
                        self.source,
                        "_shards.%s"%(metric),
                        data["_shards"][metric],
                        '',
                        ())
            for section in data["_all"]:
                for item in data["_all"][section]:
                    for metric in data["_all"][section][item]:
                        yield (timestamp,
                                "elasticsearch",
                                self.source,
                                "_all.%s.%s.%s"%(section, item, metric),
                                data["_all"][section][item][metric],
                                '',
                                ())
            for index in data["indices"]:
                for item in data["indices"][index]:
                    for part in data["indices"][index][item]:
                        for metric in data["indices"][index][item][part]:
                            yield (timestamp,
                                    "elasticsearch",
                                    self.source,
                                    "indices.%s.%s.%s.%s"%(index.replace(".","_"), item, part, metric),
                                    data["indices"][index][item][part][metric],
                                    '',
                                    ())