#/bin/sh

envsubst '${NGINX_SERVER_NAME}' < /etc/nginx/http.d/default.template > /etc/nginx/http.d/default.conf

echo "ENV set to ${ENV}"
if [[ "$ENV" == "production" ]]; then
    certbot --nginx --non-interactive --agree-tos --domains "${NGINX_SERVER_NAME}"
    pkill -9 nginx
fi

nginx -g 'daemon off'