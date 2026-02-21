from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

class CyberTheme:
    # Colors
    BACKGROUND = "#1E1E1E"
    FOREGROUND = "#FF00FF" # Magenta
    ACCENT = "#9400D3"     # Purple
    TEXT_COLOR = "#E0E0E0" # Light Grey for readability
    
    # Stylesheet
    STYLESHEET = f"""
    QMainWindow {{
        background-color: {BACKGROUND};
        color: {TEXT_COLOR};
    }}
    QWidget {{
        background-color: {BACKGROUND};
        color: {TEXT_COLOR};
        font-family: "Consolas", "Courier New", monospace;
    }}
    QLabel {{
        color: {FOREGROUND};
        font-weight: bold;
    }}
    QPushButton {{
        background-color: {ACCENT};
        color: white;
        border: 2px solid {FOREGROUND};
        border-radius: 5px;
        padding: 5px 10px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: {FOREGROUND};
        border-color: {ACCENT};
    }}
    QPushButton:pressed {{
        background-color: {BACKGROUND};
        color: {FOREGROUND};
    }}
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: #2D2D2D;
        border: 1px solid {ACCENT};
        color: {TEXT_COLOR};
        selection-background-color: {FOREGROUND};
    }}
    QTableWidget {{
        gridline-color: {ACCENT};
        selection-background-color: {ACCENT};
    }}
    QHeaderView::section {{
        background-color: {ACCENT};
        color: white;
        padding: 4px;
        border: 1px solid {BACKGROUND};
    }}
    QStatusBar {{
        color: {FOREGROUND};
    }}
    """

def apply_theme(app: QApplication):
    """Applies the Cyber Theme to the application."""
    app.setStyle("Fusion")
    
    # Set Palette for consistent look across platforms
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(CyberTheme.BACKGROUND))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(CyberTheme.TEXT_COLOR))
    palette.setColor(QPalette.ColorRole.Base, QColor("#2D2D2D"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(CyberTheme.BACKGROUND))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(CyberTheme.TEXT_COLOR))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(CyberTheme.TEXT_COLOR))
    palette.setColor(QPalette.ColorRole.Text, QColor(CyberTheme.TEXT_COLOR))
    palette.setColor(QPalette.ColorRole.Button, QColor(CyberTheme.ACCENT))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("white"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("red"))
    palette.setColor(QPalette.ColorRole.Link, QColor(CyberTheme.FOREGROUND))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(CyberTheme.ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("black"))
    
    app.setPalette(palette)
    app.setStyleSheet(CyberTheme.STYLESHEET)
