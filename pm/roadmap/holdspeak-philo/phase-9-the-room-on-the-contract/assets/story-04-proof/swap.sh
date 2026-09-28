#!/bin/zsh
# swap.sh main|branch — put main's product web files in place (branch copies
# saved first), or put the saved branch copies back. No git verb moves the tree.
cd ${0:A:h}/../../../../../..
save=.tmp/philo9-04/branch-web
files=(web/src/desk/components/DeskListView.tsx web/src/desk/components/DeskMenu.tsx
       web/src/desk/components/DeskSortableTable.tsx web/src/desk/components/chrome-menus.css
       web/src/desk/components/list-view.css web/src/styles/global.css web/src/styles/tokens.css)
if [[ $1 == main ]]; then
  for f in $files; do mkdir -p $save/${f:h}; cp $f $save/$f; git show origin/main:$f > $f; done
else
  for f in $files; do cp $save/$f $f; done
fi
(cd web && npm run build 2>&1 | tail -1)
