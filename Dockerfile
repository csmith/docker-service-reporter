FROM python:3.5.1-alpine 
MAINTAINER Chris Smith <chris87@gmail.com> 

RUN \
  pip install \
    docker-py \
    python-etcd

COPY report.py /report.py
ENTRYPOINT ["python", "/report.py"]
