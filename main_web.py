"""
Ponto de entrada — Financial Intelligence Center (Web Dashboard)
Uso local:  python main_web.py
Produção:   uvicorn web.server:app --host 0.0.0.0 --port $PORT
"""
import sys, os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env", encoding="utf-8", override=True)

import uvicorn
from web.server import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"\n⚡  Financial Intelligence Center")
    print(f"🌐  http://localhost:{port}\n")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
