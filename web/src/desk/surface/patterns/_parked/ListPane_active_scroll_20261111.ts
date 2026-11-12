// Parked: a newly opened form must start at its first row; the list yields instead.
export function revealActiveEditor(seat: HTMLElement) {
      // Fitting the list or a failure notice can shrink an active editor.
      // Scroll its own field well, without moving the pane or window.
      const active = document.activeElement;
      const fields = active instanceof HTMLElement && seat?.parentElement?.contains(active)
        ? active.closest<HTMLElement>(".surface-inspector-fields") : null;
      if (fields && active instanceof HTMLElement) {
        const control = active.getBoundingClientRect(), well = fields.getBoundingClientRect();
        if (control.bottom > well.bottom) fields.scrollTop += control.bottom - well.bottom;
        else if (control.top < well.top) fields.scrollTop -= well.top - control.top;
      }
}
