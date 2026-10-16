/** Standalone live preview using actual product runtime and factory. */
import {mountAtmosphereScene} from '@w/desk/gl/atmosphereRuntime';
const requested=new URLSearchParams(location.search).get('planet');
const name=requested==='jupiter'?'jupiter':requested==='saturn'?'saturn':'mars';
const factory=name==='jupiter'?(await import('@w/desk/gl/jupiterOrbitScene')).createJupiterOrbitScene:name==='mars'?(await import('@w/desk/gl/marsOrbitScene')).createMarsOrbitScene:(await import('@w/desk/gl/saturnOrbitScene')).createSaturnOrbitScene;
const release=mountAtmosphereScene(document.querySelector<HTMLCanvasElement>('#scene')!,factory,{seed:name==='jupiter'?0x4a555049:name==='mars'?0x4d415253:0x53415455});
addEventListener('pagehide',release,{once:true});
