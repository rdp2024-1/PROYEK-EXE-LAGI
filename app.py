import sys
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QLabel, QPushButton, QStackedWidget, QMessageBox
)
from PyQt6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineSettings,
    QWebEngineProfile,
    QWebEngineUrlRequestInterceptor
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

TARGET_URL = "https://www.mapchannels.com/routemaps3/map.htm"
ALLOWED_HOST = "www.mapchannels.com"


class GoogleAdBlocker(QWebEngineUrlRequestInterceptor):
    """Mencegat dan memblokir request ke server iklan Google."""
    AD_DOMAINS = [
        "googlesyndication.com",
        "doubleclick.net",
        "googleadservices.com",
        "pagead2.googlesyndication.com",
        "adservice.google.com"
    ]

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        for domain in self.AD_DOMAINS:
            if domain in url:
                info.block(True)
                return


class MapEnginePage(QWebEnginePage):
    """Engine browser khusus untuk navigasi aman dan izin lokasi."""
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


class LandingPageWidget(QWidget):
    """Tampilan landing page 'Keliling Dunia'."""
    def __init__(self, on_start_callback):
        super().__init__()
        self.on_start_callback = on_start_callback
        self.init_ui()

    def init_ui(self):
        self.setObjectName("LandingRoot")
        self.setStyleSheet("""
            QWidget#LandingRoot {
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0f2027, stop:0.45 #203a43, stop:0.75 #2c5364, stop:1 #e07a5f
                );
            }
            QLabel#TitleLabel {
                color: #FFFFFF;
                font-size: 50px;
                font-weight: 800;
                font-family: 'Segoe UI', Arial, sans-serif;
                margin-top: 10px;
            }
            QLabel#SubtitleLabel {
                color: #ECEFF1;
                font-size: 17px;
                font-family: 'Segoe UI', Arial, sans-serif;
                margin-bottom: 30px;
            }
            QPushButton#StartBtn {
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF512F, stop:1 #DD2476
                );
                color: #FFFFFF;
                font-size: 19px;
                font-weight: bold;
                border: none;
                border-radius: 26px;
                padding: 12px 50px;
            }
            QPushButton#StartBtn:hover {
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff6547, stop:1 #e83685
                );
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel("🧭 🏔️ ✈️")
        icon_label.setStyleSheet("font-size: 52px; background: transparent;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Keliling Dunia")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Eksplorasi rute perjalanan dan destinasi di seluruh dunia")
        subtitle.setObjectName("SubtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        start_btn = QPushButton("Mulai")
        start_btn.setObjectName("StartBtn")
        start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        start_btn.clicked.connect(self.on_start_callback)

        layout.addStretch()
        layout.addWidget(icon_label)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(start_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Keliling Dunia")
        self.resize(1366, 850)
        self.setMinimumSize(900, 650)

        # Aktifkan pencegat iklan Google
        self.ad_blocker = GoogleAdBlocker()
        QWebEngineProfile.defaultProfile().setUrlRequestInterceptor(self.ad_blocker)

        # Stacked Widget (berisi Landing Page & Map View)
        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        self.init_browser()
        self.landing_page = LandingPageWidget(on_start_callback=self.open_map)

        self.stack.addWidget(self.landing_page)  # Halaman 0
        self.stack.addWidget(self.browser)       # Halaman 1

        # Tampilkan Landing Page dulu
        self.stack.setCurrentIndex(0)

        # Pre-load peta di latar belakang agar instan saat diklik 'Mulai'
        self.browser.load(QUrl(TARGET_URL))

    def init_browser(self):
        self.browser = QWebEngineView(self)
        self.page = MapEnginePage(ALLOWED_HOST, self.browser)
        self.browser.setPage(self.page)

        settings = self.browser.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)

        self.browser.loadFinished.connect(self.on_page_loaded)

    def on_page_loaded(self, success: bool):
        if success:
            # Script CSS & JS untuk menyembunyikan sisa kontainer / slot iklan Google
            hide_ads_script = """
                (function() {
                    var css = `
                        ins.adsbygoogle, 
                        iframe[src*="googlesyndication"], 
                        div[id*="google_ads"], 
                        div[id*="aswift"] {
                            display: none !important;
                            visibility: hidden !important;
                            height: 0px !important;
                        }
                    `;
                    var head = document.head || document.getElementsByTagName('head')[0];
                    var style = document.createElement('style');
                    style.type = 'text/css';
                    style.appendChild(document.createTextNode(css));
                    head.appendChild(style);
                })();
            """
            self.browser.page().runJavaScript(hide_ads_script)

    def open_map(self):
        # Berpindah dari landing page ke halaman peta langsung
        self.stack.setCurrentIndex(1)


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("KelilingDunia")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
