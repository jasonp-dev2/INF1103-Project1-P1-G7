"""Start the Expiry & Discount Advisor."""

import logging
import os

from dotenv import load_dotenv

from AIManager.AIManager import AIManager
from classes.IO_Manager import IO_Manager
from classes.logicManagerClass import logicManager
from data_manager.DataAccessError import DataAccessError
from data_manager.data_manager import DataManager
from ExpiryAdvisorApp import ExpiryAdvisorApp


def setup_logging() -> None:
    """Send diagnostic messages (e.g. AI failures) to logs/app.log."""
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        filename="logs/app.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def run() -> None:
    load_dotenv()
    setup_logging()

    io_manager = IO_Manager()
    ai_manager = AIManager()
    try:
        data_manager = DataManager()
    except DataAccessError as error:
        io_manager.show_warning(str(error))
        return

    ExpiryAdvisorApp(io_manager, ai_manager, logicManager(), data_manager).run()


if __name__ == "__main__":
    run()
