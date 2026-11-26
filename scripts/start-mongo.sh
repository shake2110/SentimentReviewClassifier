#!/usr/bin/env bash
# Starts a local MongoDB in the background (data lives outside the repo).
set -euo pipefail
DATA_DIR="${MONGO_DATA_DIR:-$HOME/.local/var/mongodb}"
LOG_FILE="$DATA_DIR/mongod.log"
mkdir -p "$DATA_DIR"
if pgrep -x mongod >/dev/null; then
  echo "MongoDB is already running."
  exit 0
fi
mongod --dbpath "$DATA_DIR" --bind_ip 127.0.0.1 --port 27017 --fork --logpath "$LOG_FILE" >/dev/null
echo "MongoDB started on 127.0.0.1:27017 (data: $DATA_DIR, log: $LOG_FILE)"
