# PyQt6 Web Browser

A small desktop browser built with PyQt6 and Qt WebEngine. It provides tabbed browsing, a built-in domain blocker, navigation controls, and download prompts.

## Requirements

- Python 3.12 or newer, 64-bit.
- Windows is the verified platform. The code uses portable Qt APIs, but macOS and Linux are not tested by this repository.
- Runtime packages from `requirements.txt`. The tested Windows baseline uses PyQt6 and PyQt6-WebEngine 6.11.0, Qt and Qt WebEngine 6.11.2, and PyQt6-sip 13.13.0.

## Installation

Clone the repository, then create an isolated environment. These commands work in Windows PowerShell without activating the environment:

```powershell
git clone https://github.com/IchigoSolos69/Web-Browser.git
cd Web-Browser
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run

```powershell
.\.venv\Scripts\python.exe "Web Browser.py"
```

If your environment is already activated, use `python "Web Browser.py"`.

## Browsing

- Open a tab with the new-tab button or **Ctrl+T**. New tabs and Home load Google.
- Switch tabs by clicking their labels. Closing a tab selects another tab; the final tab stays open.
- Use Back, Forward, Refresh (**Ctrl+R**), Home, and the address bar to navigate. **Esc** closes the browser.
- Enter HTTP or HTTPS addresses. Bare hosts use HTTPS, with no added `www.`. For a local HTTP server, include the protocol, for example `http://localhost:8000`.
- The address bar accepts URLs, not search queries. Empty input does nothing; invalid or unsupported addresses display a status message.
- User-clicked links that request a new window open in a tab. Background-tab requests keep the current tab selected. Automatic popups are blocked.

## Domain blocker

The browser has a small, fixed list of advertising and tracking hostnames. Rules match a hostname and its subdomains, rather than words in a page's path or query string. Ordinary Amazon pages and URLs such as `/downloads/` are allowed.

This list provides limited coverage. It does not include comprehensive ad-filter rules, cosmetic filtering, or automatically updated lists. Edit `BLOCKED_HOSTS` in the browser script to change it.

## Downloads

File downloads prompt for a destination, initially suggesting the server's filename in the profile's Downloads folder. Cancel dismisses the request. Qt's built-in Save Page dialog supplies its own destination. The download button opens that Downloads folder; a file saved somewhere else remains at the location you selected.

## Saved browser data

Qt6 uses a fresh, persistent profile named `BrowserQt6`. Cookies and site data are shared across tabs and saved between launches. Qt chooses the user-specific storage and cache directories.

Existing Qt5 profile data is left untouched and is not imported. You will need to sign in again once after upgrading. Close the browser normally so Qt can flush its saved data.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests use Python's standard-library `unittest`, Qt's bundled test tools, local HTTP fixtures, and temporary browser profiles. They cover address parsing, domain matching, tab synchronization, new-tab links, downloads, and cookies/site data across process restarts. GUI tests run offscreen; no accounts or external websites are needed. GitHub Actions runs the suite on Windows with Python 3.12.

The dependency versions are pinned to the tested baseline. Update and retest the Qt runtime packages when adopting browser-engine security updates.

## Files

```text
Web-Browser/
├── Web Browser.py        # Browser entry point and domain rules
├── requirements.txt      # Tested runtime versions
├── tests/test_browser.py # Regression tests and local fixtures
└── .github/workflows/tests.yml
```
