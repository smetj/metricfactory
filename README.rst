MetricFactory
=============

Accept, process and submit metrics.


What?
-----

Build servers which accept, process and submit metrics with minimum effort.


How?
----

MetricFactory uses the WishBone library to build servers which allow you to
accept, convert and process metrics from one source and submit them to another
destination.

MetricFactory only contains encoders, decoders and filter modules which allow
yo to process metrics.  Besides these modules you will also require one or
more Wishbone IOmodules which allows you to accept and submit the metrics
outside of the framework.

Using a bootstrap file you select and connect different modules into an event
pipeline and start a Metricfactory server from commandline.


Installation
------------

Download from Github and run:

    $ python setup.py install

The installer will automatically download the latest version of Wishbone
https://github.com/smetj/wishbone from Github.


Usage
-----

Have a look at the available modules:

    $ metricfactory list

To start 2 parallel instances of a server in the background:

    $ metricfactory start --config /path/to/boostrapfile.json --instances 2


Examples
--------

https://github.com/smetj/experiments/tree/master/metricfactory
