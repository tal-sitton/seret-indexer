FROM ghcr.io/tal-sitton/heb-elastic:latest

COPY esdata/. /usr/share/elasticsearch/data

USER root
RUN chown -R elasticsearch:elasticsearch /usr/share/elasticsearch/data
USER elasticsearch
