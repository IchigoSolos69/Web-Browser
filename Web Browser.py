import re
import sys
from pathlib import Path

from PyQt6 import sip
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QAction, QDesktopServices, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QToolBar,
)
from PyQt6.QtWebEngineCore import (
    QWebEngineDownloadRequest,
    QWebEngineNewWindowRequest,
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineUrlRequestInterceptor,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView


HOMEPAGE = "https://www.google.com"
PROFILE_NAME = "BrowserQt6"
BLOCKED_HOSTS = frozenset({
    "adc3-launch.adcolony.com",
    "adfox.yandex.ru",
    "adfstat.yandex.ru",
    "api.ad.xiaomi.com",
    "app-measurement.com",
    "business-api.tiktok.com",
    "click.oneplus.cn",
    "data.mistat.india.xiaomi.com",
    "data.mistat.rus.xiaomi.com",
    "data.mistat.xiaomi.com",
    "doubleclick.net",
    "events.reddit.com",
    "events3alt.adcolony.com",
    "extmaps-api.yandex.net",
    "gemini.yahoo.com",
    "geo.yahoo.com",
    "globalapi.ad.xiaomi.com",
    "google-analytics.com",
    "googleadservices.com",
    "googlesyndication.com",
    "googletagmanager.com",
    "grs.hicloud.com",
    "iot-eu-logser.realme.com",
    "iot-logser.realme.com",
    "log.byteoversea.com",
    "log.fc.yahoo.com",
    "logbak.hicloud.com",
    "logservice.hicloud.com",
    "logservice1.hicloud.com",
    "media.net",
    "metrics.data.hicloud.com",
    "metrics.icloud.com",
    "metrics.mzstatic.com",
    "metrics2.data.hicloud.com",
    "metrika.yandex.ru",
    "open.oneplus.net",
    "samsung-com.112.2o7.net",
    "sdkconfig.ad.intl.xiaomi.com",
    "sdkconfig.ad.xiaomi.com",
    "smetrics.samsung.com",
    "stats.wp.com",
    "tracking.rus.miui.com",
    "udc.yahoo.com",
    "udcm.yahoo.com",
    "wd.adcolony.com",
})


def normalize_url(text):
    text = text.strip()
    if not text:
        return None
    if any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in text):
        raise ValueError("Enter a web address without spaces or control characters.")

    scheme = re.match(r"^([a-zA-Z][a-zA-Z0-9+.-]*):", text)
    if scheme and scheme.group(1).lower() not in {"http", "https"}:
        # A numeric port distinguishes a bare host:port from a URL scheme.
        if not re.match(r"^[^:/?#@]+:\d+(?:[/?#]|$)", text):
            raise ValueError("Only HTTP and HTTPS addresses are supported.")
        text = "https://" + text
    elif not scheme:
        text = "https://" + text

    url = QUrl(text, QUrl.ParsingMode.StrictMode)
    if not url.isValid() or not url.host() or url.scheme() not in {"http", "https"}:
        raise ValueError("Enter a valid HTTP or HTTPS address.")
    return url


class AdBlocker(QWebEngineUrlRequestInterceptor):
    @staticmethod
    def blocks_host(host):
        host = host.lower().rstrip(".")
        return any(host == rule or host.endswith("." + rule) for rule in BLOCKED_HOSTS)

    def interceptRequest(self, info):
        if self.blocks_host(info.requestUrl().host()):
            info.block(True)


class WebBrowser(QMainWindow):
    def __init__(self, profile=None):
        super().__init__()
        self.setWindowTitle("Web Browser")
        self._shutting_down = False
        self._owns_profile = profile is None

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tab_widget)

        self.setStyleSheet("background-color: #2b2b2b;")
        text_label = QLabel("Custom Browser in Python using PyQt6, Proudly Made By - 𝓐𝓜")
        text_label.setStyleSheet("color: #ffffff;")
        self.statusBar().addPermanentWidget(text_label)

        button_style = (
            "background-color: #333333; color: #ededed; border: #8d8d8d; "
            "padding: 8px 16px; font-size: 20px;"
        )
        self.toolbar = self.addToolBar("Toolbar")
        self.toolbar.setStyleSheet(
            "QToolBar QToolButton { " + button_style + " } "
            "QToolBar QToolButton:pressed { background-color: #4a4a4a; }"
        )
        self.new_tab_action = QAction("🆕", self)
        self.new_tab_action.setToolTip("New tab (Ctrl+T)")
        self.new_tab_action.setShortcut("Ctrl+T")
        self.new_tab_action.triggered.connect(lambda checked=False: self.add_new_tab(HOMEPAGE))
        self.toolbar.addAction(self.new_tab_action)

        self.url_bar = QLineEdit()
        self.url_bar.setAccessibleName("Web address")
        self.url_bar.returnPressed.connect(self.navigate)
        self.url_bar.setStyleSheet(
            "QLineEdit { background-color: #777777; color: #ededed; "
            "border: 1px solid #ffffff; padding: 8px; font-size: 16px; }"
        )

        self.go_button = QPushButton("🔍")
        self.go_button.setToolTip("Go to address")
        self.go_button.clicked.connect(self.navigate)
        self.back_button = QPushButton("🔙")
        self.back_button.setToolTip("Back")
        self.back_button.clicked.connect(lambda: self.tab_widget.currentWidget().back())
        self.forward_button = QPushButton("🔜")
        self.forward_button.setToolTip("Forward")
        self.forward_button.clicked.connect(lambda: self.tab_widget.currentWidget().forward())
        self.refresh_button = QPushButton("↻")
        self.refresh_button.setToolTip("Refresh (Ctrl+R)")
        self.refresh_button.setShortcut("Ctrl+R")
        self.refresh_button.clicked.connect(lambda: self.tab_widget.currentWidget().reload())
        self.home_button = QPushButton("🏠")
        self.home_button.setToolTip("Home")
        self.home_button.clicked.connect(self.load_homepage)
        self.download_button = QPushButton("⬇️")
        self.download_button.setToolTip("Open Downloads folder")
        self.download_button.clicked.connect(self.open_downloads_folder)

        toolbar = QToolBar("Navigation", self)
        toolbar.setMovable(False)
        toolbar.setStyleSheet(
            "QPushButton { " + button_style + " } "
            "QPushButton:pressed { background-color: #4a4a4a; }"
        )
        for widget in (
            self.back_button, self.forward_button, self.refresh_button,
            self.home_button, self.url_bar, self.go_button, self.download_button,
        ):
            toolbar.addWidget(widget)
        self.addToolBar(toolbar)

        self.close_action = QAction(self)
        self.close_action.setShortcut(QKeySequence("Esc"))
        self.close_action.triggered.connect(self.close)
        self.addAction(self.close_action)

        self.profile = profile if profile is not None else QWebEngineProfile(PROFILE_NAME, self)
        self.ad_blocker = AdBlocker(self)
        self.profile.setUrlRequestInterceptor(self.ad_blocker)
        self.profile.downloadRequested.connect(self.download_requested)
        self.tab_widget.currentChanged.connect(lambda index: self.update_url_bar(self.tab_widget.currentWidget()))
        self.add_new_tab(HOMEPAGE)

    def add_new_tab(self, url=HOMEPAGE, make_current=True):
        web_view = QWebEngineView(self.tab_widget)
        web_view.setPage(QWebEnginePage(self.profile, web_view))
        web_view.urlChanged.connect(lambda url: self.update_url_bar(web_view))
        web_view.titleChanged.connect(lambda title: self.update_title(web_view, title))
        web_view.page().newWindowRequested.connect(self.handle_new_window)
        index = self.tab_widget.addTab(web_view, "🆕")
        if make_current:
            self.tab_widget.setCurrentIndex(index)
        if url is not None:
            web_view.load(QUrl(url))
        return web_view

    def update_title(self, web_view, title):
        index = self.tab_widget.indexOf(web_view)
        if index >= 0:
            self.tab_widget.setTabText(index, title or "🆕")

    def update_url_bar(self, web_view):
        if web_view is not None and web_view is self.tab_widget.currentWidget():
            self.url_bar.setText(web_view.url().toString(QUrl.ComponentFormattingOption.FullyEncoded))

    def close_tab(self, index):
        if self.tab_widget.count() > 1 and 0 <= index < self.tab_widget.count():
            web_view = self.tab_widget.widget(index)
            self.tab_widget.removeTab(index)
            web_view.deleteLater()

    def navigate(self):
        try:
            url = normalize_url(self.url_bar.text())
        except ValueError as error:
            self.statusBar().showMessage(str(error), 5000)
            return
        if url is not None:
            self.statusBar().clearMessage()
            self.tab_widget.currentWidget().load(url)

    def load_homepage(self):
        self.tab_widget.currentWidget().load(QUrl(HOMEPAGE))

    def handle_new_window(self, request):
        if not request.isUserInitiated():
            return
        background = request.destination() == QWebEngineNewWindowRequest.DestinationType.InNewBackgroundTab
        web_view = self.add_new_tab(None, make_current=not background)
        request.openIn(web_view.page())

    def download_requested(self, download):
        # Qt's Save Page dialog has already chosen a path and accepted its request.
        if download.state() != QWebEngineDownloadRequest.DownloadState.DownloadRequested:
            return
        suggested_path = Path(self.profile.downloadPath()) / Path(download.suggestedFileName()).name
        download_path, _ = QFileDialog.getSaveFileName(self, "Save File", str(suggested_path), "All Files (*)")
        if not download_path:
            download.cancel()
            return
        destination = Path(download_path)
        download.setDownloadDirectory(str(destination.parent))
        download.setDownloadFileName(destination.name)
        download.accept()

    def open_downloads_folder(self):
        downloads_path = self.profile.downloadPath()
        if not downloads_path:
            QMessageBox.warning(self, "Downloads Folder", "The downloads folder is not set.")
        elif not QDesktopServices.openUrl(QUrl.fromLocalFile(downloads_path)):
            QMessageBox.warning(self, "Downloads Folder", "The downloads folder could not be opened.")

    def shutdown(self):
        if self._shutting_down:
            return
        self._shutting_down = True
        self.tab_widget.blockSignals(True)
        views = self.tab_widget.findChildren(QWebEngineView)
        while self.tab_widget.count():
            self.tab_widget.removeTab(0)
        # Pages must be destroyed before their shared profile is released.
        for web_view in views:
            sip.delete(web_view)
        self.profile.downloadRequested.disconnect(self.download_requested)
        self.profile.setUrlRequestInterceptor(None)
        if self._owns_profile:
            sip.delete(self.profile)

    def closeEvent(self, event):
        self.shutdown()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    browser = WebBrowser()
    app.aboutToQuit.connect(browser.shutdown)
    browser.show()
    sys.exit(app.exec())
