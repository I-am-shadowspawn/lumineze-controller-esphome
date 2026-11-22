# Lumineze Dashboard Companion

One Marketplace/HACS dashboard plugin for any number of Lumineze controller dashboards. Requires Home Assistant 2026.5 or newer and the current two-lamp Lumineze profile. No other custom cards are required.

Install this GitHub repository as a custom **Dashboard/plugin** repository and choose its default branch until a release containing `lumineze-dashboard.js` is published. Reload the browser. In **Settings → Dashboards → Add dashboard**, select **Lumineze Dashboard Companion** under Community dashboards. Choose the controller and, optionally, up to two illuminance sensors and one UV index sensor. Repeat the dashboard creation step for each vivarium. A selected sensor should measure the same lamp and position used during its calibration sweep.

For each sweep, record 0% with the lamp off, then hold each level for at least two minutes. The graph uses lamp-reported power, discards the first two one-minute samples after a level change, and shows measured lux and lux above the measured 0% ambient baseline. Recorder must retain the selected sensors' history. The graph is observational and does not change controller settings.

This companion lives here until it is moved to a separate repository. Marketplace requires root-level `hacs.json` and `dist/lumineze-dashboard.js`; both are generated/maintained alongside the isolated source in this directory. For each shared firmware release, push the tag and create a draft release for it. Run the **Dashboard companion** workflow manually from a branch containing this workflow, supplying the tag as `release_tag`. The preparation job builds from that tag and uploads the asset if missing; an existing asset must match the build. Wait for the job to succeed before publishing the draft. The release workflow verifies the published asset. Published immutable releases cannot be repaired by this workflow; if an asset is missing or incorrect, publish a new release with a new tag.

Local checks: `cd dashboard-companion && npm test && npm run build`.
