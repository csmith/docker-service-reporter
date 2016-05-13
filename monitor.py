#!/usr/bin/env python3

from collections import defaultdict
import docker


class Monitor:

  def __init__(self, host_name, on_added, on_removed):
    self._client = docker.Client(base_url='unix://var/run/docker.sock')
    self._containers = defaultdict(dict)
    self._host = host_name
    self._on_added = on_added
    self._on_removed = on_removed
    self._events = self._client.events(decode=True,
                                       filters={'type': 'container',
                                                'event': ['die', 'start']})


  def monitor(self):
    self._add(self._client.containers())

    for event in self._events:
      if event['Action'] == 'start':
        self._add(self._client.containers(filters={'id': event['id']}))
      elif event['Action'] == 'die':
        self._remove(event['id'])
      else:
        print('Monitor.monitor(): unexpected event %s' % event['Action'])


  def _add(self, infos):
    res = []
    for info in infos:
      container = {
        'host': self._host,
        'image': info['Image'],
        'labels': info['Labels'],
        'name': info['Names'][0][1:],
        'net': {
          'addr': self._get_addresses(info),
          'ports': self._get_ports(info)
        }
      }

      self._containers[info['Id']] = container
      res.append(container)

    self._on_added(res)


  def _remove(self, container_id):
    if container_id in self._containers:
      container = self._containers[container_id]
      del self._containers[container_id]
      self._on_removed([container])


  def _get_addresses(self, container):
    return {k: v['IPAddress'] for k, v in container['NetworkSettings']['Networks'].items()}


  def _get_ports(self, container):
    ports = defaultdict(dict)
    for port in container['Ports']:
      ports[port['Type']][port['PrivatePort']] = port['PublicPort'] if 'PublicPort' in port else 0
    return ports

