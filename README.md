# hand-off v2 — Global Codex Skill

A repository-grounded technical knowledge transfer workflow for independent development. Separate from `compatible-response`: the latter governs presentation; `hand-off` governs what source to investigate and what artifacts to produce.

## Scope and modes

| Mode | Example | Output |
|---|---|---|
| EXPLAIN | `این متد کجا صدا زده می‌شود؟` | Source-linked chat answer |
| EXPLORE | `معماری کنترلر و سرویس Support را توضیح بده` | Bounded execution/dependency map in chat |
| HANDOFF | `$hand-off Ticketing` or `کل احراز هویت پروژه را توضیح بده` | Chat + two Markdown files |
| REFRESH | `Hand-off تیکتینگ را با سورس فعلی آپدیت کن` | Source-diff review + safe docs update |

## Installation

In a local terminal from the extracted package root (or ask Codex to execute as directed in `codex-install-prompt.md`):

```bash
python3 setup/install.py --dry-run
python3 setup/install.py
python3 setup/install.py --verify
```

The installer honors `CODEX_HOME` for active global instructions, uses `~/.agents/skills/hand-off`, retains existing AGENTS text and `compatible-response`, keeps timestamped backups, updates legacy routing blocks without duplication, and handles active `AGENTS.override.md` without hiding prior instructions. The script is idempotent as to global routing. It does not modify projects or `config.toml`.

If you do not want to run an installer: place the entire `hand-off/` folder in `~/.agents/skills/hand-off` and append `setup/AGENTS.fragment.md` **once** to the active global Codex instructions file (choose `AGENTS.override.md` if non-empty and present, else `AGENTS.md`).

## File artifacts

For a full feature in a writable repository:

```text
docs/hand-offs/<feature-slug>/
├── developer-guide.md
└── llm-context.md
```

Documentation is generated against the repository's **current working tree**, with snapshot and evidence limits. `llm-context.md` is for external LLMs; review it before uploading outside your organization.

## Security

Handoff analysis is read-only with respect to code, databases, Git state, migrations and config. Only handoff docs are permitted writes in HANDOFF/REFRESH mode. Running potentially mutating tests requires permission. The installer alone writes global Skill and active Codex routing files.

## Practical verification

1. Start a fresh Codex session and check `/skills` or mention `$hand-off`.
2. In a real project ask `این متد کجا تعریف شده و چه کسی صداش می‌زند؟` (expect EXPLAIN and **no files**).
3. Ask `$hand-off <actual-feature>` (expect both documents, source coordinates, verification status).
4. Check neither project source nor `compatible-response` changed.
5. Use `python3 ~/.agents/skills/hand-off/scripts/validate_handoff.py <repo-root> <docs-folder>` as an optional **syntactic** check. Human/source-driven audit is still essential.

Codex's implicit selection is model-driven and not absolutely guaranteed; concise routing rules help but real routing/content evals are required before claiming production reliability.
