#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       encodegraphite.py
#       
#       Copyright 2012 Jelle Smet development@smetj.net
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
from gevent.monkey import patch_time;patch_time()


class EncodeGraphite(PrimitiveActor):
    '''**Encodes the data field into a graphite entry.**
    
    Takes a dictionary and converts it into a graphite metric entry.
    
    This module is incomplete.  The input format can change need to
    figure out a way to cope with this.
    
    Parameters:
    
        - name (str):   The instance name when initiated.
        - prefix (str): A prefix to assign to all metrics.
    
    Queues:
    
        - inbox:    Incoming events.
        - outbox:   Outgoing events.
    '''
    
    def __init__(self, name,prefix=''):
        PrimitiveActor.__init__(self, name)
        self.name=name
        self.prefix=prefix
    
    def consume(self,doc):
        #system.loadavg_1min 1.05 1257715746
        doc["data"]="%s.%s.%s %s %s"%(self.prefix,doc["data"]["hostname"].split('.')[0],doc["data"]["metric_name"],doc["data"]["value"],time())
        self.putData(doc)
       
    def shutdown(self):
        self.logging.info('Shutdown')
