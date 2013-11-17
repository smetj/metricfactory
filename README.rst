MetricFactory
=============


What?
-----

A set of Wishbone modules to build metric processing servers.


How?
----

MetricFactory uses the WishBone library to build servers which allow you to
accept, convert and process metrics from one source and submit them to another
destination.

MetricFactory is collection of encoder, decoder and filter modules to build a
pipeline of functionality.  Besides these modules you will also require one or
more Wishbone modules from https://github.com/smetj/wishboneModules which
allow you to accept and submit the metrics outside of the framework.

Decoders convert metrics into an internal format.  Encoders convert them again
to a native format.

Using a bootstrap file you select and connect different modules into an event
pipeline and start a Metricfactory server from commandline.

For more information see https://wishbone.readthedocs.org/en/latest


Installation
------------

From Pypi:

    | $ easy_install metricfactory


From Github:

    | $ git clone https://github.com/smetj/metricfactory
    | $ cd metricfactory
    | $ python setup.py install


Usage
-----

Have a look at the available modules:

    | $ metricfactory list --group metricfactory.encoder
    | $ metricfactory list --group metricfactory.decoder
    | $ metricfactory list --group metricfactory.test
    | $ metricfactory list


To start 2 parallel instances of a server in the background:

    | $ metricfactory start --config /path/to/boostrapfile.yaml --instances 2


Examples
--------

https://github.com/smetj/experiments/tree/master/metricfactory
