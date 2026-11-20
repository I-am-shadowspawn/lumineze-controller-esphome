"""Validate public remote wrappers with synthetic secrets in an empty directory."""

import argparse
import base64
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from build_profile import compile_retry


ROOT = Path(__file__).resolve().parents[1]
PROFILES = ("seasonal-production", "seasonal-development", "schedule-production", "schedule-development")
SECRETS = """wifi_ssid: ci-network
wifi_password: ci-password
my_vivarium_prot5_mac: AA:BB:CC:DD:EE:02
my_vivarium_jungle_dawn_mac: AA:BB:CC:DD:EE:01
my_vivarium_encryption_key: {key}
""".format(key=base64.b64encode(bytes(range(32))).decode())


def check_source(profile: str, source: str, expected_ref: str | None) -> str:
    refs = re.findall(r"(?m)^\s*controller_ref: ([0-9a-f]{40})$", source)
    assert len(refs) == 1, f"{profile}: expected one full immutable controller_ref"
    revision = refs[0]
    if expected_ref:
        assert revision == expected_ref, f"{profile}: unexpected revision {revision}"
    assert source.count("ref: ${controller_ref}") == 2, f"{profile}: package/component pin mismatch"
    assert f"packages/{profile}.yaml" in source, f"{profile}: wrong profile package"
    assert f"engine_family: {profile.split('-')[0]}" in source
    assert "fixture_default_maximum: 0" in source, f"{profile}: ProT5 must start at zero"
    return revision


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--esphome", default="esphome")
    parser.add_argument("--compile", action="store_true")
    parser.add_argument("--ref", help="expected pinned full SHA")
    args = parser.parse_args()
    refs = set()
    for profile in PROFILES:
        source = (ROOT / "example" / f"{profile}.yaml").read_text()
        refs.add(check_source(profile, source, args.ref))
        with tempfile.TemporaryDirectory(prefix=f"lumineze-example-{profile}-") as tmp:
            directory = Path(tmp)
            config = directory / "controller.yaml"
            shutil.copyfile(ROOT / "example" / f"{profile}.yaml", config)
            (directory / "secrets.yaml").write_text(SECRETS)
            assert not (directory / "packages").exists() and not (directory / "components").exists()
            result = subprocess.run([args.esphome, "config", str(config)], cwd=directory,
                                    capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError(f"{profile} config failed:\n{(result.stdout + result.stderr)[-4000:]}")
            print(f"PASS public {profile} config at {next(iter(refs))}", flush=True)
            if args.compile:
                compile_retry([args.esphome, "compile", str(config)], directory / "logs", cwd=directory)
                print(f"PASS public {profile} compile at {next(iter(refs))}", flush=True)
    assert len(refs) == 1, f"public examples use different revisions: {refs}"


if __name__ == "__main__":
    main()
