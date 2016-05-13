#!/usr/bin/env python3

from collections import defaultdict
from monitor import Monitor
import argparse
import etcd


def etcd_put(client, prefix, obj):
  for key, value in obj.items():
    new_prefix = "%s/%s" % (prefix, key)

    if isinstance(value, dict):
      etcd_put(client, new_prefix, value)
    else:
      client.write(new_prefix, str(value))


def add_containers(new_containers):
  global containers, host_index, label_index, network_index
  for container in new_containers:
    name = container['name']
    containers[name] = container

    for k, v in container['labels'].items():
      label_index[k][name] = v
    for k, v in container['net']['addr'].items():
      network_index[k][name] = v

    host_index[host][name] = name

  etcd_put(etcd_client, prefix + '/containers', containers)
  etcd_put(etcd_client, prefix + '/labels', label_index)
  etcd_put(etcd_client, prefix + '/networks', network_index)
  etcd_put(etcd_client, prefix + '/hosts', host_index)


def remove_containers(old_containers):
  global containers, host_index, label_index, network_index
  for container in old_containers:
    name = container['name']
    del containers[name]
    etcd_client.delete(prefix + '/containers/' + name, recursive=True)

    for k, v in container['labels'].items():
      del label_index[k][name]
      etcd_client.delete(prefix + '/labels/' + k + '/' + name)
    for k, v in container['net']['addr'].items():
      del network_index[k][name]
      etcd_client.delete(prefix + '/networks/' + k + '/' + name)
    etcd_client.delete(prefix + '/hosts/' + host + '/' + name)


parser = argparse.ArgumentParser()
parser.add_argument('--name', help='Name of this docker host', default='unknown')
parser.add_argument('--etcd-port', type=int, help='Port to connect to etcd on', default=2379)
parser.add_argument('--etcd-host', help='Host to connect to etcd on', default='etcd')
parser.add_argument('--etcd-prefix', help='Prefix to use when adding keys to etcd', default='/docker')
args = parser.parse_args()

monitor = Monitor(args.name, add_containers, remove_containers)
etcd_client = etcd.Client(host=args.etcd_host, port=args.etcd_port)
prefix = args.etcd_prefix
host = args.name

containers = {}
label_index = defaultdict(dict) 
network_index = defaultdict(dict)
host_index = defaultdict(dict)

try:
  etcd_client.delete(prefix, recursive=True)
except etcd.EtcdKeyNotFound:
  pass

monitor.monitor()
