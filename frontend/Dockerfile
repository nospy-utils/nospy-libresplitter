FROM alpine:3 AS builder

RUN apk add --no-cache nodejs npm

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npx gulp

FROM alpine:3

RUN apk add --no-cache nginx && \
    adduser -D -G nginx appuser

COPY --from=builder /app/output /usr/share/nginx/html
COPY default.conf /etc/nginx/http.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
