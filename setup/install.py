#!/usr/bin/env python3
"""Install hand-off globally into ~/.agents/skills and active Codex AGENTS file.

Uses Python 3.9+ standard library only. No application source changes.
Usage: python3 setup/install.py --dry-run
       python3 setup/install.py
       python3 setup/install.py --verify
Optional for tests: --home /tmp/simulated-user
"""
from __future__ import annotations
import argparse
import hashlib
import datetime
import os
from pathlib import Path
import shutil
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parent.parent
SRC_SKILL = ROOT / 'hand-off'
FRAGMENT = ROOT / 'setup' / 'AGENTS.fragment.md'
BEGIN = '<!-- BEGIN HAND-OFF AUTO ROUTING -->'
END = '<!-- END HAND-OFF AUTO ROUTING -->'


def stamp() -> str:
    return datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:6]


def check_marker(text: str, label: str) -> None:
    if text.count(BEGIN) != text.count(END) or text.count(BEGIN) > 1:
        raise RuntimeError(f'Unsafe or malformed hand-off markers in {label}. No changes made.')
    if BEGIN in text and text.index(BEGIN) > text.index(END):
        raise RuntimeError(f'Reversed hand-off markers in {label}. No changes made.')


def inject(before: str, block: str, label: str, add_if_missing: bool) -> str:
    check_marker(before, label)
    if BEGIN in before:
        start = before.index(BEGIN)
        finish = before.index(END) + len(END)
        return before[:start] + block.rstrip() + before[finish:]
    return (before.rstrip() + '\n\n' + block.rstrip() + '\n') if add_if_missing else before


def ensure_safe_location(path: Path) -> None:
    if path.is_symlink():
        raise RuntimeError(f'Refusing to overwrite symlink: {path}')
    if path.exists() and not path.is_file():
        raise RuntimeError(f'Expected a file at: {path}')


def stage_file_atomic(dest: Path, content: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix='.hand-off-stage-', dir=dest.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
        os.replace(temp_path, dest)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def manifest(folder: Path) -> dict[str, str]:
    result = {}
    for f in folder.rglob('*'):
        if not f.is_file() or f.suffix == '.pyc' or '__pycache__' in f.parts:
            continue
        result[str(f.relative_to(folder))] = hashlib.sha256(f.read_bytes()).hexdigest()
    return result


def main() -> int:
    p = argparse.ArgumentParser()
    group = p.add_mutually_exclusive_group()
    group.add_argument('--dry-run', action='store_true')
    group.add_argument('--verify', action='store_true')
    p.add_argument('--home', type=Path, help='Simulated user home for testing; avoids CODEX_HOME')
    args = p.parse_args()
    home = args.home.expanduser().resolve() if args.home else Path.home()
    codex_dir = (Path(os.environ['CODEX_HOME']).expanduser().resolve() if (not args.home and os.environ.get('CODEX_HOME')) else home / '.codex')
    skill_dir = home / '.agents' / 'skills' / 'hand-off'
    default = codex_dir / 'AGENTS.md'
    override = codex_dir / 'AGENTS.override.md'
    block = FRAGMENT.read_text(encoding='utf-8').strip()
    if BEGIN not in block or END not in block:
        raise RuntimeError('Routing fragment is missing markers')
    if not (SRC_SKILL / 'SKILL.md').is_file():
        raise RuntimeError('Skill source SKILL.md was not found')
    if skill_dir.is_symlink() or (skill_dir.exists() and not skill_dir.is_dir()):
        raise RuntimeError(f'Refusing to replace an unsafe skill directory: {skill_dir}')
    for f in (default, override):
        ensure_safe_location(f)
    active = override if (override.exists() and override.read_text(encoding='utf-8').strip()) else default
    # Update existing marker in inactive file as well, so removing the override later
    # cannot revive obsolete hand-off v1 routing. Do not append to inactive file.
    updates: dict[Path, str] = {}
    for f in (default, override):
        existing = f.read_text(encoding='utf-8') if f.exists() else ''
        new = inject(existing, block, str(f), add_if_missing=(f == active))
        if new != existing:
            updates[f] = new
    if args.verify:
        issues = []
        if not (skill_dir / 'SKILL.md').is_file():
            issues.append(f'Skill not found: {skill_dir / "SKILL.md"}')
        elif manifest(skill_dir) != manifest(SRC_SKILL):
            issues.append('Installed skill differs from this bundle (missing/changed files)')
        active_text = active.read_text(encoding='utf-8') if active.exists() else ''
        if active_text.count(BEGIN) != 1 or active_text.count(END) != 1:
            issues.append(f'Active Codex instructions missing exactly one routing block: {active}')
        if updates:
            issues.append('Global routing not synchronized: ' + ', '.join(str(x) for x in updates))
        if issues:
            for issue in issues:
                print('FAIL:', issue)
            return 1
        print('PASS: global hand-off skill and active routing block present.')
        print('SKILL:', skill_dir)
        print('ACTIVE AGENTS:', active)
        return 0
    print('SKILL:', skill_dir)
    print('ACTIVE AGENTS:', active)
    print('AGENTS updates:', ', '.join(str(x) for x in updates) or 'none')
    if args.dry_run:
        print('DRY RUN: no files changed.')
        return 0
    saved: dict[Path, Path | None] = {}
    touched: list[Path] = []
    backup_id = stamp()
    stage_skill: Path | None = None
    try:
        # Prepare fully staged directory before changing any active config.
        skill_dir.parent.mkdir(parents=True, exist_ok=True)
        stage_skill = skill_dir.parent / ('.hand-off-stage-' + backup_id)
        shutil.copytree(SRC_SKILL, stage_skill)
        for f in updates:
            f.parent.mkdir(parents=True, exist_ok=True)
            if f.exists():
                b = f.with_name(f.name + '.backup-' + backup_id)
                shutil.copy2(f, b)
                saved[f] = b
            else:
                saved[f] = None
        if skill_dir.exists():
            b = skill_dir.with_name('hand-off.backup-' + backup_id)
            shutil.copytree(skill_dir, b, symlinks=True)
            saved[skill_dir] = b
        else:
            saved[skill_dir] = None
        for f, value in updates.items():
            stage_file_atomic(f, value)
            touched.append(f)
        # Replace only after full source staged + prior installation backed up.
        if skill_dir.exists():
            shutil.rmtree(skill_dir)
        touched.append(skill_dir)
        os.replace(stage_skill, skill_dir)
        stage_skill = None
        if not (skill_dir / 'SKILL.md').is_file():
            raise RuntimeError('Skill validation failed after copy')
        print('INSTALLED: hand-off v2 globally. Existing files backed up where replaced.')
        print('Run: python3 setup/install.py --verify')
        print('Open a new Codex session if this skill does not appear.')
        return 0
    except Exception:
        # Best-effort restore. Never delete retained backup copies.
        for f in reversed(touched):
            old = saved.get(f)
            if f == skill_dir:
                if f.exists():
                    shutil.rmtree(f)
                if old is not None:
                    shutil.copytree(old, f, symlinks=True)
            elif old is None:
                if f.exists():
                    f.unlink()
            else:
                shutil.copy2(old, f)
        raise
    finally:
        if stage_skill is not None and stage_skill.exists():
            shutil.rmtree(stage_skill)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print(f'INSTALL ERROR: {exc}', file=sys.stderr)
        sys.exit(1)
