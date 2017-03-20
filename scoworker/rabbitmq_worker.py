#!venv/bin/python
"""SCO Workflow Engine Server - Implementation of the workflow server as a
RabbitMQ worker.
"""
import getopt
import json
import logging
import pika
import sys

from scocli import SCOClient
from scodata import SCODataStore
from scodata.mongo import MongoDBFactory
from scoengine import ModelRunRequest
from scoworker import SCODataStoreWorker, SCOClientWorker


# ------------------------------------------------------------------------------
#
# Global Variables
#
# ------------------------------------------------------------------------------

# Worker instance to handle model run request
worker = None


# ------------------------------------------------------------------------------
#
# RabbitMQ Callback handle
#
# ------------------------------------------------------------------------------

def callback(ch, method, properties, body):
    """Callback handler for client requests. Uses local worker, i.e. expects to
    be running on the same machine as the SCO data store.
    """
    # Read model run request (expects Json object)
    try:
        request = ModelRunRequest.from_json(json.loads(body))
    except Exception as ex:
        logging.exception(ex)
        ch.basic_ack(delivery_tag = method.delivery_tag)
        return
    # Request identifier for logging purposes
    req_id = request.experiment_id + ':' + request.run_id
    # Run request using local worker
    logging.info('Start model run [' + req_id + ']')
    worker.run(request)
    logging.info('Done [' + req_id + ']')
    ch.basic_ack(delivery_tag = method.delivery_tag)


def handle_requests(hostname, port, virtual_host, queue, user, password):
    """Put all code to handle requests into one routine. Allows to catch
    ConnectionClosed exceptions without having the worker exit.
    """
    # Establish connection with RabbitMQ server
    logging.info('Start : [HOST=' + hostname + ', QUEUE=' + queue + ']')
    credentials = pika.PlainCredentials(user, password)
    con = pika.BlockingConnection(pika.ConnectionParameters(
        host=hostname,
        port=port,
        virtual_host=virtual_host,
        credentials=credentials
    ))
    channel = con.channel()
    channel.queue_declare(queue=queue, durable=True)
    # Fair dispatch. Never give a worker more than one message
    channel.basic_qos(prefetch_count=1)
    # Set callback handler to read requests and run the predictive model
    channel.basic_consume(callback, queue=queue)
    # Done. Start by waiting for requests
    logging.info('Waiting for requests. To exit press CTRL+C')
    channel.start_consuming()


if __name__ == '__main__':
    """Run the RabbitMQ worker. Usage:

    rabbitmq_worker [parameters]

    Parameters:
    -----------

    -c, --port <port>         : Port that the RabbitMQ server is listening on (default: 5672)
    -d, --data <data-dir>     : Path to data store directory or client cache (default '/tmp/sco')
    -e, --env= <subject_dir>  : Path to directory for average subject [mandatory]
    -h, --host= <hostname>    : Name of host running RabbitMQ server (default: localhost)
    -l, --log= <filename>     : Log file name (default: standard output)
    -p, --password <pwd>      : RabbitMQ user password (default: '')
    -q, --queue= <quename>    : Name of RabbitMQ message queue (default: sco)
    -s, --server <url>        : Url for SCO Web API server (only if remote worker is used)
    -u, --user <username>     : RabbitMQ user (default: sco)
    -v, --vhost <virtualhost> : RabbitMQ virtual host name
    """
    # Configuration parameter
    data_dir = '/tmp/sco'
    mongo_db = 'sco'
    env_dir = None
    hostname = 'localhost'
    queue = 'sco'
    logfile = None
    password = ''
    port = 5672
    remote_worker = False
    server_url = None
    user = 'sco'
    virtual_host = '/'
    # Get command line arguments
    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            'c:d:e:h:q:l:m:p:s:u:v:',
            ['data=', 'env=', 'host=', 'queue=', 'log=', 'mongodb=', 'password=', 'port=', 'server=', 'user=', 'vhost=']
        )
    except getopt.GetoptError:
        print """rabbitmq_worker [parameters]

        Parameters:
        -----------

        -c, --port <port>         : Port that the RabbitMQ server is listening on (default: 5672)
        -d, --data <data-dir>     : Path to data store directory or client cache (default '/tmp/sco')
        -e, --env= <subject_dir>  : Path to directory for average subject [mandatory]
        -h, --host= <hostname>    : Name of host running RabbitMQ server (default: localhost)
        -l, --log= <filename>     : Log file name (default: standard output)
        -m, --mongodb= <db-name>  : Name of MongoDB database for local datastore worker (default: sco)
        -p, --password <pwd>      : RabbitMQ user password (default: '')
        -q, --queue= <quename>    : Name of RabbitMQ message queue (default: sco)
        -s, --server <url>        : Url for SCO Web API server (only if remote worker is used)
        -u, --user <username>     : RabbitMQ user (default: sco)
        -v, --vhost <virtualhost> : RabbitMQ virtual host name (default: /)
        """
        sys.exit()
    for opt, param in opts:
        if opt in ('-c', '--port'):
            try:
                port = int(param)
            except ValueError as ex:
                print 'Invalid port: ' + param
                sys.exit()
        elif opt in ('-d', '--data'):
            data_dir = param
        elif opt in ('-e', '--env'):
            env_dir = param
        elif opt in ('-h', '--host'):
            hostname = param
        elif opt in ('-l', '--log'):
            logfile = param
        elif opt in ('-m', '--mongodb'):
            mongo_db = param
        elif opt in ('-p', '--password'):
            password = param
        elif opt in ('-q', '--queue'):
            queue = param
        elif opt in ('-r', '--remote'):
            remote_worker = True
        elif opt in ('-s', '--server'):
            # Only if the server Url is given the remote worker is used
            server_url = param
            remote_worker = True
        elif opt in ('-u', '--user'):
            user = param
        elif opt in ('-v', '--vhost'):
            virtual_host = param
    # Ensure that mandatory parameter -e|--env was given
    if env_dir is None:
        print 'Missing value for parameter -e | --env'
        sys.exit()
    # Initialize message and error logging
    if not logfile is None:
        logging.basicConfig(
            filename=logfile,
            level=logging.INFO,
            format='%(asctime)s %(levelname)s:%(message)s'
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s:%(message)s'
        )
    # Set worker instance based on given parameter
    if remote_worker:
        worker = SCOClientWorker(
            SCOClient(api_url=server_url, data_dir=data_dir),
            env_dir
        )
        logging.info('Worker : [Remote]')
    else:
        worker = SCODataStoreWorker(
            SCODataStore(MongoDBFactory(db_name=mongo_db), data_dir),
            env_dir
        )
        logging.info('Worker : [Local]')
    # Start an endless loop to handle requests. Necessary because pika throws
    # ConnectionClosed exception occasionally when sending acknowledgement. This
    # way we can keep a remote worker alive by re-connecting.
    while True:
        try:
            handle_requests(hostname, port, virtual_host, queue, user, password)
        except pika.exceptions.ConnectionClosed as ex:
            logging.exception(ex)
