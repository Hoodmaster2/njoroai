import sys
from PyQt6.QtWidgets import QApplication
from src.utils.config import Config
from src.utils.logger import logger
from src.ui.main_window import MainWindow
from src.ui.theme import apply_theme
from src.tools.builtin import register_builtin_tools

def main():
    """Main application entry point."""
    try:
        # Validate configuration
        Config.validate()
        
        # Initialize Logging
        logger.info("Starting NJORO AI...")

        # Initialize Tools
        register_builtin_tools()
        logger.info("Built-in tools registered.")

        # Initialize UI
        app = QApplication(sys.argv)
        app.setApplicationName(Config.APP_NAME)
        app.setApplicationVersion(Config.APP_VERSION)
        
        # Apply Theme
        apply_theme(app)
        
        # Show Main Window
        window = MainWindow()
        window.show()
        
        # Start Event Loop
        sys.exit(app.exec())
        
    except Exception as e:
        logger.critical(f"Application crash: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
