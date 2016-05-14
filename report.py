#!/usr/bin/env python3

from monitor import Monitor
from updater import Updater
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--name', help='Name of this docker host', default='unknown')
parser.add_argument('--etcd-port', type=int, help='Port to connect to etcd on', default=2379)
parser.add_argument('--etcd-host', help='Host to connect to etcd on', default='etcd')
parser.add_argument('--etcd-prefix', help='Prefix to use when adding keys to etcd', default='/docker')
args = parser.parse_args()

updater = Updater(args.etcd_host, args.etcd_port, args.etcd_prefix)
monitor = Monitor(args.name, updater.add_containers, updater.remove_containers)

updater.wipe()
monitor.monitor()

