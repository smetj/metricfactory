#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       decodeganglia.py
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

#A big thanks to:
# Michael Rose https://bitbucket.org/michaelrose/ganglia-xdr-parser/src/da033e2bed3e/ganglia_xdr_parser.py
# Patrick Debois https://gist.github.com/1376525

from wishbone.toolkit import PrimitiveActor
import pprint
import socket
import xdrlib

class DecodeGanglia(PrimitiveActor):
    '''**DecodeGanglia is Wishbone module which converts Ganglia data into a 
    dictionary.***

    Receives xdr formatted data coming from a Ganglia client and decodes it
    into a dictionary.
    
    Parameters:
    
        - name (str):    The instance name when initiated.
    
    Queues:
    
        - inbox:    Incoming events.
        - outbox:   Outgoing events.
    '''
    
    def __init__(self, name):
        PrimitiveActor.__init__(self, name)
        
    def parse_packet(self, data):
        unpacker = xdrlib.Unpacker(data)

        version = unpacker.unpack_int()
        if version == 128:
            return GangliaMetaPacket(unpacker, version)
        elif version in (132, 133, 134):
            return GangliaHeartbeatPacket(unpacker, version)
        else:
            raise Exception('Unknown version:', version)            
    
    def consume(self,doc):        
        try:
            doc['data']=self.parse_packet(doc["data"]).__dict__
            try:
                doc['data']['value']
                self.putData(doc)
            except:
                pass
        except Exception as err:
            self.logging.debug('Could not decode data. Reason: %s'%err)
       
    def shutdown(self):
        self.logging.info('Shutdown')

class GangliaMetaPacket(object):
    def __init__(self, unpacker, version):
        self.version = version
        self.hostname = unpacker.unpack_string()
        self.metric_name = unpacker.unpack_string()
        self.spoofed_hostname = bool(unpacker.unpack_int())
        self.metric_type = unpacker.unpack_string()
        self.metric_name2 = unpacker.unpack_string()
        self.units = unpacker.unpack_string()
        self.slope = unpacker.unpack_int()
        self.tmax = unpacker.unpack_int()
        self.dmax = unpacker.unpack_int()
        
        self.data = {}
        remaining = unpacker.unpack_int()
        for i in range(remaining):
            key = unpacker.unpack_string()
            value = unpacker.unpack_string()
            self.data[key] = value
        unpacker.done()

class GangliaHeartbeatPacket(object):
    def __init__(self, unpacker, version):
        self.version = version
        self.hostname = unpacker.unpack_string()
        self.metric_name = unpacker.unpack_string()
        self.spoof = bool(unpacker.unpack_int())
        self.format = unpacker.unpack_string()

        if self.format.endswith('f'):
            self.value = unpacker.unpack_float()
        elif self.format.endswith('u') or self.format.endswith('d'):
            self.value = unpacker.unpack_int()
        elif self.format.endswith('s'):
            self.value = unpacker.unpack_string()
        unpacker.done()
