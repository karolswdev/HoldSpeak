import {cleanup, fireEvent, render, screen} from '@testing-library/react';
import {afterEach, expect, it, vi} from 'vitest';
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
