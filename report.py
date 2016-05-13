#!/usr/bin/env python3

from collections import defaultdict
import argparse
import docker 
import etcd
import sys


def etcd_put(client, prefix, obj):
  for key, value in obj.items():
    new_prefix = "%s/%s" % (prefix, key)

    if isinstance(value, dict):
      etcd_put(client, new_prefix, value)
    else:
      client.write(new_prefix, str(value))


def get_addresses(container):
  return {k: v['IPAddress'] for k, v in container['NetworkSettings']['Networks'].items()}


def get_ports(container):
  ports = defaultdict(dict)
  for port in container['Ports']:
    ports[port['Type']][port['PrivatePort']] = port['PublicPort'] if 'PublicPort' in port else 0
  return ports


parser = argparse.ArgumentParser()
parser.add_argument('--name', help='Name of this docker host', default='unknown')
parser.add_argument('--etcd-port', type=int, help='Port to connect to etcd on', default=2379)
parser.add_argument('--etcd-host', help='Host to connect to etcd on', default='etcd')
parser.add_argument('--etcd-prefix', help='Prefix to use when adding keys to etcd', default='/docker')
args = parser.parse_args()

docker_client = docker.Client(base_url='unix://var/run/docker.sock')
etcd_client = etcd.Client(host=args.etcd_host, port=args.etcd_port)
prefix = args.etcd_prefix

containers = {}
label_index = defaultdict(dict) 
network_index = defaultdict(dict)

for container in docker_client.containers():
  containers[container['Names'][0][1:]] = {
    'image': container['Image'],
    'labels': container['Labels'],
    'net': {
      'addr': get_addresses(container),
      'ports': get_ports(container)
    }
  }

for name, details in containers.items():
  for k, v in details['labels'].items():
    label_index[k][name] = v
  for k, v in details['net']['addr'].items():
    network_index[k][name] = v

try:
  etcd_client.delete(prefix, recursive=True)
except etcd.EtcdKeyNotFound:
  pass

etcd_put(etcd_client, prefix + '/containers', containers)
etcd_put(etcd_client, prefix + '/labels', label_index)
etcd_put(etcd_client, prefix + '/networks', network_index)

print(containers)
print(label_index)
print(network_index)
