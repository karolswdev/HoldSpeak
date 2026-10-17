import { THREE, type Room, randomSource } from "./sceneKit";
import { TRAIN_TERRAIN_SPAN, TRAIN_TERRAIN_SPEEDS, TRAIN_TREE_LAYERS, trainTerrainHeight, trainStationPosition, trainTravelPosition } from "./nightTrainJourney";

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

  const ridgeColors = [0x59677e, 0x3a5364, 0x29483f, 0x19362e];
  const ridges = [96, 70, 53, 7.6].map((depth, layer) => {
    const group = movingGroup(`Train ridge layer ${layer}`);
    group.position.z = -depth;
    const phase = random() * Math.PI * 2;
    const segments = 768, rows = 41, width = TRAIN_TERRAIN_SPAN * 2;
    const positions = new Float32Array((segments + 1) * rows * 3);
    const indices: number[] = [];
    const extent = [19, 16, 12, 3.2][layer];
    for (let row = 0; row < rows; row++) {
      for (let column = 0; column <= segments; column++) {
        const x = (column / segments - 0.5) * width, z = (row / (rows - 1) * 2 - 1) * extent;
        const offset = (row * (segments + 1) + column) * 3;
        positions.set([x, trainTerrainHeight(x, z, layer, phase), z], offset);
        if (row < rows - 1 && column < segments) {
          const a = row * (segments + 1) + column, b = a + segments + 1;
          indices.push(a, a + 1, b, b, a + 1, b + 1);
        }
      }
    }
    const shape = new THREE.BufferGeometry();
    shape.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    shape.setIndex(indices); shape.computeVertexNormals();
    const terrain = mesh(shape, new THREE.ShaderMaterial({
      side: THREE.DoubleSide, fog: false, vertexShader: reliefVertex,
      uniforms: { uTint: { value: new THREE.Color(ridgeColors[layer]) }, uSnow: { value: layer === 0 ? 1 : 0 } },
      fragmentShader: `uniform vec3 uTint; uniform float uSnow; varying vec3 vWorld,vNormal,vLocal;
        void main(){
          vec3 n=normalize(vNormal);
          float light = max(dot(n,normalize(vec3(-0.55,0.55,0.62))),0.0);
          float rock = sin(vLocal.x * 1.27 + vLocal.z * 0.91) * sin(vLocal.z * 2.7 - vLocal.x * 0.39);
          vec3 color = uTint * (0.40 + light * 0.92) * (0.91 + rock * 0.09);
          float frost = smoothstep(12.0,17.0,vWorld.y + rock * 1.8) * smoothstep(0.40,0.78,n.y) * uSnow;
          color = mix(color,vec3(0.31,0.36,0.42) * (0.48 + light * 0.75),frost * 0.72);
          float haze = smoothstep(30.0,115.0,-vWorld.z) * 0.42;
          color = mix(color,vec3(0.040,0.064,0.095),haze);
          gl_FragColor=vec4(color,1.0);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
        }`,
    }), group);
    terrain.name = "Train terrain";
    return { group, phase, speed: TRAIN_TERRAIN_SPEEDS[layer] };
  });

  const waterMaterial = material(new THREE.ShaderMaterial({
    side: THREE.DoubleSide, fog: false,
    uniforms: { uTime: { value: 0 } },
    vertexShader: `varying vec3 vLocal; void main(){ vLocal = position;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: `uniform float uTime; varying vec3 vLocal;
      void main(){
        vec2 p = vLocal.xy;
        float far = smoothstep(-42.0, 36.0, p.y);
        vec3 color = mix(vec3(0.025, 0.066, 0.085), vec3(0.075, 0.13, 0.17), far);
        float wave = sin(p.y * 10.0 + sin(p.x * 0.31 + uTime * 0.13) * 1.8 + uTime * 0.21);
        float broken = pow(max(0.0, sin(p.x * 1.71 + sin(p.y * 0.73) * 3.0)), 9.0);
        float glint = pow(max(0.0, wave), 28.0) * broken;
        float ribbon = exp(-pow((p.x - 5.0 - p.y * 0.16) / 22.0, 2.0));
        color += vec3(0.14, 0.17, 0.18) * glint * ribbon * 0.45;
        color += sin(p.y * 0.55 + sin(p.x * 0.11)) * vec3(0.005, 0.008, 0.010);
        gl_FragColor = vec4(color, 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  }));
  const water = mesh(new THREE.PlaneGeometry(260, 94), waterMaterial, world);
  water.name = "Train lake";
  water.rotation.x = -Math.PI / 2;
  water.position.set(0, 0.30, -50.5);

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

  const station = movingGroup("Train passing station");
  station.position.z = -6;
  const poleFinish = material(new THREE.MeshBasicMaterial({ color: 0x2f3939, fog: false }));
  const lightFinish = material(new THREE.MeshBasicMaterial({ color: 0xffd0a0, toneMapped: false, fog: false }));
  const poles = new THREE.InstancedMesh(geometry(new THREE.CylinderGeometry(0.022, 0.035, 2.1, 7)), poleFinish, 5);
  const lights = new THREE.InstancedMesh(geometry(new THREE.BoxGeometry(0.26, 0.045, 0.10)), lightFinish, 5);
  const platform = mesh(new THREE.BoxGeometry(20,0.18,2.2),poleFinish,station);
  platform.name = "Train station platform";
  platform.position.set(7,0.45,0);
  poles.name = "Train station posts"; lights.name = "Train station lights";
  for (let i = 0; i < 5; i++) {
    dummy.position.set(i * 3.5, 1.59, 0); dummy.rotation.set(0, 0, 0); dummy.scale.set(1, 1, 1); dummy.updateMatrix();
    poles.setMatrixAt(i, dummy.matrix);
    dummy.position.y = 2.64; dummy.updateMatrix(); lights.setMatrixAt(i, dummy.matrix);
  }
  station.add(poles, lights); instances.push(poles, lights);
  poles.frustumCulled = lights.frustumCulled = false;

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
    station.position.x = trainStationPosition(time);
    waterMaterial.uniforms.uTime.value = time;
  }
  update(0);
  return {
    update,
    dispose() {
      if (disposed) return;
      disposed = true;
      world.removeFromParent();
      for (const mesh of instances) mesh.dispose();
      for (const shape of geometries) shape.dispose();
      for (const finish of materials) finish.dispose();
    },
  };
}
