#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       rsyslog.py
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
import re

class Rsyslog(Actor):
    '''**Decode Rsyslog metrics.**

    This module takes JSON formatted metrics coming from Rsyslog and
    converts them to the metricfactory default format.

    Rsyslog seems to change frequently.  This module is expecting
    the metrics coming from Rsyslog 7.6.0

    The name of the metric will be point delimited.

    Parameters:

        - name (str):           The instance name.

        - source(str):          Allows to set the source manually.
                                Default: rsyslog


    Queues:

        - inbox:    Incoming events.

        - outbox:   Outgoing events.

    The template to use in Rsyslog is:

    template (name="metrics" type="string" string="%TIMESTAMP:::date-unixtimestamp% %fromhost% %msg%\n")
    '''

    # 1394101824 {"name":"imuxsock","submitted":2,"ratelimit.discarded":0,"ratelimit.numratelimiters":2}
    # 1394101824 {"name":"stats","processed":8988,"failed":0,"suspended":0,"suspended.duration":0,"resumed":0}
    # 1394101824 {"name":"local_logs","processed":3,"failed":0,"suspended":0,"suspended.duration":0,"resumed":0}
    # 1394101824 {"name":"logstash_logs","processed":3,"failed":0,"suspended":0,"suspended.duration":0,"resumed":0}
    # 1394101824 {"name":"imudp(*:514)","submitted":0}
    # 1394101824 {"name":"imudp(*:514)","submitted":0}
    # 1394101824 {"name":"imtcp(514)","submitted":0}
    # 1394101824 {"name":"resource-usage","utime":153976,"stime":280957,"maxrss":4068,"minflt":437,"majflt":0,"inblock":0,"oublock":24,"nvcsw":1591,"nivcsw":15}
    # 1394101824 {"name":"logstash_logs[DA]","size":0,"enqueued":0,"full":0,"discarded.full":0,"discarded.nf":0,"maxqsize":0}
    # 1394101824 {"name":"logstash_logs","size":0,"enqueued":3,"full":0,"discarded.full":0,"discarded.nf":0,"maxqsize":1}
    # 1394101824 {"name":"main Q","size":10,"enqueued":9001,"full":0,"discarded.full":0,"discarded.nf":0,"maxqsize":12}
    # 1394101824 {"name":"imudp(w0)","called.recvmmsg":0,"called.recvmsg":0,"msgs.received":0}


    def __init__(self, name, source="rsyslog"):

        Actor.__init__(self, name, setupbasic=True)
        self.logging.info("Initialized")
        self.source=source
        self.prev_metric={}

    def consume(self, event):
        try:
            for metric in self.__extractMetrics(event["data"].rstrip()):
                self.queuepool.outbox.put({"header":event["header"], "data":metric})
        except QueueLocked:
            self.queuepool.inbox.rescue(event)
            self.queuepool.outbox.waitUntillPutAllowed()

    def __extractMetrics(self, data):

        try:
            (time, hostname, j) = re.match('(^\d*) (.*?) (.*)', data).groups()
            j = json.loads(j)
            for (name, value) in self.__extractIndividualMetric(hostname, j):
                yield self.__formatMetric(time, name, value)
                rate = self.__getRate(time, name, value)
                yield self.__formatMetric(time, name.replace('.total','.rate'), rate)
        except Exception as err:
            self.logging.warning("Bad Rsyslog metric format.  Check the Rsyslog template to use.  Reason: %s"%(err))

    def __extractIndividualMetric(self, hostname, data):

        keys = data.keys()
        keys.remove("name")
        name = self.__scrubMetricName(data["name"])
        for item in keys:
            yield "%s.%s.%s.total"%(hostname, name, item.replace('.','')), data[item]

    def __scrubMetricName(self, name):
        for character in [")", "*", ":", "]", " "]:
            name = name.replace(character,"")
        for character in ["(","["]:
            name = name.replace(character,"_")
        return name.lower()

    def __getRate(self, time, name, value):
        try:
            previous_value = self.prev_metric[name]["value"]
            previous_time  = self.prev_metric[name]["time"]
        except KeyError:
            self.prev_metric[name]={"value":value,"time":time}
            return 0
        else:
            self.prev_metric[name]={"value":value,"time":time}
            try:
                return (int(value) - int(previous_value))/(int(time) - int(previous_time))
            except ZeroDivisionError:
                return 0

    def __formatMetric(self, timestamp, name, value):

        return ((timestamp, "rsyslog", self.source, name, value, '', ()))

