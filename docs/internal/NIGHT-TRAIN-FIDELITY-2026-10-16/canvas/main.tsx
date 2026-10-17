import {createRoot} from 'react-dom/client';
import '@w/styles/global.css';import '@w/styles/react-app.css';import '@w/desk/desk.css';
import {DeskIcon,IconGrid} from '@w/desk/surface';import {spriteUrl} from '@w/desk/sprites';import direction from './direction.svg';
const noop=()=>{};
createRoot(document.getElementById('root')!).render(<main className="desk-next train-direction" style={{height:'100dvh',position:'relative',background:'#171a1b'}}><img src={direction} alt="" className="train-direction-image" style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'cover',pointerEvents:'none'}}/><div style={{position:'absolute',left:20,top:44,width:112}}><IconGrid label="Desk drawers">{['Meetings','Personal','Reference'].map(name=><DeskIcon key={name} id={name} kind="directory" name={name} sprite={spriteUrl('directory',name)} onOpen={noop} onSelect={noop}/>)}</IconGrid></div></main>);
