import { createRoot } from 'react-dom/client';
import '@w/styles/global.css';
import '@w/styles/react-app.css';
import '@w/desk/desk.css';
import { DeskIcon, IconGrid, GadgetGroup, GadgetRow, CheckGadget, SurfaceRows, SurfaceRow } from '@w/desk/surface';
import { spriteUrl } from '@w/desk/sprites';
import jupiter from '@w/desk/gl/textures/jupiter-cassini.jpg';
import starfield from '@w/desk/gl/textures/jupiter-starfield.jpg';
import './canvas.css';
const noop = () => {};
const settings = new URLSearchParams(location.search).has('settings');
const stars = Array.from({ length: 150 }, (_, i) => ({ left: `${(i * 67.71) % 100}%`, top: `${(i * 43.19) % 100}%`, opacity: 0.2 + (i % 5) * 0.12 }));
function Direction() {
 return <main className="desk-next orbit-direction">
   <div className="cosmos" style={{ backgroundImage: `linear-gradient(125deg, #04091222, #02040944), url(${starfield})` }}>{stars.map((style, i) => <i key={i} className="star" style={style} />)}
     <div className="planet" style={{ backgroundImage: `url(${jupiter})` }} />
     <div className="moon io" /><div className="moon europa" />
   </div>
   <div className="drawers"><IconGrid label="Desk drawers">{['Meetings', 'Personal', 'Reference'].map(name => <DeskIcon key={name} id={name} kind="directory" name={name} sprite={spriteUrl('directory', name)} onOpen={noop} onSelect={noop} />)}</IconGrid></div>
   {settings && <aside className="wallpaper-direction"><GadgetGroup label="Wallpaper"><SurfaceRows><SurfaceRow title="In Jupiter's orbit" detail="In use" /></SurfaceRows><GadgetRow label="Motion"><CheckGadget label="Wallpaper motion" checked onChange={noop} /></GadgetRow></GadgetGroup></aside>}
 </main>;
}
createRoot(document.getElementById('root')!).render(<Direction />);
