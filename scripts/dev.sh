#!/usr/bin/env bash
# Start MongoDB, the API (port 5050) and the web app (port 5173). Ctrl+C stops both servers.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="$HOME/.local/bin:$HOME/.local/node/bin:$HOME/.local/mongodb/bin:$PATH"

"$ROOT/scripts/start-mongo.sh"
[ -f "$ROOT/server/.env" ] || {
  sed "s/^JWT_SECRET=$/JWT_SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))')/" \
    "$ROOT/server/.env.example" > "$ROOT/server/.env"; echo "Created server/.env"; }
(cd "$ROOT/server" && uv sync -q)
[ -d "$ROOT/client/node_modules" ] || (cd "$ROOT/client" && npm install --no-fund --no-audit)

trap 'kill 0' EXIT INT TERM
(cd "$ROOT/server" && uv run python run.py) &
(cd "$ROOT/client" && npx vite --host 127.0.0.1) &
echo "API: http://127.0.0.1:5050   App: http://localhost:5173   (models take ~10s to load)"
wait
