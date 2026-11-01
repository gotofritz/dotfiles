#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.15"
# dependencies = []
# ///

"""Generate memorable, path-derived directory aliases from Bash history."""

import argparse
import itertools
import os
import re
import shlex
import string
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

HOME = Path.home()
OUTPUT = HOME / ".folder_aliases"
MAX_ALIAS_SUFFIX = 5
MIN_VISITS = 2  # directories visited fewer times get no alias

HISTORY = HOME / ".bash_history"
NAV_COMMANDS = frozenset({"cd", "pushd", "popd"})
RESERVED_SUFFIXES = frozenset({"h", "help"})

BASH_TIMESTAMP = re.compile(r"^#\d+$")
ALIAS_LINE = re.compile(r"^\s*alias\s+(go\w+)=(.*)$")


@dataclass
class Shell:
    """Minimal model of a shell's directory state (cwd, `cd -`, dir stack)."""

    cwd: str = str(HOME)
    previous: str = str(HOME)
    stack: list[str] = field(default_factory=list)

    def resolve(self, path: str) -> str:
        path = os.path.expanduser(path)
        if not os.path.isabs(path):
            path = os.path.join(self.cwd, path)
        return os.path.normpath(path)

    def navigate(self, tokens: list[str]) -> str | None:
        """Apply a cd/pushd/popd command; return the new cwd, or None if unchanged."""
        cmd, *args = tokens

        match cmd:
            case "cd":
                args = [a for a in args if a not in ("-L", "-P")]
                if args and args[0] == "--":
                    args.pop(0)

                if not args:
                    dest = str(HOME)
                elif args[0] == "-":
                    dest = self.previous
                else:
                    dest = self.resolve(args[0])
            case "pushd" if args:
                dest = self.resolve(args[-1])
                self.stack.append(self.cwd)
            case "pushd" | "popd":
                if not self.stack:
                    return None
                dest = self.stack.pop()
                if cmd == "pushd":
                    self.stack.append(self.cwd)
            case _:
                return None

        self.previous, self.cwd = self.cwd, dest
        return self.cwd


def read_history(path: Path) -> list[str]:
    try:
        lines = path.read_text(errors="replace").splitlines()
    except OSError:
        return []

    result = []
    for line in lines:
        if line.strip() and not BASH_TIMESTAMP.match(line):
            result.append(line)
    return result


def split_commands(line: str) -> list[list[str]]:
    """Split common command separators, respecting shell quoting."""
    try:
        lexer = shlex.shlex(line, posix=True, punctuation_chars=";&|")
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        return []

    commands: list[list[str]] = []
    part: list[str] = []
    for token in tokens:
        if token and all(c in ";&|" for c in token):
            if part:
                commands.append(part)
                part = []
        else:
            part.append(token)
    if part:
        commands.append(part)
    return commands


def count_visits(history: Path) -> Counter[str]:
    """Count directories that were actually used, not just passed through."""
    visits: Counter[str] = Counter()
    shell = Shell()
    pending: str | None = None

    def flush() -> None:
        nonlocal pending
        if pending is not None and Path(pending).is_dir():
            visits[pending] += 1
        pending = None

    for line in read_history(history):
        for command in split_commands(line):
            if command[0] in NAV_COMMANDS and (dest := shell.navigate(command)):
                pending = dest
            else:
                flush()
    flush()
    return visits


def path_components(path: str) -> list[str]:
    """Prefer names relative to home; otherwise use absolute path parts."""
    p = Path(path)
    try:
        parts = p.relative_to(HOME).parts
    except ValueError:
        parts = tuple(part for part in p.parts if part not in ("/", "\\"))

    return [
        "".join(c for c in part.lower() if c in string.ascii_lowercase)
        for part in parts
        if part not in ("", ".", "..")
    ]


def candidates(path: str) -> list[str]:
    """Build candidate suffixes from prefixes of path components."""
    parts = path_components(path)
    found: set[str] = set()

    # Consider combinations of components, preserving their path order.
    for count in range(1, min(len(parts), MAX_ALIAS_SUFFIX) + 1):
        # At least one letter per chosen component.
        remaining = MAX_ALIAS_SUFFIX - count

        for chosen in itertools.combinations(parts, count):
            if not all(chosen):
                continue

            ranges = [range(1, min(len(part), remaining + 1) + 1) for part in chosen]

            for lengths in itertools.product(*ranges):
                if sum(lengths) > MAX_ALIAS_SUFFIX:
                    continue

                suffix = "".join(
                    part[:length] for part, length in zip(chosen, lengths, strict=True)
                )

                # Avoid reserved aliases and non-useful names.
                if suffix and suffix not in RESERVED_SUFFIXES:
                    found.add(suffix)

    # Short names first, then alphabetical.
    return sorted(found, key=lambda s: (len(s), s))


def existing_aliases() -> dict[str, str]:
    """Return existing directory -> alias mappings."""
    mappings: dict[str, str] = {}

    if not OUTPUT.is_file():
        return mappings

    for line in OUTPUT.read_text(errors="replace").splitlines():
        if not (match := ALIAS_LINE.match(line)):
            continue

        name, rhs = match.groups()
        try:
            outer = shlex.split(rhs, comments=True)
            if len(outer) != 1:
                continue
            command = shlex.split(outer[0])
        except ValueError:
            continue

        if len(command) == 3 and command[:2] == ["cd", "--"]:
            path = command[2]
            if path == "$HOME":
                continue
            path = os.path.normpath(os.path.abspath(path))
            mappings[path] = name

    return mappings


def iter_ranked(visits: Counter[str], skip: set[str]) -> Iterator[tuple[str, int]]:
    """Yield unaliased visited directories, most visited first."""
    unaliased = (
        (path, count)
        for path, count in visits.items()
        if path != str(HOME) and path not in skip
    )
    yield from sorted(unaliased, key=lambda item: (-item[1], item[0]))


def assign_aliases(
    existing: dict[str, str], ranked: list[tuple[str, int]], min_visits: int
) -> dict[str, str]:
    """Assign alias names to newly discovered directories with enough visits."""
    # Reserve every previously assigned name, including aliases for
    # directories that weren't visited in the current history.
    reserved = {"goh", "gohelp", *existing.values()}
    new: dict[str, str] = {}

    for path, count in ranked:
        if count < min_visits:
            continue

        name = next(
            (
                f"go{suffix}"
                for suffix in candidates(path)
                if f"go{suffix}" not in reserved
            ),
            None,
        )
        if name is not None:
            reserved.add(name)
            new[path] = name

    return new


def print_report(
    existing: dict[str, str],
    new: dict[str, str],
    ranked: list[tuple[str, int]],
    visits: Counter[str],
    min_visits: int,
) -> None:
    rows = [("kept", name, visits[path], path) for path, name in existing.items()]
    for path, count in ranked:
        if name := new.get(path):
            rows.append(("new", name, count, path))
        elif count < min_visits:
            rows.append(("skipped", "-", count, path))
        else:
            rows.append(("no-alias", "-", count, path))

    width = max((len(name) for _, name, _, _ in rows), default=0)
    for status, name, count, path in sorted(rows, key=lambda r: (-r[2], r[3])):
        print(f"{status:<9}{name:<{width}}  {count:>4} visits  {path}")


# gohelp [pattern]: with no pattern, print every alias below the function;
# with a pattern, print only aliases whose target path contains it (ignoring case).
GOHELP = r"""gohelp() {
    awk -v p="${1:-}" '
        found && (p == "" || index(tolower(substr($0, index($0, "cd -- "))), tolower(p)))
        /^}$/ { found = 1 }
    ' "$HOME/.folder_aliases" | grep -v '^$'
}"""


def alias_line(name: str, path: str) -> str:
    command = shlex.quote(f"cd -- {shlex.quote(path)}")
    return f"alias {name}={command}"


def write_aliases(new: dict[str, str], existing: dict[str, str]) -> None:
    out = [
        "# Generated automatically by gen_folder_aliases.py",
        "# Existing directory aliases are kept stable.",
        "",
        GOHELP,
        "",
        "alias goh='cd -- \"$HOME\"'",
        "",
    ]

    # Existing aliases keep their names; lines are rewritten without old comments.
    out.extend(alias_line(name, path) for path, name in existing.items())
    if existing:
        out.append("")

    # Add aliases only for newly discovered directories.
    out.extend(alias_line(name, path) for path, name in new.items())
    out.append("")
    OUTPUT.write_text("\n".join(out))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--min",
        dest="min_visits",
        type=int,
        default=MIN_VISITS,
        help="minimum visits before a directory gets an alias (default: %(default)s)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=f"only print the report; do not write {OUTPUT}",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not HISTORY.is_file():
        print(f"No Bash history file found at {HISTORY}.")
        return

    visits = count_visits(HISTORY)
    existing = existing_aliases()
    ranked = list(iter_ranked(visits, skip=set(existing)))
    new = assign_aliases(existing, ranked, args.min_visits)

    print_report(existing, new, ranked, visits, args.min_visits)

    if not args.dry_run:
        write_aliases(new, existing)
        print(f"\nWrote {OUTPUT} ({len(existing)} kept, {len(new)} new)")


if __name__ == "__main__":
    main()
