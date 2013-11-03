#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       decodemodgearman.py
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
import re
import sys

class ModGearman(Actor):
    '''**A module to decodes Mod_Gearman metrics into the default format.**

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

    Queues:

        - inbox:    Incoming events in Nagios spool directory format.
        - outbox:   Outgoing events in MetricFactory format.
    '''

    def __init__(self, name):
        Actor.__init__(self, name)
        self.regex=re.compile('(.*?)(\D+)$')

    def consume(self,event):
        try:
            for metric in self.decodeMetrics(event["data"]):
                self.queuepool.outbox.put({"header":event["header"],"data":metric})
        except Exception as err:
            self.logging.warn('Malformatted performance data received. Reason: %s'%(err))

    def decodeMetrics(self, data):

        #DATATYPE::SERVICEPERFDATA\t
        #TIMET::1383478571\t
        #HOSTNAME::dev-umi-master-101.flatns.net\t
        #SERVICEDESC::Default Processes\t
        #SERVICEPERFDATA::check_multi::check_multi::plugins=5 time=0.058422\t
        #SERVICECHECKCOMMAND::check:nagios.multicheck.status\t
        #SERVICESTATE::0\t
        #SERVICESTATETYPE::1\n\n\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00

        metadata={}
        for element in data.split("\t"):
            parts = re.search('(.*?)::(.*)',element)
            metadata[parts.group(1).lower()]=parts.group(2)

        if 'serviceperfdata' in metadata:
            metric_type = "serviceperfdata"
        if 'hostperfdata' in metadata:
            metric_type = "hostperfdata"

        for metric in re.sub('.*::', '', metadata[metric_type]).split(' '):
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
            tags=[]
            tags.append(self.__filter(metadata.get("servicecheckcommand",metadata.get("hostcheckcommand",""))))
            if "servicedesc" in metadata:
                tags.append(self.__filter(metadata["servicedesc"]))
                tags.append("servicecheck")
                basename=self.__filter(metadata["servicedesc"])
            else:
                basename="hostcheck"
                tags.append("hostcheck")

            #(1381002603.726132, 'wishbone', 'hostname', 'queue.outbox.in_rate', 0, '', ())
            yield((metadata["timet"], "nagios", self.__filter(metadata["hostname"]), "%s.%s"%(basename, self.__filter(key)), value, units, tuple(tags)))

    def __filter(self, name):
        '''Filter out problematic characters.

        This should become a separate module allowing the user to define filter rules
        from a bootstrap file and most likely become a separate module.
        '''

        name=name.replace("'",'')
        name=name.replace('"','')
        name=name.replace('!(null)','')
        name=name.replace(" ","_")
        name=name.replace("/","_")
        return name.lower()