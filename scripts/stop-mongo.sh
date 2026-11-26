#!/usr/bin/env bash
DATA_DIR="${MONGO_DATA_DIR:-$HOME/.local/var/mongodb}"
mongod --dbpath "$DATA_DIR" --shutdown 2>/dev/null && echo "MongoDB stopped." || echo "MongoDB was not running."
