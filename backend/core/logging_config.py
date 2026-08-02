"""One place that decides what logs look like.

Called once from the app lifespan, before anything else runs. Two rules:

1. Every line is timestamped and names its logger. A scheduled system that fires
   at 2 PM and fails at 2:15 is unreadable without timestamps.
2. Unhandled exceptions are logged with a traceback rather than printed. print()
   does not reach a log aggregator and cannot be filtered by level.
"""

import logging
import sys

_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S%z"

log = logging.getLogger("overseer")


def setup_logging(level: str = "INFO") -> None:
    root = logging.getLogger()

    # Reconfigure cleanly even if uvicorn/pytest already installed handlers.
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # These two are chatty at INFO and drown out everything that matters.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)

    # Anything that escapes to the top level must leave a traceback behind.
    def _on_uncaught(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        log.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))

    sys.excepthook = _on_uncaught
