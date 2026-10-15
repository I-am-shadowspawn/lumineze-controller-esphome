# T14 remote installation software evidence

On 7 October 2026, the four public `example/` wrappers were copied one at a
time into separate empty temporary directories outside the repository. Each
directory contained only `controller.yaml` and a generated `secrets.yaml` with
synthetic Wi-Fi/API values and dummy MACs. Neither local `packages/` nor local
`components/` was present. ESPHome fetched both the Git package and external
`lumineze_topology` component at immutable source
`e3bdc2b81c325379be456c0d1ac2acc8d0e16e8a`; both refs in each wrapper
were `${controller_ref}`. The wrapper text and checker are on branch
`implementation/t11-t17`. This is a candidate SHA, not a verified release tag.

Command from the repository root (the venv path is local to this run):

```sh
CCACHE_DIR=/tmp/t23-ccache /tmp/t23-esphome-env/bin/python \
  scripts/check_public_examples.py \
  --esphome /tmp/t23-esphome-env/bin/esphome \
  --ref e3bdc2b81c325379be456c0d1ac2acc8d0e16e8a --compile
```

For another host, use Python and ESPHome 2026.9.0 from its own environment,
with a writable ccache directory. ESP-IDF resolved to 5.5.5. The initial
attempt with this workspace's read-only default ccache directory stopped
before a firmware result; rerunning with `/tmp/t23-ccache` completed.

| Public wrapper | `esphome config` | `esphome compile` | Image bytes | Static RAM estimate |
| --- | --- | --- | ---: | ---: |
| `seasonal-production.yaml` | PASS | PASS | 1,303,012 | 148,008 |
| `seasonal-development.yaml` | PASS | PASS | 1,316,524 | 148,832 |
| `schedule-production.yaml` | PASS | PASS | 1,307,842 | 151,360 |
| `schedule-development.yaml` | PASS | PASS | 1,321,650 | 152,184 |

All four used the example's two fixtures, with ProT5 in slot 0 and
JungleDawn in slot 1, ESP32-C3 and the same revision. The build reported a
1,835,008-byte app partition for each. These sizes and RAM estimates do not
measure runtime heap, BLE behavior, OTA success, Home Assistant entities,
physical lamp output, or settings retention. Gate A, T13.4 and T15 remain
open. T16 must refresh the examples to the final verified stable ref after
physical and release acceptance.
