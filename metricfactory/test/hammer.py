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
        - total (int):      The total number of metrics to produce. Indefinite when 0.
                            (default 0)
        - sleep (float):    The time in seconds to wait between generating each metric.
                            (default 0)
        - rnd_source (int): When larger than 0 generates a random hostname otherwise takes
                            the host's hostname. (default 0)
        - rnd_name (int):   The length of the random metric name. Chosen from a-zA-Z0-9
                            (default 1).
        - rnd_value (int):  The maximum of the randomized metric value (default 1).

    Queues:

        - inbox:    Generated metrics.
    '''

    def __init__(self, name, total=0, sleep=0, rnd_source=0, rnd_name=1, rnd_value=1):
        PrimitiveActor.__init__(self, name)
        self.name=name
        self.total=total
        self.sleep=float(sleep)
        self.rnd_source=int(rnd_source)
        self.rnd_name=int(rnd_name)
        self.rnd_value=int(rnd_value)
        if rnd_source == 0:
            self.getHostname=self.__getHostname
        else:
            self.getHostname=self.__getRandomHostname

    def consume(self,doc):
        #Nothing to do
        pass

    def _run(self):
        #Overwrites the PrimitiveActor version
        counter=0
        while self.block() == True:
            self.sendData({"header":{},"data":self.generateMetric()},"inbox")
            counter+=1
            sleep(self.sleep)
            if self.total != 0 and counter == self.total:
                self.logging.info("Reached total number of metrics (%s) to produce. Will not produce more."%(counter))
                break

    def generateMetric(self):
        return {
        "type":"metricfactoryHammer",
        "time":int(time()),
        "source":self.getHostname(),
        "name":self.__getMetricName(),
        "value":self.__getValue(),
        "unit":"hits",
        "tags":[]
        }

    def __getValue(self):
        return randint(0,self.rnd_value)

    def __getMetricName(self):
        return "metric_%s"%(randint(0, self.rnd_name-1))

    def __getHostname(self):
        return gethostname()

    def __getRandomHostname(self):
        return "host_%s"%(randint(0,self.rnd_source-1))

    def shutdown(self):
        self.logging.info('Shutdown')