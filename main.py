# main.py
"""
Main entry point for the Sheet Pile Wall Analysis Tool.
"""

import sys
from PyQt6.QtWidgets import QApplication
from ui import MainWindow  

def main():
    """Initializes and runs the Qt application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setWindowTitle("Modern Sheet Pile Wall Analysis")
    window.resize(1600, 900)  
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
