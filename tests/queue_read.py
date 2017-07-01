import getopt
import json
import pika
import sys

from scoengine import ModelRunRequest


def callback(ch, method, properties, body):
    """Callback handler for client requests."""
    # Read model run request (expects Json object)
    try:
        request = ModelRunRequest.from_json(json.loads(body))
    except Exception as ex:
        print ex
        ch.basic_ack(delivery_tag = method.delivery_tag)
        return
    # Request identifier for logging purposes
    req_id = request.experiment_id + ':' + request.run_id
    # Run request using local worker
    print 'Start model run [' + req_id + ']'
    print 'Done [' + req_id + ']'
    ch.basic_ack(delivery_tag = method.delivery_tag)


# Connection parameter
hostname = 'localhost'
queue = 'sco'
password = ''
port = 5672
user = 'sco'
virtual_host = '/sco'
# Get command line arguments
try:
    opts, args = getopt.getopt(
        sys.argv[1:],
        'c:h:q:p:u:v:',
        ['host=', 'queue=', 'password=', 'port=', 'user=', 'vhost=']
    )
except getopt.GetoptError:
    print """queue_writer [parameters]

    Parameters:
    -----------

    -c, --port <port>         : Port that the RabbitMQ server is listening on (default: 5672)
    -h, --host= <hostname>    : Name of host running RabbitMQ server (default: localhost)
    -p, --password <pwd>      : RabbitMQ user password (default: '')
    -q, --queue= <quename>    : Name of RabbitMQ message queue (default: sco)
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
    elif opt in ('-h', '--host'):
        hostname = param
    elif opt in ('-p', '--password'):
        password = param
    elif opt in ('-q', '--queue'):
        queue = param
    elif opt in ('-u', '--user'):
        user = param
    elif op in ('-v', '--vhost'):
        virtual_host = param

# Open connection to RabbitMQ server.
print 'CONNECT: [USER=' + user + ', PASSWORD=' + password + ']'
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
print 'Waiting for requests. To exit press CTRL+C'
channel.start_consuming()
