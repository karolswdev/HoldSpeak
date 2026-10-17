import {mountAtmosphereScene,type AtmosphereSceneFactory} from '@w/desk/gl/atmosphereRuntime';
import {createNightTrainScene} from '@w/desk/gl/interiors/nightTrainScene';
const stationPreview=new URLSearchParams(location.search).has('station');
const factory:AtmosphereSceneFactory=context=>{const scene=createNightTrainScene(context);if(!stationPreview)return scene;return {...scene,update(frame){scene.update({...frame,elapsed:frame.elapsed+165})}}};
const release=mountAtmosphereScene(document.querySelector<HTMLCanvasElement>('#scene')!,factory,{seed:213});addEventListener('pagehide',release,{once:true});
