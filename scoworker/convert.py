import json
import sys

with open(sys.argv[1], 'r') as f:
    d = f.read().replace('\'', '"')
    d = '{"data":' + d + '}'
    data = json.loads(d)['data']

print 'pid,mid,correlation'
for i in data:
    #print str(i['pid'])
    #print str(i['mid'])
    #print str(i['correlation'])
    print ','.join([str(i['pid']), str(i['mid']), str(i['correlation'])])
