"""Tool Registry: FastAPI app entry point."""
from app.core.logging_config import configure_logging
from app.factory import create_app

configure_logging()

app = create_app()
