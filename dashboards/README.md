# Lumineze Dev dashboard

This is the legacy raw-YAML proof of concept. For a single-install companion
that supports multiple vivariums, use the [Dashboard Companion](../dashboard-companion/README.md).

[`lumineze-dev.yaml`](lumineze-dev.yaml) is a Home Assistant dashboard for the
60 currently exposed Lumineze controller entities. It has five views:
Overview, JungleDawn, Light calibration, Groups & Schedule, and Diagnostics.
The displayed controller and light meter are selected once in the dashboard
configuration.

## Prerequisite

Install [Config Template Card](https://github.com/iantrich/config-template-card)
and [Plotly Graph Card](https://github.com/dbuezas/lovelace-plotly-graph-card)
through HACS before adding the dashboard. Config Template Card 2.0.0 or newer
requires Home Assistant 2026.2.3 or newer. The dashboard otherwise uses
built-in cards.

## Select the controller

At the top of `lumineze-dev.yaml`, set `CONTROLLER` to the common portion of
the selected device's entity IDs between the domain and the entity suffix:

```yaml
config_template_card_vars:
  CONTROLLER: $! vivarium_lumineze_dev
  ILLUMINANCE: $! sensor.vivarium_lamp_light_meter_jungle_dawn_illuminance
  UV_ILLUMINANCE: $! sensor.vivarium_lamp_light_meter_uv_lamp_illuminance
  UV_INDEX: $! sensor.vivarium_lamp_light_meter_uv_lamp_estimated_uv_index
```

For example, if the device has
`sensor.vivarium_lumineze_lab_jungledawn_requested_level`, set the value to
`$! vivarium_lumineze_lab`. The `$! ` prefix is Config Template Card's syntax
for a literal string. Keep it when changing the value. All dashboard entity
references use `CONTROLLER`, including gauges and the history graph. Each
selected device must expose the same entity suffixes. If Home Assistant has
renamed an individual entity, restore the expected ID or edit that reference.

`ILLUMINANCE` and `UV_ILLUMINANCE` are the full Home Assistant entity IDs of
the Lamp Light Meter's Jungle Dawn and UV Lamp illuminance sensors.
`UV_INDEX` is the meter's estimated UV index. These are the IDs currently
reported by the connected Home Assistant instance. Change a setting if the
corresponding entity is renamed. All four settings use the `$! ` literal-string
prefix.

## Light calibration

The Light calibration view shows the live meter readings, a 24-hour time graph
of requested level, lamp-reported level, and both lux sensors, a UV index
history graph, and a scatter plot of both lux sensors against lamp-reported
level. Both sensors currently observe the JungleDawn setup. The scatter plot
pairs one-minute samples from Home Assistant history. It drops the first two
samples after each reported level change, then shows stable samples and the
median lux at each level that was actually observed. Each sensor has its own
0% ambient baseline. Hover over a point to see its lux difference from that
baseline within the same six-hour window. If the window has no 0% samples,
the difference is unavailable. Unmeasured percentages are not filled in.
Increase `hours_to_show` on the scatter card if a sweep takes longer than six
hours.

For a useful sweep, leave the light meter in a fixed position, keep other
lights and daylight steady, record 0% with JungleDawn off, then hold each
level for at least two minutes. Check readback freshness during the sweep;
the plotted percentage is the lamp-reported level, not the requested level.
The chart is observational and does not change the controller's calibration.
Home Assistant Recorder must retain history for the reported-level and meter
sensors over the period being plotted.

## Add to Home Assistant

1. In **Settings → Dashboards**, add a **New dashboard from scratch** named
   **Lumineze Dev**.
2. Open the new dashboard, select **Edit dashboard**, then open the menu and
   select **Raw configuration editor**.
3. Set `CONTROLLER`, `ILLUMINANCE`, `UV_ILLUMINANCE`, and `UV_INDEX` in
   `lumineze-dev.yaml`, then replace the editor contents with the file and save.
   Reload the browser if the custom cards were just installed.

The dashboard does not change any device setting until someone uses a control.
The fixed-level workflow is: enable Visible Automatic Control, set the fixed
level and duration, press Start Fixed Level, then check the lamp-reported level
and readback status for confirmation.

To make dashboards for multiple controllers, create a separate dashboard for
each one and change only its `CONTROLLER` value.
