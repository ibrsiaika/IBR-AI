"""
API Server entrypoint — allows `python -m ibr_platform.api.server`.

Starts a uvicorn server on 0.0.0.0:8000.
"""
import uvicorn

from . import app  # noqa: F401  (re-export so app is constructed)


def main() -> None:
    """Run the API server with uvicorn."""
    uvicorn.run(
        "ibr_platform.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
