"""Build-time validation for static LuminEZE fixture compositions.

This component owns descriptors only. ESPHome package fragments create the BLE
clients and transaction scripts, while the final pass checks those bindings.
"""

import re
import hashlib

import esphome.codegen as cg
import esphome.config_validation as cv
import esphome.final_validate as fv

DEPENDENCIES = ["esp32_ble_tracker", "ble_client"]

_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]*$")
_MAC = re.compile(r"^(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")
_ROLE_BY_PRODUCT = {"jungle_dawn": "visible", "prot5": "uv"}


def _calibration_key(fixture):
    """Stable key for one identity, physical slot, product and BLE assignment."""
    assignment = "|".join(
        (
            "lumineze-fixture-calibration-v1",
            fixture["id"],
            str(fixture["slot"]),
            fixture["type"],
            fixture["mac"].upper(),
        )
    )
    return int.from_bytes(hashlib.sha256(assignment.encode()).digest()[:4], "little") or 1

_CONTEXT = cv.Schema({cv.Required("id"): cv.string_strict})
_GROUP = cv.Schema(
    {
        cv.Required("id"): cv.string_strict,
        cv.Required("context"): cv.string_strict,
        cv.Required("output"): cv.one_of("visible", "uv", lower=True),
    }
)
_FIXTURE = cv.Schema(
    {
        cv.Required("id"): cv.string_strict,
        cv.Required("slot"): cv.int_range(min=0, max=3),
        cv.Optional("enabled", default=True): cv.boolean,
        cv.Optional("type"): cv.one_of(*_ROLE_BY_PRODUCT, lower=True),
        cv.Optional("group"): cv.string_strict,
        cv.Optional("mac"): cv.string_strict,
        cv.Optional("location"): cv.string_strict,
    }
)


def _unique_identifiers(items, kind):
    seen = set()
    for index, item in enumerate(items):
        identifier = item["id"]
        path = f"lumineze_topology.{kind}[{index}].id"
        if not _IDENTIFIER.fullmatch(identifier):
            raise cv.Invalid(f"{path}: use lowercase letters, digits and underscores")
        if identifier in seen:
            raise cv.Invalid(f"{path}: duplicate identity")
        seen.add(identifier)
    return seen


def _validate_topology(config):
    if config["topology_version"] != 1:
        raise cv.Invalid("lumineze_topology.topology_version: only version 1 is supported")
    if len(config["contexts"]) not in (1, 2):
        raise cv.Invalid("lumineze_topology.contexts: expected one or two contexts")
    if len(config["groups"]) not in (1, 2, 3, 4):
        raise cv.Invalid("lumineze_topology.groups: expected one to four groups")
    if len(config["fixtures"]) not in (1, 2, 3, 4):
        raise cv.Invalid("lumineze_topology.fixtures: expected one to four declared slots")

    context_ids = _unique_identifiers(config["contexts"], "contexts")
    group_ids = _unique_identifiers(config["groups"], "groups")
    fixture_ids = _unique_identifiers(config["fixtures"], "fixtures")
    if context_ids & group_ids or context_ids & fixture_ids or group_ids & fixture_ids:
        raise cv.Invalid("lumineze_topology: context, group and fixture IDs must be distinct")
    slots = set()
    macs = set()
    calibration_keys = set()
    used_groups = set()
    enabled_count = 0
    for index, fixture in enumerate(config["fixtures"]):
        path = f"lumineze_topology.fixtures[{index}]"
        if fixture["slot"] in slots:
            raise cv.Invalid(f"{path}.slot: duplicate slot")
        slots.add(fixture["slot"])
        if not fixture["enabled"]:
            if any(key in fixture for key in ("mac", "group", "type")):
                raise cv.Invalid(f"{path}: reserved slots may contain only id, slot and location")
            continue
        enabled_count += 1
        if "type" not in fixture or "group" not in fixture or "mac" not in fixture:
            raise cv.Invalid(f"{path}: enabled fixtures require type, group and mac")
        if fixture["group"] not in group_ids:
            raise cv.Invalid(f"{path}.group: unknown group")
        used_groups.add(fixture["group"])
        group = next(group for group in config["groups"] if group["id"] == fixture["group"])
        if group["output"] != _ROLE_BY_PRODUCT[fixture["type"]]:
            raise cv.Invalid(f"{path}.group: product role does not match group output")
        mac = fixture["mac"]
        if not _MAC.fullmatch(mac):
            raise cv.Invalid(f"{path}.mac: expected a device MAC address")
        normalized = mac.upper()
        if normalized in ("00:00:00:00:00:00", "FF:FF:FF:FF:FF:FF"):
            raise cv.Invalid(f"{path}.mac: placeholder or broadcast address")
        if normalized in macs:
            raise cv.Invalid(f"{path}.mac: duplicate enabled address")
        macs.add(normalized)
        calibration_key = _calibration_key(fixture)
        if calibration_key in calibration_keys:
            raise cv.Invalid(f"{path}: calibration preference key collision")
        calibration_keys.add(calibration_key)

    if not enabled_count:
        raise cv.Invalid("lumineze_topology.fixtures: an operational build needs a fixture")
    if enabled_count > 2 and not config["allow_experimental_topology"]:
        raise cv.Invalid(
            "lumineze_topology.allow_experimental_topology: required for more than two fixtures"
        )
    if used_groups != group_ids:
        raise cv.Invalid("lumineze_topology.groups: every group needs an enabled fixture")
    used_contexts = set()
    for index, group in enumerate(config["groups"]):
        if group["context"] not in context_ids:
            raise cv.Invalid(f"lumineze_topology.groups[{index}].context: unknown context")
        used_contexts.add(group["context"])
    if used_contexts != context_ids:
        raise cv.Invalid("lumineze_topology.contexts: every context needs a group")
    return config


CONFIG_SCHEMA = cv.All(
    cv.Schema(
        {
            cv.Required("topology_version"): cv.int_,
            cv.Required("engine_family"): cv.one_of("seasonal", lower=True),
            cv.Optional("input_provider", default="real"): cv.one_of(
                "real", "development", lower=True
            ),
            cv.Optional("allow_experimental_topology", default=False): cv.boolean,
            cv.Optional("operational", default=False): cv.boolean,
            cv.Required("contexts"): cv.ensure_list(_CONTEXT),
            cv.Required("groups"): cv.ensure_list(_GROUP),
            cv.Required("fixtures"): cv.ensure_list(_FIXTURE),
        }
    ),
    _validate_topology,
)


def _final_validate(config):
    full = fv.full_config.get()
    enabled = [fixture for fixture in config["fixtures"] if fixture["enabled"]]
    clients = full.get("ble_client", [])
    expected = {f'{fixture["id"]}_client' for fixture in enabled}
    actual = {str(client["id"]) for client in clients}
    if actual != expected or len(clients) != len(expected):
        raise cv.Invalid(
            "lumineze_topology.fixtures: BLE client bindings must match enabled fixture IDs"
        )
    by_id = {str(client["id"]): client for client in clients}
    for fixture in enabled:
        client = by_id[f'{fixture["id"]}_client']
        if str(client["mac_address"]).upper() != fixture["mac"].upper():
            raise cv.Invalid(
                f'lumineze_topology.fixtures.{fixture["id"]}: BLE binding address differs from descriptor'
            )
    scripts = {str(script["id"]) for script in full.get("script", [])}
    for fixture in enabled:
        if f'{fixture["id"]}_transaction' not in scripts:
            raise cv.Invalid(
                f'lumineze_topology.fixtures.{fixture["id"]}: missing transaction binding'
            )
    if "dispatcher_tick" not in scripts:
        raise cv.Invalid("lumineze_topology: missing common dispatcher_tick")
    if "esp32_ble_tracker" not in full or "esp32_ble" not in full:
        raise cv.Invalid("lumineze_topology: one BLE radio and tracker are required")
    if full["esp32_ble"]["max_connections"] < len(enabled):
        raise cv.Invalid(
            "lumineze_topology: ESPHome requires one configured BLE connection slot per enabled client"
        )
    globals_ids = {str(item["id"]) for item in full.get("globals", [])}
    has_runtime = "topology_contexts" in globals_ids
    if has_runtime != config["operational"]:
        raise cv.Invalid(
            "lumineze_topology.operational: must match the generic controller package"
        )
    if config["operational"]:
        provider_scripts = {
            "capture_topology_real_snapshot": "real",
            "capture_topology_development_snapshot": "development",
        }
        declared_providers = {
            provider_scripts[script]
            for script in scripts
            if script in provider_scripts
        }
        if declared_providers != {config["input_provider"]}:
            raise cv.Invalid(
                "lumineze_topology.input_provider: exactly the selected snapshot provider must be included"
            )
        switches = {str(item["id"]) for item in full.get("switch", [])}
        numbers = {str(item["id"]): item for item in full.get("number", [])}
        text_sensors = {str(item["id"]) for item in full.get("text_sensor", [])}
        test_entity_ids = {
            "topology_simulation_enabled",
            "topology_simulated_output_enable",
            "topology_simulation_year",
            "topology_simulation_day",
            "topology_simulation_time",
        }
        all_ids = set()
        for key in (
            "globals", "switch", "number", "button", "sensor", "binary_sensor",
            "text_sensor", "script",
        ):
            all_ids.update(str(item["id"]) for item in full.get(key, []))
        if config["input_provider"] == "real" and all_ids & test_entity_ids:
            raise cv.Invalid(
                "lumineze_topology.input_provider: production cannot contain development simulation entities"
            )
        if config["input_provider"] == "development":
            if not test_entity_ids <= all_ids:
                raise cv.Invalid(
                    "lumineze_topology.input_provider: development simulation controls are incomplete"
                )
            for entity in (
                "topology_simulation_enabled",
                "topology_simulated_output_enable",
            ):
                switch = next(
                    item for item in full.get("switch", [])
                    if str(item["id"]) == entity
                )
                if switch.get("restore_mode") != "ALWAYS_OFF":
                    raise cv.Invalid(
                        f"lumineze_topology.input_provider.{entity}: must reset off at boot"
                    )
            for entity in (
                "topology_simulation_year",
                "topology_simulation_day",
                "topology_simulation_time",
            ):
                number = numbers[entity]
                if number["restore_value"]:
                    raise cv.Invalid(
                        f"lumineze_topology.input_provider.{entity}: simulation values must not restore"
                    )
        for group in config["groups"]:
            for suffix in ("automatic", "manual"):
                if f'{group["id"]}_{suffix}' not in switches:
                    raise cv.Invalid(
                        f'lumineze_topology.groups.{group["id"]}: missing {suffix} control'
                    )
        for context in config["contexts"]:
            if f'{context["id"]}_latitude' not in numbers:
                raise cv.Invalid(
                    f'lumineze_topology.contexts.{context["id"]}: missing seasonal context package'
                )
        for fixture in enabled:
            identity = fixture["id"]
            if f"{identity}_manual" not in switches:
                raise cv.Invalid(
                    f"lumineze_topology.fixtures.{identity}: missing manual control"
                )
            maximum = numbers.get(f"{identity}_maximum")
            default = 100.0 if fixture["type"] == "jungle_dawn" else 0.0
            if maximum is None or maximum["initial_value"] != default:
                raise cv.Invalid(
                    f"lumineze_topology.fixtures.{identity}: wrong calibrated maximum default"
                )
            if maximum["restore_value"]:
                raise cv.Invalid(
                    f"lumineze_topology.fixtures.{identity}: use assignment-bound calibration storage"
                )
            for suffix in ("dispatch_status", "readback_status"):
                if f"{identity}_{suffix}" not in text_sensors:
                    raise cv.Invalid(
                        f"lumineze_topology.fixtures.{identity}: missing transport diagnostic"
                    )
    return config


FINAL_VALIDATE_SCHEMA = _final_validate


async def to_code(config):
    """Emit only immutable routing descriptors; policy remains in YAML packages."""
    cg.add_global(cg.RawStatement("#include <cstring>"), prepend=True)
    cg.add_global(
        cg.RawStatement('#include "esphome/components/lumineze_topology/runtime_types.h"'),
        prepend=True,
    )
    cg.add_global(
        cg.RawStatement('#include "esphome/components/lumineze_topology/fixture_logic.h"'),
        prepend=True,
    )
    cg.add_global(
        cg.RawStatement('#include "esphome/components/lumineze_topology/transport_logic.h"'),
        prepend=True,
    )
    contexts = config["contexts"]
    groups = config["groups"]
    fixtures = [fixture for fixture in config["fixtures"] if fixture["enabled"]]
    context_index = {context["id"]: index for index, context in enumerate(contexts)}
    group_index = {group["id"]: index for index, group in enumerate(groups)}
    context_rows = ", ".join(f'"{context["id"]}"' for context in contexts)
    group_rows = ", ".join(
        f'{{"{group["id"]}", {context_index[group["context"]]}, '
        f'{0 if group["output"] == "visible" else 1}}}'
        for group in groups
    )
    fixture_rows = ", ".join(
        f'{{"{fixture["id"]}", {fixture["slot"]}, '
        f'{group_index[fixture["group"]]}, '
        f'0x{_calibration_key(fixture):08X}U}}'
        for fixture in fixtures
    )
    cg.add_global(
        cg.RawStatement(
            """
namespace lumineze_topology {
struct Group { const char *id; int context; int role; };
struct Fixture { const char *id; int slot; int group; uint32_t calibration_key; };
"""
            + f"constexpr Group groups[] = {{{group_rows}}};\n"
            + f"constexpr Fixture fixtures[] = {{{fixture_rows}}};\n"
            + f"constexpr const char *contexts[] = {{{context_rows}}};\n"
            + f"constexpr int group_count = {len(groups)};\n"
            + f"constexpr int fixture_count = {len(fixtures)};\n"
            + f"constexpr int context_count = {len(contexts)};\n"
            + """
inline int group_index(const char *id) {
  for (int i = 0; i < group_count; ++i)
    if (std::strcmp(groups[i].id, id) == 0) return i;
  return -1;
}
inline int context_index(const char *id) {
  for (int i = 0; i < context_count; ++i)
    if (std::strcmp(contexts[i], id) == 0) return i;
  return -1;
}
inline int fixture_slot(const char *id) {
  for (int i = 0; i < fixture_count; ++i)
    if (std::strcmp(fixtures[i].id, id) == 0) return fixtures[i].slot;
  return -1;
}
inline bool slot_enabled(int slot) {
  for (const auto &fixture : fixtures)
    if (fixture.slot == slot) return true;
  return false;
}
inline int group_for_slot(int slot) {
  for (const auto &fixture : fixtures)
    if (fixture.slot == slot) return fixture.group;
  return -1;
}
inline uint32_t calibration_key(int slot) {
  for (const auto &fixture : fixtures)
    if (fixture.slot == slot) return fixture.calibration_key;
  return 0;
}
}  // namespace lumineze_topology
"""
        )
    )
    if config["operational"]:
        cg.add_global(
            cg.RawStatement(
                """namespace lumineze_topology {
inline void (*dispatchers[4])(uint32_t) = {};
inline void (*stoppers[4])() = {};
inline void (*disconnectors[4])() = {};
inline void (*status_publishers[4])(const char *) = {};
inline void (*readback_publishers[4])(const char *) = {};
inline void (*group_off_publishers[4])() = {};
inline void (*fixture_off_publishers[4])() = {};
inline void dispatch(int slot, uint32_t token) {
  if (slot >= 0 && slot < 4 && dispatchers[slot]) dispatchers[slot](token);
}
inline void stop(int slot) {
  if (slot >= 0 && slot < 4 && stoppers[slot]) stoppers[slot]();
}
inline void disconnect(int slot) {
  if (slot >= 0 && slot < 4 && disconnectors[slot]) disconnectors[slot]();
}
inline void status(int slot, const char *message) {
  if (slot >= 0 && slot < 4 && status_publishers[slot])
    status_publishers[slot](message);
}
inline void readback_status(int slot, const char *message) {
  if (slot >= 0 && slot < 4 && readback_publishers[slot])
    readback_publishers[slot](message);
}
inline void group_controls_off(int group) {
  if (group >= 0 && group < 4 && group_off_publishers[group])
    group_off_publishers[group]();
}
inline void fixture_control_off(int slot) {
  if (slot >= 0 && slot < 4 && fixture_off_publishers[slot])
    fixture_off_publishers[slot]();
}
}  // namespace lumineze_topology
"""
            )
        )
        for fixture in fixtures:
            slot = fixture["slot"]
            identity = fixture["id"]
            for array, parameter, body in (
                ("dispatchers", "uint32_t token", f"{identity}_transaction->execute(token)"),
                ("stoppers", "", f"{identity}_transaction->stop()"),
                ("disconnectors", "", f"{identity}_client->disconnect()"),
                (
                    "status_publishers",
                    "const char *message",
                    f"{identity}_dispatch_status->publish_state(message)",
                ),
                (
                    "readback_publishers",
                    "const char *message",
                    f"{identity}_readback_status->publish_state(message)",
                ),
                (
                    "fixture_off_publishers",
                    "",
                    f"{identity}_manual->publish_state(false)",
                ),
            ):
                cg.add(
                    cg.RawStatement(
                        f"lumineze_topology::{array}[{slot}] = "
                        f"[]({parameter}) {{ {body}; }};"
                    )
                )
        for index, group in enumerate(groups):
            identity = group["id"]
            cg.add(
                cg.RawStatement(
                    f"lumineze_topology::group_off_publishers[{index}] = []() {{ "
                    f"{identity}_automatic->publish_state(false); "
                    f"{identity}_manual->publish_state(false); }};"
                )
            )
