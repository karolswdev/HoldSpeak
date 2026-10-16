// Direction only, shared production library with declared sample content.
import {useState} from 'react';
import {createRoot} from 'react-dom/client';
import '@w/styles/global.css';
import '@w/styles/react-app.css';
import '@w/desk/desk.css';
import {RuntimeBusProvider} from '@w/runtime/RuntimeBus';
import {DeskWindowFrame} from '@w/desk/components/DeskWindow';
import {Button} from '@w/components/signal/Signal';
import {PadGadget,FoldGadget,LampGadget} from '@w/desk/surface/gadgets';
import {SurfaceTraffic,SurfaceTrafficTurn,SurfaceWell,SurfaceState} from '@w/desk/surface/Surface';
import {SurfaceFooter} from '@w/desk/surface/SurfaceFooter';
import {FilterTokens} from '@w/desk/surface/FilterTokens';
import {Material} from '@w/desk/surface/Material';
import './canvas.css';
const noop=()=>{};
const face=new URLSearchParams(location.search).get('face')||'thread';
function Direction(){const[text,setText]=useState(''),[mode,setMode]=useState('review');const thread=face==='thread';return <RuntimeBusProvider><main className="desk-next direction-floor">
<DeskWindowFrame id="conversation-direction" label={thread?'Release review':'Ask AI'} title={thread?'Release review':'Ask AI'} glyph={thread?'▤':'✦'} minW={320} defaultW={660} defaultH={face==='compose'?360:660} open entrance={false} onClose={noop} className="desk-surface-window">
<div className="desk-surface-body direction-body">
{thread?<div className="direction-mode"><FilterTokens label="Thread mode" value={mode} onChange={setMode} options={[{value:'review',label:'Architecture review'},{value:'plan',label:'Plan'},{value:'write',label:'Write'},{value:'explore',label:'Explore'}]}/></div>:null}
{face!=='compose'?<div className="direction-reading"><SurfaceTraffic showEmpty={false}><SurfaceTrafficTurn prefix="You"><p>What needs to happen before we release the migration?</p></SurfaceTrafficTurn><SurfaceTrafficTurn prefix={thread?'Assistant':'Answer'} meta={<span className="surface-token">Qwen · LAN</span>} verbs={<><Button dense variant="ghost" onClick={noop}>Copy</Button>{thread?<><Button dense variant="ghost" onClick={noop}>Keep</Button><Button dense variant="ghost" onClick={noop}>Fork</Button></>:null}</>}><Material>{'## Release gate\n\nConfirm the rollback owner and complete the reconciliation checks.\n\n- **Jordan:** verify the restore path.\n- **Mira:** review the reconciliation results.\n\nKeep the gate closed until both checks pass.'}</Material></SurfaceTrafficTurn></SurfaceTraffic></div>:<div className="direction-empty"/>}
{thread||face==='compose'?<div className="direction-composer"><PadGadget label={thread?'Thread message':'Ask about your work'} value={text} onChange={setText} rows={3} placeholder={thread?'Continue this conversation':'Ask about your work'} micDraftScope="direction"/><div className="direction-send"><FoldGadget title={thread?'Attach':'Add notes'}><span className="surface-token">Release checklist</span></FoldGadget><Button variant="primary" disabled={!text.trim()} onClick={noop}>{thread?'Send':'Ask'}</Button></div><div className="direction-engine"><LampGadget on tone="ok" label="Qwen · LAN"/></div></div>:null}
</div><div className="desk-surface-foot"><SurfaceFooter receipt={<span className="surface-token">{thread?'Ready':face==='compose'?'':'Answered · Qwen'}</span>} verbs={face==='compose'?<Button dense variant="ghost" onClick={noop}>Cancel</Button>:thread?<Button dense variant="ghost" onClick={noop}>Close</Button>:<><Button dense variant="ghost" onClick={noop}>Bin</Button><Button dense variant="primary" onClick={noop}>Keep</Button></>}/></div>
</DeskWindowFrame>
{face==='notice'?<aside className="direction-notice"><div className="direction-notice-source"><LampGadget on tone="warn" label="Conductor"/><Button dense variant="ghost" onClick={noop}>Dismiss</Button></div><strong>Coder needs an answer</strong><SurfaceWell><Material>Which release gate should I use?</Material></SurfaceWell><div className="direction-notice-actions"><Button dense variant="primary" onClick={noop}>Review source</Button></div></aside>:null}
</main></RuntimeBusProvider>}
createRoot(document.getElementById('root')!).render(<Direction/>);
