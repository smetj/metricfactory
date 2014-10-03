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

    '''**Decode Nagios peformance data coming from Mod_Gearman.**

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

        - name(str)
           |  The name of the module.

        - size(int)
           |  The default max length of each queue.

        - frequency(int)
           |  The frequency in seconds to generate metrics.

        - sanitize_hostname(bool)(False)
           |  If True converts "." to "_".
           |  Might be practical when FQDN hostnames mess up the namespace
           |  such as Graphite.


    Queues:

        - inbox:    Incoming events in Nagios spool directory format.

        - outbox:   Outgoing events in MetricFactory format.
    '''

    def __init__(self, name, size=100, frequency=1, sanitize_hostname=False):
        Actor.__init__(self, name, size, frequency)
        self.regex = re.compile('(.*?)(\D+)$')
        self.sanitize_hostname = sanitize_hostname
        self.pool.createQueue("inbox")
        self.pool.createQueue("outbox")
        self.registerConsumer(self.consume, "inbox")

    def preHook(self):
        if self.sanitize_hostname:
            self.replacePeriod = self.__doReplacePeriod
        else:
            self.replacePeriod = self.__doNoReplacePeriod

    def consume(self, event):
        try:
            for metric in self.decodeMetrics(event["data"]):
                self.submit({"header": event["header"], "data": metric}, self.pool.queue.outbox)
        except Exception as err:

            self.logging.warn('Malformatted performance data received. Reason: %s Line: %s' % (err, sys.exc_traceback.tb_lineno))
            raise

    def decodeMetrics(self, data):

        # DATATYPE::HOSTPERFDATA    TIMET::1411637927   HOSTNAME::prod-cpp-corewspro-w2-204.flatns.net  HOSTPERFDATA::rta=0.751ms;3000.000;5000.000;0; pl=0%;80;100;;   HOSTCHECKCOMMAND::check:host.alive!(null)   HOSTSTATE::0    HOSTSTATETYPE::1
        # DATATYPE::SERVICEPERFDATA TIMET::1411637603   HOSTNAME::ct-cpp-pgdball-w0-001.flatns.net  SERVICEDESC::Postgres backends sources  SERVICEPERFDATA::time=0.02  'kangaroo'=20;540;570;0;600 'moma'=0;540;570;0;600 'postgres'=1;540;570;0;600 'slf'=128;540;570;0;600 'template0'=0;540;570;0;600 'template1'=0;540;570;0;600 'trafficsign'=42;540;570;0;600    SERVICECHECKCOMMAND::check:postgres.backends.status SERVICESTATE::0 SERVICESTATETYPE::1

        d = self.__chopStringDict(data)

        for metric in re.findall('(\w*?\'*=\d*(?:\.\d*)?(?:s|us|ms|%|B|MB|KB|TB|c)?)', d["perfdata"]):
            # name and value
            (metric_name, metric_value) = metric.split('=')
            metric_name = self.__filter(metric_name)

            # metric time
            metric_timet = d["timet"]

            # metric unit
            re_unit = re.search("\D+$", metric_value)
            if re_unit is None:
                metric_unit = ''
            else:
                metric_unit = re_unit.group(0)
            metric_value = metric_value.rstrip(metric_unit)

            # tags
            tags = [d["type"], d["checkcommand"]]

            yield (metric_timet, "nagios", d["hostname"], "%s.%s" % (d["name"], metric_name), metric_value, metric_unit, tuple(tags))

    def __chopStringDict(self, data):
        '''Returns a dictionary of the provided raw service/host check string.'''

        r = {}
        d = data.split('\t')
        for item in d:
            item_parts = item.split('::')
            if len(item_parts) == 2:
                (name, value) = item_parts
            else:
                name = item_parts[0]
                value = item_parts[1]

            name = self.__filter(name)
            r[name] = value

        if "hostperfdata" in r:
            r["type"] = "hostcheck"
            r["perfdata"] = r["hostperfdata"]
            r["checkcommand"] = re.search("(.*?)!\(?.*", r["hostcheckcommand"]).group(1)
            r["name"] = "hostcheck"
        else:
            r["type"] = "servicecheck"
            r["perfdata"] = r["serviceperfdata"]
            r["checkcommand"] = re.search("((.*)(?=\!)|(.*))", r["servicecheckcommand"]).group(1)
            r["name"] = self.__filter(r["servicedesc"])

        r["hostname"] = self.replacePeriod(self.__filter(r["hostname"]))

        return r

    def __filter(self, name):
        '''Filter out problematic characters.

        This should become a separate module allowing the user to define filter rules
        from a bootstrap file and most likely become a separate module.
        '''

        name = name.replace("'", '')
        name = name.replace('"', '')
        name = name.replace('!(null)', '')
        name = name.replace(" ", "_")
        name = name.replace("/", "_")
        name = name.replace(".", "_")
        return name.lower()

    def __doReplacePeriod(self, data):
        return data.replace(".", "_")

    def __doNoReplacePeriod(self, data):
        return data
