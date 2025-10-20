"""Logging utilities for NebulaVis."""

from __future__ import annotations

import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="[%(levelname)s] %(asctime)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )


class NamedLoggerAdapter(logging.LoggerAdapter):
    """Attach contextual information to log records."""

    def process(self, msg, kwargs):
        return f"[{self.extra.get('context', 'app')}] {msg}", kwargs
