import sys
import threading
import time
import uvicorn
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl

# 1. IMPORT YOUR ORIGINAL APP
# Replace 'main' with your filename and 'app' with your FastAPI variable name
from main import app 

def run_server():
    """Runs the FastAPI server in the background."""
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

class DesktopWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Digital Notice Board - Desktop")
        self.resize(1200, 800)

        # Create the web view (The "Browser" inside the app)
        self.browser = QWebEngineView()
        
        # Load your FastAPI URL
        self.browser.setUrl(QUrl("http://127.0.0.1:8000"))

        # Layout setup
        layout = QVBoxLayout()
        layout.addWidget(self.browser)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

if __name__ == "__main__":
    # 2. START FASTAPI IN A BACKGROUND THREAD
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Give the server a second to boot up before opening the window
    time.sleep(1)

    # 3. START THE PYQT APPLICATION
    qt_app = QApplication(sys.argv)
    window = DesktopWindow()
    window.show()
    sys.exit(qt_app.exec())