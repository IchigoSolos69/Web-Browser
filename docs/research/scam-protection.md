# Scam-protection research

Research date: 28 October 2026. Defaults chosen by the user: personal use first, Windows first, local checks with optional cloud assistance, and permission to consider a Chromium-family fork. This document distinguishes verified platform capabilities from proposed product behavior.

## Recommendation

Retain an established browser's native security pipeline, then add fresh local threat intelligence and narrowly evaluated defenses against deceptive behavior. Keep scam checks independent of ad-filter exceptions. A larger advertising-domain list is not a phishing detector, file scanner, or fraud guarantee.

The current Qt application has a fixed advertising/tracking host list and basic download prompts. It has no implemented threat-feed updater, reputation checks, scam interstitials, or file-reputation service. Qt's own description states that its Chromium integration omits Google's Safe Browsing service. Chromium-based rendering alone therefore does not establish Chrome-like anti-phishing coverage. [Qt's relationship to Chromium](https://wiki.qt.io/QtWebengine)

## What Brave already does

Brave documents default Safe Browsing protection for websites, downloads, and extensions. Desktop website checks use local URL-hash prefixes and online confirmation through a Brave proxy. Its dangerous-download application-reputation check is separate from URL-list matching. That is a substantial baseline to preserve and verify in a custom build. [Brave's Safe Browsing implementation](https://support.brave.app/hc/en-us/articles/15222663599629-Safe-Browsing-in-Brave)

Brave's current privacy policy confirms desktop proxying and describes automatic browser updates. A fork must operate its own working update and service configuration; keeping source code does not grant access to Brave's production infrastructure. [Brave browser privacy policy](https://brave.com/privacy/browser/)

## Threats need different defenses

| Threat | Primary protection | What a blocklist misses |
|---|---|---|
| Credential phishing | Fresh URL reputation, reliable origin display, and lookalike checks | New campaigns and compromised legitimate pages |
| Fake security/support pages | Browser-controlled permission gates, dialog limits, fullscreen escape, and behavior warnings | Coercive instructions on previously unseen pages |
| ClickFix fake verification | Local checks around deceptive instructions and page-initiated clipboard writes | Malware launched by the user outside the browser |
| Malicious downloads | Native dangerous-file pipeline, provenance, and OS protection | A benign-looking URL can deliver a harmful or changed file |
| Fake shops and investment/crypto fraud | Reputation plus explainable warning signals | A valid certificate and plausible page can still front a scam |
| Permission abuse | User-initiated, origin-specific prompts with denial/revocation | Notifications or device access granted through misleading instructions |

Microsoft describes ClickFix campaigns that use fake CAPTCHAs or repair instructions to persuade users to paste commands into Run or a terminal. This is a useful concrete test target beyond known phishing domains. [Microsoft ClickFix research](https://www.microsoft.com/en-us/security/blog/2025/08/21/think-before-you-clickfix-analyzing-the-clickfix-social-engineering-technique/)

## Reputation sources and operational limits

These are candidates, not accounts or integrations that have been provisioned.

| Source | Coverage and documented freshness | Access/usage facts | Proposed role |
|---|---|---|---|
| Google Safe Browsing v5 | Phishing/deceptive pages, malware URLs, unwanted software; local-list and real-time modes | Non-commercial API; cloud confirmation and provider setup required | Optional cloud-assisted personal protection |
| OpenPhish Community | Limited phishing feed; every 12 hours | Personal/independent research terms; do not redistribute its data without permission | Initial directly downloaded local supplement |
| PhishTank | Verified online phishing URLs; hourly bulk data | Frequent downloads require a key; without one, a few downloads daily | Optional supplement if usable access exists |
| URLhaus | Malware-distribution URLs; exports every 5 minutes | User Auth-Key and fair-use limits | Optional local malware-URL supplement |
| Google Web Risk | Commercial URL reputation; lookup and local hashed-list update APIs | Enterprise service; separate commercial terms | Future public/commercial evaluation |

Sources: [Safe Browsing v5](https://developers.google.com/safe-browsing/reference), [OpenPhish feed tiers](https://openphish.com/phishing_feeds.html), [OpenPhish terms](https://openphish.com/terms.html), [PhishTank developer information](https://phishtank.org/developer_info.php), [URLhaus API](https://urlhaus.abuse.ch/api/), [Web Risk overview](https://docs.cloud.google.com/web-risk/docs/overview).

Important access details checked for this research:

- PhishTank's registration page currently says new registration is temporarily disabled. Do not make obtaining a new key a prerequisite. Its FAQ permits commercial and non-commercial API use, subject to the documented access limits. [Registration status](https://phishtank.org/register.php), [FAQ](https://phishtank.org/faq.php)
- URLhaus is a malware-URL source, not a general phishing or fake-shop database. The abuse.ch terms updated on 21 October 2026 require authentication and describe not-for-profit fair use, possible paid commercial access, and restrictions on AI training. Do not assume all abuse.ch feeds are unrestricted CC0 data. [Current abuse.ch terms](https://abuse.ch/terms-of-use/)
- The OpenPhish Community interval and limited coverage make it a supplement, not an equivalent substitute for a broad real-time service. Fetch it directly for permitted personal use; do not commit feed contents into this repository.

### Google-specific requirements

Safe Browsing v5 distinguishes raw `urls.search` queries from URL-expression hash-prefix queries through `hashes.search`. Optional Oblivious HTTP can separate the provider from the user's IP only when a working independent relay is actually configured. Hashing alone does not provide anonymity. [Protocol and privacy model](https://developers.google.com/safe-browsing/reference)

Current terms require appropriate attribution and clear limitations, Google attribution only for Google-sourced warnings, and updated information received within 30 minutes before treating a Google-listed URL as unsafe. Commercial use needs a separate agreement or another suitable product. Respect protocol cache lifetimes as well as these terms. [Safe Browsing terms](https://developers.google.com/safe-browsing/terms)

The public URL-hash API does not accept executable SHA-256 hashes as a substitute for file scanning. Enabling URL reputation does not automatically provide a custom browser with Brave's download-verdict backend.

## Proposed behavior

### 1. Local checks and data updates

Keep phishing/malware URL records separate from advertising filters. Store provider, canonical match, update time, expiry, and reason. Preserve URL/path scope when supplied: one malicious page on shared hosting does not justify banning every unrelated page on that host.

Fetch authorized snapshots over HTTPS outside navigation callbacks. Enforce format and size limits, validate a candidate database, and switch atomically. Maintain a last working snapshot and visible stale/unavailable states. Each provider needs its own expiration policy. Expired Google evidence must not continue to produce Google-based blocking; other sources must also follow their terms.

For browser behavior, use distinct results: `known threat`, `suspicious behavior`, `not found in current sources`, and `check unavailable`. None of the last three means that a site has been proven safe.

### 2. Native navigation and warning pages

Integrate the final fork through native navigation/security hooks so redirects, forms, frames, and downloads cannot bypass checks made only in the address-bar handler. Show warnings in browser-controlled UI, with Return to safety as the primary action. Escape untrusted text. Any override must be explicit, limited, and unable to silently trust unrelated origins.

Keep Chromium's URL formatting, IDN handling, and registrable-domain logic instead of inventing a second display/parser policy. These are security-sensitive parts of identifying a page's actual origin. [Chromium URL display guidance](https://github.com/chromium/chromium/blob/main/docs/security/url_display_guidelines/url_display_guidelines.md), [IDN and lookalike protections](https://github.com/chromium/chromium/blob/main/docs/idn.md)

Qt's request interceptor is synchronous; its navigation-request object provides accept/reject rather than a general asynchronous pause. Do not perform online reputation calls inside the interceptor or cancel and replay arbitrary POST form submissions. This is an important reason to prefer native browser integration for the final product. [Qt interception](https://doc.qt.io/qt-6.11/qwebengineurlrequestinterceptor.html), [Qt navigation requests](https://doc.qt.io/qt-6.11/qwebenginenavigationrequest.html)

### 3. Behavioral protection against unknown scams

Start with local, explainable signals and controlled fixtures:

- Detect combinations such as infection claims plus payment/remote-access instructions, or fake verification plus an executable command copied by the page.
- Require user intent and clear origin context for notifications, sensitive device permissions, fullscreen, pointer/keyboard lock, and external application launches.
- Preserve an exit that page scripts cannot suppress, and stop repeated dialog loops.
- Treat weak signals as warnings while evaluating false positives. A young domain, non-English hostname, ordinary install command, or unsigned file is not independently proof of a scam.
- Keep passwords, typed form values, OS clipboard contents, and complete browsing histories out of experimental telemetry. Inspect only the minimum local page/action signals needed for a rule.

Do not start with an unrestricted cloud LLM or a large local model. Establish a labeled evaluation set first. Google's documented Gemini Nano tech-support defense performs local signal extraction followed by a server verdict; it is not evidence that a downloadable model alone supplies an offline solution to all scams. [Google's system description](https://blog.google/security/using-ai-to-stop-tech-support-scams-in/?hl=en)

### 4. Download protection

Preserve and verify the native browser's file-type, reputation, quarantine/release, and dangerous-download behavior. Never auto-open executables. Ensure Windows Internet-origin marking and attachment policies survive the download workflow. The Windows attachment interfaces can consult trust services and persist provenance; they are not an unconditional antivirus guarantee. [Windows attachment handling](https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nn-shobjidl_core-iattachmentexecute), [Save behavior](https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nf-shobjidl_core-iattachmentexecute-save)

### 5. Explicit privacy modes

**Local mode:** approved feed downloads may contact publishers, exposing updater IP and ordinary request metadata, but visited addresses and page contents are not sent for reputation checks. Generic feed downloads are different from browsing-dependent queries. Show reduced coverage/freshness honestly.

**Cloud-assisted mode:** activate only after informed opt-in and working provider configuration. Prefer URL-hash queries; disclose IP exposure unless an independent relay has been verified. Do not fall back silently to raw-URL uploads. Keep keys outside source control.

Brave's existing prefix confirmations and download-hash queries count as cloud assistance. A fork cannot leave them enabled while claiming it is entirely local. Conversely, disabling them can reduce protection relative to official Brave. Evaluate the two modes separately rather than hiding this tradeoff.

## Evidence needed before calling it better

- Use independently labeled, held-out phishing and benign URL records; time-split campaigns and deduplicate related hosts. A detector evaluated only on its own source feed is a membership test, not evidence of general scam detection.
- Report recall, benign false-positive rate, first-seen-to-detection delay, data age, provider availability, and navigation overhead. Separate known-list results from unknown-page behavioral detection.
- Use local inert fixtures for redirects, POST forms, frames, impersonation, IDNs, support-dialog loops, fake verification, clipboard lures, permissions, and download release.
- Compare against recorded upstream Brave with equivalent online/privacy settings. Report where the local-only mode loses coverage as well as where it improves behavior warnings.
- Use official provider test pages and inert files for integration checks. Evaluating URL records does not require executing live threats.

No service account was created, API key acquired, feed downloaded, live malicious page visited, executable scanned, or detection accuracy measured. See [the roadmap](roadmap.md) for dependencies and [the ad-blocking research](ad-blocking.md) for the separate filtering system.
