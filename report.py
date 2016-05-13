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


docker_client = docker.Client(base_url='unix://var/run/docker.sock')
etcd_client = etcd.Client(host='etcd', port=4001)
prefix = '/docker'

containers = {}
label_index = defaultdict(dict) 
network_index = defaultdict(dict)

for container in docker_client.containers():
  name = container['Names'][0][1:]
  image = container['Image']
  labels = container['Labels']
  addrs = {}
  ports = defaultdict(dict)

  for net_name, net_config in container['NetworkSettings']['Networks'].items():
    addrs[net_name] = net_config['IPAddress']

  for port in container['Ports']:
    ports[port['Type']][port['PrivatePort']] = port['PublicPort'] if 'PublicPort' in port else 0

  containers[name] = {
    'image': image,
    'labels': labels,
    'net': {
      'addr': addrs,
      'ports': ports
    }
  }

  for k, v in labels.items():
    label_index[k][name] = v
  for k, v in addrs.items():
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
