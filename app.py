import sys
from urllib.parse import urlparse
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineSettings
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

TARGET_URL = "https://www.mapchannels.com/routemaps3/map.htm"
ALLOWED_HOST = "www.mapchannels.com"

class MapEnginePage(QWebEnginePage):
    def __init__(self, allowed_host: str, parent=None):
        super().__init__(parent)
        self.allowed_host = allowed_host
        self.featurePermissionRequested.connect(self.handle_permission)

    def handle_permission(self, security_origin: QUrl, feature: QWebEnginePage.Feature):
        if feature == QWebEnginePage.Feature.Geolocation:
            self.setFeaturePermission(
                security_origin, 
                feature, 
                QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
            )

    def acceptNavigationRequest(self, url: QUrl, nav_type: QWebEnginePage.NavigationType, is_main_frame: bool) -> bool:
        if not is_main_frame:
            return True

        target_host = url.host()
        if not target_host or target_host == self.allowed_host or target_host.endswith("." + self.allowed_host):
            return True

        return False

    def createWindow(self, _type: QWebEnginePage.WebWindowType) -> QWebEnginePage:
        return self


class MapMiniBrowser(QMainWindow):
    def __init__(self, target_url: str):
        super().__init__()
        self.target_url = target_url
        self.init_ui()
        self.init_web_engine()

    def init_ui(self):
        self.setWindowTitle("Route Maps Portal")
        self.resize(1366, 850)
        self.setMinimumSize(800, 600)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

    def init_web_engine(self):
        self.browser = QWebEngineView(self)
        self.page = MapEnginePage(ALLOWED_HOST, self.browser)
        self.browser.setPage(self.page)

        settings = self.browser.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)

        self.browser.loadFinished.connect(self.on_load_finished)
        self.setCentralWidget(self.browser)
        self.browser.load(QUrl(self.target_url))

    def on_load_finished(self, success: bool):
        if not success:
            QMessageBox.warning(
                self,
                "Koneksi Gagal",
                f"Gagal memuat peta dari MapChannels.\nPeriksa koneksi internet Anda.",
                QMessageBox.StandardButton.Ok
            )


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("RouteMapsMiniBrowser")
    window = MapMiniBrowser(target_url=TARGET_URL)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
