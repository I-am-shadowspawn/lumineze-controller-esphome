import test from "node:test";
import assert from "node:assert/strict";
import {
  calibrationPoints, generateDashboard, historySeries, resolveRoles,
} from "../src/lumineze-dashboard.js";

const role = (device, original, entity) => ({
  device_id: device, original_name: original, entity_id: entity,
});
const entries = [
  role("one", "JungleDawn Requested Level", "sensor.first_renamed_request"),
  role("one", "JungleDawn Lamp-Reported Level", "sensor.first_renamed_report"),
  role("one", "Visible Automatic Control", "switch.first_visible"),
  role("one", "JungleDawn Fixed Level", "number.first_fixed"),
  role("two", "JungleDawn Requested Level", "sensor.second_request"),
  role("two", "JungleDawn Lamp-Reported Level", "sensor.second_report"),
  role("two", "Visible Automatic Control", "switch.second_visible"),
  role("two", "JungleDawn Fixed Level", "number.second_fixed"),
];
const hass = {
  devices: { one: { id: "one", name: "Vivarium A" }, two: { id: "two", name: "Vivarium B" } },
  states: {
    "sensor.meter_a": { attributes: { unit_of_measurement: "lx", friendly_name: "Meter A" } },
    "sensor.meter_b": { attributes: { unit_of_measurement: "lx", friendly_name: "Meter B" } },
    "sensor.uv_a": { attributes: { friendly_name: "UV Index" } },
    "sensor.other": { attributes: { unit_of_measurement: "%" } },
  },
};

test("entity resolution is device scoped and survives entity ID renaming", () => {
  assert.equal(resolveRoles(entries, "one").jungledawn_requested_level,
    "sensor.first_renamed_request");
  assert.equal(resolveRoles(entries, "two").jungledawn_requested_level,
    "sensor.second_request");
  assert.equal(resolveRoles(entries, "absent").jungledawn_requested_level, undefined);
});

test("two generated dashboards never refer to each other's controller entities", () => {
  for (const [selected, other] of [["one", "second"], ["two", "first"]]) {
    const config = generateDashboard({ controller_device_id: selected,
      lux_entities: ["sensor.meter_a", "sensor.meter_b"], uv_index_entity: "sensor.uv_a" }, hass, entries);
    const rendered = JSON.stringify(config);
    assert.match(rendered, new RegExp(selected === "one" ? "first_renamed_report" : "second_report"));
    assert.doesNotMatch(rendered, new RegExp(`${other}_(request|report|visible|fixed)`));
    assert.equal(config.views.length, 5);
    const chart = config.views[2].cards.find((card) => card.mode === "scatter");
    assert.deepEqual(chart.meters.map((meter) => meter.entity), ["sensor.meter_a", "sensor.meter_b"]);
  }
});

test("meter selection is optional, unique, and validates lux units", () => {
  const bare = generateDashboard({ controller_device_id: "one" }, hass, entries);
  assert.equal(bare.views.length, 4);
  const metered = generateDashboard({ controller_device_id: "one",
    lux_entities: ["sensor.meter_a", "sensor.meter_a", "sensor.other"] }, hass, entries);
  assert.equal(metered.views.length, 5);
  assert.deepEqual(metered.views[2].cards.find((card) => card.mode === "time")
    .meters.map((meter) => meter.entity), ["sensor.meter_a"]);
  const missing = generateDashboard({ controller_device_id: "missing" }, hass, entries);
  assert.equal(missing.views.length, 1);
  assert.doesNotMatch(JSON.stringify(missing), /first_|second_/);
});

test("history parser and calibration use stable reported level and per-meter ambient", () => {
  const minute = 60000;
  const reported = [0, 0, 0, 0, 50, 50, 50, 50, 100, 100, 100, 100]
    .map((value, index) => ({ time: index * minute, value }));
  const lux = [20, 20, 21, 22, 80, 85, 90, 92, 140, 150, 160, 165]
    .map((value, index) => ({ time: index * minute, value }));
  const result = calibrationPoints(reported, lux, 0, 11 * minute);
  assert.equal(result.baseline, 21.5);
  assert.deepEqual(result.curve.map((point) => point.pct), [0, 50, 100]);
  assert.deepEqual(result.curve.map((point) => point.count), [2, 2, 2]);
  assert.equal(result.curve[1].lx, 91);
  assert.equal(result.curve[1].delta, 69.5);
  const noZero = calibrationPoints(reported.slice(4), lux.slice(4), 4 * minute, 11 * minute);
  assert.equal(noZero.baseline, null);
  assert.equal(noZero.curve[0].delta, null);
  assert.deepEqual(historySeries({ lamp: [{ s: "45", lu: 12 }, { s: "unavailable", lu: 13 }] }, "lamp"),
    [{ time: 12000, value: 45 }]);
});

test("browser module registers a dashboard strategy, editor, and chart", async () => {
  const previous = {
    window: globalThis.window, HTMLElement: globalThis.HTMLElement,
    customElements: globalThis.customElements, document: globalThis.document,
  };
  const elements = new Map();
  globalThis.window = {};
  globalThis.HTMLElement = class {};
  globalThis.customElements = {
    get: (name) => elements.get(name),
    define: (name, constructor) => elements.set(name, constructor),
  };
  globalThis.document = { createElement: (name) => ({ tagName: name }) };
  try {
    await import("../src/lumineze-dashboard.js?browser-smoke");
    assert.ok(elements.has("ll-strategy-dashboard-lumineze-dashboard"));
    assert.ok(elements.has("lumineze-strategy-editor"));
    assert.ok(elements.has("lumineze-calibration-chart"));
    assert.deepEqual(globalThis.window.customStrategies.map((item) => item.type),
      ["lumineze-dashboard"]);
    const strategy = elements.get("ll-strategy-dashboard-lumineze-dashboard");
    assert.equal(strategy.configRequired, true);
    assert.equal(strategy.getConfigElement().tagName, "lumineze-strategy-editor");
    const generated = await strategy.generate({ controller_device_id: "one" }, {
      ...hass, callWS: async () => entries,
    });
    assert.equal(generated.views.length, 4);
  } finally {
    for (const [key, value] of Object.entries(previous)) {
      if (value === undefined) delete globalThis[key];
      else globalThis[key] = value;
    }
  }
});
