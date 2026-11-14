"""Observe actual list fitter geometry phases, native gestures and idle work."""
TRACE_LIST_LAYOUT = r'''() => {
  const trace = window.listLayoutTrace = {frames:[],outside:[],duringScroll:[],idle:0};
  let current = null;
  const styles = new WeakMap(), moving = new WeakSet();
  const listNode = node => node instanceof Element && (node.closest('.object-list') || node.matches('.surface-list-pane,.surface-list-pane-list'));
  const record = (kind,node,property) => {
    if (!listNode(node)) return;
    const event={kind,property};
    if (current) current.events.push(event);
    else if(kind==='write') trace.outside.push(event);
    const well=node.matches('.object-list-rows')?node:node.matches('.object-list')?node.querySelector('.object-list-rows'):null;
    if(kind==='write' && well && moving.has(well)) trace.duringScroll.push(event);
  };
  const rect=Element.prototype.getBoundingClientRect;
  Element.prototype.getBoundingClientRect=function(){record('read',this,'rect');return rect.call(this);};
  const computed=window.getComputedStyle;
  window.getComputedStyle=function(node,...args){record('read',node,'computed');return computed.call(this,node,...args);};
  for(const property of ['clientHeight','clientWidth','offsetHeight','clientTop','scrollHeight','scrollTop']) {
    let owner=Element.prototype,descriptor;
    while(owner && !(descriptor=Object.getOwnPropertyDescriptor(owner,property))) owner=Object.getPrototypeOf(owner);
    if(!descriptor?.get)continue;
    Object.defineProperty(owner,property,{...descriptor,get(){record('read',this,property);return descriptor.get.call(this);},...(descriptor.set?{set(value){record('write',this,property);return descriptor.set.call(this,value);}}:{})});
  }
  const style=Object.getOwnPropertyDescriptor(HTMLElement.prototype,'style');
  Object.defineProperty(HTMLElement.prototype,'style',{...style,get(){const result=style.get.call(this);styles.set(result,this);return result;}});
  for(const property of ['height','flex']) {
    const descriptor=Object.getOwnPropertyDescriptor(CSSStyleDeclaration.prototype,property);
    if(!descriptor?.set)continue;
    Object.defineProperty(CSSStyleDeclaration.prototype,property,{...descriptor,set(value){const node=styles.get(this);if(node?.matches('.object-list-rows'))record('write',node,property);return descriptor.set.call(this,value);}});
  }
  const setProperty=CSSStyleDeclaration.prototype.setProperty;
  CSSStyleDeclaration.prototype.setProperty=function(property,...args){const node=styles.get(this);if(property==='--surface-list-min'||property==='--object-list-row-floor'||(node?.matches('.object-list-rows')&&property==='height'))record('write',node,property);return setProperty.call(this,property,...args);};
  const raf=window.requestAnimationFrame;
  window.requestAnimationFrame=function(callback){return raf.call(this,time=>{const previous=current,frame={time,events:[],duration:0};current=frame;const start=performance.now();try{callback(time);}finally{frame.duration=performance.now()-start;current=previous;if(frame.events.length)trace.frames.push(frame);}});};
  document.addEventListener('scroll',event=>{if(event.target instanceof Element && event.target.matches('.object-list-rows'))moving.add(event.target);},true);
  document.addEventListener('scrollend',event=>moving.delete(event.target),true);
}'''

READ_LIST_TRACE = r'''() => {
 const trace=window.listLayoutTrace;
 const fitted=trace.frames.filter(frame=>frame.events.some(event=>event.kind==='write'));
 const thrash=fitted.filter(frame=>{let wrote=false;return frame.events.some(event=>{if(event.kind==='write')wrote=true;return wrote && event.kind==='read';});});
 const durations=fitted.map(frame=>frame.duration).sort((a,b)=>a-b);
 return {frames:fitted.length,readAfterWrite:thrash,outside:trace.outside,duringScroll:trace.duringScroll,
   durations:{p50:durations[Math.floor(durations.length*.5)]??0,p95:durations[Math.floor(durations.length*.95)]??0,max:durations.at(-1)??0},
   writes:trace.frames.flatMap(frame=>frame.events).filter(event=>event.kind==='write').length};
}'''
