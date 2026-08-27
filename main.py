import sys
import os
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter
from PySide6.QtCore import Qt
from gui.main_window import MainWindow
from gui.tray_icon import TrayIcon
from core.config import config

logging.basicConfig(
    level=getattr(logging, config.get_setting("logging_level") or "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)

def create_placeholder_icon():
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor("transparent"))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    painter.setBrush(QColor("#4CAF50")) # Green circle
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(2, 2, 60, 60)
    
    painter.setPen(QColor("white"))
    font = painter.font()
    font.setPixelSize(30)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "AC")
    
    painter.end()
    return QIcon(pixmap)

def main():
    logger.info("Initializing AirClicker...")
    
    app = QApplication(sys.argv)
    
    # Ensure High DPI support is standard in PySide6
    app.setStyle("Fusion")
    
    # Global Dark Stylesheet
    app.setStyleSheet("""
        QWidget {
            background-color: #1e1e1e;
            color: #eeeeee;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        QScrollBar:vertical {
            border: none;
            background: #2a2a2a;
            width: 10px;
            margin: 0px 0px 0px 0px;
        }
        QScrollBar::handle:vertical {
            background: #555;
            min-height: 20px;
            border-radius: 5px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            border: none;
            background: none;
        }
    """)
    
    # Setup Application Icon
    app_icon = create_placeholder_icon()
    app.setWindowIcon(app_icon)
    
    # Create Main App Window
    window = MainWindow()
    if not config.get_setting("minimize_to_tray") or "--start-minimized" not in sys.argv:
        window.show()
    
    # Setup System Tray
    tray_icon = TrayIcon(app_icon, app)
    # Using window.showNormal raises the window if minimized/hidden, activate brings it forward.
    tray_icon.show_window_signal.connect(window.showNormal)
    tray_icon.show_window_signal.connect(window.activateWindow)
    
    def on_quit():
        window.cleanup()
        app.quit()
        
    tray_icon.quit_signal.connect(on_quit)
    tray_icon.show()
    
    logger.info("AirClicker GUI loop started.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
