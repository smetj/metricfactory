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
from time import time
from random import randint, choice
import string
from gevent import sleep
from gevent.socket import gethostname
from gevent import spawn
from gevent.event import Event

class Hammer(Actor):
    '''**Generates random metric events.**

    Generates random metrics events in internal format with the purpose of
    testing.  Metrics are generated in batches.  One batch is a list of
    dictionaries.

    (time, type, source, name, value, unit, (tag1, tag2))

    Parameters:

        - name (str):       The instance name when initiated.

        - batch (int):      The number of batches to produce.  0 is unlimited.
                            (default: 0)

        - batch_size(int):  The number of unique data sets in 1 batch.
                            (default: 1)

        - set_size(int):    The number of unique metrics per set.
                            (default: 1)

        - sleep (float):    The time to sleep in between generating batches.
                            (default: 1)

        - value (int):      The maximum of the randomized metric value (default 1).

        - prefix (str):     The top level name.
                            (default: hammer)

    Queues:

        - outbox:    Generated metrics.


    Metrics names will have following name structure:

        <prefix>.set_<batch_size>.metric_<set_size>


        hammer.set_0.metric_0 34534 1382173076

    '''

    def __init__(self, name, batch=0, batch_size=1, set_size=1, sleep=1, value=1, prefix='hammer'):
        Actor.__init__(self, name, setupbasic=False)
        self.name=name

        self.batch=batch
        self.batch_size=batch_size
        self.set_size=set_size
        self.sleep_value=float(sleep)
        self.value=value
        self.prefix=prefix

        if batch == 0:
            self.generateNextBatchAllowed = self.__returnTrue
        else:
            self.generateNextBatchAllowed = self.__evaluateCounter

        if sleep == 0:
            self.doSleep = self.__doNoSleep
        else:
            self.doSleep = self.__doSleep

        self.pause = Event()
        self.pause.set()

    def preHook(self):
        sleep(1)
        spawn(self.generate)

    def generate(self):
        switcher = self.getContextSwitcher(100)
        batch_counter=0
        while switcher():
            if self.generateNextBatchAllowed(batch_counter) == True:
                for event in self.generateBatch():
                    try:
                        self.queuepool.outbox.put({"header":{}, "data":event})
                    except:
                        self.queuepool.outbox.waitUntilPutAllowed()
                        self.queuepool.outbox.put({"header":{}, "data":event})
                batch_counter+=1
            else:
                break
            self.doSleep()
        self.logging.warn('Reached the batch_size of %s.  Not generating any further metrics.'%(self.batch_size))

    def generateBatch(self):
        #(time, type, source, name, value, unit, (tag1, tag2))
        #(1381002603.726132, 'wishbone', 'wishbone', 'queue.outbox.in_rate', 0, '', ())
        timestamp = time()

        for set_name in xrange(self.batch_size):
            for metric_name in xrange(self.set_size):
                self.pause.wait()
                yield (timestamp, 'test', 'hammer', '%s.set_%s.metric_%s'%(self.prefix, set_name, metric_name), randint(0, self.value), '', () )

    def __evaluateCounter(self, counter):
        if counter == self.batch:
            return False
        else:
            return True

    def __returnTrue(self, counter):
        return True

    def __doSleep(self):
        sleep(self.sleep_value)

    def __doNoSleep(self):
        sleep(0.0001)

    def enableThrottling(self):
        self.pause.clear()

    def disableThrottling(self):
        self.pause.set()
