Standard Cortical Observer - Worker
===================================

Worker classes are used to execute predictive model run requests. Different implementations for these workers may exists. We currently distinguish based on the way they interact with the SCO data store to retrieve and create resources.

A worker that runs on the same machine as the SCO data store can use an instance of the SCODataStore class to access SCO resources. A worker that runs on a remote machine will use the SCOClient to access SCO resources.

Communication between the web server and the worker is via the SCO engine client using different Communication channels (e.g., socket IO or RabbitMQ).
