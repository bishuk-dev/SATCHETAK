from __future__ import annotations

import os

import uvicorn


def main() -> None:
    uvicorn.run(
        "satchetak.main:app",
        host=os.environ.get("SATCHETAK_HOST", "127.0.0.1"),
        port=int(os.environ.get("SATCHETAK_PORT", "8000")),
        reload=os.environ.get("SATCHETAK_RELOAD", "0") == "1",
    )


if __name__ == "__main__":
    main()
