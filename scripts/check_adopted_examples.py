"""Validate adopted public wrappers and the adoption entry point contract.

Default mode is network-free: static contract checks plus an end-to-end config
resolved from the working tree through a temporary git commit. ``--remote``
repeats the end-to-end step against the pinned GitHub SHAs, which requires the
pinned revisions to already exist upstream (post-push release rehearsal).

Static contract enforced for each adopted example:
- exactly one full immutable ``controller_ref`` pin,
- all three remote pins (adopt package, profile package, helper component)
  reference that revision,
- the wrapper resolves through ``adopt/lumineze.yaml`` plus one production
  profile package rather than a full-config import,
- credentials come only from ``!secret``,
- ProT5 starts at zero and engine family matches the profile.

The adopted examples must also share one revision with the four classic public
wrappers so release promotion bumps every wrapper together.
"""
import argparse
import base64
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from build_profile import compile_retry

ROOT = Path(__file__).resolve().parents[1]
URL = "https://github.com/I-am-shadowspawn/lumineze-controller-esphome"
EXAMPLES = ("adopted-seasonal-production", "adopted-schedule-production")
CLASSIC_EXAMPLES = ("seasonal-production", "seasonal-development",
                    "schedule-production", "schedule-development")
ADOPT_ENTRY = "adopt/lumineze.yaml"
SECRETS = """wifi_ssid: ci-network
wifi_password: ci-password
my_vivarium_prot5_mac: AA:BB:CC:DD:EE:02
my_vivarium_jungle_dawn_mac: AA:BB:CC:DD:EE:01
my_vivarium_encryption_key: {key}
""".format(key=base64.b64encode(bytes(range(32))).decode())


def check_source(profile: str, source: str) -> str:
    refs = re.findall(r"(?m)^\s*controller_ref: ([0-9a-f]{40})$", source)
    assert len(refs) == 1, f"{profile}: expected one full immutable controller_ref"
    revision = refs[0]
    pins = source.count("ref: ${controller_ref}")
    assert pins == 3, f"{profile}: expected three ${'{controller_ref}'} pins, found {pins}"
    assert ADOPT_ENTRY in source, f"{profile}: wrapper must resolve the adoption entry point"
    core = profile.removeprefix("adopted-")
    assert f"packages/{core}.yaml" in source, f"{profile}: profile package missing"
    engine = core.removesuffix("-production").removesuffix("-development")
    assert f"engine_family: {engine}" in source, f"{profile}: engine family mismatch"
    assert "fixture_default_maximum: 0" in source, f"{profile}: ProT5 must start at zero"
    assert "import_full_config: true" not in source, f"{profile}: full-config import rejected"
    assert "ssid: !secret" in source and "password: !secret" in source, f"{profile}: Wi-Fi must come from secrets"
    assert "key: !secret" in source, f"{profile}: API key must come from secrets"
    assert "ci-network" not in source and "AA:BB:CC:DD" not in source, f"{profile}: live credentials or placeholder MACs must stay in secrets"
    return revision


def working_tree_commit() -> str:
    """Create a throwaway commit capturing the uncommitted working tree."""
    # The index path must not pre-exist: git rejects an empty (0-byte) index
    # file, so hand out a fresh nonexistent path instead of a tempfile.
    scratch = Path(tempfile.mkdtemp(prefix="lumineze-index-"))
    index = str(scratch / "index")
    env = {**os.environ, "GIT_INDEX_FILE": index}
    subprocess.run(["git", "add", "-A"], cwd=ROOT, env=env, check=True, capture_output=True)
    tree = subprocess.run(["git", "write-tree"], cwd=ROOT, env=env, check=True,
                          capture_output=True, text=True).stdout.strip()
    commit = subprocess.run(
        ["git", "commit-tree", tree, "-p", "HEAD", "-m", "adopted example validation"],
        cwd=ROOT, env={**env, "GIT_AUTHOR_NAME": "ci", "GIT_AUTHOR_EMAIL": "ci@localhost",
                       "GIT_COMMITTER_NAME": "ci", "GIT_COMMITTER_EMAIL": "ci@localhost"},
        check=True, capture_output=True, text=True).stdout.strip()
    assert re.fullmatch("[0-9a-f]{40}", commit), "working tree commit missing"
    return commit


def run_config(profile: str, config: Path, esphome: str, directory: Path, compile: bool) -> None:
    (directory / "secrets.yaml").write_text(SECRETS)
    assert not (directory / "packages").exists() and not (directory / "components").exists()
    result = subprocess.run([esphome, "config", str(config)], cwd=directory,
                            capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"{profile} config failed:\n{(result.stdout + result.stderr)[-4000:]}")
    print(f"PASS adopted {profile} config at {next(iter(_refs))}", flush=True)
    if compile:
        compile_retry([esphome, "compile", str(config)], directory / "logs", cwd=directory)
        print(f"PASS adopted {profile} compile at {next(iter(_refs))}", flush=True)


_refs: set[str] = set()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--esphome", default="esphome")
    parser.add_argument("--compile", action="store_true")
    parser.add_argument("--remote", action="store_true",
                        help="fetch the pinned GitHub SHAs instead of the working tree")
    parser.add_argument("--ref", help="expected pinned full SHA")
    args = parser.parse_args()
    # Bare names (no directory separator) are PATH lookups and must stay
    # unresolved; only relative filesystem paths are anchored at ROOT.
    esphome = Path(args.esphome)
    if not esphome.is_absolute() and os.sep in args.esphome:
        esphome = ROOT / esphome
    args.esphome = str(esphome)

    sources: dict[str, str] = {}
    for profile in EXAMPLES:
        sources[profile] = (ROOT / "example" / f"{profile}.yaml").read_text()
        _refs.add(check_source(profile, sources[profile]))
    bootstrap = (ROOT / "example" / "bootstrap.yaml").read_text()
    bootstrap_pins = re.findall(r"github://[^\s]+@([0-9a-f]{40})\s*$", bootstrap, re.M)
    assert len(bootstrap_pins) == 1, "bootstrap example must pin one immutable SHA"
    _refs.add(bootstrap_pins[0])
    for profile in CLASSIC_EXAMPLES:
        classic = (ROOT / "example" / f"{profile}.yaml").read_text()
        refs = re.findall(r"(?m)^\s*controller_ref: ([0-9a-f]{40})$", classic)
        assert len(refs) == 1, f"{profile}: classic wrapper pin missing"
        _refs.add(refs[0])
    assert len(_refs) == 1, f"public wrappers drift across revisions: {sorted(_refs)}"
    revision = next(iter(_refs))
    if args.ref:
        assert revision == args.ref, f"{revision} does not match expected {args.ref}"

    local_root = str(ROOT)
    local_revision = working_tree_commit() if not args.remote else revision
    for profile in EXAMPLES:
        with tempfile.TemporaryDirectory(prefix=f"lumineze-adopted-{profile}-") as tmp:
            directory = Path(tmp)
            config = directory / "controller.yaml"
            if args.remote:
                shutil.copyfile(ROOT / "example" / f"{profile}.yaml", config)
            else:
                # Resolve against the working tree so pre-push changes are
                # exercisable end to end without touching the pinned SHAs.
                # Package URLs require a scheme; file:// points at this
                # checkout while the temporary commit carries its content.
                config.write_text(sources[profile]
                                  .replace(URL, f"file://{local_root}")
                                  .replace("${controller_ref}", local_revision))
            run_config(profile, config, args.esphome, directory, args.compile)
    if args.remote:
        print(f"PASS remote adopted wrappers at {revision}", flush=True)
    else:
        print(f"PASS adopted wrappers resolved from working tree at {local_revision}", flush=True)


if __name__ == "__main__":
    main()
