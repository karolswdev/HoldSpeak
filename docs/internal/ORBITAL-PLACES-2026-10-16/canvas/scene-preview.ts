/** Private direct authored timeline; no product debug API. */
const name=new URLSearchParams(location.search).get('planet')==='saturn'?'saturn':'mars';
const canvas=document.querySelector<HTMLCanvasElement>('#scene')!;
const factory=name==='mars'?(await import('@w/desk/gl/marsOrbitScene')).createMarsOrbitScene:(await import('@w/desk/gl/saturnOrbitScene')).createSaturnOrbitScene;
const scene=factory({canvas,seed:name==='mars'?0x4d415253:0x53415455,reducedMotion:false});
scene.resize({width:innerWidth,height:innerHeight,devicePixelRatio:devicePixelRatio});
const frame=(elapsed:number)=>{scene.update({delta:0.05,elapsed,pointer:{x:0,y:0}});scene.render();};frame(0);
Object.assign(window,{orbitObservation:{scene,name,frame}});
