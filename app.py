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
    """Memblokir network request ke penyedia iklan Google dan tracker."""
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
    """Engine browser dengan isolasi domain dan auto-grant lokasi."""
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
    """Halaman pembuka bertema pemandangan 'Keliling Dunia'."""
    def __init__(self, on_start_callback):
        super().__init__()
        self.on_start_callback = on_start_callback
        self.init_ui()

    def init_ui(self):
        # Desain pemandangan gradien langit & pegunungan modern via QSS
        self.setStyleSheet("""
            QWidget#LandingRoot {
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0f2027, stop:0.4 #203a43, stop:0.7 #2c5364, stop:1 #ff7e5f
                );
            }
            QLabel#TitleLabel {
                color: #FFFFFF;
                font-size: 54px;
                font-weight: 800;
                font-family: 'Segoe UI', Arial, sans-serif;
                letter-spacing: 2px;
            }
            QLabel#SubtitleLabel {
                color: #E0E0E0;
                font-size: 18px;
                font-family: 'Segoe UI', Arial, sans-serif;
                margin-bottom: 25px;
            }
            QPushButton#StartBtn {
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF512F, stop:1 #DD2476
                );
                color: #FFFFFF;
                font-size: 18px;
                font-weight: bold;
                border: none;
                border-radius: 28px;
                padding: 14px 48px;
                min-width: 140px;
            }
            QPushButton#StartBtn:hover {
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff6547, stop:1 #e83685
                );
            }
            QPushButton#StartBtn:pressed {
                background-color: #b81d60;
            }
        """)

        self.setObjectName("LandingRoot")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Ikon dekorasi globe
        icon_label = QLabel("🌏")
        icon_label.setStyleSheet("font-size: 64px; background: transparent;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Keliling Dunia")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Jelajahi berbagai rute dan peta dunia dengan mudah")
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
        self.setWindowTitle("Keliling Dunia - Route Maps")
        self.resize(1366, 850)
        self.setMinimumSize(900, 650)

        # Inisialisasi Stacked Widget untuk transisi landing page -> browser
        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        # Setup AdBlocker
        self.ad_blocker = GoogleAdBlocker()
        QWebEngineProfile.defaultProfile().setUrlRequestInterceptor(self.ad_blocker)

        # Setup Views
        self.init_browser()
        self.landing_page = LandingPageWidget(on_start_callback=self.open_map)

        self.stack.addWidget(self.landing_page)  # Index 0
        self.stack.addWidget(self.browser)       # Index 1

        # Tampilkan landing page di awal
        self.stack.setCurrentIndex(0)

        # Pre-load peta di background agar saat tombol "Mulai" ditekan tidak ada delay
        self.browser.load(QUrl(TARGET_URL))

    def init_browser(
