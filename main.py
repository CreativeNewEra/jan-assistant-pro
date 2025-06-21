#!/usr/bin/env python3
"""
Jan Assistant Pro
A powerful local-first AI assistant with tools
"""

import os
import sys
from tkinter import messagebox

from src.core.logging_config import get_logger, setup_logging
from src.core.metrics import start_metrics_server

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

setup_logging()
logger = get_logger(__name__)

try:
    from src.gui.main_window import JanAssistantGUI
    from src.core.config import Config
except ImportError as e:
    logger.error(
        "Import error during startup",
        extra={"extra_fields": {"error": str(e)}},
    )
    logger.error("Please ensure all dependencies are installed: poetry install")
    sys.exit(1)


def main():
    """Main application entry point"""
    try:
        # Load configuration
        config = Config()

        # Start metrics server
        start_metrics_server(bind_address="localhost")

        # Create and run GUI
        app = JanAssistantGUI(config)
        app.run()

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start application: {str(e)}")
        logger.error(
            "Failed to start application",
            extra={"extra_fields": {"error": str(e)}},
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
