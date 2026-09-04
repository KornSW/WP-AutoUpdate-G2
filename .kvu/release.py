#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import html
import json
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "doc"
CHANGELOG = DOC / "changelog.md"
VERSIONINFO = DOC / "versioninfo.json"
UPDATE_JSON = DOC / "update.json"
ENTRY_MARKER = DOC / "plugin-entry.txt"
UPDATER_PREFIX = DOC / "updater-prefix.txt"
SELF_UPDATE_TEMPLATE = ROOT / ".kvu/templates/self-update.php"
DIST = ROOT / "dist"

SELF_UPDATE_START = "/*************** SELF-UPDATE ***************/"
SELF_UPDATE_END = "/*******************************************/"

RELEASE_HEADER_RE = re.compile(r"^\s*##\s+v\s+(\d+)\.(\d+)\.(\d+)\s*$", re.I)
UPCOMING_RE = re.compile(r"^\s*##\s+Upcoming Changes(?:\s+\(([^)]+)\))?\s*$", re.I)
PLUGIN_NAME_RE = re.compile(r"(?mi)^\s*\*\s*Plugin Name:\s*(.+?)\s*$")
HEADER_LINE_RE = {
    "Version": re.compile(r"(?mi)^(\s*\*\s*Version:\s*).*$"),
    "Plugin URI": re.compile(r"(?mi)^(\s*\*\s*Plugin URI:\s*).*$"),
    "Update URI": re.compile(r"(?mi)^(\s*\*\s*Update URI:\s*).*$"),
    "Description": re.compile(r"(?mi)^\s*\*\s*Description:\s*(.*?)\s*$"),
    "Author": re.compile(r"(?mi)^\s*\*\s*Author:\s*(.*?)\s*$"),
    "Requires at least": re.compile(r"(?mi)^\s*\*\s*Requires at least:\s*(.*?)\s*$"),
    "Requires PHP": re.compile(r"(?mi)^\s*\*\s*Requires PHP:\s*(.*?)\s*$"),
}
SKIP_MARKERS_RE = re.compile(r"\[(?:skip ci|ci skip|no ci|skip actions|actions skip)\]", re.I)

def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)

def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()

def is_plugin_entry(path: Path) -> bool:
    if not path.is_file() or path.suffix.lower() != ".php":
        return False
    try:
        head = path.read_text(encoding="utf-8", errors="ignore")[:16384]
    except OSError:
        return False
    return PLUGIN_NAME_RE.search(head) is not None

def detect_entry() -> Path:
    if ENTRY_MARKER.exists():
        rel = ENTRY_MARKER.read_text(encoding="utf-8").strip()
        candidate = (ROOT / rel).resolve()
        try:
            candidate.relative_to(ROOT.resolve())
        except ValueError:
            fail("doc/plugin-entry.txt points outside the repository.")
        if not is_plugin_entry(candidate):
            fail(f"Configured plugin entry is invalid: {rel}")
        return candidate

    candidates: list[Path] = []
    for path in ROOT.glob("*.php"):
        if is_plugin_entry(path):
            candidates.append(path)
    for directory in ROOT.iterdir():
        if not directory.is_dir() or directory.name.startswith("."):
            continue
        for path in directory.glob("*.php"):
            if is_plugin_entry(path):
                candidates.append(path)

    candidates = sorted(set(candidates))
    if len(candidates) == 0:
        fail("No WordPress plugin entry file found in repository root or exactly one directory level below it.")
    if len(candidates) > 1:
        listing = "\n".join(f" - {p.relative_to(ROOT)}" for p in candidates)
        fail("Multiple WordPress plugin entry files found. Create doc/plugin-entry.txt with one relative path:\n" + listing)
    return candidates[0]

def header_value(content: str, name: str) -> str:
    if name == "Plugin Name":
        m = PLUGIN_NAME_RE.search(content)
    else:
        m = HEADER_LINE_RE[name].search(content)
    if not m:
        return ""
    return m.group(1).strip()

def set_header(content: str, name: str, value: str) -> str:
    pattern = HEADER_LINE_RE[name]
    if pattern.search(content):
        return pattern.sub(lambda m: m.group(1) + value, content, count=1)

    plugin_name_match = PLUGIN_NAME_RE.search(content)
    if not plugin_name_match:
        fail("Cannot patch plugin headers because Plugin Name header is missing.")

    line_end = content.find("\n", plugin_name_match.end())
    if line_end == -1:
        fail("Cannot patch malformed plugin header.")
    insertion = f" * {name}: {value}\n"
    return content[:line_end+1] + insertion + content[line_end+1:]

def short_plugin_token(plugin_name: str, slug: str) -> str:
    source = plugin_name.strip() or slug.strip()
    tokens = re.findall(r"[A-Za-z0-9]+", source.lower())
    tokens = [t for t in tokens if t not in {"wordpress", "plugin"}]
    compact = "".join(tokens)
    if not compact:
        compact = re.sub(r"[^a-z0-9]", "", slug.lower())
    if not compact:
        compact = "upd"
    return compact[:12]

def get_or_create_updater_prefix(plugin_name: str, slug: str) -> tuple[str, str]:
    DOC.mkdir(parents=True, exist_ok=True)
    if UPDATER_PREFIX.exists():
        prefix = UPDATER_PREFIX.read_text(encoding="utf-8").strip()
        if not re.fullmatch(r"[a-z][a-z0-9]{5,31}", prefix):
            fail("doc/updater-prefix.txt contains an invalid updater prefix.")
    else:
        prefix = f"ksw{short_plugin_token(plugin_name, slug)}{secrets.token_hex(2)}"
        UPDATER_PREFIX.write_text(prefix + "\n", encoding="utf-8")

    class_prefix = prefix.upper()
    return prefix, class_prefix

def render_self_update(prefix: str, class_prefix: str) -> str:
    template = SELF_UPDATE_TEMPLATE.read_text(encoding="utf-8")
    rendered = template.replace("{{KSWUPD_PREFIX}}", prefix)
    rendered = rendered.replace("{{KSWUPD_CLASS_PREFIX}}", class_prefix)
    if "{{KSWUPD_" in rendered:
        fail("Unresolved self-update template placeholder remains after rendering.")
    return rendered

def self_update_block(prefix: str) -> str:
    return (
        SELF_UPDATE_START + "\n"
        + "require_once __DIR__ . '/self-update.php';\n"
        + f"{prefix}_bootstrap( __FILE__ );\n"
        + SELF_UPDATE_END
    )

def ensure_update_block(content: str, prefix: str) -> str:
    block = self_update_block(prefix)
    managed = re.compile(
        re.escape(SELF_UPDATE_START) + r".*?" + re.escape(SELF_UPDATE_END),
        re.S,
    )
    if managed.search(content):
        return managed.sub(block, content, count=1)

    # Prefer inserting directly after the common ABSPATH guard.
    guard = re.search(
        r"if\s*\(\s*!\s*defined\s*\(\s*['\"]ABSPATH['\"]\s*\)\s*\)\s*\{.*?\}\s*",
        content,
        re.S,
    )
    if guard:
        pos = guard.end()
        return content[:pos] + "\n" + block + "\n\n" + content[pos:]

    # Fallback: after the plugin header docblock.
    plugin_name_match = PLUGIN_NAME_RE.search(content)
    if plugin_name_match:
        start = content.rfind("/**", 0, plugin_name_match.start())
        end = content.find("*/", plugin_name_match.end())
        if start != -1 and end != -1:
            pos = end + 2
            return content[:pos] + "\n\n" + block + content[pos:]

    fail("Unable to find a safe insertion point for the SELF-UPDATE block.")

def create_initial_changelog() -> None:
    DOC.mkdir(parents=True, exist_ok=True)
    if CHANGELOG.exists():
        return
    CHANGELOG.write_text(
        "# Change log\n\n"
        "## Upcoming Changes\n\n"
        "*(none)*\n",
        encoding="utf-8",
    )

def read_changelog():
    create_initial_changelog()
    lines = CHANGELOG.read_text(encoding="utf-8").splitlines()

    upcoming_idx = None
    first_release_idx = None
    latest = (0, 0, 0)

    for i, line in enumerate(lines):
        if UPCOMING_RE.match(line) and upcoming_idx is None:
            upcoming_idx = i
            continue
        rm = RELEASE_HEADER_RE.match(line)
        if rm and first_release_idx is None:
            first_release_idx = i
            latest = tuple(map(int, rm.groups()))

    if upcoming_idx is None:
        fail("changelog.md is missing '## Upcoming Changes'.")
    if first_release_idx is None:
        first_release_idx = len(lines)

    incoming = []
    for line in lines[upcoming_idx + 1:first_release_idx]:
        s = line.strip()
        if not s or s == "*(none)*":
            continue
        if s.lower().startswith("released **"):
            continue
        if s.startswith("- ") or s.startswith("* "):
            s = s[2:].strip()
        incoming.append(s)

    return lines, upcoming_idx, first_release_idx, latest, incoming

def newest_merged_version_tag() -> str | None:
    try:
        tags = git(
            "for-each-ref",
            "--merged=HEAD",
            "--sort=-creatordate",
            "--format=%(refname:short)",
            "refs/tags",
        ).splitlines()
    except subprocess.CalledProcessError:
        return None

    for tag in tags:
        if re.search(r"\d+\.\d+(?:\.\d+)?(?:\.\d+)?", tag):
            return tag
    return None

def git_fallback_changes() -> list[str]:
    boundary = newest_merged_version_tag()
    range_arg = f"{boundary}..HEAD" if boundary else "HEAD"
    try:
        subjects = subprocess.check_output(
            ["git", "log", range_arg, "--format=%s", "--max-count=20"],
            cwd=ROOT,
            text=True,
        ).splitlines()
    except subprocess.CalledProcessError:
        subjects = []

    result = []
    for subject in subjects:
        if "VERSIONING" in subject.upper():
            continue
        subject = SKIP_MARKERS_RE.sub("", subject).strip()
        if subject:
            result.append(subject)
    return result

def classify(changes: list[str], previous: tuple[int, int, int]):
    grade = "fix"
    mvp = False
    groups = {"major": [], "minor": [], "fix": []}
    mvp_lines = []

    for change in changes:
        lower = change.lower()
        if "**mvp**" in lower:
            mvp = True
            mvp_lines.append(change)

        if "**breaking change:**" in lower:
            group = "major"
            grade = "major"
        elif "**new feature:**" in lower:
            group = "minor"
            if grade != "major":
                grade = "minor"
        else:
            group = "fix"

        groups[group].append(change)

    if mvp_lines:
        for line in reversed(mvp_lines):
            for group in groups.values():
                while line in group:
                    group.remove(line)
            groups["major"].insert(0, line)

    ordered = groups["major"] + groups["minor"] + groups["fix"]

    major, minor, patch = previous
    if mvp and major == 0:
        next_version = (1, 0, 0)
    elif grade == "major":
        if major == 0:
            next_version = (major, minor + 1, 0)
        else:
            next_version = (major + 1, 0, 0)
    elif grade == "minor":
        next_version = (major, minor + 1, 0)
    else:
        if previous == (0, 0, 0):
            next_version = (0, 1, 0)
        else:
            next_version = (major, minor, patch + 1)

    change_grade = "initial" if previous == (0, 0, 0) else grade
    return next_version, change_grade, ordered

def version_string(v: tuple[int, int, int]) -> str:
    return f"{v[0]}.{v[1]}.{v[2]}"

def materialize_changelog(lines, upcoming_idx, first_release_idx, version, date_info, changes):
    before = lines[:upcoming_idx]
    history = lines[first_release_idx:]
    block = [
        "## Upcoming Changes",
        "",
        "*(none)*",
        "",
        f"## v {version}",
        f"released **{date_info}**, including:",
    ]
    block.extend(f" - {c}" for c in changes)
    block.extend(["", ""])
    CHANGELOG.write_text("\n".join(before + block + history).rstrip() + "\n", encoding="utf-8")

def build_zip(plugin_dir: Path, slug: str) -> Path:
    DIST.mkdir(exist_ok=True)
    zip_path = DIST / f"{slug}.zip"
    if zip_path.exists():
        zip_path.unlink()

    ignored_names = {".git", ".github", ".kvu", "doc", "dist", "__pycache__"}
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in plugin_dir.rglob("*"):
            if not path.is_file():
                continue
            if any(part in ignored_names for part in path.relative_to(plugin_dir).parts):
                continue
            arcname = f"{slug}/{path.relative_to(plugin_dir).as_posix()}"
            zf.write(path, arcname)

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        if not names:
            fail("Generated plugin ZIP is empty.")
        if any(not name.startswith(slug + "/") for name in names):
            fail("ZIP contains files outside the single expected top-level plugin directory.")

    return zip_path

def main() -> None:
    repository = (Path.cwd() and __import__("os").environ.get("GITHUB_REPOSITORY", "")).strip()
    branch = __import__("os").environ.get("GITHUB_REF_NAME", "master").strip() or "master"
    if not repository or "/" not in repository:
        fail("GITHUB_REPOSITORY must contain owner/repository.")

    entry = detect_entry()
    plugin_dir = entry.parent
    content = entry.read_text(encoding="utf-8")

    plugin_name = header_value(content, "Plugin Name")
    description = header_value(content, "Description")
    author = header_value(content, "Author")
    requires_wp = header_value(content, "Requires at least")
    requires_php = header_value(content, "Requires PHP")

    slug = plugin_dir.name if plugin_dir != ROOT else entry.stem
    homepage = f"https://github.com/{repository}"
    update_uri = f"https://raw.githubusercontent.com/{repository}/master/doc/update.json"

    # Create/load the persistent per-plugin updater prefix and personalize the runtime template.
    updater_prefix, updater_class_prefix = get_or_create_updater_prefix(plugin_name, slug)
    (plugin_dir / "self-update.php").write_text(
        render_self_update(updater_prefix, updater_class_prefix),
        encoding="utf-8",
    )

    # Add/update repository metadata and materialize the managed bootstrap block.
    content = set_header(content, "Plugin URI", homepage)
    content = set_header(content, "Update URI", update_uri)
    content = ensure_update_block(content, updater_prefix)

    lines, upcoming_idx, first_release_idx, previous, changes = read_changelog()
    if not changes:
        changes = git_fallback_changes()
    if not changes:
        changes = ["New revision without significant changes"]

    next_version_tuple, change_grade, ordered_changes = classify(changes, previous)
    next_version = version_string(next_version_tuple)

    content = set_header(content, "Version", next_version)
    entry.write_text(content, encoding="utf-8")

    now = dt.datetime.now().astimezone()
    date_info = now.strftime("%Y-%m-%d")
    time_info = now.strftime("%H:%M:%S")

    materialize_changelog(
        lines,
        upcoming_idx,
        first_release_idx,
        next_version,
        date_info,
        ordered_changes,
    )

    notes = "".join(f"- {c}\n" for c in ordered_changes)
    version_info = {
        "currentVersionWithSuffix": next_version,
        "releaseType": "",
        "currentVersion": next_version,
        "currentMajor": next_version_tuple[0],
        "currentMinor": next_version_tuple[1],
        "currentFix": next_version_tuple[2],
        "previousVersion": version_string(previous),
        "changeGrade": change_grade,
        "versionTimeInfo": time_info,
        "versionDateInfo": date_info,
        "versionNotes": notes,
    }
    VERSIONINFO.write_text(json.dumps(version_info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    tag = f"v{next_version}"
    asset_name = f"{slug}.zip"
    download_url = f"https://github.com/{repository}/releases/download/{tag}/{asset_name}"

    changelog_html = (
        f"<h4>Version {html.escape(next_version)}</h4><ul>"
        + "".join(f"<li>{html.escape(c)}</li>" for c in ordered_changes)
        + "</ul>"
    )

    update_data = {
        "name": plugin_name,
        "version": next_version,
        "author": author,
        "homepage": homepage,
        "download_url": download_url,
        "requires": requires_wp,
        "requires_php": requires_php,
        "tested": "",
        "sections": {
            "description": description,
            "changelog": changelog_html,
        },
    }
    UPDATE_JSON.write_text(json.dumps(update_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    zip_path = build_zip(plugin_dir, slug)
    release_notes = DIST / "release-notes.md"
    release_notes.write_text(f"# {next_version}\n\n{notes}", encoding="utf-8")

    result = {
        "entry": entry.relative_to(ROOT).as_posix(),
        "slug": slug,
        "version": next_version,
        "tag": tag,
        "asset": zip_path.relative_to(ROOT).as_posix(),
        "notes": release_notes.relative_to(ROOT).as_posix(),
    }
    (DIST / "release-result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))

if __name__ == "__main__":
    main()
