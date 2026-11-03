# Khadem (خادم) — Arabic-first Hermes Agent

الدليل العربي: [README.ar.md](README.ar.md)

Khadem is a fork of [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) that
turns it into an Arabic-first agent. The fork is built so that **upstream can be merged at any time
and the Arabic experience keeps working**: nothing in upstream's files is edited.

## What Khadem adds

| Layer | Where | What it does |
|---|---|---|
| Branding | `plugins/khadem/branding.py` | At load time reads upstream's own `locales/ar.yaml` + `ar.tui.yaml` and registers a pack layer that renames Hermes → خادم (commands, paths, env vars untouched). New upstream strings are branded automatically. |
| Arabic overrides | `plugins/khadem/locales/ar[.tui].yaml` (optional) | Khadem's own Arabic for keys upstream has not translated yet, or wording Khadem prefers. Wins over upstream. |
| Persona | `plugins/khadem/persona.py` | Plugin system-prompt section: the agent is خادم, writes polished Modern Standard Arabic (or the user's dialect), RTL-aware documents, and today's Gregorian + Hijri date. English persona under non-Arabic locales. |
| Arabic defaults | `plugins/khadem/defaults.py` | On a local home, writes `display.language: ar`, `stt.language: ar` and `display.skin: khadem` **only if unset** — an explicit user choice always wins. |
| Tools | `plugins/khadem/tools.py`, `arabic.py` | `arabic_text` (normalize, diacritics, Eastern/Western digits, number→words, money in words / تفقيط for 20 currencies, text stats) and `hijri_date` (official Umm al-Qura calendar, vendored table, 1343–1500 AH). |
| CLI/TUI skin | `plugins/khadem/skins/khadem.yaml`, `skins.py` | Emerald/gold skin with Arabic labels and a KHADEM banner, installed into `<home>/skins/`; selected via `display.skin: khadem` only when unset. |
| Skills | `plugins/khadem/skills/*` | `khadem:arabic-writing`, `arabic-translation`, `arabic-documents` (RTL Word/PDF/Excel/PPT/images), `arabic-dialects` (incl. Arabizi), `hijri-calendar`, `arabic-nlp`. |

The plugin is a bundled `kind: backend` plugin, so it loads by default with no config entry.
Turn it off with `hermes plugins disable khadem` or `KHADEM_DISABLE=1`.
Under pytest it stays inert unless `KHADEM_FORCE=1`, so upstream's own test-suite keeps testing
upstream behaviour; `tests/plugins/test_khadem_plugin.py` opts in.

## Syncing upstream

```bash
scripts/khadem/sync-upstream.sh      # fetch + merge upstream/main, then scripts/khadem/check.sh
```

`check.sh` runs the Khadem contract tests (including **seam tests** that fail if upstream renames a
core function Khadem relies on), upstream's i18n/system-prompt tests, and
`scripts/khadem/i18n_report.py` (Arabic coverage: missing keys, stale overrides, branded count).

`.github/workflows/khadem-sync.yml` does the same weekly and opens a PR from `khadem/upstream-sync`.
The built-in Actions token cannot push merges that change `.github/workflows/` (upstream often
does); add a `KHADEM_SYNC_TOKEN` secret (PAT with repo + workflow scopes) to make that fully
automatic — without it the workflow opens an "Upstream sync ready" issue with the check results.

### When a sync reports something

- **Missing Arabic keys** — upstream added English strings it has not translated yet. They show in
  English until upstream translates them; to translate them now, add them to
  `plugins/khadem/locales/ar.yaml` (core) or `ar.tui.yaml` (TUI) using the same dotted keys.
- **Stale overrides** — delete the listed keys from `plugins/khadem/locales/`.
- **Seam test failure** — upstream moved an internal function; update the import in
  `plugins/khadem/` (the test names the module and attribute).

## Patch ledger (edits to upstream files)

None. Khadem-owned paths: `plugins/khadem/`, `tests/plugins/test_khadem_plugin.py`,
`scripts/khadem/`, `.github/workflows/khadem-sync.yml`, `KHADEM.md`, `README.ar.md`.
A merge conflict can therefore only come from a file someone edited outside this list — keep
Khadem files as ours, take upstream for everything else.
