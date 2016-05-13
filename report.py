#!/usr/bin/env python3

from collections import defaultdict
import docker 
import etcd

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

for name, details in containers.items():
  cprefix = prefix + '/containers/' + name
  etcd_client.write(cprefix + '/image', details['image'])
  for k, v in details['labels'].items():
    etcd_client.write(cprefix + '/labels/' + k, v)
  for k, v in details['net']['addr'].items():
    etcd_client.write(cprefix + '/net/addr/' + k, v)
  for proto, ports in details['net']['ports'].items():
    for k, v in ports.items():
      etcd_client.write(cprefix + '/net/ports/' + proto + '/' + str(k), v)

for name, values in label_index.items():
  lprefix = prefix + '/labels/' + name + '/'
  for cont, value in values.items():
    etcd_client.write(lprefix + cont, value)

for name, values in network_index.items():
  nprefix = prefix + '/networks/' + name + '/'
  for cont, value in values.items():
    etcd_client.write(nprefix + cont, value)

print(containers)
print(label_index)
print(network_index)
