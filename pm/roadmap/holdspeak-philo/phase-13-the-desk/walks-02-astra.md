# H-A1 — backend lifecycle walks

**DRAFT — UNCHECKED — awaiting Muad'Dib.** These are HTTP lifecycle proofs with browser reload. The pictures show the desk shell; they do not certify the Parked filter or Restore Button.

| Case and viewport | Verdict | Observation |
|---|---|---|
| meeting-1440-final | pass | [record](assets/story-02-backend/final/meeting-1440-final/20261002T034710Z-case.p13.meeting.park_restore-astra-1440/observation.json) |
| meeting-393-final | pass | [record](assets/story-02-backend/final/meeting-393-final/20261002T034814Z-case.p13.meeting.park_restore-astra-393/observation.json) |
| workbench-1440-final | pass | [record](assets/story-02-backend/final/workbench-1440-final/20261002T034924Z-case.p13.workbench.park_restore-astra-1440/observation.json) |
| workbench-393-final | pass | [record](assets/story-02-backend/final/workbench-393-final/20261002T035047Z-case.p13.workbench.park_restore-astra-393/observation.json) |

Each actual atlas case ran in its own invocation and HOME. Astra read the observation and both shots before the next run. The 393 runs use native touch for their desk entry; park and restore use the real HTTP routes. The final trigger reloads the browser after restore. Both Workbench parked cycles restart the hub; the Meeting parked cycle does so once.

The first Meeting attempt expected the VTT parser to strip `Blair:`; the real importer retains that prefix. The second and third attempts found screenshot readiness gaps. Those calibration records remain byte-identical under `calibration/`. Final cases explicitly wait for the desk after each reload. The wait uses the schema timeout_s field; all four cases were rerun after correcting that field.

The VTT import proves retention of its three transcript segments. Non-empty summary, action, artifact and project-link retention is proved by the real stored-state producer test. Workbench live cases retain two produced IDs and their saved content. The real-runner test separately proves artifact, run and receipt links through park, DB reopen and restore.

No inference engine or real send ran in these live cases. All DB paths are inside the recorded run HOME. The pictures do not prove the 8-second client removal window, receipt branches or Parked/Restore face; these remain A1-F acceptance work.
