# Ad-blocking research

Research date: 28 October 2026. Audience: a personal Windows browser, with a Chromium-family fork permitted. This is source research and a proposed design, not a claim of measured superiority. Browser code was not changed for this research.

## Recommendation

Use a small Brave-core fork as the eventual browser foundation. Keep the existing Qt application as a working prototype and fixture client. Prove new filtering policies against upstream Brave before taking on a full build and release process. A raw Chromium fork creates substantially more filtering integration work.

This is an engineering recommendation: reuse an established engine and concentrate changes on demonstrable gaps, recovery from broken sites, and a browser that introduces no advertising of its own. Copying an engine or choosing stronger defaults does not by itself make a browser better than Brave.

## What the current browser lacks

`Web Browser.py` currently matches request hostnames against 45 static rules. It does not consume maintained subscriptions, distinguish request types for filtering, hide page elements, apply site-specific scriptlets, or expose site exceptions and filter explanations. Its tests establish correctness of the small blocker, not broad ad coverage.

Domain matching cannot distinguish an advertisement from useful content on the same host. DNS filtering has the same basic limitation; shared video/content domains make blanket blocking destructive. [AdGuard explanation of DNS filtering](https://adguard.com/en/blog/what-is-dns-filtering.html)

## The Brave benchmark

Brave Standard generally omits first-party network-list blocking; Aggressive applies first- and third-party rules and enables CNAME uncloaking. Brave also has special video-ad behavior and continuing anti-adblock fixes. Compare against **both Standard and Aggressive**, rather than presenting an existing stronger setting as a new technical advantage. [Brave blocking policy](https://github.com/brave/brave-browser/wiki/Blocking-goals-and-policy)

The underlying `adblock-rust` engine supports network filtering, cosmetic filtering, resource replacements, hosts rules, and extensions to filter syntax. Its resources can supply scriptlets and replacement content. Those capabilities still need browser integration: the library alone is not a complete browser blocker. [Engine documentation](https://github.com/brave/adblock-rust)

## Capabilities required

| Layer | Job | Important acceptance case |
|---|---|---|
| Network rules | Match URLs with resource type, initiating site, domain restrictions, and exceptions | Block an advertising script without blocking the site's useful scripts |
| Cosmetic rules | Hide remaining sponsored elements and collapse empty placeholders | Dynamic feed ads disappear without hiding ordinary posts |
| Scriptlets | Apply reviewed, site-specific changes to page behavior | A required fix runs early enough and in the correct JavaScript world |
| Replacement resources | Substitute safe local resources where outright blocking breaks a page | The page works without the blocked advertising dependency |
| Update pipeline | Keep lists and fixes current | A corrupt update cannot replace the working blocker |
| Site controls | Explain filtering and recover from breakage | A temporary ad-filter exception does not turn off scam protection |

Filter syntaxes are not interchangeable. Network modifiers, procedural cosmetics, scriptlets, and preprocessing differ by engine. Record unsupported operations and test compatibility; do not silently count an unsupported rule as active protection. [uBlock Origin filter syntax](https://github.com/gorhill/uBlock/wiki/Static-filter-syntax)

## Architecture comparison

| Foundation | Advantages | Costs and limits | Recommendation |
|---|---|---|---|
| Small Brave-core fork | Native filtering integration and an established browser security architecture | Large builds, upstream merges, service configuration, and release maintenance | Long-term target |
| Raw Chromium fork | Maximum control over browser internals | Must implement and maintain additional filtering integration and policies | Avoid for the first version |
| Existing Qt browser | Small codebase; fast local experiments | Additional native bindings, injection integration, and security-service work | Retain as a prototype |
| Rules and an experimental extension on official Brave | Fast way to evaluate policies while retaining the vendor's browser updates | Cannot replace native navigation/download security gates | First evidence-gathering stage |

Brave-core already connects Chromium, its own patches, and the Rust engine. That existing integration is the reason to choose it. Pin a reviewed stable upstream revision and keep the fork's patch set small. [Brave-core architecture and workflow](https://raw.githubusercontent.com/brave/brave-core/master/README.md)

### If the Qt application is extended instead

Qt exposes request URL, first-party URL, initiator, resource type, and navigation type. A proper engine adapter must map these accurately. [Request context API](https://doc.qt.io/qt-6.11/qwebengineurlrequestinfo.html)

The interceptor stalls requests until it finishes. Never download lists, compile rules, perform DNS resolution, or call a reputation API inside that callback. Prepare immutable snapshots outside the request path. [Interceptor documentation](https://doc.qt.io/qt-6.11/qwebengineurlrequestinterceptor.html)

Qt user scripts support injection timing, isolated worlds, and subframes. An isolated world's JavaScript cannot directly replace the page world's functions, and document creation is too early for normal DOM operations. Test early page-world scriptlets separately from DOM-based cosmetics, including restrictive content-security policies and nested frames. [Script timing and worlds](https://doc.qt.io/qt-6.11/qwebenginescript.html)

Qt 6.10+ also has an extension manager, but it supports Manifest V3 only and cannot load extensions into off-the-record profiles. The presence of that API does not establish compatibility with a particular ad blocker or parity with Brave's native implementation. [Qt extension manager](https://doc.qt.io/qt-6.11/qwebengineextensionmanager.html)

### Avoid the old Python-wrapper shortcut

The published Python `adblock` package is version 0.6.0 from July 2022, with a Windows x64 wheel. Its source pins the Rust engine to 0.5.6. Installing that package is not equivalent to integrating the current engine used by Brave. A serious Qt route needs a maintained binding and tested Windows wheels against a reviewed current upstream version. [Published package](https://pypi.org/project/adblock/), [pinned Rust dependency](https://raw.githubusercontent.com/ArniDagur/python-adblock/master/Cargo.toml)

## Filtering policy for the personal browser

These are proposed product defaults, not claims about current behavior:

- Use aggressive first- and third-party filtering with narrow per-site recovery. Do not add a paid-ad exception program, sponsored new-tab tiles, or replacement advertising.
- Use EasyList, EasyPrivacy, upstream-compatible fixes, and relevant language lists. Enable extra annoyance lists individually after compatibility checks instead of subscribing to every available list.
- Distinguish paid sponsored placements from ordinary recommendations, navigation, and useful first-party content. Provide an element picker for personal preferences rather than hiding every recommendation by default.
- Keep cookie controls separate from cosmetic banner removal. Hiding a consent dialog is not evidence that consent was rejected or that tracking stopped.
- Show the responsible rule/list and update age. Keep request logs local, bounded, and clearable; do not collect browsing history for analytics.

EasyList intentionally does not target all self-promotion. A requirement to remove every form of promotion therefore exceeds its stated policy and needs separate, explicit user rules. [EasyList coverage policy](https://raw.githubusercontent.com/easylist/easylist/master/README.md)

## List supply chain

Maintain a small source registry containing each publisher, HTTPS URL, declared license, revision, expiry, and supported syntax. Preserve attribution. Engine code and list data have separate licensing: for example, `adblock-rust` declares MPL-2.0, while uAssets carries GPLv3. Follow each list's referenced license before redistributing it. [Engine license](https://github.com/brave/adblock-rust), [uAssets license](https://raw.githubusercontent.com/uBlockOrigin/uAssets/master/LICENSE), [EasyList license reference](https://easylist.to/easylist/easylist.txt)

The proposed updater must:

1. Respect publisher expiry and HTTP caching instructions; use conditional downloads.
2. Apply transfer/decompression limits and reject HTML errors, malformed syntax, and unexpectedly empty files.
3. Compile and validate a candidate snapshot outside browsing callbacks, then activate it atomically.
4. Retain the last working snapshot and provide rollback after a bad update.
5. Ship reviewed scriptlet implementations with the application or authenticated component system. A text subscription may select approved primitives; it must not introduce arbitrary remote JavaScript.
6. Use signed application/component updates where we control publishing. Do not describe ordinary upstream text lists as signed if they are not.

## How to demonstrate an improvement

Create at least 50 representative benign sites across search, news, shopping, social, video, and regional content. Record browser builds, operating system, region, account state, filters, revision hashes, and settings. Run at least three paired repetitions with fresh profiles and separate cold/warm results.

Compare visible ads left on the page, unwanted transferred bytes, core tasks broken, rendering/interaction latency, CPU, memory, and update failures. Use screenshots and task completion alongside request logs. A larger blocked-request counter, or a single synthetic ad-test score, does not establish better browsing.

Use deterministic fixtures for rule exceptions, request types, same-origin ads, dynamic DOMs, SPAs, frames, CSP, scriptlets, malformed updates, offline startup, and rollback. Reserve a held-out set so fixes are not judged only on the sites used to develop them.

Call the result better at a named task only when it improves the measured gap without a meaningful regression in working pages or security. If Brave Aggressive already removes all measured ads on a site, report a tie.

## Limits and work not performed

Server-generated sponsored content, advertisements embedded in a video stream, creator sponsorships, and evolving anti-adblock systems prevent a credible promise of zero ads everywhere forever. AdGuard also documents why DNS-level rules cannot reliably separate shared-domain video ads from content. [Video/DNS limitations](https://adguard.com/fc/en/article/how-to-block-ads-on-youtube.html)

No fork was built, new blocker installed, live ad comparison performed, or performance advantage measured. See [the roadmap](roadmap.md) for sequencing and build constraints, and [the separate scam-protection research](scam-protection.md) for security requirements.
