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
        print('New container %s' % event['id'])
        self._add(self._client.containers(filters={'id': event['id']}))
      elif event['Action'] == 'die':
        print('Dead container %s' % event['id'])
      else:
        print('Unexpected event %s' % event['Action'])


  def _add(self, infos):
    res = []
    for info in infos:
      name = info['Names'][0][1:]
      container = {
        'host': self._host,
        'image': info['Image'],
        'labels': info['Labels'],
        'name': name,
        'net': {
          'addr': self._get_addresses(info),
          'ports': self._get_ports(info)
        }
      }

      self._containers[name] = container
      res.append(container)

    self._on_added(res)


  def _get_addresses(self, container):
    return {k: v['IPAddress'] for k, v in container['NetworkSettings']['Networks'].items()}


  def _get_ports(self, container):
    ports = defaultdict(dict)
    for port in container['Ports']:
      ports[port['Type']][port['PrivatePort']] = port['PublicPort'] if 'PublicPort' in port else 0
    return ports

