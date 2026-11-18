/* Lumineze Dashboard Companion. This file is the complete Marketplace module. */

const STRATEGY = "lumineze-dashboard";
const SVG = "http://www.w3.org/2000/svg";
const COLORS = ["#e78b16", "#9655c7"];

// These are the entity's original ESPHome names, normalized to Home Assistant
// slugs. The registry's device_id is always checked before a role is used.
export const GROUPS = {
  glance: [
    "controller_time_valid", "vivarium_evaluation_status",
    "vivarium_visible_delivery", "vivarium_uv_delivery",
  ],
  status: [
    "jungledawn_temporary_lighting_status", "jungledawn_temporary_time_remaining",
    "jungledawn_dispatch_status", "jungledawn_readback_status",
    "jungledawn_request_pending",
  ],
  quick: [
    "visible_automatic_control", "uv_automatic_control",
    "jungledawn_fixed_level", "jungledawn_fixed_duration",
    "jungledawn_start_fixed_level", "jungledawn_cancel_temporary_lighting",
  ],
  stop: [
    "jungledawn_request_off", "vivarium_uv_request_off",
    "request_all_fixtures_off",
  ],
  temporary: [
    "visible_automatic_control", "jungledawn_fixed_level",
    "jungledawn_fixed_duration", "jungledawn_start_fixed_level",
    "jungledawn_cancel_temporary_lighting", "jungledawn_fixed_level_active",
    "jungledawn_temporary_time_remaining", "jungledawn_temporary_lighting_status",
  ],
  maximum: [
    "jungledawn_today_s_automatic_maximum",
    "jungledawn_apply_today_s_maximum", "jungledawn_temporary_maximum_active",
  ],
  manual: [
    "jungledawn_manual_override", "jungledawn_manual_absolute_level",
    "jungledawn_request_off",
  ],
  delivery: [
    "jungledawn_requested_level", "jungledawn_lamp_reported_level",
    "jungledawn_last_completed_level", "jungledawn_dispatch_status",
    "jungledawn_readback_status", "jungledawn_ble_connected",
    "jungledawn_request_pending", "jungledawn_readback_fresh",
    "jungledawn_readback_mismatch",
  ],
  fixture: [
    "jungledawn_calibrated_maximum", "jungle_dawn_minimum_automatic_change",
  ],
  visible: [
    "visible_automatic_control", "vivarium_visible_manual_override",
    "vivarium_visible_manual_of_fixture_maximum", "vivarium_visible_demand",
    "vivarium_visible_delivery", "vivarium_visible_request_off",
  ],
  uv: [
    "uv_automatic_control", "vivarium_uv_manual_override",
    "vivarium_uv_manual_of_fixture_maximum", "vivarium_uv_demand",
    "vivarium_uv_delivery", "vivarium_uv_request_off",
  ],
  clock: [
    "vivarium_latitude", "vivarium_solar_noon",
    "vivarium_season_phase_offset", "controller_time_valid",
    "vivarium_evaluation_status",
  ],
  visibleCurve: [
    "vivarium_visible_winter_peak", "vivarium_visible_summer_peak",
    "vivarium_visible_curve_exponent",
  ],
  uvCurve: [
    "vivarium_uv_start_after_sunrise", "vivarium_uv_end_before_sunset",
    "vivarium_uv_winter_peak", "vivarium_uv_summer_peak",
    "vivarium_uv_curve_exponent",
  ],
  safety: [
    "controller_time_valid", "invalid_time_fail_safe",
    "invalid_time_grace_period", "automatic_recovery_interval",
    "vivarium_evaluation_status",
  ],
  communication: [
    "jungledawn_ble_connected", "jungledawn_request_pending",
    "jungledawn_readback_fresh", "jungledawn_readback_mismatch",
    "jungledawn_dispatch_status", "jungledawn_readback_status",
    "jungledawn_completed_transactions", "jungledawn_failed_transactions",
  ],
  tuning: [
    "ble_maximum_attempts", "ble_minimum_same_fixture_interval",
    "ble_inter_fixture_quiet_time", "ble_retry_base_delay",
    "ble_transaction_timeout",
  ],
};

const slug = (value) => String(value || "").toLowerCase()
  .replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");

export function resolveRoles(entries, deviceId) {
  const roles = {};
  if (!deviceId) return roles;
  const wanted = new Set(Object.values(GROUPS).flat());
  for (const entry of entries || []) {
    if (entry.device_id !== deviceId || entry.disabled_by || !entry.entity_id) continue;
    const original = slug(entry.original_name);
    const unique = slug(entry.unique_id);
    const id = entry.entity_id.split(".")[1] || "";
    for (const role of wanted) {
      if (roles[role]) continue;
      if (original === role || unique.endsWith(`_${role}`) ||
          id === role || id.endsWith(`_${role}`)) {
        roles[role] = entry.entity_id;
      }
    }
  }
  return roles;
}

export function isLux(state) {
  return state?.attributes?.unit_of_measurement === "lx" ||
    state?.attributes?.device_class === "illuminance";
}

function meterSelection(config, hass) {
  const ids = [...new Set((config.lux_entities || []).filter(Boolean))].slice(0, 2);
  return ids.filter((id) => isLux(hass.states?.[id]));
}

const markdown = (content) => ({ type: "markdown", content });
const row = (entity, name) => name ? { entity, name } : { entity };

function entitiesCard(title, keys, roles, names = {}) {
  const entities = keys.filter((key) => roles[key])
    .map((key) => row(roles[key], names[key]));
  return entities.length ? {
    type: "entities", title, show_header_toggle: false, entities,
  } : markdown(`**${title}:** No matching entities on the selected controller.`);
}

function view(title, path, icon, cards) {
  return { title, path, icon, cards };
}

export function generateDashboard(config, hass, entries) {
  const deviceId = config.controller_device_id;
  const device = hass.devices?.[deviceId];
  if (!deviceId || !device) {
    return {
      title: "Lumineze",
      views: [view("Setup", "setup", "mdi:alert-circle-outline", [
        markdown("Select an available Lumineze controller in this dashboard's strategy settings."),
      ])],
    };
  }
  const roles = resolveRoles(entries, deviceId);
  const lux = meterSelection(config, hass);
  const uvIndex = hass.states?.[config.uv_index_entity]
    ? config.uv_index_entity : undefined;
  const missing = ["jungledawn_requested_level", "jungledawn_lamp_reported_level"]
    .filter((key) => !roles[key]);
  const warning = missing.length ? [markdown(
    `**Controller profile incomplete:** Missing ${missing.join(", ")}. Check that this is the current two-lamp Lumineze controller and its entities are enabled.`,
  )] : [];
  const unavailableMeters = (config.lux_entities || []).filter((id) =>
    id && !lux.includes(id));
  if (config.uv_index_entity && !uvIndex) unavailableMeters.push(config.uv_index_entity);
  if (unavailableMeters.length) warning.push(markdown(
    `**Meter unavailable:** Check ${unavailableMeters.join(", ")} in this dashboard's strategy settings.`,
  ));
  const title = config.title || device.name_by_user || device.name || "Lumineze";
  const glance = entitiesCard("At a glance", GROUPS.glance, roles);
  glance.entities?.push(...lux.map((id) => row(id, hass.states[id].attributes.friendly_name)));
  if (uvIndex) glance.entities?.push(row(uvIndex, "Estimated UV index"));
  const gauges = ["jungledawn_lamp_reported_level", "jungledawn_requested_level"]
    .filter((key) => roles[key]).map((key) => ({
      type: "gauge", entity: roles[key],
      name: key.includes("reported") ? "JungleDawn reported" : "JungleDawn requested",
      min: 0, max: 100,
    }));
  const overview = view("Overview", "overview", "mdi:view-dashboard", [
    ...warning,
    markdown("# Vivarium lighting\nCheck lamp-reported level and readback status to confirm a requested change."),
    glance,
    ...(gauges.length ? [{ type: "grid", columns: 2, square: false, cards: gauges }] : []),
    entitiesCard("JungleDawn status", GROUPS.status, roles),
    entitiesCard("Quick controls", GROUPS.quick, roles),
    entitiesCard("Stop controls", GROUPS.stop, roles),
  ]);
  const jungle = view("JungleDawn", "jungledawn", "mdi:lightbulb-on-outline", [
    markdown("## Fixed level\nEnable Visible Automatic Control, choose a level and duration, then press Start Fixed Level. Confirm delivery with reported level and readback."),
    entitiesCard("Temporary lighting", GROUPS.temporary, roles),
    entitiesCard("Today's automatic maximum", GROUPS.maximum, roles),
    entitiesCard("Manual control", GROUPS.manual, roles),
    ...(roles.jungledawn_requested_level && roles.jungledawn_lamp_reported_level ? [{
      type: "history-graph", title: "Requested and reported level",
      hours_to_show: 24, entities: [
        roles.jungledawn_requested_level, roles.jungledawn_lamp_reported_level,
      ],
    }] : []),
    entitiesCard("Delivery and confirmation", GROUPS.delivery, roles),
    entitiesCard("Fixture settings", GROUPS.fixture, roles),
  ]);
  const views = [overview, jungle];
  if (lux.length || uvIndex) {
    const measurement = [
      roles.jungledawn_requested_level && row(roles.jungledawn_requested_level, "Requested level (%)"),
      roles.jungledawn_lamp_reported_level && row(roles.jungledawn_lamp_reported_level, "Lamp-reported level (%)"),
      ...lux.map((id) => row(id, hass.states[id].attributes.friendly_name)),
      uvIndex && row(uvIndex, "Estimated UV index"),
      roles.jungledawn_readback_status && row(roles.jungledawn_readback_status, "Readback status"),
      roles.jungledawn_readback_fresh && row(roles.jungledawn_readback_fresh, "Readback fresh"),
    ].filter(Boolean);
    const calibration = [
      markdown("## JungleDawn level to illuminance\nKeep each meter fixed and other lighting steady. Measure 0% with JungleDawn off, then hold each level at least two minutes. Use fresh readback to trust each point."),
      { type: "entities", title: "Current measurement", show_header_toggle: false, entities: measurement },
    ];
    if (lux.length && roles.jungledawn_lamp_reported_level) {
      const common = {
        reported: roles.jungledawn_lamp_reported_level,
        requested: roles.jungledawn_requested_level,
        meters: lux.map((id) => ({ entity: id, name: hass.states[id].attributes.friendly_name || id })),
      };
      calibration.push(
        { type: "custom:lumineze-calibration-chart", mode: "time", ...common },
        { type: "custom:lumineze-calibration-chart", mode: "scatter", ...common },
      );
    }
    if (uvIndex) calibration.push({
      type: "history-graph", title: "Estimated UV index",
      hours_to_show: 24, entities: [uvIndex],
    });
    views.push(view("Light calibration", "light-calibration", "mdi:chart-scatter-plot", calibration));
  }
  views.push(view("Groups & Schedule", "groups-schedule", "mdi:weather-sunset", [
    entitiesCard("Visible group", GROUPS.visible, roles),
    entitiesCard("UV group", GROUPS.uv, roles),
    entitiesCard("Vivarium clock and location", GROUPS.clock, roles),
    entitiesCard("Visible seasonal curve", GROUPS.visibleCurve, roles),
    entitiesCard("UV timing and seasonal curve", GROUPS.uvCurve, roles),
  ]));
  views.push(view("Diagnostics", "diagnostics", "mdi:stethoscope", [
    entitiesCard("Controller safety", GROUPS.safety, roles),
    entitiesCard("JungleDawn communication", GROUPS.communication, roles),
    entitiesCard("BLE dispatch tuning", GROUPS.tuning, roles),
  ]));
  return { title, views };
}

export function historySeries(history, entityId) {
  return (history?.[entityId] || []).filter((item) =>
    item.s !== null && item.s !== undefined && item.s !== "")
    .map((item) => ({
    time: Number(item.lu) * 1000,
    value: Number(item.s),
  })).filter((item) => Number.isFinite(item.time) && Number.isFinite(item.value))
    .sort((a, b) => a.time - b.time);
}

function latestAt(series, time) {
  let low = 0, high = series.length - 1, found = -1;
  while (low <= high) {
    const middle = (low + high) >> 1;
    if (series[middle].time <= time) { found = middle; low = middle + 1; }
    else high = middle - 1;
  }
  return found < 0 ? null : { ...series[found], index: found };
}

const median = (values) => {
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
};

export function calibrationPoints(reported, lux, start, end) {
  const samples = [];
  if (!reported.length || !lux.length) return { samples, curve: [], baseline: null };
  let changedAt = reported[0].time;
  let lastLevel = reported[0].value;
  let position = 0;
  for (let time = Math.ceil(start / 60000) * 60000; time <= end; time += 60000) {
    while (position + 1 < reported.length && reported[position + 1].time <= time) {
      position++;
      if (reported[position].value !== lastLevel) {
        changedAt = reported[position].time;
        lastLevel = reported[position].value;
      }
    }
    const power = latestAt(reported, time);
    const light = latestAt(lux, time);
    if (!power || !light || time - changedAt < 120000 ||
        time - power.time > 300000 || time - light.time > 300000 ||
        power.value < 0 || power.value > 100 || light.value < 0) continue;
    samples.push({ pct: power.value, lx: light.value, time });
  }
  const ambient = samples.filter((point) => point.pct === 0).map((point) => point.lx);
  const baseline = ambient.length ? median(ambient) : null;
  const levels = new Map();
  for (const point of samples) {
    if (!levels.has(point.pct)) levels.set(point.pct, []);
    levels.get(point.pct).push(point.lx);
    point.delta = baseline === null ? null : point.lx - baseline;
  }
  const curve = [...levels].sort((a, b) => a[0] - b[0])
    .map(([pct, values]) => ({ pct, lx: median(values), count: values.length,
      delta: baseline === null ? null : median(values) - baseline }));
  return { samples, curve, baseline };
}

const BaseElement = globalThis.HTMLElement || class {};

class LuminezeStrategyEditor extends BaseElement {
  setConfig(config) { this.config = { ...config }; this.render(); }
  set hass(hass) {
    this._hass = hass;
    if (hass && !this._registryLoaded) {
      this._registryLoaded = true;
      hass.callWS({ type: "config/entity_registry/list" })
        .then((entries) => { this.entries = entries; this.render(); })
        .catch(() => { this.entries = []; this.render(); });
    }
    this.render();
  }
  connectedCallback() {
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this.render();
  }
  change(patch) {
    this.config = { ...(this.config || {}), ...patch, type: `custom:${STRATEGY}` };
    this.dispatchEvent(new CustomEvent("config-changed", {
      detail: { config: this.config }, bubbles: true, composed: true,
    }));
    this.render();
  }
  render() {
    if (!this.shadowRoot || !this._hass) return;
    const root = this.shadowRoot;
    root.replaceChildren();
    const style = document.createElement("style");
    style.textContent = ":host{display:block;padding:8px}label{display:block;margin:12px 0;font-weight:600}select{display:block;width:100%;padding:8px;margin-top:5px;color:var(--primary-text-color);background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:5px}p{color:var(--secondary-text-color)}";
    root.append(style);
    const config = this.config || {};
    const entries = this.entries || [];
    const controllers = Object.values(this._hass.devices || {}).filter((device) => {
      const name = `${device.name || ""} ${device.model || ""} ${device.manufacturer || ""}`;
      return /lumineze/i.test(name) ||
        entries.some((entry) => entry.device_id === device.id &&
          /jungledawn.*requested.level/i.test(entry.original_name || entry.entity_id));
    });
    const control = (label, value, choices, onChange) => {
      const wrap = document.createElement("label");
      wrap.textContent = label;
      const select = document.createElement("select");
      for (const [id, name] of choices) {
        const option = document.createElement("option");
        option.value = id; option.textContent = name; option.selected = id === value;
        select.append(option);
      }
      if (value && !choices.some(([id]) => id === value)) {
        const option = document.createElement("option");
        option.value = value; option.textContent = `${value} (unavailable)`; option.selected = true;
        select.append(option);
      }
      select.addEventListener("change", () => onChange(select.value));
      wrap.append(select); root.append(wrap);
    };
    control("Lumineze controller", config.controller_device_id || "", [
      ["", "Select a controller"],
      ...controllers.map((device) => [device.id, device.name_by_user || device.name || device.id]),
    ], (id) => this.change({ controller_device_id: id }));
    if (!this.entries) {
      const hint = document.createElement("p");
      hint.textContent = "Loading device entities…"; root.append(hint);
    }
    const luxChoices = Object.entries(this._hass.states || {})
      .filter(([, state]) => isLux(state))
      .map(([id, state]) => [id, state.attributes.friendly_name || id])
      .sort((a, b) => a[1].localeCompare(b[1]));
    for (let index = 0; index < 2; index++) {
      control(`Illuminance meter ${index + 1} (optional)`, config.lux_entities?.[index] || "", [
        ["", "None"], ...luxChoices,
      ], (id) => {
        const values = [...(config.lux_entities || [])];
        values[index] = id;
        this.change({ lux_entities: values });
      });
    }
    const uvChoices = Object.entries(this._hass.states || {})
      .filter(([id, state]) => id.startsWith("sensor.") &&
        (/uv.index/i.test(id) || /uv.index/i.test(state.attributes?.friendly_name || "")))
      .map(([id, state]) => [id, state.attributes.friendly_name || id]);
    control("Estimated UV index (optional)", config.uv_index_entity || "", [
      ["", "None"], ...uvChoices,
    ], (id) => this.change({ uv_index_entity: id }));
  }
}

class LuminezeDashboardStrategy extends BaseElement {
  static configRequired = true;
  static registryDependencies = ["entities", "devices"];
  static getCreateSuggestions() {
    return { title: "Lumineze", icon: "mdi:lightbulb-on-outline" };
  }
  static getConfigElement() { return document.createElement("lumineze-strategy-editor"); }
  static async generate(config, hass) {
    try {
      const entries = await hass.callWS({ type: "config/entity_registry/list" });
      return generateDashboard(config, hass, entries);
    } catch (error) {
      return { title: "Lumineze", views: [view("Setup", "setup", "mdi:alert-circle-outline", [
        markdown(`Unable to load the Home Assistant entity registry: ${String(error)}`),
      ])] };
    }
  }
}

function svgNode(tag, attributes = {}, text = "") {
  const node = document.createElementNS(SVG, tag);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, String(value));
  if (text) node.textContent = text;
  return node;
}

class LuminezeCalibrationChart extends BaseElement {
  setConfig(config) {
    if (!config.reported || !Array.isArray(config.meters) ||
        !["time", "scatter"].includes(config.mode)) throw new Error("Invalid Lumineze chart config");
    this.config = config;
    this.history = undefined;
    this.lastFetch = 0;
    this.render();
  }
  set hass(hass) {
    this._hass = hass;
    if (hass && this.isConnected && Date.now() - (this.lastFetch || 0) >= 60000) this.refresh();
  }
  connectedCallback() {
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this.render();
    if (this._hass) this.refresh();
    this.timer = setInterval(() => { if (this._hass) this.refresh(); }, 60000);
  }
  disconnectedCallback() { clearInterval(this.timer); }
  async refresh() {
    if (!this.config || !this._hass || this.loading) return;
    this.loading = true;
    this.lastFetch = Date.now();
    const hours = this.config.mode === "scatter" ? 6 : 24;
    const end = new Date();
    const start = new Date(end.getTime() - hours * 3600000);
    const ids = [...new Set([
      this.config.reported, this.config.requested,
      ...this.config.meters.map((meter) => meter.entity),
    ].filter(Boolean))];
    try {
      this.history = await this._hass.callWS({
        type: "history/history_during_period", start_time: start.toISOString(),
        end_time: end.toISOString(), entity_ids: ids,
        minimal_response: true, no_attributes: true,
      });
      this.start = start.getTime(); this.end = end.getTime();
      this.error = undefined;
    } catch (error) { this.error = String(error); }
    finally { this.loading = false; this.render(); }
  }
  render() {
    if (!this.shadowRoot || !this.config) return;
    const root = this.shadowRoot;
    root.replaceChildren();
    const style = document.createElement("style");
    style.textContent = ":host{display:block}ha-card{display:block;padding:16px}h3{margin:0 0 12px;font-size:18px}svg{width:100%;height:auto;display:block}p{color:var(--secondary-text-color)}.legend{font-size:12px;display:flex;gap:14px;flex-wrap:wrap}.legend span{white-space:nowrap}.table-wrap{overflow-x:auto;margin-top:12px}table{border-collapse:collapse;width:100%;font-size:13px}th,td{text-align:left;padding:5px 8px;border-bottom:1px solid var(--divider-color)}";
    root.append(style);
    const card = document.createElement("ha-card");
    const heading = document.createElement("h3");
    heading.textContent = this.config.mode === "scatter"
      ? "Measured lux by lamp-reported level (6 hours)"
      : "Level and illuminance over time (24 hours)";
    card.append(heading);
    if (this.error || !this.history) {
      const message = document.createElement("p");
      message.textContent = this.error ? `History unavailable: ${this.error}` : "Loading history…";
      card.append(message); root.append(card); return;
    }
    const svg = svgNode("svg", { viewBox: "0 0 680 370", role: "img",
      "aria-label": heading.textContent });
    const left = 55, right = 610, top = 20, bottom = 305;
    const line = (x1, y1, x2, y2, color = "#888") =>
      svg.append(svgNode("line", { x1, y1, x2, y2, stroke: color, "stroke-width": 1 }));
    line(left, top, left, bottom); line(left, bottom, right, bottom);
    const label = (x, y, value, anchor = "middle") => svg.append(svgNode("text", {
      x, y, fill: "var(--primary-text-color)", "font-size": 12, "text-anchor": anchor,
    }, value));
    const legend = document.createElement("div"); legend.className = "legend";
    let detailTable;
    const legendItem = (name, color) => {
      const item = document.createElement("span");
      item.style.color = color; item.textContent = `● ${name}`; legend.append(item);
    };
    const reported = historySeries(this.history, this.config.reported);
    const meterSeries = this.config.meters.map((meter) => historySeries(this.history, meter.entity));
    const maxLux = Math.max(1, ...meterSeries.flat().map((point) => point.value).filter((value) => value >= 0));
    label(45, 14, "Level %", "start");
    label(635, 14, "Lux", "end");
    for (const tick of [0, 25, 50, 75, 100]) {
      const y = bottom - (tick / 100) * (bottom - top);
      line(left, y, right, y, "#8884"); label(47, y + 4, String(tick), "end");
      if (tick === 0 || tick === 50 || tick === 100)
        label(620, y + 4, String(Math.round(maxLux * tick / 100)), "start");
    }
    if (this.config.mode === "time") {
      const x = (time) => left + (time - this.start) / (this.end - this.start) * (right - left);
      const yLevel = (value) => bottom - Math.min(100, Math.max(0, value)) / 100 * (bottom - top);
      const yLux = (value) => bottom - Math.max(0, value) / maxLux * (bottom - top);
      const draw = (series, color, y, name, dash = "") => {
        const points = series.filter((point) => point.time >= this.start && point.time <= this.end)
          .map((point) => `${x(point.time)},${y(point.value)}`).join(" ");
        if (!points) return;
        svg.append(svgNode("polyline", { points, fill: "none", stroke: color,
          "stroke-width": 2, "stroke-dasharray": dash }));
        legendItem(name, color);
      };
      if (this.config.requested)
        draw(historySeries(this.history, this.config.requested), "#5178bd", yLevel, "Requested %", "5 4");
      draw(reported, "#2eaf7d", yLevel, "Reported %");
      meterSeries.forEach((series, index) => draw(series, COLORS[index], yLux,
        this.config.meters[index].name));
      label(left, 330, new Date(this.start).toLocaleString(), "start");
      label(right, 330, new Date(this.end).toLocaleString(), "end");
    } else {
      const x = (pct) => left + pct / 100 * (right - left);
      const y = (lux) => bottom - lux / maxLux * (bottom - top);
      let total = 0;
      const calibrationResults = [];
      meterSeries.forEach((series, index) => {
        const result = calibrationPoints(reported, series, this.start, this.end);
        calibrationResults.push({ name: this.config.meters[index].name, result });
        total += result.samples.length;
        for (const point of result.samples) {
          const dot = svgNode("circle", { cx: x(point.pct), cy: y(point.lx), r: 3,
            fill: COLORS[index], opacity: 0.5 });
          dot.append(svgNode("title", {}, `${this.config.meters[index].name}: ${point.pct}% → ${point.lx.toFixed(1)} lx; above ambient: ${point.delta === null ? "no 0% baseline" : `${point.delta.toFixed(1)} lx`}; ${new Date(point.time).toLocaleString()}`));
          svg.append(dot);
        }
        const points = result.curve.map((point) => `${x(point.pct)},${y(point.lx)}`).join(" ");
        if (points) svg.append(svgNode("polyline", { points, fill: "none",
          stroke: COLORS[index], "stroke-width": 2 }));
        for (const point of result.curve) {
          const dot = svgNode("circle", { cx: x(point.pct), cy: y(point.lx), r: 5,
            fill: COLORS[index] });
          dot.append(svgNode("title", {}, `${this.config.meters[index].name}: ${point.pct}% → median ${point.lx.toFixed(1)} lx (${point.count} samples); above ambient: ${point.delta === null ? "no 0% baseline" : `${point.delta.toFixed(1)} lx`}`));
          svg.append(dot);
        }
        legendItem(`${this.config.meters[index].name} median`, COLORS[index]);
      });
      for (const tick of [0, 25, 50, 75, 100]) label(x(tick), 324, String(tick));
      label(332, 348, "Lamp-reported level (%)");
      if (!total) {
        const message = document.createElement("p");
        message.textContent = "No stable paired samples in this six-hour window.";
        card.append(message);
      }
      if (total) {
        const wrap = document.createElement("div");
        wrap.className = "table-wrap";
        const table = document.createElement("table");
        const header = document.createElement("tr");
        for (const heading of ["Reported", "Meter", "Median lux", "Above 0% ambient", "Samples"]) {
          const cell = document.createElement("th");
          cell.textContent = heading; header.append(cell);
        }
        table.append(header);
        for (const { name, result } of calibrationResults) {
          for (const point of result.curve) {
            const row = document.createElement("tr");
            for (const value of [
              `${point.pct}%`, name, `${point.lx.toFixed(1)} lx`,
              point.delta === null ? "No 0% sample" : `${point.delta.toFixed(1)} lx`,
              String(point.count),
            ]) {
              const cell = document.createElement("td");
              cell.textContent = value; row.append(cell);
            }
            table.append(row);
          }
        }
        wrap.append(table); detailTable = wrap;
      }
    }
    card.append(svg, legend);
    if (detailTable) card.append(detailTable);
    root.append(card);
  }
}

if (globalThis.customElements && globalThis.window) {
  if (!customElements.get("lumineze-strategy-editor"))
    customElements.define("lumineze-strategy-editor", LuminezeStrategyEditor);
  if (!customElements.get("ll-strategy-dashboard-lumineze-dashboard"))
    customElements.define("ll-strategy-dashboard-lumineze-dashboard", LuminezeDashboardStrategy);
  if (!customElements.get("lumineze-calibration-chart"))
    customElements.define("lumineze-calibration-chart", LuminezeCalibrationChart);
  window.customStrategies = window.customStrategies || [];
  if (!window.customStrategies.some((item) => item.type === STRATEGY && item.strategyType === "dashboard"))
    window.customStrategies.push({
      type: STRATEGY, strategyType: "dashboard", name: "Lumineze Dashboard Companion",
      description: "A controller dashboard for each vivarium.",
      documentationURL: "https://github.com/I-am-shadowspawn/lumineze-controller-esphome/tree/development/dashboard-companion",
    });
}
