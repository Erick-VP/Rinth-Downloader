"""
Configuração central de logging: tudo que acontece vai pra tela (nível INFO)
e também pra um arquivo de log (nível DEBUG, mais detalhado), pra dar pra
debugar depois se algo falhar no meio de uma execução grande.
"""
import logging
from pathlib import Path

LOG_DIR = Path.home() / ".modrinth_toolkit_logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "modrinth_toolkit.log"

_configured = False


def get_logger(name: str = "modrinth_toolkit") -> logging.Logger:
    global _configured
    logger = logging.getLogger(name)

    if not _configured:
        logger.setLevel(logging.DEBUG)

        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter("%(message)s"))

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        _configured = True

    return logger
