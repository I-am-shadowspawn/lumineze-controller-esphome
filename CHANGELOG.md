# Changelog

## 2.0.0-dev — unreleased candidate

- Adds a generic, fixture-based controller with independent seasonal and daily
  schedule firmware profiles. Schedule edit, Apply and Cancel controls use a
  versioned two-bank preference record.
- Adds distinct production and development profiles, explicit source/profile
  information and a four-profile CI matrix.
- Keeps the legacy package path as a compatibility build. Migration of a live
  controller requires calibration, HA identity, storage and recovery checks.
- Gate A, T23 physical acceptance and T15 hardware/OTA evidence are still open.
  This entry does not advertise a stable release or a verified installation.

Existing `v1.0.0` recovery and `v1.9.0-rc` candidate tags remain immutable.
