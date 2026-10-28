import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import Mock, patch
from urllib.parse import urlsplit

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# Offscreen tests do not need a hardware GPU context.
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu")

from PyQt6 import sip
from PyQt6.QtCore import QPoint, Qt, QUrl
from PyQt6.QtTest import QSignalSpy, QTest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest, QWebEngineNewWindowRequest, QWebEngineProfile


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("browser", ROOT / "Web Browser.py")
browser = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(browser)


def wait_until(predicate, timeout=10000):
    deadline = time.monotonic() + timeout / 1000
    while not predicate():
        if time.monotonic() >= deadline:
            raise AssertionError("Timed out waiting for Qt browser state")
        QTest.qWait(10)


def javascript(view, source):
    result = []
    view.page().runJavaScript(source, result.append)
    wait_until(lambda: bool(result))
    return result[0]


def load(view, url):
    finished = QSignalSpy(view.loadFinished)
    view.load(QUrl(url))
    wait_until(lambda: len(finished) > 0)
    if not finished[-1][0]:
        raise AssertionError("Fixture failed to load: " + url)


class FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/background")
            self.end_headers()
            return
        if path == "/download":
            body = b"browser regression download\n"
            content_type = "application/octet-stream"
        else:
            body = (
                f"<html><head><title>{path}</title></head><body>"
                '<a id="new" href="/destination" target="_blank" '
                'style="display:block;width:200px;height:60px">New tab</a>'
                "</body></html>"
            ).encode()
            content_type = "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if path == "/download":
            self.send_header("Content-Disposition", 'attachment; filename="fixture.txt"')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class UrlTests(unittest.TestCase):
    def test_valid_addresses(self):
        cases = {
            "https://github.com": "https://github.com",
            "http://example.com/a?q=1#part": "http://example.com/a?q=1#part",
            "example.com/downloads/": "https://example.com/downloads/",
            "  example.com  ": "https://example.com",
            "HTTPS://Example.com": "https://example.com",
            "localhost:8000/path": "https://localhost:8000/path",
            "127.0.0.1:8080": "https://127.0.0.1:8080",
            "http://localhost:8000": "http://localhost:8000",
            "[::1]:8080/path": "https://[::1]:8080/path",
            "https://example.com/a%20b": "https://example.com/a b",
            "https://user:pass@example.com/path": "https://user:pass@example.com/path",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(browser.normalize_url(text).toString(), expected)

    def test_empty_input_does_not_navigate(self):
        for text in ("", "   ", "\n\t"):
            self.assertIsNone(browser.normalize_url(text))

    def test_invalid_and_unsupported_addresses(self):
        for text in (
            "http://", "https:///path", "https://example.com:70000",
            "http://localhost:abc", "bad address", "example.com/a\nb",
            "https://example.com/\x00", "https://example.com/%zz",
            "file:///tmp/a", "javascript:alert(1)", "mailto:a@example.com",
            "ftp://example.com", "data:text/html,hello", "about:blank",
        ):
            with self.subTest(text=text), self.assertRaises(ValueError):
                browser.normalize_url(text)


class BlockerTests(unittest.TestCase):
    def test_blocks_exact_hosts_and_subdomains(self):
        for host in ("doubleclick.net", "ads.doubleclick.net", "DOUBLECLICK.NET.", "stats.wp.com"):
            with self.subTest(host=host):
                self.assertTrue(browser.AdBlocker.blocks_host(host))

    def test_allows_ordinary_hosts_and_lookalikes(self):
        for host in ("", "www.amazon.com", "www.python.org", "notdoubleclick.net", "doubleclick.net.example.org"):
            with self.subTest(host=host):
                self.assertFalse(browser.AdBlocker.blocks_host(host))

    def test_interceptor_uses_only_the_hostname(self):
        blocker = browser.AdBlocker()
        for url, blocked in (
            ("https://example.org/downloads/?topic=analytics", False),
            ("https://doubleclick.net@example.org/ads", False),
            ("https://example.org/doubleclick.net", False),
            ("https://example.org@ads.doubleclick.net/script.js", True),
        ):
            with self.subTest(url=url):
                info = Mock()
                info.requestUrl.return_value = QUrl(url)
                blocker.interceptRequest(info)
                if blocked:
                    info.block.assert_called_once_with(True)
                else:
                    info.block.assert_not_called()


class BrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(["browser-tests"])
        cls.app.setQuitOnLastWindowClosed(False)
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        cls.server.daemon_threads = True
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.base = "http://127.0.0.1:" + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.profile = QWebEngineProfile()
        self.profile.setDownloadPath(self.temp.name)
        with patch.object(browser, "HOMEPAGE", "about:blank"):
            self.window = browser.WebBrowser(self.profile)
        self.window.resize(1100, 700)
        self.window.show()
        self.first = self.window.tab_widget.currentWidget()
        load(self.first, self.base + "/first")

    def tearDown(self):
        self.window.close()
        sip.delete(self.window)
        sip.delete(self.profile)
        QTest.qWait(10)
        self.temp.cleanup()

    def test_switching_and_background_redirect_keep_correct_address(self):
        second = self.window.add_new_tab(None)
        load(second, self.base + "/second")
        self.assertEqual(self.window.url_bar.text(), self.base + "/second")
        self.window.tab_widget.setCurrentWidget(self.first)
        self.assertEqual(self.window.url_bar.text(), self.base + "/first")
        load(second, self.base + "/redirect")
        self.assertEqual(second.url().toString(), self.base + "/background")
        self.assertEqual(self.window.url_bar.text(), self.base + "/first")
        self.window.tab_widget.setCurrentWidget(second)
        self.assertEqual(self.window.url_bar.text(), self.base + "/background")

    def test_background_and_late_titles_update_their_own_tab(self):
        second = self.window.add_new_tab(None, make_current=False)
        load(second, self.base + "/second")
        wait_until(lambda: self.window.tab_widget.tabText(1) == "/second")
        javascript(second, "document.title = 'Later title'")
        wait_until(lambda: self.window.tab_widget.tabText(1) == "Later title")
        self.assertEqual(self.window.tab_widget.tabText(0), "/first")
        self.window.close_tab(0)
        javascript(second, "document.title = 'Moved title'")
        wait_until(lambda: self.window.tab_widget.tabText(0) == "Moved title")

    def test_closing_active_tab_syncs_address_and_keeps_last_tab(self):
        second = self.window.add_new_tab(None)
        load(second, self.base + "/second")
        self.window.close_tab(1)
        self.assertIs(self.window.tab_widget.currentWidget(), self.first)
        self.assertEqual(self.window.url_bar.text(), self.base + "/first")
        self.window.close_tab(0)
        self.window.close_tab(-1)
        self.assertEqual(self.window.tab_widget.count(), 1)
        for _ in range(5):
            self.window.add_new_tab(None)
            self.window.close_tab(1)
        self.assertEqual(self.window.tab_widget.count(), 1)

    def test_invalid_and_empty_navigation_do_not_replace_page(self):
        for text in ("", "javascript:alert(1)"):
            self.window.url_bar.setText(text)
            self.window.navigate()
            self.assertEqual(self.first.url().toString(), self.base + "/first")
        self.assertIn("HTTP", self.window.statusBar().currentMessage())

    def test_encoded_addresses_can_be_submitted_again(self):
        load(self.first, self.base + "/has%20space?q=hello%20world")
        self.assertIn("%20", self.window.url_bar.text())
        self.assertEqual(browser.normalize_url(self.window.url_bar.text()), self.first.url())

    def test_toolbar_navigation_uses_active_tab(self):
        self.window.url_bar.setText(self.base + "/second")
        finished = QSignalSpy(self.first.loadFinished)
        self.window.go_button.click()
        wait_until(lambda: len(finished) > 0)
        self.assertEqual(self.first.url().toString(), self.base + "/second")
        self.window.back_button.click()
        wait_until(lambda: self.first.url().toString() == self.base + "/first")
        self.window.forward_button.click()
        wait_until(lambda: self.first.url().toString() == self.base + "/second")
        with patch.object(browser, "HOMEPAGE", self.base + "/home"):
            self.window.home_button.click()
            wait_until(lambda: self.first.url().toString() == self.base + "/home")

    def test_new_window_routing_preserves_background_and_blocks_popups(self):
        destination = QWebEngineNewWindowRequest.DestinationType
        for requested in (destination.InNewTab, destination.InNewWindow, destination.InNewDialog, destination.InNewBackgroundTab):
            with self.subTest(destination=requested):
                self.window.tab_widget.setCurrentWidget(self.first)
                request = Mock()
                request.isUserInitiated.return_value = True
                request.destination.return_value = requested
                count = self.window.tab_widget.count()
                self.window.handle_new_window(request)
                new_view = self.window.tab_widget.widget(count)
                request.openIn.assert_called_once_with(new_view.page())
                self.assertIs(new_view.page().profile(), self.profile)
                expected_active = self.first if requested == destination.InNewBackgroundTab else new_view
                self.assertIs(self.window.tab_widget.currentWidget(), expected_active)
        request = Mock()
        request.isUserInitiated.return_value = False
        count = self.window.tab_widget.count()
        self.window.handle_new_window(request)
        self.assertEqual(self.window.tab_widget.count(), count)
        request.openIn.assert_not_called()

    def test_clicked_target_blank_opens_a_real_tab(self):
        load(self.first, self.base + "/links")
        rect = javascript(self.first, "document.getElementById('new').getBoundingClientRect().toJSON()")
        requests = QSignalSpy(self.first.page().newWindowRequested)
        QTest.mouseClick(
            self.first.focusProxy(), Qt.MouseButton.LeftButton,
            pos=QPoint(int(rect["x"] + 20), int(rect["y"] + 20)),
        )
        wait_until(lambda: self.window.tab_widget.count() == 2)
        opened = self.window.tab_widget.widget(1)
        wait_until(lambda: opened.url().toString() == self.base + "/destination")
        self.assertEqual(len(requests), 1)
        self.assertIs(self.window.tab_widget.currentWidget(), opened)

    def test_control_click_opens_real_background_tab(self):
        load(self.first, self.base + "/links")
        rect = javascript(self.first, "document.getElementById('new').getBoundingClientRect().toJSON()")
        QTest.mouseClick(
            self.first.focusProxy(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ControlModifier,
            pos=QPoint(int(rect["x"] + 20), int(rect["y"] + 20)),
        )
        wait_until(lambda: self.window.tab_widget.count() == 2)
        opened = self.window.tab_widget.widget(1)
        wait_until(lambda: opened.url().toString() == self.base + "/destination")
        self.assertIs(self.window.tab_widget.currentWidget(), self.first)
        self.assertEqual(self.window.url_bar.text(), self.base + "/links")

    def test_automatic_javascript_popup_is_blocked(self):
        requests = QSignalSpy(self.first.page().newWindowRequested)
        javascript(self.first, "window.open('/destination', '_blank'); true")
        wait_until(lambda: len(requests) > 0)
        self.assertEqual(self.window.tab_widget.count(), 1)

    def test_keyboard_shortcuts(self):
        with patch.object(browser, "HOMEPAGE", self.base + "/new"):
            QTest.keyClick(self.window.url_bar, Qt.Key.Key_T, Qt.KeyboardModifier.ControlModifier)
            wait_until(lambda: self.window.tab_widget.count() == 2)
        opened = self.window.tab_widget.currentWidget()
        wait_until(lambda: opened.title() == "/new")
        finished = QSignalSpy(opened.loadFinished)
        QTest.keyClick(self.window.url_bar, Qt.Key.Key_R, Qt.KeyboardModifier.ControlModifier)
        wait_until(lambda: len(finished) > 0)
        QTest.keyClick(self.window.url_bar, Qt.Key.Key_Escape)
        self.assertTrue(self.window._shutting_down)
        self.assertFalse(self.window.isVisible())

    def test_download_dialog_accepts_and_cancels(self):
        download = Mock()
        download.state.return_value = QWebEngineDownloadRequest.DownloadState.DownloadRequested
        download.suggestedFileName.return_value = "fixture.txt"
        target = Path(self.temp.name) / "chosen name.txt"
        with patch.object(browser.QFileDialog, "getSaveFileName", return_value=(str(target), "")) as dialog:
            self.window.download_requested(download)
        self.assertEqual(Path(dialog.call_args.args[2]), Path(self.temp.name) / "fixture.txt")
        self.assertEqual(download.method_calls, [
            unittest.mock.call.state(),
            unittest.mock.call.suggestedFileName(),
            unittest.mock.call.setDownloadDirectory(str(target.parent)),
            unittest.mock.call.setDownloadFileName(target.name),
            unittest.mock.call.accept(),
        ])
        download.reset_mock()
        with patch.object(browser.QFileDialog, "getSaveFileName", return_value=("", "")):
            self.window.download_requested(download)
        download.cancel.assert_called_once_with()
        download.accept.assert_not_called()

    def test_real_download_writes_selected_path(self):
        target = Path(self.temp.name) / "downloaded.txt"
        requested = QSignalSpy(self.profile.downloadRequested)
        with patch.object(browser.QFileDialog, "getSaveFileName", return_value=(str(target), "")):
            self.first.page().download(QUrl(self.base + "/download"))
            wait_until(lambda: len(requested) > 0)
            request = requested[0][0]
            wait_until(request.isFinished)
        self.assertEqual(target.read_bytes(), b"browser regression download\n")

    def test_cancelled_real_download_writes_nothing(self):
        requested = QSignalSpy(self.profile.downloadRequested)
        with patch.object(browser.QFileDialog, "getSaveFileName", return_value=("", "")):
            self.first.page().download(QUrl(self.base + "/download"))
            wait_until(lambda: len(requested) > 0)
        self.assertEqual(list(Path(self.temp.name).iterdir()), [])

    def test_save_page_keeps_the_destination_already_chosen_by_qt(self):
        target = Path(self.temp.name) / "saved.mhtml"
        requested = QSignalSpy(self.profile.downloadRequested)
        with patch.object(browser.QFileDialog, "getSaveFileName") as dialog:
            self.first.page().save(str(target))
            wait_until(lambda: len(requested) > 0)
            request = requested[0][0]
            wait_until(request.isFinished)
        dialog.assert_not_called()
        self.assertTrue(target.exists())
        self.assertGreater(target.stat().st_size, 0)

    def test_download_folder_uses_shared_profile(self):
        with patch.object(browser.QDesktopServices, "openUrl", return_value=True) as open_url:
            self.window.open_downloads_folder()
        self.assertEqual(Path(open_url.call_args.args[0].toLocalFile()), Path(self.temp.name))

    def test_profile_is_shared_between_tabs(self):
        javascript(self.first, "localStorage.setItem('shared', 'yes'); document.cookie = 'shared=yes; path=/'")
        second = self.window.add_new_tab(None)
        load(second, self.base + "/second")
        self.assertEqual(javascript(second, "localStorage.getItem('shared')"), "yes")
        self.assertIn("shared=yes", javascript(second, "document.cookie"))

    def test_persistent_profile_survives_restart_and_leaves_qt5_data_untouched(self):
        root = Path(self.temp.name)
        legacy = root / "Default"
        legacy.mkdir()
        sentinel = legacy / "legacy-data.txt"
        sentinel.write_bytes(b"old Qt5 site data")
        for mode in ("write", "read"):
            result = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--profile-probe", mode, str(root), self.base],
                capture_output=True, text=True, timeout=40,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("Release of profile requested", result.stderr)
            self.assertIn('"storage": "saved"', result.stdout)
            self.assertIn("persistent=yes", result.stdout)
        self.assertEqual(sentinel.read_bytes(), b"old Qt5 site data")
        self.assertEqual(list(legacy.iterdir()), [sentinel])


def profile_probe(mode, root, base):
    app = QApplication(["browser-profile-probe"])
    app.setQuitOnLastWindowClosed(False)
    real_profile = QWebEngineProfile

    def isolated_profile(name, owner):
        assert name == "BrowserQt6"
        profile = real_profile(name, owner)
        assert Path(profile.persistentStoragePath()).name == name
        profile.setPersistentStoragePath(str(Path(root) / name))
        profile.setCachePath(str(Path(root) / "cache" / name))
        assert not profile.isOffTheRecord()
        return profile

    with patch.object(browser, "QWebEngineProfile", side_effect=isolated_profile), patch.object(browser, "HOMEPAGE", "about:blank"):
        window = browser.WebBrowser()
    view = window.tab_widget.currentWidget()
    load(view, base + "/persistence")
    if mode == "write":
        added = QSignalSpy(window.profile.cookieStore().cookieAdded)
        javascript(view, "localStorage.setItem('persistent', 'saved'); document.cookie='persistent=yes; max-age=3600; path=/'")
        wait_until(lambda: any(bytes(row[0].name()) == b"persistent" for row in added))
    result = javascript(view, "({storage: localStorage.getItem('persistent'), cookies: document.cookie})")
    assert result["storage"] == "saved", result
    assert "persistent=yes" in result["cookies"], result
    window.close()
    window.shutdown()
    sip.delete(window)
    print(json.dumps(result))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--profile-probe":
        profile_probe(*sys.argv[2:])
    else:
        unittest.main()
