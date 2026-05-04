import sys
from pathlib import Path
from loguru import logger

logger.remove()

# ── Консоль ───────────────────────────────────────────────
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{name}</cyan> | <level>{message}</level>",
    level="INFO",
)

# ── Файл с ротацией ───────────────────────────────────────
log_file = Path(__file__).parent / "logs" / "bot_history.log"
log_file.parent.mkdir(parents=True, exist_ok=True)

logger.add(
    log_file,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name} | {message}",
    level="DEBUG",
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    encoding="utf-8"
)
