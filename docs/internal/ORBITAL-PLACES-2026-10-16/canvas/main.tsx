import {createRoot} from 'react-dom/client';
import '@w/styles/global.css'; import '@w/styles/react-app.css'; import '@w/desk/desk.css';
import {DeskIcon,IconGrid} from '@w/desk/surface'; import {spriteUrl} from '@w/desk/sprites';
import mars from '@w/desk/gl/textures/mars-viking.jpg'; import stars from '@w/desk/gl/textures/jupiter-starfield.jpg';
import './canvas.css';
const planet=new URLSearchParams(location.search).get('planet')||'mars';const noop=()=>{};
createRoot(document.getElementById('root')!).render(<main className={`desk-next orbit-direction ${planet}`}>
<div className="cosmos" style={{backgroundImage:`linear-gradient(125deg,#02051135,#02040970),url(${stars})`}}>
{planet==='saturn'?<div className="saturn-system"><div className="rings back"/><div className="planet saturn-globe"/><div className="rings front"/></div>:<div className="planet mars-globe" style={{backgroundImage:`url(${mars})`}}/>}
<div className="moon inner"/><div className="moon outer"/>
</div><div className="drawers"><IconGrid label="Desk drawers">{['Meetings','Personal','Reference'].map(name=><DeskIcon key={name} id={name} kind="directory" name={name} sprite={spriteUrl('directory',name)} onOpen={noop} onSelect={noop}/>)}</IconGrid></div>
</main>);
