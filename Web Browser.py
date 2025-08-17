from PyQt5.QtGui import QDesktopServices
import sys
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QFrame, QLabel, QMainWindow, QStatusBar, QHBoxLayout, QApplication, QWidget
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlScheme, QWebEngineUrlSchemeHandler
from PyQt5.QtGui import QDesktopServices

class AdBlocker(QWebEngineUrlRequestInterceptor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.blocked_urls = [
            "ads", "advertising", "adserver", "doubleclick", "googlesyndication",
            "googleadservices", "googletagmanager", "ad.doubleclick", "analytics",
            "media.net", "amazon", "stats.wp.com", "bugsnag", "sentry",
            "hotjar", "mouseflow", "freshmarketer", "luckyorange",
            "pagead2.googlesyndication", "static.media.net", "media.net",
            "adtago.s3.amazonaws", "analyticsengine.s3.amazonaws", "affiliationjs.s3.amazonaws",
            "amazonaax", "google-analytics", "ssl.google-analytics", "hotjar",
            "static.hotjar", "mouseflow", "freshmarketer", "luckyorange",
            "cdn.luckyorange", "w1.luckyorange", "upload.luckyorange", "cs.luckyorange",
            "settings.luckyorange", "notify.bugsnag", "sessions.bugsnag", "api.bugsnag",
            "app.bugsnag", "browser.sentry-cdn", "app.getsentry", "pixel.facebook",
            "an.facebook", "analytics.pointdrive.linkedin", "log.pinterest", "analytics.pinterest",
            "trk.pinterest", "widgets.pinterest", "events.redditmedia", "d.reddit",
            "analytics-sg.tiktok", "analytics.tiktok", "analytics.yahoo", "appmetrica.yandex",
            "yandexadexchange", "analytics.mobile.yandex", "app-measurement.com",
            "events.reddit.com", "business-api.tiktok.com", "log.byteoversea.com", "geo.yahoo.com",
            "udc.yahoo.com", "udcm.yahoo.com", "log.fc.yahoo.com", "gemini.yahoo.com",
            "extmaps-api.yandex.net", "adfstat.yandex.ru", "metrika.yandex.ru", "adfox.yandex.ru",
            "iot-eu-logser.realme.com", "iot-logser.realme.com", "api.ad.xiaomi.com", "data.mistat.xiaomi.com",
            "data.mistat.india.xiaomi.com", "data.mistat.rus.xiaomi.com", "sdkconfig.ad.xiaomi.com",
            "sdkconfig.ad.intl.xiaomi.com", "globalapi.ad.xiaomi.com", "tracking.rus.miui.com",
            "click.oneplus.cn", "open.oneplus.net", "metrics.data.hicloud.com", "metrics2.data.hicloud.com",
            "grs.hicloud.com", "logservice.hicloud.com", "logservice1.hicloud.com", "logbak.hicloud.com",
            "smetrics.samsung.com", "samsung-com.112.2o7.net", "metrics.icloud.com", "metrics.mzstatic.com",
            "adc3-launch.adcolony.com", "events3alt.adcolony.com", "wd.adcolony.com"
        ]

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        if any(domain in url for domain in self.blocked_urls):
            info.block(True)

class WebBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Web Browser")

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tab_widget)

        self.view = QWebEngineView()
        self.view.urlChanged.connect(self.update_url_bar)
        self.view.page().profile().downloadRequested.connect(self.download_requested)

        self.ad_blocker = AdBlocker()
        self.blocked_urls = [
            "ads", "advertising", "adserver", "doubleclick", "googlesyndication",
            "googleadservices", "googletagmanager", "ad.doubleclick", "analytics",
            "media.net", "amazon", "stats.wp.com", "bugsnag", "sentry",
            "hotjar", "mouseflow", "freshmarketer", "luckyorange",
            "pagead2.googlesyndication", "static.media.net", "media.net",
            "adtago.s3.amazonaws", "analyticsengine.s3.amazonaws", "affiliationjs.s3.amazonaws",
            "amazonaax", "google-analytics", "ssl.google-analytics", "hotjar",
            "static.hotjar", "mouseflow", "freshmarketer", "luckyorange",
            "cdn.luckyorange", "w1.luckyorange", "upload.luckyorange", "cs.luckyorange",
            "settings.luckyorange", "notify.bugsnag", "sessions.bugsnag", "api.bugsnag",
            "app.bugsnag", "browser.sentry-cdn", "app.getsentry", "pixel.facebook",
            "an.facebook", "analytics.pointdrive.linkedin", "log.pinterest", "analytics.pinterest",
            "trk.pinterest", "widgets.pinterest", "events.redditmedia", "d.reddit",
            "analytics-sg.tiktok", "analytics.tiktok", "analytics.yahoo", "appmetrica.yandex",
            "yandexadexchange", "analytics.mobile.yandex", "app-measurement.com",
            "events.reddit.com", "business-api.tiktok.com", "log.byteoversea.com", "geo.yahoo.com",
            "udc.yahoo.com", "udcm.yahoo.com", "log.fc.yahoo.com", "gemini.yahoo.com",
            "extmaps-api.yandex.net", "adfstat.yandex.ru", "metrika.yandex.ru", "adfox.yandex.ru",
            "iot-eu-logser.realme.com", "iot-logser.realme.com", "api.ad.xiaomi.com", "data.mistat.xiaomi.com",
            "data.mistat.india.xiaomi.com", "data.mistat.rus.xiaomi.com", "sdkconfig.ad.xiaomi.com",
            "sdkconfig.ad.intl.xiaomi.com", "globalapi.ad.xiaomi.com", "tracking.rus.miui.com",
            "click.oneplus.cn", "open.oneplus.net", "metrics.data.hicloud.com", "metrics2.data.hicloud.com",
            "grs.hicloud.com", "logservice.hicloud.com", "logservice1.hicloud.com", "logbak.hicloud.com",
            "smetrics.samsung.com", "samsung-com.112.2o7.net", "metrics.icloud.com", "metrics.mzstatic.com",
            "adc3-launch.adcolony.com", "events3alt.adcolony.com", "wd.adcolony.com"
        ]

        self.view.page().profile().setRequestInterceptor(self.ad_blocker)

        self.add_new_tab()
       
        text_label = QLabel("Custom Browser in Python using PyQt5, Proudly Made By - 𝓐𝓜                                                                                                                                                                                                                                                                          Enjoy an ad-free browsing experience with the most effective built-In AdBlocker🪧      ")
        text_label.setStyleSheet("color: #ffffff;")
        self.statusBar().addPermanentWidget(text_label)
        self.setStyleSheet("background-color: #2b2b2b;")

        self.toolbar = self.addToolBar("Toolbar")
        self.new_tab_action = QAction("🆕", self)
        self.new_tab_action.setShortcut("Ctrl+T")
        self.new_tab_action.triggered.connect(self.add_new_tab)
        self.toolbar.setStyleSheet("QToolBar QToolButton { background-color: #333333; color: #ededed; border: #8d8d8d; padding: 8px 16px; font-size: 20px; } QToolBar QToolButton:pressed { background-color: #4a4a4a; }")
        self.toolbar.addAction(self.new_tab_action)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate)
        self.url_bar.setStyleSheet(
            "QLineEdit { background-color: #777777; color: #ededed; border: 1px solid #ffffff ; padding: 8px; font-size: 16px; }")

        self.go_button = QPushButton("🔍")
        self.go_button.clicked.connect(self.navigate)
        self.go_button.setStyleSheet(
            "QPushButton { background-color: #333333; color: #ededed; border: #8d8d8d; padding: 8px 16px; font-size: 20px; } QPushButton:pressed { background-color: #4a4a4a; }")

        self.back_button = QPushButton("🔙")
        self.back_button.clicked.connect(lambda: self.tab_widget.currentWidget().layout().itemAt(0).widget().back())
        self.back_button.setStyleSheet(
            "QPushButton { background-color: #333333; color: #ededed; border: #8d8d8d; padding: 8px 16px; font-size: 20px; } QPushButton:pressed { background-color: #4a4a4a; }")

        self.forward_button = QPushButton("🔜")
        self.forward_button.clicked.connect(lambda: self.tab_widget.currentWidget().layout().itemAt(0).widget().forward())
        self.forward_button.setStyleSheet(
            "QPushButton { background-color: #333333; color: #ededed; border: #8d8d8d; padding: 8px 16px; font-size: 20px; } QPushButton:pressed { background-color: #4a4a4a; }")

        self.refresh_button = QPushButton("↻")
        self.refresh_button.setShortcut("Ctrl+R")
        self.refresh_button.clicked.connect(lambda: self.tab_widget.currentWidget().layout().itemAt(0).widget().reload())
        self.refresh_button.setStyleSheet(
            "QPushButton { background-color: #333333; color: #ededed; border: #8d8d8d; padding: 8px 16px; font-size: 20px; } QPushButton:pressed { background-color: #4a4a4a; }")

        self.home_button = QPushButton("🏠")
        self.home_button.clicked.connect(self.load_homepage)
        self.home_button.setStyleSheet(
            "QPushButton { background-color: #333333; color: #ededed; border: #8d8d8d; padding: 8px 16px; font-size: 20px; } QPushButton:pressed { background-color: #4a4a4a; }")

        self.download_button = QPushButton("⬇️")
        self.download_button.clicked.connect(self.open_downloads_folder)
        self.download_button.setStyleSheet(
            "QPushButton { background-color: #333333; color: #ededed; border: #8d8d8d; padding: 8px 16px; font-size: 20px; } QPushButton:pressed { background-color: #4a4a4a; }")

        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.addWidget(self.back_button)
        toolbar.addWidget(self.forward_button)
        toolbar.addWidget(self.refresh_button)
        toolbar.addWidget(self.home_button)
        toolbar.addWidget(self.url_bar)
        toolbar.addWidget(self.go_button)
        toolbar.addWidget(self.download_button)
        self.addToolBar(toolbar)

        self.setStyleSheet("background-color: #2b2b2b;")

    def add_new_tab(self):
        web_view = QWebEngineView()
        web_view.urlChanged.connect(self.update_url_bar)
        web_view.loadStarted.connect(self.update_title)
        web_view.loadFinished.connect(self.update_title)
        web_view.load(QUrl("https://www.google.com"))

        tab_widget_page = QWidget()
        tab_layout = QVBoxLayout(tab_widget_page)
        tab_layout.addWidget(web_view)

        tab_index = self.tab_widget.addTab(tab_widget_page, "\U0001F195")  # Unicode representation of 🆕 emoji
        self.tab_widget.setCurrentIndex(tab_index)

    def update_title(self):
        current_tab = self.tab_widget.currentWidget().layout().itemAt(0).widget()
        title = current_tab.page().title()
        index = self.tab_widget.currentIndex()
        self.tab_widget.setTabText(index, title)

    def close_tab(self, index):
        if self.tab_widget.count() > 1:
            widget = self.tab_widget.widget(index)
            widget.deleteLater()
            self.tab_widget.removeTab(index)

    def navigate(self):
        url = self.url_bar.text()
        if not url.startswith("http://") and not url.startswith("https://www."):
            url = "https://www." + url
        current_tab = self.tab_widget.currentWidget().layout().itemAt(0).widget()
        current_tab.load(QUrl(url))

    def load_homepage(self):
        homepage_url = "https://www.google.com"
        current_tab = self.tab_widget.currentWidget().layout().itemAt(0).widget()
        current_tab.load(QUrl(homepage_url))

    def update_url_bar(self, url):
        self.url_bar.setText(url.toString())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        self.view.close()

    def resizeEvent(self, event):
        if hasattr(self, 'view'):
            self.view.resize(self.centralWidget().size())

    def download_requested(self, download):
        download_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "All Files (*)")
        if download_path:
            download.setPath(download_path)
            download.accept()

    def open_downloads_folder(self):
        downloads_path = QWebEngineProfile.defaultProfile().downloadPath()
        if not downloads_path:
            QMessageBox.warning(self, "Downloads Folder", "The downloads folder is not set.")
            return

        QDesktopServices.openUrl(QUrl.fromLocalFile(downloads_path))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    browser = WebBrowser()
    browser.show()

    sys.exit(app.exec_())