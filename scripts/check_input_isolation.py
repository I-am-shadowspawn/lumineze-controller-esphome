"""Verify production and development input controls are composed separately."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_CONFIGS = ("ci/controller.yaml", "ci/topology-generic.yaml")
DEVELOPMENT_CONFIGS = (
    "ci/controller-development.yaml",
)
DEVELOPMENT_IDS = (
    "solar_test_mode",
    "solar_simulated_output_enable",
    "solar_test_year",
    "solar_test_calendar_day",
    "solar_test_time_minutes",
)


def config_output(command, path):
    result = subprocess.run(
        [*command, "config", path],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout + result.stderr
    if result.returncode:
        raise AssertionError(f"{path} failed configuration:\n{output[-2500:]}")
    return output


def main():
    command = sys.argv[1:]
    if not command:
        raise SystemExit("pass an ESPHome command")
    for path in PRODUCTION_CONFIGS:
        output = config_output(command, path)
        for identifier in DEVELOPMENT_IDS:
            if identifier in output:
                raise AssertionError(
                    f"{path} contains development entity {identifier}"
                )
        print(f"PASS {path} excludes development controls")
    for path in DEVELOPMENT_CONFIGS:
        output = config_output(command, path)
        for identifier in DEVELOPMENT_IDS:
            if identifier not in output:
                raise AssertionError(
                    f"{path} is missing development entity {identifier}"
                )
        if "restore_mode: ALWAYS_OFF" not in output:
            raise AssertionError(f"{path} does not reset simulation switches off")
        print(f"PASS {path} includes non-restoring development controls")


if __name__ == "__main__":
    main()
