"""Central logging setup. Use get_logger(__name__) in each module."""
import logging

from app.core.config import settings


def configure_logging(level: str | None = None) -> None:
    """Configure root logger format and level. Call once at app startup."""
    level = (level or settings.log_level).upper()
    numeric = getattr(logging, level, logging.INFO)
    logging.basicConfig(
        level=numeric,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a logger for the given module name."""
    return logging.getLogger(name)
