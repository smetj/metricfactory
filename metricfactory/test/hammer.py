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

from wishbone.toolkit import PrimitiveActor
from time import time
from random import randint, choice
import string
from gevent import sleep
from gevent.socket import gethostname

class Hammer(PrimitiveActor):
    '''**Generates random metric events.**

    Generates random metrics events in internal format with the purpose of
    testing.  Metrics are generated in batches.  One batch is a list of
    dictionaries.

    metric = {  "type":string,
                "time":time(),
                "source":string,
                "name":string,
                "value":string,
                "units":string,
                "tags":list
                }

    Parameters:

        - name (str):       The instance name when initiated.

        - total (int):      The total number of metrics to produce in random mode. Indefinite when 0.
                            (default 0)

        - mode (str):       The mode to run in. Options: sequential, random.
                            (default random)

        - sleep (float):    The time in seconds to wait between generating each metric.
                            (default 0)

        - host (int):       The maximum suffix number for the source host: host_
                            (default 0)

        - metric (int):     The maximum suffix number for the metric name: metric_
                            (default 0)

        - value (int):      The maximum of the randomized metric value (default 1).

    Queues:

        - inbox:    Generated metrics.

    When mode is random, for each metric a random hostname and metric name is
    chosen within the boundaries set by *host* and *metric*. You can control
    the total number of metrics using the *total* parameter.

    When mode is sequential, X unique metrics are generate per N hosts, where
    X is the *metric* parameter and N is the *host* parameter.  In this case
    each metric will only contain 1 value, effectively creating X * Y unique
    metrics.  In this case the total parameter has no meaning.
    '''

    def __init__(self, name, total=0, mode="random", sleep=0, host=0, metric=0, value=1):
        PrimitiveActor.__init__(self, name)
        self.name=name
        self.total=total
        self.mode=mode
        self.sleep=float(sleep)
        self.host=int(host)
        self.metric=int(metric)
        self.value=int(value)

    def consume(self,doc):
        #Nothing to do since we do not expect incoming data.
        pass

    def _run(self):
        #Overwrites the PrimitiveActor version
        if self.mode == "random" and self.total == 0:
            while self.block() == True:
                self.sendData({"header":{},"data":self.generateMetric()},"inbox")
                sleep(self.sleep)
        elif self.mode == "random" and self.total > 0:
            for counter in xrange(self.total):
                self.sendData({"header":{},"data":self.generateMetric()},"inbox")
                sleep(self.sleep)
            self.logging.info("Reached total number of metrics (%s) to produce. Will not produce more."%(self.total))
        elif self.mode == "sequential":
            for host in xrange(self.host):
                for metric in xrange(self.metric):
                    data = self.generateMetric(host="host_%s"%(host), metric="metric_%s"%(metric))
                    self.sendData({"header":{},"data":data},"inbox")
                    sleep(self.sleep)
            self.logging.info("Reached total number of metrics (%s) to produce. Will not produce more."%(self.host*self.metric))

    def generateMetric(self, host=None, metric=None, value=None):
        if host == None:
            host = self.__getHostname()
        if metric == None:
            metric = self.__getMetricName()
        if value == None:
            value = self.__getValue()

        return {
        "type":"metricfactoryHammer",
        "time":time(),
        "source":host,
        "name":metric,
        "value":value,
        "unit":"hits",
        "tags":[]
        }

    def __getValue(self):
        return randint(0,self.value)

    def __getMetricName(self):
        return "metric_%s"%(randint(0, self.metric))

    def __getHostname(self):
        return "host_%s"%(randint(0,self.host))

    def shutdown(self):
        self.logging.info('Shutdown')