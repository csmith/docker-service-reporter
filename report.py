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


def add_containers(infos):
  global containers, label_index, network_index
  for info in infos:
    container = {
      'image': info['Image'],
      'labels': info['Labels'],
      'net': {
        'addr': get_addresses(info),
        'ports': get_ports(info)
      }
    }

    name = info['Names'][0][1:]
    containers[name] = container

    for k, v in container['labels'].items():
      label_index[k][name] = v
    for k, v in container['net']['addr'].items():
      network_index[k][name] = v


parser = argparse.ArgumentParser()
parser.add_argument('--name', help='Name of this docker host', default='unknown')
parser.add_argument('--etcd-port', type=int, help='Port to connect to etcd on', default=2379)
parser.add_argument('--etcd-host', help='Host to connect to etcd on', default='etcd')
parser.add_argument('--etcd-prefix', help='Prefix to use when adding keys to etcd', default='/docker')
args = parser.parse_args()

docker_client = docker.Client(base_url='unix://var/run/docker.sock')
etcd_client = etcd.Client(host=args.etcd_host, port=args.etcd_port)
prefix = args.etcd_prefix

event_gen = docker_client.events(decode=True, filters={'type': 'container', 'event': ['die', 'start']})

containers = {}
label_index = defaultdict(dict) 
network_index = defaultdict(dict)

add_containers(docker_client.containers())

try:
  etcd_client.delete(prefix, recursive=True)
except etcd.EtcdKeyNotFound:
  pass

etcd_put(etcd_client, prefix + '/containers', containers)
etcd_put(etcd_client, prefix + '/labels', label_index)
etcd_put(etcd_client, prefix + '/networks', network_index)

for event in event_gen:
  if event['Action'] == 'start':
    print('New container %s' % event['id'])
    add_containers(docker_client.containers(filters={'id': event['id']}))
  elif event['Action'] == 'die':
    print('Dead container %s' % event['id'])
  else:
    print('Unexpected event %s' % event['Action'])

