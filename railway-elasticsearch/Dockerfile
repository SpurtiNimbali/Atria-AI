FROM elasticsearch:8.11.0

USER root
COPY elasticsearch.yml /usr/share/elasticsearch/config/elasticsearch.yml
RUN chown elasticsearch:root /usr/share/elasticsearch/config/elasticsearch.yml
COPY entrypoint.sh /railway-elasticsearch-entrypoint.sh
RUN chmod +x /railway-elasticsearch-entrypoint.sh

ENTRYPOINT ["/bin/tini", "--", "/railway-elasticsearch-entrypoint.sh"]
CMD ["eswrapper"]
