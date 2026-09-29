# Aero-Astra: Architecture Audit Tasks

Source: the updated "Code-Driven Analysis" data flow, checked against the repo files shared on Sep 20 to 22, 2026.
Companion file: `NEBIUS_SUBMISSION_GUIDE.md`. Do the Nebius integration, cold-start and deployment tasks from that guide first. This file covers the architecture and logic problems.

## How to use this file

Evidence labels:

- **[code]** verified in files I could read
- **[api.py]** cannot be settled without `backend/api.py` (and `src/App.jsx`), so it starts as a check
- **[inference]** my reasoning, needs a test to confirm

Priority: **P0** fix or verify before the video and README, **P1** strongly improves credibility, **P2** stretch.

Work rules:

1. Run every "Check" first and write the result under the task before changing code.
2. One task, one commit. Commit prefixes: `fix:`, `feat:`, `docs:`, `test:`, `refactor:`.
3. After each fix, add a line to `CHANGELOG_SUBMISSION.md`.
4. A task is done only when its "Pass if" line is true and you ran it.

Suggested order: Phase 0, then Phase 1, then P0 items of Phases 2 to 4, then Phase 5 (improvements), then P1 and P2.

---

## Phase 0: Verify what I could not see

### V1. Where do ORACLE's `fault_name` and `fault_severity` come from? (P0, [api.py])
Why it matters: `SherlockDiagnosis` holds a root-cause subsystem (for example `TCS`), not a fault ID (for example `tcs_thermal_runaway`). If `api.py` passes the simulator's ground-truth fault label to ORACLE, ORACLE gets the answer key instead of the diagnosis.
Check:
```bash
grep -n "OracleRequest\|fault_name\|fault_severity\|active_fault\|run_oracle" backend/api.py
```
Pass if: `fault_name` is derived from SHERLOCK's diagnosis (or a documented mapping from diagnosis to candidate fault hypotheses), never from `state.active_fault` or the playlist's `fault` field.
If it fails: build a diagnosis-to-hypothesis map, and let ORACLE evaluate the top hypotheses when the mapping is ambiguous. Document that ORACLE never sees ground truth.
- [ ] Result recorded, [ ] fixed or confirmed clean

### V2. Order of ATHENA, ORACLE and GUARDIAN in `api.py` (P0, [api.py])
The README and UI comments suggest GUARDIAN fires right after SHERLOCK. `guardian.evaluate()` needs ATHENA's `RecoveryPlan`.
Check:
```bash
grep -n "guardian\|evaluate(\|athena\|oracle\|sherlock" backend/api.py | head -80
```
Pass if: you can write the exact call order with line numbers under this task, and the flow diagram in the README matches it.
- [ ] Order documented

### V3. What actually triggers the SENTINEL alert? (P0, [api.py])
Known [code]: `engines.py` hardcodes `flagged_subsystem="ADCS"`, disables Engine C in `score_telemetry_window`, and the XGBoost model cannot see the six simulated faults. `vitals/agent.py` returns `worst_health`, described as the trigger fallback.
Check:
```bash
grep -n "worst_health\|sentinel_alert\|flagged_subsystem\|score_telemetry_window\|ResidualCorrelationDetector\|combined_score\|score_state" backend/api.py
```
Pass if: for each of the three replay faults, you know which detector fired, with what threshold, and which subsystem it reported.
- [ ] Table written: fault, detector, threshold, reported subsystem

### V4. Does ATHENA's choice get re-validated by ORACLE? (P1, [api.py])
The ATHENA prompt says the recommended action is "independently re-validated by Oracle with 200 runs, 600 steps". The written data flow does not list this step.
Check:
```bash
grep -n "n_runs\|steps=\|revalid\|re-valid\|recommended_action" backend/api.py
```
Pass if: the re-validation exists and is documented, or the prompt sentence is removed.
- [ ] Confirmed or removed

### V5. Which option does GUARDIAN evaluate when the operator picks option 2 or 3? (P0, [api.py])
The UI lets an operator select `selectedMitigation`. `evaluate()` reads only `recommended_action`.
Check:
```bash
grep -n "selectedMitigation\|setSelectedMitigation\|mitigation_option\|handleApprove" src/App.jsx backend/api.py
```
Pass if: the gate is re-run on the operator's actual choice, or the UI stops offering other options.
- [ ] Confirmed

### V6. Does the LLM call block the WebSocket loop? (P1, [api.py])
SHERLOCK and ATHENA call synchronous `openai` clients, with up to 3 retries per attempt chain and long timeouts.
Check:
```bash
grep -n "run_in_executor\|to_thread\|asyncio\|await .*diagnose\|\.plan(" backend/api.py
```
Pass if: LLM calls run in a thread or executor, so telemetry, heartbeats and other WebSocket messages keep flowing during a call. Test by activating SHERLOCK and watching whether the dashboard freezes.
- [ ] Confirmed

### V7. Simulation time base across the system (P0, [code] plus check)
Known: replay uses `dt=1.0`. ORACLE hardcodes `dt=23.0` with a comment that says "5 hours" but 300 steps of 23 s is about 1.9 hours. Sandbox uses `dt` of 5, 10 or 20.
Check:
```bash
grep -rn "dt=" backend/oracle backend/simulator backend/api.py backend/replay
grep -n "fault_onset\|def get_fault_modifiers" backend/simulator/faults.py
```
Pass if: you have a table of every `dt` and `steps` in use, and you know how `get_fault_modifiers` behaves when `fault_onset=0` is applied to an already-degraded state (does the ramp restart from zero effect?).
- [ ] Table written

### V8. Is anything persisted server-side? (P1, [api.py])
Check: `grep -n "open(\|json.dump\|sqlite\|append" backend/api.py`.
Pass if: you know whether SCRIBE and CHRONICLE data survive a browser refresh (expected: they do not).
- [ ] Confirmed

---

## Phase 1: Contradictions inside the data-flow document

### C1. ORACLE and ATHENA circular dependency (P0, docs)
Flaw: the document says ORACLE takes `proposed_actions` from ATHENA, and ATHENA takes `OracleResponse` as input. Actual [code] order: ORACLE ranks all six catalog actions, then ATHENA writes options over that result.
Fix: rewrite the flow so it shows ORACLE (rank all) then ATHENA (select and explain) then optional ORACLE re-validation. Remove "proposed_actions (from ATHENA)" unless that path is real.
Pass if: the README diagram and this description match the call order found in V2.
- [ ] Done

### C2. No incident ID or single provenance contract (P0)
Flaw [code]: timestamps are `timestamp`, `diagnosis_timestamp`, `generated_at` (a float in ORACLE, a datetime in ATHENA) and `decided_at`. Only ORACLE has a `request_id`. Nothing carries `anomaly_id` forward, so an incident's records cannot be joined. The document's claim that provenance is "passed through untouched" is false.
Fix: create `backend/contracts.py` with a shared `IncidentContext` (fields: `incident_id`, `agent`, `model`, `provider`, `latency_ms`, `tokens_in`, `tokens_out`, `attempts`, `ts_utc` as ISO 8601 string). Every agent output and every WebSocket message includes it.
Pass if: one incident yields one `incident_id` visible in every message and in the log.
- [ ] Done

### C3. `AnomalyEvent` lives in `sherlock.schemas` (P1, refactor)
Flaw: SENTINEL (the detector) imports its output type from SHERLOCK (the diagnostician).
Fix: move `AnomalyEvent` and its enums into `contracts.py`. Keep a re-export in `sherlock` so existing imports still work.
Pass if: `backend/sentinel` does not import from `backend/sherlock`.
- [ ] Done

### C4. The pipeline has no execution or verification stage (P0)
Flaw: the flow ends at a GUARDIAN decision. Nothing applies the action, and nothing checks the result. See I3.
Fix: add EXECUTE and VERIFY stages to the diagram, and implement I3.
- [ ] Diagram updated, [ ] implemented

### C5. GUARDIAN output name and shape (P2, docs)
The earlier description said `GuardianClearance` with Approved or Rejected. [code] the type is `GuardianDecision` with three tiers and no rejection path. Make docs match, then see G3 for adding real rejection.
- [ ] Done

---

## Phase 2: Claims the code contradicts

### T1. ATHENA numbers can outweigh ORACLE (P0, [code])
Flaw: the "LLM cannot hallucinate physical safety" claim is true only for `safety_score`. `effectiveness_score` (weight 0.35) and `operator_effort` (weight 0.15) come from the LLM and enter `blended_rank`. `recommended_action` is `options[0]`, the top by that rank.
Check: in one saved incident, compare ORACLE's order with ATHENA's final order.
Fix: see I4 (effectiveness and effort come from catalog metadata, and the recommendation is chosen deterministically).
Pass if: changing the LLM's effectiveness or effort output can never change `recommended_action`.
- [ ] Done

### T2. ORACLE's winner is not enforced (P0, [code])
Flaw: the prompt says `recommended_action` must be the ORACLE winner unless a constraint forbids it. No schema field or check enforces this. ATHENA returns 2 to 3 of 6 actions, and the winner can be omitted.
Fix: after parsing, assert the ORACLE best action is in `options`, else reprompt (add a fourth validation phase in `athena/agent.py`).
Pass if: a unit test where the LLM omits the winner triggers a reprompt or a hard error.
- [ ] Done

### T3. `MissionConstraints` are not enforced anywhere (P0, [code])
Flaw: `athena/schemas.py` says GUARDIAN enforces the hard limits. GUARDIAN has five rules and none check `min_fuel_reserve_pct` or `max_operator_effort`. The constraints are only text in an LLM prompt.
Fix: see G2.
Pass if: a plan violating `max_operator_effort` cannot reach AUTOMATED_GUARDED.
- [ ] Done

### T4. GUARDIAN reads no telemetry and inspects no plan steps (P0, [code])
Fix: see G1 to G3. Also correct the docs so "validates against flight rules" is not claimed until true.
- [ ] Done

### T5. Safety score meaning has drifted (P1, [code])
Flaw: `guardian` and `athena` docstrings describe `safety_score = nominal_recovery_rate - mission_loss_rate`. The real formula is a multi-factor composite (SOC 0.40, affinity 0.25, variance 0.10, attitude 0.05, loss 0.20), range about -0.43 to +0.65. GUARDIAN's floor is 0.2 and ORACLE's unsafe threshold is 0.10. The floors were set for the old meaning.
Fix: decide what each floor should mean on the new scale, update every docstring, and add a unit test that pins the range.
Pass if: one document states the formula, the range, and the meaning of both thresholds.
- [ ] Done

### T6. ORACLE's simulation time base (P0, [code])
Flaw: `dt=23.0` hardcoded, comment contradicts the arithmetic (see V7). Physics that depend on `dt` (heater hysteresis, watchdog accumulator, thermal time constants) are quantized differently from the replay's `dt=1`.
Fix: put `dt` in `OracleRequest`, default it to the live simulation's `dt`, and pick `steps` to cover a stated horizon in seconds.
Pass if: ORACLE's horizon is stated in seconds in the UI, and results are stable when `dt` is halved (test it).
- [ ] Done

### T7. SENTINEL claims (P0, [code])
Flaws:
- `flagged_subsystem` hardcoded to `"ADCS"` in `score_telemetry_window`.
- Engine C is disabled there ("Dormant"), while `residual_update` WebSocket messages suggest another path exists (see V3).
- The spike detector hardcodes OPS-SAT magnetometer channel names (`CADC0872` to `CADC0874`).
- `sentinel_ensemble.json` sets the LSTM weight to 0 and no code loads it. No One-Class SVM exists in the files I read.
- The XGBoost model is trained on flatline features and cannot see your simulated ramps (your own `engine_b.py` docstring says so).
Fix: describe SENTINEL as it works (see docs), remove unused ensemble config or wire it in, and make subsystem attribution come from the detector that fired.
Pass if: README and UI text list only detectors that exist and run, and each alert reports the correct subsystem for all seven faults.
- [ ] Done

### T8. Static telemetry and UI display values (P0, carried over)
The UI honesty audit in `NEBIUS_SUBMISSION_GUIDE.md` section 9 is still open: derived outcome distribution, formula-generated SOC trajectory, fake progress animation, mislabeled ATHENA effectiveness, hardcoded VITALS and AnomalyLabels strings, hardcoded "Nominal" in SCRIBE.
Pass if: every number on screen is real backend data or is labeled "estimated" or "sample".
- [ ] Done

---

## Phase 3: Logic flaws

### L1. The emergency path runs last (P0)
Flaw: GUARDIAN Rule 1 (TTC under 5 minutes gives autonomous safing) fires only after SHERLOCK, ORACLE and ATHENA finish, which is tens of seconds of LLM and simulation latency.
Fix: see I1.
Pass if: safing is issued within 1 second of the SENTINEL alarm when deterministic TTC is under 5 minutes.
- [ ] Done

### L2. LLM output gates autonomy (P0, [code])
Flaw: `time_to_critical_estimate_minutes` and `urgency` come from SHERLOCK's LLM output, from a single snapshot with no trend, and they drive Rules 1 and 2.
Fix: see I1 (deterministic TTC), and log every disagreement between the model's number and the computed one.
Pass if: GUARDIAN's tier is identical across 10 runs of the same incident with different LLM sampling.
- [ ] Done

### L3. Rule 1 always sheds non-essential load (P1, [code])
Flaw: `_SAFING_ACTION_NAME` is fixed as `shed_nonessential_load`, whatever the fault. Your affinity table rates it 0.2 or lower for some faults, and GUARDIAN can record the `-999.0` sentinel as its safety score.
Check: for each fault, look up the affinity of `shed_nonessential_load` in `_FAULT_ACTION_AFFINITY`.
Fix: choose the safing action per fault class from a small, reviewed safing table (with a fallback), and never emit `-999.0` (use `None` and a status field).
Pass if: every fault has a documented safing action, and the schema allows `safety_score=None`.
- [ ] Done

### L4. ORACLE validates against the author's own beliefs (P1, [code])
Flaw: a hand-written affinity table supplies 25% of the score, and hand-written recovery modifiers drive the simulation. Agreement between them is not independent evidence. There is also no do-nothing baseline, and uncertainty is only sensor noise.
Fix: see I5.
- [ ] Done

### L5. Ground contact is modeled but unused (P1, [code])
`orbit.py` models ground contact windows. No decision uses it.
Fix: see I2.
- [ ] Done

### L6. The world pauses while agents think (P1, [inference])
Flaw: the stream freezes at the fault, so LLM latency costs no simulated time, and a real fault would keep evolving.
Fix: keep the simulation running during diagnosis, and show elapsed decision latency against TTC on screen.
Pass if: stream keeps advancing while SHERLOCK and ATHENA run, and the recovery plan shows the state at execution time, not at detection time.
- [ ] Done

### L7. Mandatory manual "Activate" buttons (P2)
Flaw: contradicts the "autonomous" framing.
Fix: add an autonomy mode setting (auto pipeline or step-by-step for demos). Default to auto for the video.
- [ ] Done

---

## Phase 4: Why the product feels like a toy

Root causes, each mapped to a fix:

1. Decisions do not change what happens next (I3).
2. One scripted fault at a time, no measured results (I7).
3. Incidents live only in browser memory (I6).
4. Numbers on screen are partly derived or hardcoded (T8).
5. The safety gate never says no (G3).

---

## Phase 5: Improvements

### I1. Fast path with deterministic time-to-critical (P0)
Build:
1. New module `backend/guardian/ttc.py`: for each monitored parameter in `sentinel/engine_b.RULES`, fit a linear trend over the last 30 frames and compute time to reach `critical` and `mission_loss`. TTC is the minimum across parameters. Return `(ttc_minutes, limiting_parameter, confidence)`.
2. `guardian.evaluate` takes `ttc_minutes` and `ttc_source` (`"deterministic"` or `"llm"`). Deterministic wins. Store both in the decision for audit.
3. On SENTINEL alarm, call GUARDIAN's fast path immediately. If TTC is under 5 minutes, execute safing now, and let SHERLOCK, ORACLE and ATHENA continue in parallel.
Pass if: unit tests cover flat, slow and fast trends. On all three replay faults, the safing timestamp is within 1 second of the alarm when TTC is under 5 minutes.
- [ ] Done

### I2. Use ground contact in the decision (P0)
Build:
1. Add `OrbitClock.minutes_to_next_contact(t)`.
2. Pass it into GUARDIAN. Write the policy in `docs/GUARDIAN_POLICY.md`, for example: if TTC is shorter than time to next contact, autonomy is justified for reversible actions with an adequate score. If a pass arrives before TTC and the action is irreversible, require approval.
3. Add the fields to `GuardianDecision`, and show them in the UI.
Pass if: a decision table test covers every combination of (TTC vs contact) x (reversible vs not) x (score above vs below floor).
- [ ] Done

### I3. Close the loop: execute, then verify (P0)
Build:
1. On approval, apply `get_recovery_modifiers(action)` to the live simulation from that timestamp. Switch the replay loop from pre-recorded Act 3 frames to a live `simulate_scenario_stream` continuing from the current state.
2. VERIFY stage: after a fixed horizon, classify the actual outcome with the same thresholds as `_classify_outcome`, and compare with ORACLE's predicted rates for that action.
3. If the outcome is worse than ORACLE's predicted range, emit an escalation event and raise the tier to manual.
4. Show predicted versus actual on screen and in SCRIBE.
Pass if: for each of the seven faults, the recovery visibly changes the telemetry, and a VERIFY record exists.
- [ ] Done

### I4. ATHENA becomes a constrained selector (P0)
Build:
1. Candidate set = ORACLE's top three actions by `safety_score`.
2. Move `effectiveness_prior` and `operator_effort` into `RECOVERY_CATALOG` metadata. The LLM no longer outputs them.
3. Compute `recommended_action` deterministically, with the LLM output limited to narrative, `contra_indications`, and fault-specific notes.
4. Build `procedure_steps` from a per-action template, and let the LLM add notes but not replace steps.
5. Keep validations from T2.
Pass if: T1 and T2 pass, and a test proves the recommendation is identical across LLM outputs.
- [ ] Done

### I5. Make ORACLE credible (P0)
Build:
1. Add a `no_action` baseline to the catalog, and report every action's improvement over it.
2. Sample uncertainty per run: severity ~ N(s, 0.1), action efficacy ~ U(0.7, 1.0), action delay ~ U(0, 60 s).
3. Return real `outcome_counts` and per-step SOC percentiles (p10, p50, p90), and send them to the UI (this also closes T8).
4. Add a rank-stability metric: how often the top action stays first across seeds.
5. Demote the affinity table to a documented prior with a small weight, or remove it.
6. Fix `dt` (T6).
Pass if: the UI shows real counts and trajectories, and the README reports rank stability.
- [ ] Done

### I6. Server-side incident store and SCRIBE (P1)
Build:
1. Append-only JSONL per incident in `data/incidents/<incident_id>.jsonl`, each record carrying the SHA-256 hash of the previous record.
2. SCRIBE runs server-side from that log, including model IDs, providers, token counts and latencies. Endpoint: `GET /api/incidents/{id}/runbook`.
3. CHRONICLE reads from the same store, and survives a browser refresh.
Pass if: refreshing the browser mid-incident loses nothing, and `verify_chain.py` detects a tampered record.
- [ ] Done

### I7. Evaluation harness (P0)
Build `scripts/eval/run_eval.py`:
- Matrix: 7 faults x 20 seeds x severities [0.5, 0.7, 0.9] for detection metrics, plus 20 fault-free runs.
- LLM-involved metrics on a smaller matrix (5 seeds per fault). Estimated token spend is roughly 35 incidents at about a cent each.
- Metrics: detection latency, false-alarm rate, root-cause accuracy (SHERLOCK against the true subsystem), ATHENA regret against ORACLE's best action, GUARDIAN tier correctness against the policy in I2, LLM attempts and latency.
- Output: `docs/EVAL_RESULTS.md` table, referenced from the README.
Pass if: one command reproduces the table.
- [ ] Done

### I8. Stretch (P2)
- [ ] Two overlapping faults (cascades)
- [ ] Operator workflow: saved incidents, roles, sign-off
- [ ] Real-data mode: replay OPS-SAT telemetry through SENTINEL
- [ ] "What if the operator picks option 2" comparison view

---

## Phase 6: GUARDIAN as a real gate

### G1. Give GUARDIAN telemetry (P1)
`evaluate()` also receives the current `SatelliteState`. Rules can then reference battery, comms and fuel.
- [ ] Done

### G2. Enforce `MissionConstraints` (P0)
Rule: reject or downgrade to manual if the plan's action breaks `min_fuel_reserve_pct` or `max_operator_effort`. Log which constraint fired.
Pass if: unit tests for each constraint.
- [ ] Done

### G3. Real rules that can say no (P1)
Add a `REJECTED` tier and rules such as:
- No plan that leaves the satellite without a comms path (check TT&C state and the action's target subsystems).
- No action on a subsystem outside `affected_subsystems` unless irreversibility rules pass.
- No second irreversible action within a stated interval.
Pass if: at least three rules can produce `REJECTED`, each covered by a test, and the UI shows a rejection with the reason.
- [ ] Done

### G4. Gate the operator's actual choice (P0)
Re-run `evaluate` on whichever option the operator selects (see V5), and record which option executed in SCRIBE.
- [ ] Done

---

## Tracking

| Phase | Tasks | Done |
|---|---|---|
| 0 Verify | V1 to V8 | 0 of 8 |
| 1 Contradictions | C1 to C5 | 0 of 5 |
| 2 Claims vs code | T1 to T8 | 0 of 8 |
| 3 Logic flaws | L1 to L7 | 0 of 7 |
| 5 Improvements | I1 to I8 | 0 of 8 |
| 6 GUARDIAN | G1 to G4 | 0 of 4 |

Suggested cut if time runs short before Oct 30: V1 to V7, C1, C2, C4, T1, T2, T6, T7, T8, L2, I1, I2, I3, I5, I7, G4. Everything else becomes "future work" in the README, and stating that honestly beats leaving the flaw unmentioned.
