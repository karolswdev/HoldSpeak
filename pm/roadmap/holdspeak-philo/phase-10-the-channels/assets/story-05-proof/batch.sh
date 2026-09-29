#!/bin/zsh
# PHILO-10-05: every retained atlas run of the story, serially by batch (each
# batch runs its cases 4 at a time, one hub each). Labels are written once.
# Each step's status is logged ("=== <step> exit N"); a step's nonzero exit is
# a not-pass run, read in the evidence, not a driver error.
cd ${0:A:h}/../../../../../..
P=pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-05-proof
G=docs/internal/philo/graph
W=$PWD
for step in "$@"; do
  echo "=== $step $(date -u +%H:%M:%SZ)"
  case $step in
    p10) $P/rig_phase.sh p10-merged 4 $G/atlas-phase10.json ;;
    p789) $P/rig_phase.sh p789-merged 4 $G/atlas-phase7.json $G/atlas-phase8.json $G/atlas-phase9.json $G/atlas-phase9-steward.json ;;
    base) OBS_ONLY=1 $P/rig_phase.sh base-merged 4 $G/atlas.json $G/atlas-phase3.json ;;
    p789-before) OBS_ONLY=1 ROOT=$W/.tmp/main-dce3afa9 KEEP_RIG=1 $P/rig_phase.sh p789-dce3afa9 4 $G/atlas-phase7.json $G/atlas-phase8.json $G/atlas-phase9.json $G/atlas-phase9-steward.json ;;
    base-before) OBS_ONLY=1 ROOT=$W/.tmp/main-dce3afa9 KEEP_RIG=1 $P/rig_phase.sh base-dce3afa9 4 $G/atlas.json $G/atlas-phase3.json ;;
    red) ROOT=$W/.tmp/main-98ea2cfa $P/rig_phase.sh red-98ea2cfa 4 $G/atlas-phase10.json ;;
  esac
  echo "=== $step exit $? $(date -u +%H:%M:%SZ)"
done
