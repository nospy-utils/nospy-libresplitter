#/bin/sh

chmod o+r -R /usr/share/nginx/html
envsubst '${NGINX_SERVER_NAME}' < /etc/nginx/http.d/default.template > /etc/nginx/http.d/default.conf

echo "ENV set to ${ENV}"
if [[ "$ENV" == "production" ]]; then
    certbot --nginx --non-interactive --agree-tos --domains "${NGINX_SERVER_NAME}" -v --test-cert
    pkill -9 nginx
fi

nginx -g 'daemon off;'