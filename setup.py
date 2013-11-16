#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  setup.py
#
#  Copyright 2013 Jelle Smet <development@smetj.net>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import sys

PROJECT = 'metricfactory'
VERSION = '0.2.2'
install_requires=['wishbone']

try:
    long_description = open('README.rst', 'rt').read()
except IOError:
    long_description = ''

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)

setup(
    name=PROJECT,
    version=VERSION,

    description='A set of Wishbone modules to consume, process and submit metrics.',
    long_description=long_description,

    author='Jelle Smet',
    author_email='development@smetj.net',

    url='https://github.com/smetj/metricfactory',
    download_url='https://github.com/smetj/metricfactory/tarball/master',

    classifiers=['Development Status :: 4 - Beta',
                 'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.6',
                 'Programming Language :: Python :: 2.7',
                 'Intended Audience :: Developers',
                 'Intended Audience :: System Administrators',
                 ],
    platforms=['Linux'],

    provides=[],
    install_requires=install_requires,
    namespace_packages=[],
    packages=find_packages(),
    zip_safe=False,
    entry_points={
        'console_scripts': ['metricfactory = metricfactory.main:main'],
        'metricfactory.encoder': [
        "graphite = metricfactory.encoder:Graphite"
        ],
        'metricfactory.decoder': [
        "modgearman = metricfactory.decoder:ModGearman",
        "ganglia = metricfactory.decoder:Ganglia",
        "elasticsearch = metricfactory.decoder:Elasticsearch"
        ],
        'metricfactory.filter': [
        "metricfilter = metricfactory.filter:MetricFilter"
        ],
        'metricfactory.test': [
        "hammer = metricfactory.test:Hammer"
        ]

    }
)
