#/bin/sh
envsubst '${NGINX_SERVER_NAME}' < /etc/nginx/http.d/default.template > /etc/nginx/http.d/default.conf
nginx -g 'daemon off;'