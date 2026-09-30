"""Check that operational and verbose entities stay in their intended builds."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "ci/.esphome/build"
PROFILES = {
    "legacy production": BUILD / "lumineze-ci/src/main.cpp",
    "legacy development": BUILD / "lumineze-development-ci/src/main.cpp",
    "topology production": BUILD / "lumineze-generic-ci/src/main.cpp",
    "topology development": BUILD / "lumineze-generic-development-ci/src/main.cpp",
}


def source(profile):
    path = PROFILES[profile]
    if not path.is_file():
        raise AssertionError(f"missing compiled {profile} source: {path}")
    return path.read_text()


def require(text, profile, entity):
    if entity not in text:
        raise AssertionError(f"{profile} is missing expected entity: {entity}")


def forbid(text, profile, entity):
    if entity in text:
        raise AssertionError(f"{profile} unexpectedly contains entity: {entity}")


def main():
    legacy_prod = source("legacy production")
    legacy_dev = source("legacy development")
    topology_prod = source("topology production")
    topology_dev = source("topology development")

    for entity in (
        "Controller Time Valid",
        "JungleDawn BLE Connected",
        "JungleDawn Readback Mismatch",
        "JungleDawn Last Completed Level",
        "JungleDawn Failed Transactions",
    ):
        require(legacy_prod, "legacy production", entity)
        require(legacy_dev, "legacy development", entity)
    for entity in (
        "Solar Declination",
        "JungleDawn Calculated Target",
        "ProT5 Window Envelope",
        "Simulated Sun Above Horizon",
    ):
        forbid(legacy_prod, "legacy production", entity)
        require(legacy_dev, "legacy development", entity)

    for entity in (
        "Controller Time Valid",
        "Fixture A BLE Connected",
        "Fixture A Readback Mismatch",
        "Fixture A Requested Level",
        "Fixture A Lamp Reported Level",
        "Fixture A Failed Transactions",
    ):
        require(topology_prod, "topology production", entity)
        require(topology_dev, "topology development", entity)
    forbid(topology_prod, "topology production", "Fixture A Automatic Preview")
    require(topology_dev, "topology development", "Fixture A Automatic Preview")
    print("PASS compiled diagnostic profile inventories")


if __name__ == "__main__":
    main()
