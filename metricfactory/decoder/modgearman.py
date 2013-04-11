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
import re
import sys

class ModGearman(PrimitiveActor):
    '''**DecodeModGearman is MetricFactory module which decodes Mod_Gearman metrics
    into a MetricFactory format.***

    Receives Nagios spool directory formatted data and decodes it into a
    MetricFactory format.

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

        - inbox:    Incoming events in Nagios spool directory format.
        - outbox:   Outgoing events in MetricFactory format.
    '''

    def __init__(self, name):
        PrimitiveActor.__init__(self, name)
        self.regex=re.compile('(.*?)(\D+)$')

    def consume(self,doc):
        try:
            for metric in self.decodeMetrics(doc["data"]):
                self.sendData({"header":doc["header"],"data":metric})
        except Exception as err:
            self.logging.warn('Malformatted performance data received. Reason: %s'%(err))

    def decodeMetrics(self, data):
        metadata={}
        for element in data.split("\t"):
            (key, value) = element.split('::')
            metadata[key.lower()]=value

        if 'serviceperfdata' in metadata:
            metric_type = "serviceperfdata"
        if 'hostperfdata' in metadata:
            metric_type = "hostperfdata"

        for metric in metadata[metric_type].split(" "):
            (key,value)=metric.split('=')
            value=value.split(";")[0]
            value_unit = self.regex.search(value)

            if value_unit == None:
                units=''
            elif value_unit.group(2):
                value=value_unit.group(1)
                units=value_unit.group(2)
            else:
                units=''
            yield ({"type":"nagios",
                    "time":metadata["timet"],
                    "source":metadata["hostname"],
                    "name":key,
                    "value":value,
                    "units":units,
                    "tags":[metadata.get("servicecheckcommand",metadata.get("hostcheckcommand","")),metadata.get("servicedesc","hostcheck")]
                    })

    def shutdown(self):
        self.logging.info('Shutdown')
