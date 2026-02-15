import sys
from PySide6.QtWidgets import QApplication, QLabel

def main() -> int:
    app = QApplication(sys.argv)
    window = QLabel("Network Monitor")
    window.setWindowTitle("Network Monitor")
    window.resize(320, 120)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
