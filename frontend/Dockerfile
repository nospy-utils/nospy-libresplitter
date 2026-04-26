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
COPY --from=builder /app/default.template /etc/nginx/http.d/default.template
COPY --from=builder /app/run.sh /app/
EXPOSE 80 443

CMD ["/bin/sh","/app/run.sh"]
