#!/bin/bash

source ~/.bashrc

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

docker-compose -f docker-compose.yml down

git pull

docker rmi nospy-libresplitter_frontend nospy-libresplitter_backend alpine:3

docker-compose -f docker-compose.yml up --build -d