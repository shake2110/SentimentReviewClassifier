"""Start the API:  uv run python run.py   (from the server/ directory)."""
import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5050"))  # 5000 is taken by AirPlay on macOS
    app.run(host="127.0.0.1", port=port, debug=os.getenv("FLASK_DEBUG") == "1", use_reloader=False)
