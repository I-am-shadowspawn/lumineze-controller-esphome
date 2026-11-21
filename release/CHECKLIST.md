# Modular release checklist

This checklist is for a future T16 candidate. Current project version
`2.0.0-dev` and `release/candidate.json` are not stable release evidence.

1. Record Gate A and T23 physical traces at the exact candidate SHA. Complete
   T15 for all advertised profiles, including runtime heap/OTA, settings
   retention, BLE readback and a physical recovery route.
2. Freeze the source SHA and a stable project version in a reviewable change.
   Update `CHANGELOG.md`, the release manifest and examples. Do not reuse the
   existing `v1.0.0` or `v1.9.0-rc` tags.
3. Run the Required validation GitHub check at the frozen SHA; inspect each
   profile log/size and the remote consumer rehearsal for all four profiles.
   A canceled or pending job is not a pass.
4. Build the four ordinary wrappers and external component from the same
   immutable SHA. Record checksum, builder/toolchain, partition and dummy
   fixture build results. Record real bench firmware versions privately.
5. Review the compatibility matrix, backup/export and rollback procedure. Have
   the operator confirm the previous known-good firmware/settings and USB route.
6. Only after all gates pass, create one immutable version tag and a release
   pointing to the exact tested SHA. Verify a clean remote consumer using that
   tag and check its SHA matches the frozen candidate.
7. Handoff the tag/SHA, hardware trace links, limits and recovery instructions
   to T17. Do not silently enable any lamp during an upgrade or profile switch.
