#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       elasticsearch.py
#
#       Copyright 2014 Jelle Smet development@smetj.net
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
from gevent import monkey
monkey.patch_time()
from time import time
import json


class Elasticsearch(Actor):

    '''**Decode Elasticsearch metrics.**

    This module takes a JSON formatted coming from an Elasticsearch
    clusternode and converts the metrics into the common format.

    The name of the metric will be point delimited.

    This module deals with JSON documents coming from:

        - /_stats
        - /_cluster/stats
        - /_nodes/stats

    Feeding this module any other stats data will not work.
    Requires Elasticsearch >= 1.0.0

    Parameters:

        - name(str)
           |  The name of the module.

        - size(int)
           |  The default max length of each queue.

        - frequency(int)
           |  The frequency in seconds to generate metrics.

        - source(str)("elasticsearch")
           |  Allows to set the source manually.

        - indices(list)([])
           |  The indices to include when polling /_stats


    Queues:

        - inbox:    Incoming events.

        - outbox:   Outgoing events.
    '''

    def __init__(self, name, size=100, frequency=1, source="elasticsearch", indices=[]):
        Actor.__init__(self, name, size, frequency)
        self.pool.createQueue("inbox")
        self.pool.createQueue("outbox")
        self.registerConsumer(self.consume, "inbox")
        self.logging.info("Initialized")
        self.source = source
        self.indices = indices

    def consume(self, event):

        try:
            data = json.loads(event["data"])
            for metric in self.extractMetrics(data):
                self.submit({"header": event["header"], "data": metric}, self.pool.queue.outbox)
        except ValueError as err:
            self.logging.error("Problem reading JSON data.  Reason: %s" % (err))
            raise
        except Exception as err:
            self.logging.error("Unexpected error encountered possibly due to the event format. Event dropped.  Reason: %s" % (err))
            raise

    def __formatMetric(self, timestamp, name, value):
        return (timestamp, "elasticsearch", self.source, name, value, '', ())

    def __crawlDictionary(self, timestamp, dictionary,  breadcrumbs=""):

        for k, v in dictionary.iteritems():
            b = "%s.%s" % (breadcrumbs, k)
            if isinstance(v, dict):
                for metric in self.__crawlDictionary(timestamp, v, b):
                    yield metric
            elif isinstance(v, list):
                continue
            elif isinstance(v, (int, long, float, complex)):
                yield self.__formatMetric(timestamp, b, v)

    def extractMetrics(self, data):
        # (time, type, source, name, value, unit, (tag1, tag2))
        # (1381002603.726132, 'wishbone', 'hostname', 'queue.outbox.in_rate', 0, '', ())

        timestamp = time()
        if all(False for k in ["_shards", "_all", "indices"] if k not in data):
            # We have received metrics from /_stats
            for element in ["_shards", "_all"]:
                for metric in self.__crawlDictionary(timestamp, data[element], "indices.%s" % (element)):
                    yield metric
            for index in self.indices:
                try:
                    for metric in self.__crawlDictionary(timestamp, data["indices"][index], index):
                        yield metric
                except KeyError:
                    self.logging.error("Index %s does not exist." % (metric))
        elif all(False for k in ["timestamp", "cluster_name", "status", "indices", "nodes"] if k not in data):
            # We have received metrics from /_cluster/stats
            for element in ["indices", "nodes"]:
                for metric in self.__crawlDictionary(data["timestamp"] / 1000, data[element], "cluster.%s" % (element)):
                    yield metric

        elif all(False for k in ["cluster_name", "nodes"] if k not in data):
            # We have received metrics from /_nodes/stats
            for node in data["nodes"]:
                for metric in self.__crawlDictionary(data["nodes"][node]["timestamp"] / 1000, data["nodes"][node], "nodes.%s" % (data["nodes"][node]["name"])):
                    yield metric

        elif all(False for k in ["cluster_name", "status", "timed_out"] if k not in data):
            # We have received metrics from /_cluster/health
            for metric in self.__crawlDictionary(timestamp, data, "cluster.health"):
                yield metric
        else:
            self.logging.error("Unrecognized dataset.  Are you sure you have polled the right resource?")
