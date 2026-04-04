FROM elasticsearch:8.11.0

USER root
COPY entrypoint.sh /railway-elasticsearch-entrypoint.sh
RUN chmod +x /railway-elasticsearch-entrypoint.sh

ENTRYPOINT ["/bin/tini", "--", "/railway-elasticsearch-entrypoint.sh"]
CMD ["eswrapper"]
