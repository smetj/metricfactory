#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       decodeganglia.py
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

#A big thanks to:
# Michael Rose https://bitbucket.org/michaelrose/ganglia-xdr-parser/src/da033e2bed3e/ganglia_xdr_parser.py
# Patrick Debois https://gist.github.com/1376525

from wishbone import Actor
import xdrlib
from time import time
from gevent.monkey import patch_time;patch_time()

class DecodeGangliaException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Ganglia(Actor):
    '''**DecodeGanglia is MetricFactory module which decodes Ganglia metrics into
    a MetricFactory format.***

    Receives xdr formatted data coming from a Ganglia client and decodes it
    into a MetricFactory format.

    metric = {  "type":string,
                "time":time(),
                "source":string,
                "name":string,
                "value":string,
                "units":string,
                "tags":list
                }


    Parameters:

        - name (str):   The instance name when initiated.
        - meta (bool):  When True, drops data with version 128

    Queues:

        - inbox:    Incoming events.
        - outbox:   Outgoing events.
    '''

    def __init__(self, name, meta=False):
        Actor.__init__(self, name)
        self.name=name
        self.meta=meta

    def parsePacket(self, data):
        unpacker = xdrlib.Unpacker(data)
        version = unpacker.unpack_int()

        if version in (132,133,134):
            return self.doHeartBeatPacket(unpacker,version)
        elif version == 128:
            if self.meta == True:
                return self.doMetaPacket(unpacker,version)
            else:
                raise DecodeGangliaException("Version 128 is ignored.")
        else:
            raise Exception("Unknown version number: %s"%version)

    def consume(self,doc):
        try:
            data = self.parsePacket(doc["data"])
            doc['data']={ "type":"ganglia","time":time(),"source":data["hostname"],"name":data["metric_name"],"value":data["value"],"units":None,"tags":[] }
            self.putData(doc)
        except Exception as err:
            self.logging.debug ( "Failed to decode package. Reason: %s" %err )
        except DecodeGangliaException as err:
            self.logging.debug ( err )

    def doMetaPacket(self, unpacker, version):
        data = {"version":version,
                "hostname":unpacker.unpack_string(),
                "metric_name":unpacker.unpack_string(),
                "spoofed_hostname":bool(unpacker.unpack_int()),
                "metric_type":unpacker.unpack_string(),
                "metric_name2":unpacker.unpack_string(),
                "units":unpacker.unpack_string(),
                "slope":unpacker.unpack_int(),
                "tmax":unpacker.unpack_int(),
                "dmax":unpacker.unpack_int(),
                "metrics":{}
                }
        remaining = unpacker.unpack_int()
        for i in range(remaining):
            data["metrics"][unpacker.unpack_string()]=unpacker.unpack_string()
        unpacker.done()
        if data != None:
            return data
        else:
            raise Exception ("Empty dataset")

    def doHeartBeatPacket(self, unpacker, version):
        data = {"version":version,
                "hostname":unpacker.unpack_string(),
                "metric_name":unpacker.unpack_string(),
                "spoof":bool(unpacker.unpack_int()),
                "format":unpacker.unpack_string()
                }

        if data["format"].endswith('f'):
            data["value"] = unpacker.unpack_float()
        elif data["format"].endswith('u') or data["format"].endswith('d'):
            data["value"] = unpacker.unpack_int()
        elif data["format"].endswith('s'):
            data["value"] = unpacker.unpack_string()
        unpacker.done()
        if data != None:
            return data
        else:
            raise Exception ("Empty dataset")

