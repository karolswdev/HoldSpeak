"""Facts about the rendered Send form, shared by its real-hub glass cases."""
from typing import Any


def send_face_facts(root: Any, *, six_lines: bool = False) -> dict[str, Any]:
    facts = root.evaluate("""root => {
      const shown = e => e && e.checkVisibility() && e.getBoundingClientRect().height > 0;
      const find = s => [...root.querySelectorAll(s)].find(shown);
      const word = find('[data-testid=send-destination-word]');
      const actions = word?.closest('.surface-inspector-actions');
      const face = find('[data-send=face]');
      const bounds = e => {
        if(!e) return null;
        const r=e.getBoundingClientRect(); let top=Math.max(0,r.top),bottom=Math.min(innerHeight,r.bottom),left=Math.max(0,r.left),right=Math.min(innerWidth,r.right);
        for(let p=e.parentElement;p;p=p.parentElement) {
          const s=getComputedStyle(p),b=p.getBoundingClientRect();
          if(/auto|scroll|hidden|clip/.test(s.overflowY)){top=Math.max(top,b.top);bottom=Math.min(bottom,b.bottom);}
          if(/auto|scroll|hidden|clip/.test(s.overflowX)){left=Math.max(left,b.left);right=Math.min(right,b.right);}
        }
        return {top:r.top,bottom:r.bottom,height:r.height,width:r.width,visibleHeight:Math.max(0,bottom-top),visibleWidth:Math.max(0,right-left)};
      };
      const row = [...root.querySelectorAll('.gadget-row')].find(e => shown(e) && e.querySelector('[aria-label=Destination]'));
      const heading = find('[data-send=preview] .surface-pane-group > h3');
      const payload = find('[data-send=preview] .surface-well-body');
      const tabs = find('[role=tablist][aria-label="Send to"]');
      const form = face?.querySelector('.surface-inspector-form > .surface-inspector-fields');
      const props=['backgroundColor','borderTopColor','borderTopWidth','borderRadius','color','fontFamily','fontSize','fontWeight','lineHeight','paddingTop','paddingRight','paddingBottom','paddingLeft','minHeight','boxShadow'];
      const style = e => e ? Object.fromEntries(props.map(k=>[k,getComputedStyle(e)[k]])) : null;
      const add = find('[data-testid=send-add-destination]'), choice = row?.querySelector('.gadget-cycle');
      const ancestors=[]; for(let e=word;e;e=e.parentElement){const s=getComputedStyle(e);ancestors.push({cls:e.className,box:bounds(e),display:s.display,flex:s.flex,minHeight:s.minHeight,height:s.height,overflow:s.overflow});}
      const documentRow = [...root.querySelectorAll('.gadget-row')].find(e => shown(e) && e.querySelector('[aria-label=Document]'));
      return {document:bounds(documentRow),ancestors,paper:face ? getComputedStyle(face).backgroundColor : null,word:word?.textContent,wordBounds:bounds(word),completion:bounds(actions),destination:bounds(row),tabs:bounds(tabs),heading:bounds(heading),payload:bounds(payload),
        lineHeight:payload ? parseFloat(getComputedStyle(payload).lineHeight) : null,
        form:form ? {scrollTop:form.scrollTop,scrollHeight:form.scrollHeight,height:form.clientHeight} : null,
        addTrailing: Boolean(add && row?.contains(add) && choice && add.getBoundingClientRect().left >= choice.getBoundingClientRect().right+6),
        styles:{cancel:style(actions?.querySelector('button:not(.btn--primary):not(.surface-completion-leading button)')),send:style(actions?.querySelector('.btn--primary')),add:style(add)}};
    }""")
    assert facts["word"], facts
    for name in ("wordBounds", "completion"):
        box = facts[name]
        assert box and box["visibleHeight"] >= box["height"] - 1 and box["visibleWidth"] >= box["width"] - 1, facts
    if facts["payload"]:
        assert facts["tabs"] and facts["heading"] and facts["destination"], facts
        if facts["document"]:
            assert facts["document"]["bottom"] <= facts["tabs"]["top"] + 1, facts
        assert facts["tabs"]["bottom"] <= facts["destination"]["top"] + 1, facts
        assert facts["destination"]["bottom"] <= facts["heading"]["top"] + 1, facts
        assert facts["heading"]["bottom"] <= facts["payload"]["top"] + 1, facts
        assert facts["payload"]["bottom"] <= facts["completion"]["top"] + 1, facts
        assert facts["addTrailing"], facts
        if six_lines:
            assert facts["payload"]["visibleHeight"] >= 6 * facts["lineHeight"], facts
            assert facts["form"]["scrollTop"] == 0 and facts["form"]["scrollHeight"] <= facts["form"]["height"] + 1, facts
    return facts
