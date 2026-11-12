/** Round two owner findings, on the existing hub recordings. */
import {fireEvent, render, screen, waitFor, within} from '@testing-library/react';
import {beforeEach,afterEach,it,expect,vi} from 'vitest';
import {hubWire} from './wire/hubWire';
const api=vi.hoisted(()=>({fetch:vi.fn(),request:vi.fn()}));
vi.mock('../../lib/api',async original=>({...await original<typeof import('../../lib/api')>(),apiFetch:api.fetch,apiRequest:api.request}));
vi.mock('../../runtime/RuntimeBus',()=>({useRuntimeBus:()=>({state:'connected',subscribe:()=>()=>undefined}),useOptionalRuntimeBus:()=>null,useRuntimeFrame:()=>null}));
vi.mock('../components/MicButton',()=>({MicButton:()=>null}));
import {borrowGuideView} from '../walk/viewState';
import {ConductorWindow} from '../conductor/ConductorWindow';
import {__resetConductor} from '../conductor/store';
import {__resetLane} from '../lane/laneStore';
import {useAgentFlights} from '../agentFlights';
import {useDeskWriteReceipt,dismissWriteFailure} from '../hooks/useWriteReceipt';
let group='agents-ag7';
let seenRefused = true;
beforeEach(()=>{
 group='agents-ag7'; seenRefused = true; __resetConductor(); __resetLane(); dismissWriteFailure();
 useAgentFlights.setState({sessions:[],flights:[],loaded:false});
 vi.useFakeTimers({toFake:['Date']}); vi.setSystemTime(new Date(hubWire('../fixtures/agents-ag7/coders-sessions').captured_at));
 api.fetch.mockImplementation(async(url:string)=>{
  if(url.startsWith('/api/coders/sessions'))return hubWire(`../fixtures/${group}/coders-sessions`).wire;
  if(url==='/api/onboarding/agents')return hubWire('onboarding-agents.isolated').wire;
  if(url.startsWith('/api/coders/own-agents'))return {agents:[]};
  if(url.includes('/seen')) {if (seenRefused) throw new Error('seen write refused'); return {};}
  if(url.includes('launch_ag7_held/lane'))return hubWire('../fixtures/agents-ag7/lane.held').wire;
  if(url.includes('launch_ag8_ask/lane'))return hubWire('../fixtures/agents-ag2/lane.asks').wire;
  return {};
 });
});
afterEach(()=>{__resetLane();dismissWriteFailure();vi.useRealTimers();});
function Fallback(){return <aside data-testid="fallback">{useDeskWriteReceipt({fallback:true}).receipt}</aside>;}
async function select(id:string){await waitFor(()=>expect(document.querySelector(`[data-testid="agents-list"] [data-object-id="${id}"]`)).toBeTruthy());fireEvent.click(document.querySelector(`[data-testid="agents-list"] [data-object-id="${id}"]`)!);}
it('puts Deny first and focuses it, with the meaning of Allow beside the command',async()=>{
 render(<ConductorWindow/>);await select('launch:launch_ag7_held');
 const deny=await screen.findByTestId('conductor-deny'), allow=screen.getByTestId('conductor-approve');
 expect(deny.compareDocumentPosition(allow)&Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
 await waitFor(()=>expect(deny).toHaveFocus());expect(allow.className).not.toMatch(/btn--(?:primary|brass)/);
 expect(screen.getByText('The agent runs this command one time.')).toBeTruthy();
});
it('draws selected verbs once in the verb row, and only answers in the question',async()=>{
 group='agents-ag8';render(<ConductorWindow/>);await select('launch:launch_ag8_ask');
 await screen.findByTestId('conductor-ask-row');
 const pane=screen.getByTestId('agents-pane');
 expect(within(pane).queryByRole('button',{name:'Open terminal'})).toBeNull();
 expect(within(pane).queryByRole('button',{name:'Tell it'})).toBeNull();
 expect(within(pane).queryByRole('button',{name:'Stop'})).toBeNull();
 expect(screen.getByTestId('conductor-bar-terminal')).toBeTruthy();
});
it('seats a refused seen write inside Agents and suppresses the system-band fallback',async()=>{
 render(<><Fallback/><ConductorWindow/></>);await select('launch:launch_ag7_held');
 await screen.findByText('Could not mark it seen');
 expect(within(screen.getByTestId('fallback')).queryByText('Could not mark it seen')).toBeNull();
 const host=screen.getByTestId('conductor-window');
 expect(within(host).getByRole('alert')).toHaveTextContent('Could not mark it seen');
 expect(within(host).getByRole('button',{name:'Try again'})).toBeEnabled();
 seenRefused = false; fireEvent.click(within(host).getByRole('button',{name:'Try again'}));
 await waitFor(()=>expect(within(host).queryByRole('alert')).toBeNull());
});
it('names the selected task in its question and gives the cancel act distinct words',async()=>{
 group='agents-ag8';render(<ConductorWindow/>);await select('launch:launch_ag8_ask');
 fireEvent.click(await screen.findByTestId('conductor-bar-stop'));
 expect(screen.getByRole('region',{name:'Stop Write the on-call note?'})).toBeTruthy();
 const queue=document.querySelector('[data-testid="agents-list"] [data-object-id^="queue:"]')!;fireEvent.click(queue);
 fireEvent.click(await screen.findByTestId('conductor-bar-cancel'));
 const question=screen.getByRole('region',{name:/Cancel Tidy the ledger runbook\?/});
 expect(within(question).getByRole('button',{name:'Keep it'})).toHaveFocus();
 expect(within(question).getByRole('button',{name:'Cancel task'})).toBeTruthy();
});

it('shows the list for the first guide step and restores the borrowed inspector',async()=>{
 render(<ConductorWindow/>);await select('launch:launch_ag7_held');
 const pane=document.querySelector('.surface-list-pane')!;
 expect(pane).toHaveAttribute('data-detail-open');
 let restore: () => void = () => undefined;
 const {act}=await import('@testing-library/react');
 act(()=>{restore=borrowGuideView('conductor');});
 expect(pane).not.toHaveAttribute('data-detail-open');
 act(()=>restore());expect(pane).toHaveAttribute('data-detail-open');
});
