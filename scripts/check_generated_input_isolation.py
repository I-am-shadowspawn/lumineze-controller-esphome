"""Inspect compiled C++ to ensure development providers stay profile-local."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "ci/.esphome/build"
PRODUCTION = {
    "legacy": BUILD / "lumineze-ci/src/main.cpp",
    "topology": BUILD / "topology-visible-sparse/src/main.cpp",
}
DEVELOPMENT = {
    "legacy": BUILD / "lumineze-development-ci/src/main.cpp",
    "topology": BUILD / "topology-development-input/src/main.cpp",
}
FORBIDDEN = {
    "legacy": (
        "solar_test_mode",
        "solar_test_year",
        "solar_test_calendar_day",
        "solar_test_time_minutes",
        "solar_simulated_output_enable",
        "capture_development_evaluation_snapshot",
    ),
    "topology": (
        "topology_simulation_enabled",
        "topology_simulated_output_enable",
        "topology_simulation_year",
        "topology_simulation_day",
        "topology_simulation_time",
        "capture_topology_development_snapshot",
    ),
}
EXPECTED = {
    "legacy": ("solar_test_mode", "solar_simulated_output_enable"),
    "topology": ("topology_simulation_enabled",
                 "topology_simulated_output_enable"),
}


def main():
    for profile, path in PRODUCTION.items():
        if not path.is_file():
            raise AssertionError(f"missing compiled production source: {path}")
        source = path.read_text()
        for symbol in FORBIDDEN[profile]:
            if symbol in source:
                raise AssertionError(
                    f"production {profile} source contains development symbol {symbol}"
                )
        print(f"PASS compiled production {profile} excludes development symbols")
    for profile, path in DEVELOPMENT.items():
        if not path.is_file():
            raise AssertionError(f"missing compiled development source: {path}")
        source = path.read_text()
        for symbol in EXPECTED[profile]:
            if symbol not in source:
                raise AssertionError(
                    f"development {profile} source is missing {symbol}"
                )
        print(f"PASS compiled development {profile} contains simulation controls")


if __name__ == "__main__":
    main()
