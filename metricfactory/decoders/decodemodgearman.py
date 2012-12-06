#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       decodemodgearman.py
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
import sys

class DecodeModGearman(PrimitiveActor):
    '''Class which converts Nagios perfdata into a dictionary coming in through mod_gearman.
    '''
    
    def __init__(self, name, *args, **kwargs):
        PrimitiveActor.__init__(self, name)
    
    def consume(self,doc):
        try:
            doc["data"] = self.chopMetrics(self.chopMessage(doc["data"]))
            self.sendData(doc)
        except Exception as err:
            self.logging.warn('Malformatted performance data received for. Reason: %s'%(err))
    
    def chopMessage(self, data):        
        '''Chops the message into a dictionary and lc all key values.'''
        
        d={"metadata":{},"metrics":{}}
        for element in data.split("\t"):
            (key, value) = element.split('::')
            d["metadata"][key.lower()]=value
        return d
    
    def chopMetrics(self, data):        
        
        '''Chops the metrics into a dictionary.'''
        
        if 'serviceperfdata' in data["metadata"]:
            data["metrics"] = self.doChop(data["metadata"]["serviceperfdata"])
            del data["metadata"]["serviceperfdata"]
        if 'hostperfdata' in data["metadata"]:
            data["metrics"] = self.doChop(data["metadata"]["hostperfdata"])
            del data["metadata"]["hostperfdata"]
        
        return data
    
    def doChop(self, data):
        
        '''Chop the individual perfdata entries into a dictionary'''
        
        metrics={}
        d = data.split(" ")
        for item in d:
            (key,value)=item.split('=')
            value=value.split(";")[0]
            metrics[key]=value
        return metrics
        
       
    def shutdown(self):
        self.logging.info('Shutdown')
