import getopt
import json
import pika
import sys

from scoengine import ModelRunRequest


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

channel.basic_publish(
    exchange='',
    routing_key=queue,
    body=json.dumps(ModelRunRequest('A', 'B', 'C').to_dict()),
    properties=pika.BasicProperties(
        delivery_mode = 2, # make message persistent
    )
)
