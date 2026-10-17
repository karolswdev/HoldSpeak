/** Private direct authored timeline; no product debug API. */
const requested=new URLSearchParams(location.search).get('planet');
const name=requested==='jupiter'?'jupiter':requested==='saturn'?'saturn':'mars';
const canvas=document.querySelector<HTMLCanvasElement>('#scene')!;
const factory=name==='jupiter'?(await import('@w/desk/gl/jupiterOrbitScene')).createJupiterOrbitScene:name==='mars'?(await import('@w/desk/gl/marsOrbitScene')).createMarsOrbitScene:(await import('@w/desk/gl/saturnOrbitScene')).createSaturnOrbitScene;
const scene=factory({canvas,seed:name==='jupiter'?0x4a555049:name==='mars'?0x4d415253:0x53415455,reducedMotion:false});
scene.resize({width:innerWidth,height:innerHeight,devicePixelRatio:devicePixelRatio});
const frame=(elapsed:number)=>{scene.update({delta:0.05,elapsed,pointer:{x:0,y:0}});scene.render();};frame(0);
Object.assign(window,{orbitObservation:{scene,name,frame}});
