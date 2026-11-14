"""The list's painted row boundaries, independent of a particular row height."""
WHOLE_ROWS = r'''el => {
  const result=[];
  for(const well of el.querySelectorAll('.object-list-rows')) {
    const b=well.getBoundingClientRect(); if(!b.width||!b.height)continue;
    const top=b.top+well.clientTop,bottom=top+well.clientHeight;
    const rows=[...well.querySelectorAll('.object-list-row')].map(row=>{const r=row.getBoundingClientRect();return {id:row.dataset.objectId,top:r.top,bottom:r.bottom,selected:row.getAttribute('aria-selected')==='true'};});
    const headings=[...well.querySelectorAll('.object-list-group-label')].map(el=>el.getBoundingClientRect());
    const covered=Math.max(0,...headings.filter(r=>r.top<=top+1&&r.bottom>top).map(r=>r.bottom-top));
    const visible=rows.filter(row=>row.bottom>top+covered+1&&row.top<bottom-1);
    result.push({label:well.closest('[role=grid]')?.getAttribute('aria-label'),top,bottom,whole:visible.filter(row=>row.top>=top+covered-1&&row.bottom<=bottom+1).length,
      partial:visible.filter(row=>row.top<top+covered-1||row.bottom>bottom+1),selected:rows.filter(row=>row.selected),
      selectedWhole:rows.filter(row=>row.selected).every(row=>row.top>=top+covered-1&&row.bottom<=bottom+1)});
  }
  return result;
}'''

def row_faults(win, state, minimum=0):
    readings=win.evaluate(WHOLE_ROWS)
    return [(state,row) for row in readings if row['partial'] or not row['selectedWhole'] or row['whole']<minimum]
