# Codex installation request — hand-off v2

Install/update the attached `hand-off v2` skill **globally for my macOS Codex user**, not per project. This is an **installation task**, not a request to analyze or modify this repository. Complete it now with local verification.

## Source bundle

Use the extracted directory containing this file, `hand-off/SKILL.md`, and `setup/install.py`. If only the ZIP is available, safely extract it to a temporary location and locate the bundle root. If you cannot access the files, **do not fabricate them or claim installation**; report the missing local path.

## Required installation behavior

1. First inspect the current active Codex home: use `CODEX_HOME` when set; otherwise `~/.codex`. Read (don't overwrite) both `AGENTS.md` and `AGENTS.override.md`; remember the active nonempty one. Inspect `~/.agents/skills/hand-off` and `~/.agents/skills/compatible-response` if they exist.
2. Review `hand-off/SKILL.md`, relevant references, setup fragment and installer. Check the bundle is self-contained, paths point to real files, and the installer does not touch any application source or the separate `compatible-response` skill.
3. Run `python3 setup/install.py --dry-run`; inspect the proposed file locations and collision/marker conditions. Resolve any failures non-destructively; do not delete existing user configuration.
4. Run `python3 setup/install.py` from the bundle root. Global Skill path must be `~/.agents/skills/hand-off/`. Add exactly one concise auto-routing block to the active global Codex AGENTS file. Honor `AGENTS.override.md` precedence. Preserve all unrelated configuration, existing skills and manual notes. Keep backups.
5. Run `python3 setup/install.py --verify` and independently verify the installed `SKILL.md`, all its reference and template files, a single active auto-routing block, and unchanged `compatible-response` contents. Check active AGENTS size/truncation risk without modifying unrelated `config.toml` settings.
6. Perform non-mutating smoke checks: ensure YAML frontmatter name/description is valid, paths and Python script compile, and no duplicate routing markers exist. Do not claim real implicit routing works without a fresh Codex session and actual model test. If possible, start a fresh session only if safe and available.
7. Final response in Persian, compact: installed skill path; active global AGENTS file; installer/smoke result; backup paths; any unresolved issue; examples for `$hand-off Ticketing` and a natural-language auto-trigger.

## Behavioral contract to preserve

- `EXPLAIN`: small method/class question => precise grounded chat answer, no docs.
- `EXPLORE`: bounded architectural question => verified flow/map, no docs.
- `HANDOFF`: `$hand-off <feature>` or complete natural-language feature handoff => `developer-guide.md` plus standalone `llm-context.md` under `docs/hand-offs/<slug>/`.
- `REFRESH`: re-check code changes and safely update the two docs, preserving manual edits.
- Full forward/reverse call tracing, DI/registration, routes, permissions, state, error/async flows, source/line evidence, independent development/debugging/refactor/testing playbook, real coverage limits and snapshot freshness.
- Never edit application source during handoff; never infer unobserved runtime success; never export secrets.
- `compatible-response` remains a completely separate globally installed skill governing output presentation and brevity. **Do not modify, duplicate, or install it as part of this task.**

Proceed without unnecessary questions; if Codex sandbox prevents writing to the user home, request permission only for those exact target paths and report the limitation if denied. Never use broad `--yolo`/sandbox bypass flags.
