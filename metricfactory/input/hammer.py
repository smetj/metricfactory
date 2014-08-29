#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       hammer.py
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

    Metrics names will have following name structure:

        <prefix>.set_<batch_size>.metric_<set_size>

        hammer.set_0.metric_0 34534 1382173076


    Parameters:

        - name(str)
           |  The name of the module.

        - size(int)
           |  The default max length of each queue.

        - frequency(int)
           |  The frequency in seconds to generate metrics.

        - batch(int)(0)
            |  The number of batches to produce.
            |  0 is unlimited.

        - batch_size(int)(1)
            |  The number of unique data sets in 1 batch.

        - set_size(int)(1)
            |  The number of unique metrics per set.

        - sleep(float)(1)
            |  The time to sleep in between generating batches.

        - value (int)(1)
            |  The maximum of the randomized metric value (default 1).

        - prefix(str)(hammer)
            |  The top level name.


    Queues:

        - outbox
           |  Outgoing messges

    '''

    def __init__(self, name, size=100, frequency=1, batch=0, batch_size=1, set_size=1, sleep=1, value=1, prefix='hammer'):
        Actor.__init__(self, name, size, frequency)
        self.name = name

        self.batch = batch
        self.batch_size = batch_size
        self.set_size = set_size
        self.sleep_value = float(sleep)
        self.value = value
        self.prefix = prefix

        if batch == 0:
            self.generateNextBatchAllowed = self.__returnTrue
        else:
            self.generateNextBatchAllowed = self.__evaluateCounter

        if sleep == 0:
            self.doSleep = self.__doNoSleep
        else:
            self.doSleep = self.__doSleep

        self.pool.createQueue("outbox")

    def preHook(self):
        spawn(self.generate)

    def generate(self):
        batch_counter = 0
        while self.loop():
            if self.generateNextBatchAllowed(batch_counter) is True:
                for event in self.generateBatch():
                    self.submit({"header": {}, "data": event}, self.pool.queue.outbox)
                batch_counter += 1
            else:
                self.logging.warn('Reached the batch_size of %s.  Not generating any further metrics.' % (self.batch_size))
                break
            self.doSleep()

    def generateBatch(self):
        # (time, type, source, name, value, unit, (tag1, tag2))
        # (1381002603.726132, 'wishbone', 'wishbone', 'queue.outbox.in_rate', 0, '', ())
        timestamp = time()

        for set_name in xrange(self.batch_size):
            for metric_name in xrange(self.set_size):
                yield (timestamp, 'test', 'hammer', '%s.set_%s.metric_%s' % (self.prefix, set_name, metric_name), randint(0, self.value), '', ())

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
        pass
