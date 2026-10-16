import logging


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,  # minimum level of severity (e.g. DEBUG (severity = 10) will not be displayed)
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%m/%d/%Y %I:%M %p",  # MM/DD/YYYY HH:MM AM/PM (e.g., 10/14/2026 06:04 PM)
    )
