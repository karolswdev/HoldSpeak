/** Standalone live preview using actual product runtime and factory. */
import {mountAtmosphereScene} from '@w/desk/gl/atmosphereRuntime';
const name=new URLSearchParams(location.search).get('planet')==='saturn'?'saturn':'mars';
const factory=name==='mars'?(await import('@w/desk/gl/marsOrbitScene')).createMarsOrbitScene:(await import('@w/desk/gl/saturnOrbitScene')).createSaturnOrbitScene;
const release=mountAtmosphereScene(document.querySelector<HTMLCanvasElement>('#scene')!,factory,{seed:name==='mars'?0x4d415253:0x53415455});
addEventListener('pagehide',release,{once:true});
