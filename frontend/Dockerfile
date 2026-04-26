FROM alpine:3 AS builder

RUN apk add --no-cache nodejs npm

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npx gulp

FROM alpine:3

RUN apk add --no-cache nginx envsubst certbot certbot-nginx && \
    adduser -D -G nginx appuser

COPY --from=builder /app/output /usr/share/nginx/html
COPY default.template /etc/nginx/http.d/default.template
COPY run.sh /app/
EXPOSE 80

CMD ["/bin/sh","/app/run.sh"]
