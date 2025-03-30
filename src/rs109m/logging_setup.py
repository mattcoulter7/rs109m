import logging
from pathlib import Path

def configure_logging() -> None:
    """
    Configure logging to write to ~/.rs109m/logs/rs109m.log
    as well as to the console (stdout).
    """
    # 1) Build the log directory path: ~/.rs109m/logs
    log_dir = Path.home() / ".rs109m" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # 2) Build the full log file path: ~/.rs109m/logs/rs109m.log
    log_file = log_dir / "rs109m.log"

    # 3) Set up basicConfig with desired level and format
    logging.basicConfig(
        level=logging.DEBUG,  # or DEBUG, etc.
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            # Writes log records to ~/.rs109m/logs/rs109m.log
            logging.FileHandler(log_file, mode='a', encoding='utf-8'),
            # Also prints log records to the console
            logging.StreamHandler()
        ]
    )
