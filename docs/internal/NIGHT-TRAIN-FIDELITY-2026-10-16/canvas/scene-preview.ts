import {Room} from '@w/desk/gl/interiors/sceneKit';
let room:Room;const originalFinish=Room.prototype.finish;Room.prototype.finish=function(){room=this;return originalFinish.call(this)};
import {createNightTrainScene} from '@w/desk/gl/interiors/nightTrainScene';
const canvas=document.querySelector<HTMLCanvasElement>('#scene')!;const scene=createNightTrainScene({canvas,seed:213,reducedMotion:false});scene.resize({width:innerWidth,height:innerHeight,devicePixelRatio});const frame=(elapsed:number)=>{scene.update({elapsed,delta:.016,pointer:{x:0,y:0}});scene.render()};frame(0);Object.assign(window,{trainObservation:{scene,frame,get room(){return room}}});
