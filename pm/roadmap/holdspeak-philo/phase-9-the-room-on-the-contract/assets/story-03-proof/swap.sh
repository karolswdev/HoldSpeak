#!/bin/zsh
# swap.sh base [ref] | branch -- put a ref's copies of this story's product
# files in place (default HEAD's parent line: the story's base, main + story
# 02; its web files are origin/main's apart from story 02's own), the branch
# copies saved first; or put the saved branch copies back. No git verb moves
# the tree: `git show <ref>:<path>` only reads.
cd ${0:A:h}/../../../../../..
save=.tmp/philo9-03/branch-files
ref=${2:-aeae7bd8}
files=(holdspeak/services/project_service.py
  web/src/desk/chair/ChairHome.tsx web/src/desk/components/SystemShade.tsx web/src/desk/components/inline-editor.css
  web/src/desk/shell.ts web/src/desk/surface/egress.ts web/src/desk/surface/gadgets.css
  web/src/desk/surface/patterns/progress-plan.css web/src/desk/surface/patterns/provenance.css web/src/desk/surface/surface.css web/src/styles/global.css
  web/src/features/project-room/ProjectRoomCore.tsx web/src/features/project-room/project-room.css
  web/src/features/project-room/recall/RecallFace.tsx
  web/src/features/project-room/steward/StewardPosture.tsx web/src/features/project-room/steward/steward-posture.css
  web/src/features/project-room/steward/useStewardController.ts
  web/src/features/project-room/update/UpdatePosture.tsx web/src/features/project-room/update/api.ts
  web/src/features/project-room/update/model.ts web/src/features/project-room/update/update-posture.css
  web/src/features/project-room/update/useUpdateController.ts web/src/pages/cores/history/MeetingReview.tsx)
if [[ $1 == base ]]; then
  for f in $files; do mkdir -p $save/${f:h}; cp $f $save/$f; git show $ref:$f > $f; done
else
  for f in $files; do cp $save/$f $f; done
fi
(cd web && npm run build 2>&1 | tail -1)
