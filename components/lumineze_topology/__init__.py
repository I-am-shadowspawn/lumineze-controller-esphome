"""Build-time validation for static LuminEZE fixture compositions.

This component owns descriptors only. ESPHome package fragments create the BLE
clients and transaction scripts, while the final pass checks those bindings.
"""

import re

import esphome.config_validation as cv
import esphome.final_validate as fv

DEPENDENCIES = ["esp32_ble_tracker", "ble_client"]

_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]*$")
_MAC = re.compile(r"^(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")
_ROLE_BY_PRODUCT = {"jungle_dawn": "visible", "prot5": "uv"}

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
    _unique_identifiers(config["fixtures"], "fixtures")
    slots = set()
    macs = set()
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
            cv.Optional("allow_experimental_topology", default=False): cv.boolean,
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
    return config


FINAL_VALIDATE_SCHEMA = _final_validate


async def to_code(config):
    """Static descriptors are consumed by package fragments, not runtime code."""
