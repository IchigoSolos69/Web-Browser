# Roadmap for a stronger personal browser

Research date: 28 October 2026. Companion reports: [ad blocking](ad-blocking.md) and [scam protection](scam-protection.md).

## Direction

Build toward a small Brave-core fork, with no browser-owned ads, aggressive filtering, and additional local scam defenses. Preserve the existing Qt browser while the new direction is evaluated. The first deliverable should establish evidence and service feasibility; it should not replace the working application with an untested source build.

This recommendation follows the user's choices: personal use first, Windows first, local checks with optional cloud assistance, and permission to change the browser foundation. No paid service, public distribution, or upload of browsing content is assumed.

The objective is measurable improvement in specific ad and scam scenarios while retaining working sites and timely security fixes. Neither complete ad removal nor complete scam prevention is a defensible release promise.

## Foundation decision

| Option | Decision | Why |
|---|---|---|
| Brave-core fork | Eventual target | Reuses native filtering and browser-security integration |
| Raw Chromium fork | Defer | Recreates substantial integration already present in Brave |
| Current Python/Qt app | Preserve as a prototype | Useful existing tests and fixtures; not the full security foundation |
| Official Brave with custom rules and a narrow experimental extension | First test vehicle | Can evaluate incremental policies without initially maintaining the engine |

Brave-core contains Chromium customization, engine integration, build tooling, and an upstream synchronization workflow. A future fork should keep custom changes small and traceable. [Brave-core source and build documentation](https://raw.githubusercontent.com/brave/brave-core/master/README.md)

An extension is only an early test vehicle: it cannot substitute for native pre-navigation checks, download release gates, or secure browser-owned warning UI. Use it to test local classifiers and rules, not to claim full native integration.

## Practical build and service gates

The repository's current Qt environment is already small and functional. Read-only inspection during this research found approximately **24 GiB free on C:** and no Visual Studio instance returned by the installed discovery tool. CPU/RAM inventory was unavailable to the sandbox. These are local observations, not a full hardware audit.

Chromium's Windows build instructions currently require at least 100 GB free disk space and at least 8 GB RAM, recommending more than 16 GB. This machine's current C: free space is below that documented disk requirement. Reserve a separate build volume or deliberately provision another build environment before downloading the source. More space than the minimum is sensible for build outputs and updates. [Chromium Windows requirements](https://chromium.googlesource.com/chromium/src/+/main/docs/windows_build_instructions.md)

Use the toolchain required by the selected upstream stable revision. Brave's Windows wiki and Chromium main can describe different Visual Studio versions; do not mix their versions without checking the selected revision. Do not weaken runtime sandboxing or system security protections to make a build work. [Brave Windows setup](https://github.com/brave/brave-browser/wiki/Windows-Development-Environment)

A custom build needs its own authorized service configuration. Brave documents an API-key step for Safe Browsing, while Chromium documents API access and quota limitations. Compiling source does not grant permission to reuse Brave's service credentials, proxy, or update infrastructure. File-reputation connectivity needs separate verification. [Brave service setup](https://raw.githubusercontent.com/brave/brave-core/master/README.md), [Chromium API keys](https://www.chromium.org/developers/how-tos/api-keys/)

## Staged implementation

### Stage 1: Baselines and personal-use proof

- Keep application code unchanged until implementation is requested. Record the current Qt behavior and choose a specific upstream Brave stable release for comparative work.
- Establish Brave Standard, Brave Aggressive, and candidate configurations with recorded filter revisions. Do not claim a win merely from enabling a setting already offered by Brave. [Brave policy](https://github.com/brave/brave-browser/wiki/Blocking-goals-and-policy)
- Build local fixtures and a reproducible benchmark manifest. Start with 50 benign sites across six content categories, three paired runs, and defined core tasks. Keep live sites separate from deterministic fixtures.
- Prototype custom filtering policies and explainable unknown-scam signals on official Brave with explicit local-only/optional-cloud behavior. Keep any experimental extension's permissions narrow and all records local.
- Demonstrate source access for at least one permitted phishing feed. OpenPhish Community is a possible personal supplement; URLhaus needs a user key, and PhishTank new registration is currently unavailable. Missing access must appear as unavailable, not as successful protection.

Exit: reproducible baseline results, a working local experiment, and a list of demonstrated improvements and regressions. There is no superiority claim yet.

### Stage 2: Establish a maintainable native build

- Satisfy disk/toolchain requirements, select the stable upstream revision, and reproduce an otherwise unmodified Brave-core build before adding features.
- Use a separate development profile. Do not silently import or overwrite the user's existing Brave or Qt browser data.
- Establish the security-update and component-update process, test signatures/rollback where we publish updates, and identify the exact service endpoints used by the build.
- Verify safe URL display, sandboxing, TLS error behavior, permissions, and download protections. An absent backend must not be presented as a working inherited feature.
- Keep nonessential features disabled through documented build/runtime options where practical. Avoid broad deletion of upstream code that makes future security merges harder.

Exit: repeatable build/update procedure and verified security/service behavior. Do not promote an outdated or incompletely configured fork for daily use.

### Stage 3: Implement both protection tracks

**Ads:** reuse the upstream native engine; add reviewed policy differences, compatible list subscriptions, early cosmetics/scriptlets, site recovery, bounded local logs, and safe updates. Default to aggressive protection for this personal build, with narrow exceptions.

**Scams:** add source-aware local threat snapshots, native navigation checks, browser-owned warnings, targeted ClickFix/support-page signals, restrictive permission handling, and verified download provenance/release behavior. Avoid blanket bans on new domains, non-English names, or ordinary technical documentation.

Use separate controls. Temporarily relaxing ads must leave phishing, TLS, permission, and dangerous-download protection enabled. Use distinct outcomes for known threats, suspicion, no list match, and unavailable checks.

Cloud assistance stays off until opt-in and correct provider configuration. Native Safe Browsing confirmation requests are cloud assistance too; local-only mode must disclose its coverage difference. No silent raw-URL fallback, credential upload, page-content upload, or shared production API key.

Exit: both tracks pass their deterministic tests and privacy checks, including real navigation/redirect/form/download paths rather than only address-bar calls.

### Stage 4: Evaluate, then decide what earns daily use

- Compare candidate and Brave Aggressive for visible ads left, broken tasks, latency, CPU/memory, update reliability, and filter freshness. Publish ties and losses.
- Evaluate known threats and novel scam behavior separately using independent labels and campaign/time splits. Do not score a feed against itself.
- Compare local-only and cloud-assisted modes separately. A stronger privacy choice can have lower threat recall; report that tradeoff.
- Test corrupt updates, offline startup, stale evidence, provider timeouts, key failure, transient exceptions, and recovery without disabling unrelated defenses.
- Promote only a candidate that improves defined held-out scenarios without material security or compatibility regressions. Use specific claims tied to the evaluated build and date.

There is no fixed delivery estimate until build infrastructure and service access are established. A source build or an impressive synthetic counter is not evidence that the browser is ready.

## Minimum interfaces for later implementation

Prefer existing upstream interfaces. These are behavior contracts, not a request to invent another framework:

| Boundary | Required contract |
|---|---|
| Ad decision | Receive request and initiating-site context; return allow/block/replace plus rule/source for local explanation |
| Threat decision | Preserve URL scope, source, freshness, and reason; distinguish threat, suspicion, no match, and unavailable |
| Feed update | Validate a candidate outside browsing callbacks; atomically activate or retain the previous valid snapshot |
| Warning action | Use browser-controlled UI and limited overrides; do not replay arbitrary form submissions |
| Privacy choice | Explicit local or cloud-assisted mode; no network query implied by a local result |
| Benchmark result | Record build/settings/list hashes, corpus revision, task outcome, and measured costs |

## Research limits

The source research is complete, but fork builds, live ad benchmarks, feed/provider account access, API eligibility, service connectivity, download verdicts, and detector accuracy have not been validated. No live malicious content was executed, external service provisioned, or browser code changed for these reports.

Public distribution would require a separate decision about branding, licenses, service terms, signing, updates, and support. That work is deliberately outside the personal-use first version.
