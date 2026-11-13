import {cleanup, fireEvent, render, screen} from '@testing-library/react';
import {afterEach, expect, it, vi} from 'vitest';
import {Button} from "../../../../components/signal/Signal";
import {PaneViews} from "../PaneViews";
import {InspectorActions,PaneActions} from "../PreferencePane";
import {ConfirmVerb, StatusBar} from '../../index';
import {DeskWindowFrame} from '../../../components/DeskWindow';
afterEach(cleanup);
it('gives even a primary confirmation a safe first answer and its focus',()=>{
 render(<ConfirmVerb label="Apply" confirmLabel="Apply this change?" targetId="one" armedVariant="primary" onConfirm={vi.fn()}/>);
 fireEvent.click(screen.getByRole('button',{name:'Apply'}));
 expect(screen.getByRole('button',{name:'Cancel'})).toHaveFocus();
});
it('draws separate status meanings as separate parts',()=>{
 render(<StatusBar inPlace parts={[{text:'Listening'},{text:'Me'}]}/>);
 const parts=screen.getByRole('status').querySelectorAll(':scope > .kit-statusbar-item');
 expect([...parts].map(part=>part.textContent)).toEqual(['Listening','Me']);
});
it('makes the frame own a direct ink strip when an app declares nothing',()=>{
 const {container}=render(<DeskWindowFrame id="r2-clock" title="Clock" open onClose={()=>{}}><p>Body</p></DeskWindowFrame>);
 expect(container.querySelector('.desk-surface-foot > .kit-statusbar time')).toHaveAccessibleName('Time');
});

it('returns focus to Actions when its declared verb is folded',()=>{
 const adopted=document.adoptedStyleSheets;
 vi.stubGlobal('CSSStyleSheet',class{replaceSync(){}});
 document.adoptedStyleSheets=[];
 try{
  const {container}=render(<PaneActions><Button>First</Button><Button>Last</Button></PaneActions>);
  const last=screen.getByRole('button',{name:'Last'});last.style.display='none';
  fireEvent.change(container.querySelector('.surface-verb-row')!);
  const more=screen.getByRole('button',{name:'Actions'});
  vi.spyOn(more,'getClientRects').mockReturnValue([new DOMRect(0,0,80,32)] as unknown as DOMRectList);
  last.focus();expect(more).toHaveFocus();
 }finally{cleanup();document.adoptedStyleSheets=adopted;vi.unstubAllGlobals();}
});

it('does not replace an app view that deliberately has no picker tab',()=>{
 const change=vi.fn();
 render(<PaneViews label="Meeting contents" value="send" onChange={change} tabs={[{id:"summary",label:"Summary"}]}><p>Send meeting</p></PaneViews>);
 expect(change).not.toHaveBeenCalled();expect(screen.getByText("Send meeting")).toBeVisible();
});

it('keeps input focus when a question is present but not opened by the owner',()=>{
 render(<><input aria-label="Working words" autoFocus/><InspectorActions danger focusSafe={false} completion={{cancel:vi.fn(),primary:{label:"Allow",run:vi.fn()}}}/></>);
 expect(screen.getByRole('textbox',{name:'Working words'})).toHaveFocus();
});
