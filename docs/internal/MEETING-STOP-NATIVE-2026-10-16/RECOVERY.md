# Meeting stop recovery — 2026-10-16

The owner confirmed the existing hub hung while stopping a meeting. Root sampled
that exact process: the web uvloop thread waited in PortAudio
`FinishStoppingStream → AudioOutputUnitStop → AudioDeviceStop → HALB_Mutex::Lock`.
Even health requests timed out. This is an observed native shutdown hang; the
reason CoreAudio did not release its mutex is unknown.

The capture journal had continuously written both tracks. Root made a complete
backup, verified every file hash, and confirmed no changes during the backup or
shutdown. The old manifest checkpoint lagged the complete files by about three
seconds. Before restarting, root retained the original manifest and both full
tracks. Root attempted graceful termination, then terminated the exact wedged
process after it did not release its port.

After termination, root checked both complete tracks for four-byte alignment,
finite float samples, and unchanged hashes. Root fsynced them and atomically
promoted the manifest's durable byte lengths to their validated full lengths.
The existing capture recovery API finalized the same meeting and its stop fence.
Root finalized the journal metadata after the API completed. No transcript or
recording content was printed, no capture was discarded, and no provider was
called for this recovery.

The restarted hub served merged main (including the moon-size correction), build
`0ce82ada178bf199`. Health, Desk, Conductor and Models returned HTTP200; runtime
reported no active meeting, idle voice, loaded base speech model with no error,
and available global hotkey. The recovered meeting API reported finalized
capture, no capture failure, and an end time. This verifies retention and saved
meeting state; it does not claim the untranscribed tail was transcribed.

Private local recovery records and full backup remain under
`.tmp/meeting-stop/` in this worktree. The original capture remains under the
owner's normal capture directory. Normal delivery/recovery used owner state;
all implementation checks use isolated HOME and native state disabled.
