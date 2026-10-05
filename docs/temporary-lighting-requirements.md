# Feature request: temporary lighting controls

**Status:** software implementation is on branch `t23-codex`. Physical
ESP32-C3/BLE acceptance evidence remains outstanding. The behavior contract for
that bench validation is below.

## Scope and meaning

Add two Home Assistant controls to each commissioned fixture in the seasonal
production and development profiles assembled by T09:

1. **Today's automatic maximum:** an absolute lamp percentage that temporarily
   limits automatic output for the controller's current local calendar day.
2. **Timed fixed level:** an absolute lamp percentage held for a selected
   number of hours, followed by a fresh automatic evaluation.

Both act on one physical fixture. Two fixtures in the same group can therefore
have different temporary settings. Neither changes the seasonal context,
curve, peak, permanent calibrated maximum, group settings, or BLE protocol.
The seasonal engine continues calculating for every context, including while a
fixture is held at a fixed level. “Pause the solar calculation” means pause its
**application to that fixture**; other fixtures must continue normally.

This first implementation targets the T09 generic seasonal profiles. The
legacy v1 package keeps its existing behavior; using these controls requires
the documented migration to a supported seasonal profile. The policy boundary
should remain usable by a future schedule engine, but T10–T11 and schedule
support are separate work.

## Today's automatic maximum

The selected percentage is compared with the **normal final integer automatic
lamp target**, after the usual seasonal calculation, fixture calibration,
rounding and permanent limits. It is an absolute 0–100% lamp level, not a new
solar peak or a percentage of the curve. The controller retains the original
calculated target for its decisions and diagnostics.

- Applying the maximum requires a valid live local date, valid seasonal output
  and an enabled automatic group. It takes effect immediately for that fixture
  and expires no later than the next local date change. A reboot clears it.
  If the curve starts at/below the maximum, the override remains armed until a
  normal target first rises above it; initial at/below values do not end it.
- While the normal target is at or below the temporary maximum, ordinary
  automatic commands continue. While it is above the maximum, no **new higher
  automatic target** is submitted over BLE. The fixture holds its last
  authorized target at or below the maximum. Retries of that already authorized
  target remain permitted.
- If applying or lowering the maximum finds an outstanding target, completed
  target or fresh lamp report above it, the controller revokes any pending
  higher automatic request and submits one corrective target at the lower of
  the current normal target and the temporary maximum.
  An in-flight BLE write may finish first; diagnostics must show that physical
  enforcement is pending until readback confirms it. Unknown/stale readback is
  not reported as a confirmed physical cap.
- The normal calculation continues during the hold. On the dusk descent, the
  first valid normal target **at or below** the maximum ends the override and
  resumes ordinary automatic commands. Exact equality is not required: a
  sampled curve may jump from 61% to 59% around a 60% maximum. This first
  returning target bypasses the ordinary minimum-change filter so the descent
  resumes promptly; it does not create a duplicate command if the accepted
  target is already identical.
- A maximum that the curve never exceeds has no effect on output and expires
  at the next local date change. Applying a new maximum while one is active
  replaces it and reevaluates against the current normal target. Cancelling it
  reevaluates immediately and may command the current higher curve level.

Example with a 60% maximum: normal targets `20, 45, 60, 65, 80, 75, 61, 59,
40` yield automatic requests `20, 45, 60, [hold], [hold], [hold], [hold], 59,
40`, subject to existing unchanged-target and BLE timing rules. The normal
calculation still reaches 80%; its peak setting remains unchanged.

## Timed fixed level

The user selects a fixture level from 0–100% and a duration from 0.25 to 24
hours in 0.25-hour steps, then presses **Start Fixed Level**. The requested
absolute level still passes through the fixture's permanent calibrated maximum
and existing safety checks. A 0% level is a timed off request. A duration of
zero, a non-finite value, a value outside the supported range, or a value not
on a quarter-hour step is rejected. Validation also applies to API actions.

- Start submits the fixed target immediately through the normal fixture policy
  and dispatcher. Its duration starts at the accepted **Start** action, not at
  BLE confirmation. Seasonal calculations continue in the background but do
  not submit targets for that fixture during the timed hold.
- The duration is measured by monotonic elapsed controller time, independent
  of Home Assistant connectivity, wall-clock changes, midnight and daylight
  saving. It clears on reboot rather than restoring an old deadline.
- At expiry, the controller discards pending fixed-level retries, obtains a
  fresh real-time evaluation and resumes the then-current automatic target.
  It does not replay a target calculated when the hold started. An in-flight
  transaction may finish first; the current target then takes precedence.
- Start requires a commissioned fixture with valid live seasonal output,
  automatic control enabled and no active fixture or group manual override.
  These preconditions make “return to the curve” meaningful. A second Start
  replaces the fixed level and restarts the duration from that action. Editing
  the level or duration fields alone does not change an active hold.

Example: starting 35% for 2 hours submits 35% now. If the normal curve moves
from 45% to 75% during those 2 hours, neither value is sent for this fixture.
At expiry, a fresh 75% (or whatever the curve currently requests) is submitted
under the ordinary permanent limits and BLE rules.

## Shared control rules

- Only one of these temporary modes may be active per fixture. Starting one
  cancels the other. Activating a fixture/group manual override, turning
  automatic control off, requesting explicit safe-off or losing valid live
  time cancels the temporary mode. Existing safety, commissioning,
  simulation-output and calibrated-maximum gates keep their priority.
  Temporary controls never authorize an otherwise blocked lamp command.
- Both modes are volatile and default inactive on boot. The editable Home
  Assistant values may display defaults, but they must not activate themselves
  through restore, API reconnect or a package update.
- Every accepted Apply, Start/restart, replacement, release, cancellation or
  expiry revokes obsolete pending/retry generations, including a write already
  in flight. An obsolete completion remains physical history and cannot mark
  the latest request readback fresh. Existing
  transaction tokens and readback freshness rules still determine whether a
  lamp actually followed a command. A failed or disconnected lamp is reported
  as pending/faulted, never as confirmed at the requested level.
- Automatic minimum-change filtering remains in force during normal operation.
  The initial corrective cap, fixed-level Start and first descending release
  are explicit transitions and may bypass that filter.
- In development simulation, the existing calculation-only gate remains in
  force. Simulated time cannot use either control to transmit to a lamp unless
  the existing explicit bench-output gate authorizes it.

## Home Assistant contract

Each fixture gains staged configuration values, actions and status entities:

| Entity | Purpose |
| --- | --- |
| Today's Automatic Maximum (%) | Edit 0–100% absolute lamp maximum for this activation |
| Apply Today's Maximum | Activate or replace the maximum for the current local date |
| Fixed Level (%) | Edit the absolute lamp level for the next timed hold |
| Fixed Duration (hours) | Edit 0.25–24 hours for the next timed hold |
| Start Fixed Level | Activate or restart the timed hold |
| Cancel Temporary Lighting | Cancel either mode and reevaluate automatic output |
| Temporary Lighting Status | Inactive, armed, holding, enforcing, fixed, returning, or rejected reason; distinguish requested from confirmed output |
| Temporary Time Remaining (minutes) | Remaining timed hold; zero when inactive |
| Temporary Maximum Active / Fixed Level Active | Separate state indicators for dashboards and automations |

Pressing Apply or Start snapshots the staged values. Editing a staged number
alone does not activate, cancel or extend an override. A rejected action leaves
the current operational decision intact and reports why. A status update does
not imply that the lamp physically changed; the existing requested, completed,
reported and readback entities retain that distinction.

## Acceptance criteria

1. The 60% example follows the requested/hold/descending sequence above. A
   61% → 59% downward sample releases the maximum and submits 59% even when the
   ordinary minimum-change threshold would suppress that one-percent step.
2. Applying 60% when the accepted or fresh reported lamp level is 80% revokes
   pending 80% work and requests a 60% correction. Diagnostics remain
   unconfirmed until a fresh matching report arrives; an older in-flight 80%
   completion cannot restore the higher request.
3. The seasonal calculated peak and permanent calibrated maximum do not
   change. At/under-limit automatic levels and other fixtures continue as
   before. A cap above today's peak expires at the next local date change.
4. Local midnight, reboot, cancel, a changed cap, manual action, automatic-off
   and safety action have the expiration/replacement behavior stated above.
   Invalid live time rejects applying today's maximum.
5. A timed 35% level for 2 hours starts one fixed request, suppresses later
   automatic requests for that fixture, and triggers a fresh automatic target
   within one evaluation interval after expiry. Repeated Start resets the
   deadline. The timer survives HA disconnection and wall-clock/DST changes,
   but not controller reboot.
6. Expiry or cancellation while a BLE write is pending/in flight cannot revive
   an obsolete fixed or over-limit target. A disconnected lamp is not marked
   confirmed. The other fixtures keep progressing.
7. Home Assistant exposes all entities above in production and development;
   staged values do nothing until activated. Actions with invalid settings or
   unmet automatic/commissioning preconditions report rejection without
   altering the current target.
8. The seasonal production and development profiles validate and compile;
   deterministic policy cases cover threshold crossing, rollover and request
   generation. A bench check verifies one fixture's rise/hold/descent and timed
   return with actual BLE readback. Existing seasonal parity tests pass when
   both temporary modes are inactive.
