MetricFactory
=============


What?
-----

A collection of Wishbone modules to build metric processing servers.


How?
----

MetricFactory makes use of the Wishbone framework to build metric processing
servers.

The collection of encoder, decoder and filter modules are interconnecting
processing blocks which enable you to construct a processing pipeline. You can
combine these modules with the [builtin Wishbone
modules](http://wishbone.readthedocs.org/en/latest/builtin%20modules.html).

Decoders convert metrics into an internal Wishbone format.  Encoders convert
them again to a native format.

A bootstrap file defines the modules, how they're initialized and connected
and allows you to start a server from cli.

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
