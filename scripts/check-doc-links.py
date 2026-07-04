#!/usr/bin/env python3
"""Repo-wide broken-relative-link sweep for tracked markdown.

Walks every `git ls-files '*.md'`, resolves each non-external markdown link
relative to its file, and prints unresolved targets. Exit 1 if any are broken.
Shared across epic #211 children (#215/#214/#212/#213).
"""
import os, re, subprocess, sys

root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).decode().strip()
os.chdir(root)
files = subprocess.check_output(["git", "ls-files", "*.md"]).decode().split()
link_re = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
broken = []
for f in files:
    d = os.path.dirname(f)
    try:
        txt = open(f, encoding="utf-8").read()
    except OSError:
        continue
    for m in link_re.finditer(txt):
        tgt = m.group(1).strip()
        if tgt.startswith(("http://", "https://", "mailto:", "#", "tel:")):
            continue
        path = tgt.split("#", 1)[0].split("?", 1)[0].strip()
        if not path:
            continue
        if not os.path.exists(os.path.normpath(os.path.join(d, path))):
            broken.append((f, tgt))
print(f"BROKEN RELATIVE LINKS: {len(broken)}")
for f, tgt in broken:
    print(f"  {f} -> {tgt}")
sys.exit(1 if broken else 0)
