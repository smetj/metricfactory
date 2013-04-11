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

Using a bootstrap file you can start a Metricfactory server from commandline.


Installation
------------

Download from Github and run:

    $ python setup.py install

The installer will automatically download the latest version of Wishbone
https://github.com/smetj/wishbone from Github.


Usage
-----



Examples
--------

https://github.com/smetj/experiments/tree/master/metricfactory
