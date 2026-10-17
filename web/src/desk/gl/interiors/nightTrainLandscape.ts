import { THREE, type Room, randomSource } from "./sceneKit";
import { createTrainStation } from "./nightTrainStation";
import { TRAIN_TERRAIN_SPAN, TRAIN_TERRAIN_EXTENTS, TRAIN_TERRAIN_SPEEDS, TRAIN_TREE_LAYERS, trainTerrainHeight, trainTravelPosition } from "./nightTrainJourney";

/** Bounded scenery owned by this helper; Room owns its renderer and room assets. */
export function createTrainLandscape(room: Room): { update(elapsed: number): void; dispose(): void } {
  const seed = Math.floor(room.random() * 0x100000000);
  const random = randomSource(seed);
  const world = room.moving(room.group());
  world.name = "Night train landscape";
  const geometries = new Set<THREE.BufferGeometry>();
  const materials = new Set<THREE.Material>();
  const instances: THREE.InstancedMesh[] = [];
  const geometry = <T extends THREE.BufferGeometry>(value: T): T => { geometries.add(value); return value; };
  const material = <T extends THREE.Material>(value: T): T => { materials.add(value); return value; };
  const movingGroup = (name: string) => {
    const group = room.moving(room.group([0, 0, 0], world));
    group.name = name;
    return group;
  };
  const mesh = (shape: THREE.BufferGeometry, finish: THREE.Material, parent: THREE.Object3D) => {
    const object = room.moving(new THREE.Mesh(geometry(shape), material(finish)));
    parent.add(object);
    return object;
  };
  let disposed = false;
  const reliefVertex = `
    varying vec3 vWorld, vNormal, vLocal;
    void main() {
      vec3 p = position, n = normal;
      #ifdef USE_INSTANCING
        p = (instanceMatrix * vec4(p, 1.0)).xyz;
        n = mat3(instanceMatrix) * (n / vec3(dot(instanceMatrix[0].xyz, instanceMatrix[0].xyz),
          dot(instanceMatrix[1].xyz, instanceMatrix[1].xyz), dot(instanceMatrix[2].xyz, instanceMatrix[2].xyz)));
      #endif
      vLocal = position;
      vWorld = (modelMatrix * vec4(p, 1.0)).xyz;
      vNormal = normalize(mat3(modelMatrix) * n);
      gl_Position = projectionMatrix * viewMatrix * vec4(vWorld, 1.0);
    }`;
  const sky = mesh(new THREE.PlaneGeometry(260, 150), new THREE.ShaderMaterial({
    depthWrite: false, fog: false,
    vertexShader: `varying vec3 vWorld; void main(){ vWorld = (modelMatrix * vec4(position, 1.0)).xyz;
      gl_Position = projectionMatrix * viewMatrix * vec4(vWorld, 1.0); }`,
    fragmentShader: `varying vec3 vWorld;
      float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453); }
      float noise(vec2 p){ vec2 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);
        return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y); }
      void main(){
        float elevation = smoothstep(0.0, 35.0, vWorld.y);
        vec3 color = mix(vec3(0.045,0.075,0.115),vec3(0.008,0.019,0.048),elevation);
        float drift = noise(vWorld.xy * vec2(0.028,0.13));
        float bands = exp(-pow((vWorld.y - 18.0 - drift * 5.0 - sin(vWorld.x * 0.018) * 2.0) * 0.30,2.0));
        float wisps = noise(vWorld.xy * vec2(0.075,0.43)) * noise(vWorld.xy * vec2(0.019,0.15));
        color += vec3(0.018,0.021,0.026) * bands * smoothstep(0.16,0.45,wisps);
        color += vec3(0.010,0.005,0.003) * exp(-pow((vWorld.y - 3.0) * 0.19,2.0));
        gl_FragColor = vec4(color,1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  }), world);
  sky.name = "Train dusk sky";
  sky.position.set(0, 28, -118);

  const ridgeColors = [0x6c7381, 0x465563, 0x253c3a, 0x18302f];
  const skyline = [new Float32Array(769),new Float32Array(769)];
  const ridges = [96, 82, 53, 7.6].map((depth, layer) => {
    const group = movingGroup(`Train ridge layer ${layer}`);
    group.position.z = -depth;
    const phase = random() * Math.PI * 2;
    const segments = 768, rows = 41, width = TRAIN_TERRAIN_SPAN * 2;
    const positions = new Float32Array((segments + 1) * rows * 3);
    const indices: number[] = [];
    const extent = TRAIN_TERRAIN_EXTENTS[layer];
    for (let row = 0; row < rows; row++) {
      for (let column = 0; column <= segments; column++) {
        // Existing boundary rows/columns become vertical skirts, so no triangle
        // density is added and no high front edge can reveal the world beneath.
        const columnSample=Math.max(1,Math.min(segments-1,column));
        const rowSample=Math.max(1,Math.min(rows-2,row));
        const x=(columnSample/segments-0.5)*width;
        const z=((rowSample-1)/(rows-3)*2-1)*extent;
        const offset = (row * (segments + 1) + column) * 3;
        const boundary=row===0||row===rows-1||column===0||column===segments;
        const height=boundary?-5:trainTerrainHeight(x,z,layer,phase);
        positions.set([x,height,z],offset);
        if(layer < 2) skyline[layer][column] = Math.max(skyline[layer][column],height);
        if (row < rows - 1 && column < segments) {
          const a = row * (segments + 1) + column, b = a + segments + 1;
          indices.push(a,b,a+1,b,b+1,a+1);
        }
      }
    }
    const shape = new THREE.BufferGeometry();
    shape.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    shape.setIndex(indices); shape.computeVertexNormals();
    const terrain = mesh(shape, new THREE.ShaderMaterial({
      side: THREE.DoubleSide, fog: false, vertexShader: reliefVertex,
      uniforms: { uTint: { value: new THREE.Color(ridgeColors[layer]) }, uSnow: { value: layer === 0 ? 1 : 0 }, uRock: { value: layer < 2 ? 1 : 0 } },
      fragmentShader: `uniform vec3 uTint; uniform float uSnow,uRock; varying vec3 vWorld,vNormal,vLocal;
        float hash(vec2 p){ return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }
        float noise(vec2 p){ vec2 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);
          return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y); }
        void main(){
          vec3 n=normalize(vNormal);
          float light=max(dot(n,normalize(vec3(-0.64,0.44,0.64))),0.0);
          float grain=noise(vLocal.xz*1.7)*0.55+noise(vLocal.xz*4.3)*0.3+noise(vLocal.xz*8.1)*0.15;
          float strata=sin(vLocal.y*2.1+noise(vLocal.xz*0.19)*5.0)*0.065;
          float cliff=1.0-smoothstep(0.35,0.83,n.y);
          vec3 surface=uTint*(0.73+grain*0.48+strata*uRock);
          surface=mix(surface,surface*vec3(0.83,0.85,0.89),cliff*uRock*0.45);
          float lowCover=(1.0-smoothstep(2.0,6.0,vWorld.y))*smoothstep(0.45,0.88,n.y);
          surface=mix(surface,vec3(0.018,0.033,0.031),lowCover*uRock*0.30);
          vec3 color=surface*(vec3(0.12,0.17,0.25)+vec3(0.82,0.94,1.06)*light*0.56);
          float patches=noise(vLocal.xz*0.39+vec2(vLocal.y*0.14,0.0));
          float snow=smoothstep(18.0,23.0,vWorld.y+(patches-0.5)*2.5)
            *smoothstep(0.30,0.76,n.y)*smoothstep(0.38,0.70,patches)*uSnow;
          vec3 frost=vec3(0.20,0.24,0.28)*(vec3(0.20,0.27,0.36)+light*0.45);
          color=mix(color,frost,snow*0.75);
          float haze=smoothstep(42.0,125.0,-vWorld.z)*0.52;
          color=mix(color,vec3(0.035,0.054,0.080),haze);
          gl_FragColor=vec4(color,1.0);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
        }`,
    }), group);
    terrain.name = "Train terrain";
    return { group, phase, speed: TRAIN_TERRAIN_SPEEDS[layer] };
  });

  // A tiny synchronous skyline atlas lets water echo the actual authored massifs.
  const reflectionPixels=new Uint8Array(769*4);
  for(let i=0;i<769;i++) reflectionPixels.set([
    Math.round(Math.min(1,skyline[0][i]/40)*255),
    Math.round(Math.min(1,skyline[1][i]/40)*255),0,255,
  ],i*4);
  const reflectionMap=new THREE.DataTexture(reflectionPixels,769,1);
  reflectionMap.wrapS=THREE.RepeatWrapping;
  reflectionMap.minFilter=reflectionMap.magFilter=THREE.LinearFilter;
  reflectionMap.needsUpdate=true;
  const waterMaterial = material(new THREE.ShaderMaterial({
    side: THREE.DoubleSide,fog:false,
    uniforms: { uTime:{value:0},uSkyline:{value:reflectionMap},uMountainTravel:{value:new THREE.Vector2()} },
    vertexShader: `varying vec3 vWorld; void main(){vWorld=(modelMatrix*vec4(position,1.0)).xyz;
      gl_Position=projectionMatrix*viewMatrix*vec4(vWorld,1.0);}`,
    fragmentShader: `uniform float uTime;uniform sampler2D uSkyline;uniform vec2 uMountainTravel;varying vec3 vWorld;
      float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
      float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);
        return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);}
      void main(){
        vec2 p=vWorld.xz;
        float flow=noise(p*vec2(0.11,0.18)+vec2(uTime*0.006,-uTime*0.003));
        float broken=noise(p*vec2(0.07,0.41));
        float wave=(sin(p.y*(2.2+flow*0.8)+p.x*0.17+flow*13.0+uTime*0.17)*0.24
          +sin(p.y*1.37-p.x*0.63+noise(p*0.31)*7.0-uTime*0.11)*0.13)*(0.25+broken*0.75);
        vec3 ray=normalize(vWorld-cameraPosition);
        vec3 reflected=normalize(vec3(ray.x,-ray.y,ray.z));
        vec3 sky=mix(vec3(0.025,0.049,0.075),vec3(0.013,0.028,0.050),smoothstep(0.0,0.22,reflected.y));
        float t=(-96.0-vWorld.z)/min(-0.001,reflected.z);
        vec3 hit=vWorld+reflected*max(0.0,t);
        float h=texture2D(uSkyline,vec2(fract((hit.x-uMountainTravel.x+600.0+wave*1.8)/1200.0),0.5)).r*40.0;
        float mountain=(1.0-smoothstep(h-0.7,h+0.7,hit.y+wave*0.35))*step(0.0,t);
        float nearT=(-82.0-vWorld.z)/min(-0.001,reflected.z);
        vec3 nearHit=vWorld+reflected*max(0.0,nearT);
        float nearH=texture2D(uSkyline,vec2(fract((nearHit.x-uMountainTravel.y+600.0+wave)/1200.0),0.5)).g*40.0;
        mountain=max(mountain,(1.0-smoothstep(nearH-0.5,nearH+0.5,nearHit.y+wave*0.25))*step(0.0,nearT));
        vec3 reflection=mix(sky,vec3(0.010,0.020,0.029),mountain*0.82);
        float fresnel=0.12+0.78*pow(1.0-clamp(-ray.y,0.0,1.0),5.0);
        vec3 color=mix(vec3(0.008,0.026,0.030),reflection,fresnel);
        float rake=exp(-pow((p.x-8.0-p.y*0.09)/18.0,2.0));
        color+=vec3(0.003,0.005,0.006)*wave*rake;
        gl_FragColor=vec4(color,1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  }));
  const water=mesh(new THREE.PlaneGeometry(260,94),waterMaterial,world);
  water.name="Train lake";
  water.rotation.x=-Math.PI/2;
  water.position.set(0,0.30,-50.5);

  // Many narrow, asymmetric branch sprays merge into one shared fir. Their
  // tips sag, radii vary around the trunk, and instance rotation changes outline.
  const branchPositions: number[] = [];
  const triangle = (a: number[], b: number[], c: number[]) => branchPositions.push(...a,...b,...c);
  const sides = 13;
  for (let tier = 0; tier < 20; tier++) {
    const height = 0.13 + tier * 0.043, radius = (1.0 - height) * 0.25;
    const offsetX = Math.sin(tier * 2.7) * 0.025, offsetZ = Math.cos(tier * 1.9) * 0.023;
    const apex = [offsetX,height + 0.11,offsetZ];
    const underside = [offsetX,height - 0.035,offsetZ];
    const ring = Array.from({ length: sides },(_, side) => {
      const angle = side / sides * Math.PI * 2 + tier * 0.83;
      const reach = radius * (0.72 + random() * 0.65);
      return [offsetX+Math.cos(angle)*reach,height - random()*0.055,offsetZ+Math.sin(angle)*reach];
    });
    for (let side=0;side<sides;side++) {
      triangle(apex,ring[side],ring[(side+1)%sides]);
      triangle(underside,ring[(side+1)%sides],ring[side]);
    }
  }
  for(let side=0;side<7;side++){
    const a=side/7*Math.PI*2,b=(side+1)/7*Math.PI*2;
    triangle([Math.cos(a)*0.014,0,Math.sin(a)*0.014],[Math.cos(b)*0.014,0,Math.sin(b)*0.014],[0,0.85,0]);
  }
  const treeShape = geometry(new THREE.BufferGeometry());
  treeShape.setAttribute("position",new THREE.Float32BufferAttribute(branchPositions,3));
  treeShape.computeVertexNormals();
  const dummy = new THREE.Object3D();
  const woods = TRAIN_TREE_LAYERS.map((layer, index) => {
    const group = movingGroup(`Train ${layer.name}`);
    const finish = material(new THREE.ShaderMaterial({
      side: THREE.DoubleSide, fog: false, vertexShader: reliefVertex,
      uniforms: { uTint: { value: new THREE.Color([0x28443f,0x1c392d,0x132b20][index]) } },
      fragmentShader: `uniform vec3 uTint; varying vec3 vWorld,vNormal,vLocal;
        void main(){
          float light=max(dot(normalize(vNormal),normalize(vec3(-0.55,0.55,0.62))),0.0);
          vec3 color=uTint*(0.52+light*0.82)*(0.88+vLocal.y*0.2);
          color=mix(color,vec3(0.040,0.064,0.095),smoothstep(18.0,100.0,-vWorld.z)*0.34);
          gl_FragColor=vec4(color,1.0);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
        }`,
    }));
    const trees = new THREE.InstancedMesh(treeShape, finish, layer.count);
    trees.name = `Train ${layer.name} trees`;
    trees.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    trees.frustumCulled = false;
    group.add(trees);
    instances.push(trees);
    const clusters = Array.from({ length: index === 2 ? 18 : 12 }, () => (random()-0.5)*layer.spread);
    const seeds = Array.from({ length: layer.count }, (_, i) => {
      const x = trainTravelPosition(clusters[i % clusters.length] + (random()+random()-1)*(index===2?3:11),0,0,layer.spread);
      const z = -layer.depth - random() * (index === 2 ? 1.4 : 6);
      const terrainIndex = index === 2 ? 3 : 2;
      const ridge = ridges[terrainIndex];
      const base = trainTerrainHeight(x,z-ridge.group.position.z,terrainIndex,ridge.phase);
      const shore = THREE.MathUtils.smoothstep(base,0.32,0.55);
      return { x, z, base, shore,
        height: layer.height * (0.62 + random() * 0.9), width: 0.62 + random() * 0.70,
        angle: random() * Math.PI * 2, lean: (random() - 0.5) * 0.09 };
    });
    return { layer, trees, seeds };
  });

  const station = createTrainStation(room,world);

  function update(elapsed: number) {
    if (disposed) return;
    const time = Math.max(0, elapsed);
    ridges.forEach(({ group, speed }) => { group.position.x = trainTravelPosition(0, time, speed, TRAIN_TERRAIN_SPAN); });
    woods.forEach(({ layer, trees, seeds }) => {
      seeds.forEach((seed, index) => {
        const x = trainTravelPosition(seed.x,time,layer.speed,TRAIN_TERRAIN_SPAN);
        dummy.position.set(x,seed.base,seed.z);
        dummy.rotation.set(seed.lean, seed.angle, seed.lean * 0.5);
        dummy.scale.set(seed.height * seed.width * seed.shore, seed.height * seed.shore, seed.height * seed.width * seed.shore);
        dummy.updateMatrix(); trees.setMatrixAt(index, dummy.matrix);
      });
      trees.instanceMatrix.needsUpdate = true;
    });
    station.update(time);
    waterMaterial.uniforms.uMountainTravel.value.set(ridges[0].group.position.x,ridges[1].group.position.x);
    waterMaterial.uniforms.uTime.value = time;
  }
  update(0);
  return {
    update,
    dispose() {
      if (disposed) return;
      disposed = true;
      station.dispose();
      world.removeFromParent();
      reflectionMap.dispose();
      for (const mesh of instances) mesh.dispose();
      for (const shape of geometries) shape.dispose();
      for (const finish of materials) finish.dispose();
    },
  };
}
