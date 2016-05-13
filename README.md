# Docker service reporter 

This is a small python script that will discover all running
docker containers and store information about them in etcd.

## Why?

Having service details in shared storage such as etcd allows
other processes to discover services, or automate configuration
or administration tasks (such as configuring reverse proxies).

## Usage

The container requires access to the docker API, so you need
to volume mount the docker socket:

```bash
docker run -d --name service-reporter \
              --restart always \
              -v /var/run/docker.sock:/var/run/docker.sock \ 
              csmith/service-reporter:latest
```

## Schema

The script stores values relating to containers, labels, and
networks in etcd:

```
/docker/containers/{name}/image = "ubuntu:xenial"
                         /labels/service = "foo"
                         /labels/org.example.some-label = "bar"
                         /net/addr/{network1} = "172.1.2.3"
                                  /{network2} = "172.0.2.3"
                             /ports/tcp/{container_port1} = {host_port} 
                                       /{container_port2} = 0 # Not exposed
                                   /udp/...

/docker/labels/{label_1}/{container_name_1} = "foo"
                        /{container_name_2} = "bar"
              /{label_2}/...

/docker/networks/{network1}/{container_name_1} = "172.1.2.3"
                           /{container_name_2} = "172.0.2.3"
                /{network2}/...
```

## Current known issues

* The docker node is deleted when the script starts, so you can't run multiple
  copies on multiple hosts
* The script updates once and exits, instead of listening for events
* There's no way to get notified when the script has finished, rather than
  mid-update

