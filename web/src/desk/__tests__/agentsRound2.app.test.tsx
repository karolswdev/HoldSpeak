/** Round two owner findings, on the existing hub recordings. */
import {fireEvent, render, screen, waitFor, within} from '@testing-library/react';
import {beforeEach,afterEach,it,expect,vi} from 'vitest';
import {hubWire} from './wire/hubWire';
const api=vi.hoisted(()=>({fetch:vi.fn(),request:vi.fn(),compact:false}));
vi.mock('../../lib/api',async original=>({...await original<typeof import('../../lib/api')>(),apiFetch:api.fetch,apiRequest:api.request}));
vi.mock('../../runtime/RuntimeBus',()=>({useRuntimeBus:()=>({state:'connected',subscribe:()=>()=>undefined}),useOptionalRuntimeBus:()=>null,useRuntimeFrame:()=>null}));
vi.mock('../useCompactViewport',async original=>({...await original<typeof import('../useCompactViewport')>(),useCompactViewport:()=>api.compact}));
vi.mock('../components/MicButton',()=>({MicButton:()=>null}));
import {ApiError} from '../../lib/api';
import {borrowGuideView} from '../walk/viewState';
import {ConductorWindow} from '../conductor/ConductorWindow';
import {__resetConductor} from '../conductor/store';
import {__resetLane} from '../lane/laneStore';
import {useAgentFlights,markLaunchSeen,fromWireFlight} from '../agentFlights';
import {useDeskWriteReceipt,dismissWriteFailure} from '../hooks/useWriteReceipt';
let group='agents-ag7';
let seenRefused = true;
let checked=false;
let refuseAnswer=false;
beforeEach(()=>{
 checked=false;refuseAnswer=false;api.compact=false; group='agents-ag7'; seenRefused = true; __resetConductor(); __resetLane(); dismissWriteFailure();
 useAgentFlights.setState({sessions:[],flights:[],loaded:false});
 vi.useFakeTimers({toFake:['Date']}); vi.setSystemTime(new Date(hubWire('../fixtures/agents-ag7/coders-sessions').captured_at));
 api.fetch.mockImplementation(async(url:string)=>{
  if(url.startsWith('/api/coders/sessions'))return hubWire(`../fixtures/${group}/coders-sessions${checked ? ".checked" : ""}`).wire;
  if(url==='/api/onboarding/agents')return hubWire('onboarding-agents.isolated').wire;
  if(url.startsWith('/api/coders/own-agents'))return {agents:[]};
  if(url.endsWith('/steer') && refuseAnswer) { const wire=hubWire('../fixtures/agents-ag2/answer.binding-refused').wire;throw new ApiError(409,String(wire.detail),wire); }
  if(url.includes('launch_ag0_done/lane'))return hubWire('../fixtures/agents-ag0/lane.done').wire;
  if(url.includes('/seen')) {if (seenRefused) throw new Error('seen write refused'); return hubWire('../fixtures/agents-ag0/seen').wire;}
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
it('does not mark an unchanged permission seen or ask the owner to repair that read',async()=>{
 render(<><Fallback/><ConductorWindow/></>);await select('launch:launch_ag7_held');
 await screen.findByTestId('conductor-held-call');
 expect(api.fetch.mock.calls.some(([url])=>String(url).includes('/seen'))).toBe(false);
 expect(screen.queryByRole('alert')).toBeNull();
});
it('keeps New after a refused automatic mark and clears it only after acknowledgement',async()=>{
 const wire=hubWire('../fixtures/agents-ag0/coders-sessions').wire;
 useAgentFlights.setState({flights:wire.flights.map(fromWireFlight),sessions:[],loaded:true});
 render(<Fallback/>);
 await markLaunchSeen('launch_ag0_done',null);
 expect(useAgentFlights.getState().flights.find(f=>f.launchId==='launch_ag0_done')?.isNew).toBe(true);
 expect(screen.getByTestId('fallback')).toBeEmptyDOMElement();
 seenRefused=false;
 await markLaunchSeen('launch_ag0_done',null);
 expect(useAgentFlights.getState().flights.find(f=>f.launchId==='launch_ag0_done')?.isNew).toBe(false);
});
it('does not apply a late seen acknowledgement to a newer result',async()=>{
 const original=hubWire('../fixtures/agents-ag0/coders-sessions').wire.flights.map(fromWireFlight);
 const newer=hubWire('../fixtures/agents-ag3/coders-sessions.answered').wire.flights.map(fromWireFlight);
 useAgentFlights.setState({flights:original,sessions:[],loaded:true});
 let acknowledge!: (body: unknown)=>void;
 api.fetch.mockReturnValueOnce(new Promise(resolve=>{acknowledge=resolve;}));
 const pending=markLaunchSeen('launch_ag0_done',null);
 useAgentFlights.setState({flights:newer});
 acknowledge(hubWire('../fixtures/agents-ag0/seen').wire);
 await pending;
 expect(useAgentFlights.getState().flights.find(f=>f.launchId==='launch_ag0_done')?.isNew).toBe(true);
});
it('names the selected task in its question and gives the cancel act distinct words',async()=>{
 group='agents-ag8';render(<ConductorWindow/>);await select('launch:launch_ag8_ask');
 fireEvent.click(await screen.findByTestId('conductor-bar-stop'));
 expect(screen.getByRole('region',{name:'Stop Write the on-call note?'})).toBeTruthy();
 const queue=document.querySelector('[data-testid="agents-list"] [data-object-id^="queue:"]')!;fireEvent.click(queue);
 expect(await screen.findByTestId('conductor-bar-cancel')).toHaveTextContent('Cancel task');
 fireEvent.click(await screen.findByTestId('conductor-bar-cancel'));
 const question=screen.getByRole('region',{name:/Cancel Tidy the ledger runbook\?/});
 expect(within(question).getByRole('button',{name:'Keep it'})).toHaveFocus();
 expect(within(question).getByRole('button',{name:'Cancel task'})).toBeTruthy();
});

it('keeps launch facts in the question and answer body',async()=>{
 group='agents-ag8';render(<ConductorWindow/>);await select('launch:launch_ag8_ask');
 const question=await screen.findByTestId('conductor-ask-row');
 expect(await within(question).findByText('Branch')).toBeTruthy();
 expect(within(question).getByText('Launched')).toBeTruthy();
 const answer=within(question).getByTestId('conductor-answer');
 expect(answer.compareDocumentPosition(within(question).getByText('Branch'))&Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
});

it('omits Files when the launch has no local worktree and no pull request',async()=>{
 group='agents-ag8';render(<ConductorWindow/>);await select('launch:launch_ag8_ask');
 await waitFor(()=>expect(api.fetch).toHaveBeenCalledWith(expect.stringContaining('launch_ag8_ask/lane')));
 expect(screen.queryByRole('tab',{name:'Files'})).toBeNull();
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

it('keeps both mast facts in compact words',async()=>{
 api.compact=true;group='agents-ag8';render(<ConductorWindow/>);
 await select('launch:launch_ag8_ask');
 expect(document.querySelector('.surface-mast-facts')).toHaveTextContent('6 sessions · 3 here');
});

it('keeps the track and latest activity with Remove and closes that question when a step opens',async()=>{
 group='agents-ag0';checked=true;render(<ConductorWindow/>);await select('launch:launch_ag0_done');
 fireEvent.click(await screen.findByTestId('conductor-bar-remove'));
 const question=await screen.findByRole('region',{name:/Remove Draft test scaffolding for flags/});
 expect(question).toBeTruthy();
 const track=screen.getByRole('tablist',{name:'Agent progress'});
 expect(screen.getByRole('log',{name:'Latest activity'})).toHaveTextContent('Ran · git status');
 fireEvent.click(within(track).getByRole('tab',{name:/Step 1:/}));
 expect(screen.queryByRole('region',{name:/Remove Draft test scaffolding for flags/})).toBeNull();
 expect(screen.getByRole('tab',{name:'Facts'})).toHaveAttribute('aria-selected','true');
 expect(api.fetch.mock.calls.some(([url])=>String(url).endsWith('/remove'))).toBe(false);
});
it('reads the question again after a binding refusal without sending the retained answer twice',async()=>{
 group='agents-ag8';refuseAnswer=true;render(<ConductorWindow/>);await select('launch:launch_ag8_ask');
 const input=await screen.findByTestId('agent-row-answer-field');
 fireEvent.change(input,{target:{value:'Keep Jordan'}});
 fireEvent.click(screen.getByTestId('conductor-answer'));
 expect(await screen.findByTestId('agent-row-refusal')).toHaveTextContent('The answer was not sent; read the question again.');
 fireEvent.click(screen.getByRole('button',{name:'Read again'}));
 await waitFor(()=>expect(screen.queryByTestId('agent-row-refusal')).toBeNull());
 expect(input).toHaveValue('Keep Jordan');
 expect(api.fetch.mock.calls.filter(([url])=>String(url).endsWith('/steer'))).toHaveLength(1);
});
