#!/usr/bin/env python3
"""Check a release's GPL/LGPL source is published, and write its notes.

    verify_release.py <version> <dir with the release files>
    verify_release.py --notes <version> <dir with the release files>

The packages bundle Deskflow (GPL-2.0) and, in the Flatpak, a patched
libportal (LGPL-3.0). Their complete source must be available from
junrobo/synapshare-oss, release synapshare-v<version>: the Flatpak's pinned
revisions, and the Deskflow commit of every official binary a Windows or
macOS package bundles (from the deskflow-manifest-<platform>.json files the
build jobs attached). Exits non-zero, naming what is missing, otherwise.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List, Set, Tuple

OSS_REPO = "junrobo/synapshare-oss"
RELEASES_REPO = "junrobo/synapshare-releases"


def main(argv: List[str]) -> int:
    notes = bool(argv) and argv[0] == "--notes"
    if notes:
        argv = argv[1:]
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    version, directory = argv[0], Path(argv[1])

    oss_tag = "synapshare-v%s" % version
    assets = oss_release_assets(oss_tag)
    manifests = deskflow_manifests(directory)
    problems = missing_sources(assets, manifests, has_flatpak(directory))
    if assets is None:
        problems.insert(0, "%s has no release %s" % (OSS_REPO, oss_tag))
    if problems:
        for problem in problems:
            print("::error::%s" % problem, file=sys.stderr)
        print(
            "Run scripts/make_source_release.sh %s <commit...> in synapshare-oss and "
            "upload the archives to its release %s, then publish again." % (version, oss_tag),
            file=sys.stderr,
        )
        return 1

    if notes:
        sys.stdout.write(release_notes(version, oss_tag, manifests))
    else:
        print("GPL/LGPL sources for %s are published in %s %s" % (version, OSS_REPO, oss_tag))
    return 0


def oss_release_assets(tag: str):
    url = "https://api.github.com/repos/%s/releases/tags/%s" % (OSS_REPO, tag)
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "synapshare-release"}
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer %s" % token
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
            release = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise
    if release.get("draft"):
        return None
    return {asset["name"] for asset in release.get("assets", [])}


def deskflow_manifests(directory: Path) -> Dict[str, Tuple[str, str]]:
    """platform -> (Deskflow release, commit) for every bundled official binary."""
    manifests = {}
    for path in sorted(directory.glob("deskflow-manifest-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        platform = path.stem[len("deskflow-manifest-"):]
        manifests[platform] = (str(data.get("release", "")), str(data.get("commit", "")).lower())
    return manifests


def has_flatpak(directory: Path) -> bool:
    return any(directory.glob("*.flatpak"))


def missing_sources(assets, manifests: Dict[str, Tuple[str, str]], flatpak: bool) -> List[str]:
    names: Set[str] = assets or set()
    problems = []
    for platform, (release, commit) in manifests.items():
        if len(commit) < 12:
            problems.append(
                "The %s package's Deskflow build (%s) has no recorded commit; rebuild it "
                "so fetch_deskflow.py can record one" % (platform, release or "unknown release")
            )
            continue
        archive = "deskflow-%s-src.tar.gz" % commit[:12]
        if archive not in names:
            problems.append("%s is missing %s (Deskflow bundled by %s)" % (OSS_REPO, archive, platform))
    if flatpak:
        for prefix in ("deskflow-", "libportal-"):
            if not any(n.startswith(prefix) and n.endswith("-src.tar.gz") for n in names):
                problems.append("%s is missing the %s source archive the Flatpak is built from" % (OSS_REPO, prefix.rstrip("-")))
    return problems


def release_notes(version: str, oss_tag: str, manifests: Dict[str, Tuple[str, str]]) -> str:
    lines = [
        "SynapShare %s for Windows, macOS, Linux (Flatpak) and Android." % version,
        "",
        "### Verify your download",
        "",
        "- Checksums: `SHA256SUMS` (`sha256sum -c SHA256SUMS --ignore-missing`)",
        "- Build provenance: `gh attestation verify <file> -R %s`" % RELEASES_REPO,
        "",
        "### Open-source components",
        "",
        "SynapShare is proprietary software distributed with open-source components; "
        "see `THIRD_PARTY_NOTICES.md` in each package. The complete corresponding "
        "source of its GPL/LGPL components is at "
        "https://github.com/%s/releases/tag/%s." % (OSS_REPO, oss_tag),
    ]
    if manifests:
        lines += ["", "Deskflow bundled by the binary packages:", ""]
        for platform, (release, commit) in manifests.items():
            lines.append("- %s: `%s` (Deskflow release %s)" % (platform, commit[:12], release))
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
