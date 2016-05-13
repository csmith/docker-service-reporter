#!/usr/bin/env python3

from collections import defaultdict
import docker 
import etcd


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


docker_client = docker.Client(base_url='unix://var/run/docker.sock')
etcd_client = etcd.Client(host='etcd', port=4001)
prefix = '/docker'

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
