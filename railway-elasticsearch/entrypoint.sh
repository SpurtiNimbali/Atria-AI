#!/usr/bin/env bash
# Railway volumes are root-owned; official ES image runs as UID 1000 and cannot
# chown. We fix ownership as root, then exec the stock entrypoint as elasticsearch.
# ES 8 explicitly refuses to run as root, so RAILWAY_RUN_UID=0 is incompatible.
set -euo pipefail
DATA="/usr/share/elasticsearch/data"
mkdir -p "$DATA"
chown -R elasticsearch:elasticsearch "$DATA" || true
exec runuser -u elasticsearch -- /usr/local/bin/docker-entrypoint.sh "$@"
