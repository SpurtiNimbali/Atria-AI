#!/bin/sh
set -e
# Docker Compose: api:8000 | Railway (split services): api.railway.internal:8000
UP="${API_UPSTREAM:-api:8000}"
sed "s|__API_UPSTREAM__|${UP}|g" /opt/nginx.default.conf.template > /etc/nginx/conf.d/default.conf
exec nginx -g "daemon off;"
