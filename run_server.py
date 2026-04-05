"""
run_server.py
Convenience launcher for the FastAPI backend.

Usage:
    python run_server.py
"""

import uvicorn
from config.settings import API_HOST, API_PORT, DEBUG

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=DEBUG,
    )