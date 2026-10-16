import * as THREE from "three";
import jupiterTextureUrl from "./textures/jupiter-cassini.jpg";
import starfieldTextureUrl from "./textures/jupiter-starfield.jpg";
import type {
  AtmosphereFrame, AtmosphereScene, AtmosphereSceneContext, AtmosphereViewport,
} from "./atmosphereRuntime";
import {
  JUPITER_CLOUD_FLOW, JUPITER_ENCOUNTER_WINDOW_SECONDS, JUPITER_MOONS,
  JUPITER_RADIUS, JUPITER_SKY_STAR_COUNT,
  jupiterEncounterForWindow, jupiterEncounterGlint, jupiterMoonPosition,
  jupiterRenderSize, makeJupiterRandom,
  type JupiterEncounter, type JupiterEncounterKind,
} from "./jupiterOrbitModel";

const noiseShader = /* glsl */ `
  float hash(vec3 p) {
    p = fract(p * 0.3183099 + vec3(0.13, 0.27, 0.41));
    p *= 17.0;
    return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
  }
  float noise(vec3 p) {
    vec3 i = floor(p), f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(mix(hash(i), hash(i + vec3(1,0,0)), f.x),
                   mix(hash(i + vec3(0,1,0)), hash(i + vec3(1,1,0)), f.x), f.y),
               mix(mix(hash(i + vec3(0,0,1)), hash(i + vec3(1,0,1)), f.x),
                   mix(hash(i + vec3(0,1,1)), hash(i + vec3(1,1,1)), f.x), f.y), f.z);
  }
  float terrain(vec3 p) {
    return noise(p) * 0.58 + noise(p * 2.03) * 0.27 + noise(p * 4.07) * 0.15;
  }
`;

const sphereVertex = /* glsl */ `
  varying vec2 vUv;
  varying vec3 vLocal, vWorld, vNormal;
  void main() {
    vUv = uv;
    vLocal = normalize(position);
    vWorld = (modelMatrix * vec4(position, 1.0)).xyz;
    vNormal = normalize(mat3(modelMatrix) * normal);
    gl_Position = projectionMatrix * viewMatrix * vec4(vWorld, 1.0);
  }
`;

const planetFragment = /* glsl */ `
  uniform sampler2D uMap;
  uniform bool uReady;
  uniform vec3 uSun, uMoons[4];
  uniform float uRadii[4];
  uniform float uCloudTime;
  varying vec2 vUv;
  varying vec3 vLocal, vWorld, vNormal;
  ${noiseShader}
  vec2 cloudCoordinate(vec2 uv) {
    float latitude = vLocal.y;
    float jets = sin(latitude * 22.0) * 0.8 + sin(latitude * 51.0) * 0.2;
    float poles = max(0.0, 1.0 - pow(abs(latitude), 6.0));
    vec2 spot = (uv - vec2(0.362, 0.390)) / vec2(0.047, 0.027);
    float storm = exp(-dot(spot, spot) * 1.8);
    float angle = uCloudTime * ${JUPITER_CLOUD_FLOW.stormRate.toFixed(8)};
    mat2 rotation = mat2(cos(angle), -sin(angle), sin(angle), cos(angle));
    uv += (rotation * spot - spot) * vec2(0.047, 0.027) * storm;
    // Bounded analytic jet travel never accumulates an ever-growing UV shear.
    uv.x += jets * poles * ${JUPITER_CLOUD_FLOW.jetAmplitude.toFixed(8)}
      * sin(uCloudTime * ${JUPITER_CLOUD_FLOW.jetRate.toFixed(8)}) * (1.0 - storm * 0.8);
    float phase = uCloudTime * ${JUPITER_CLOUD_FLOW.eddyRate.toFixed(8)};
    vec2 cell = vec2(uv.x * 75.398, uv.y * 100.531);
    // Paired eddies move local cloud details across each jet.
    vec2 eddy = vec2(
      sin(cell.x + phase) * cos(cell.y - phase * 0.71) - sin(cell.x) * cos(cell.y),
      cos(cell.x - phase * 0.63) * sin(cell.y + phase) - cos(cell.x) * sin(cell.y)
    );
    uv += eddy * vec2(${JUPITER_CLOUD_FLOW.eddyLongitude.toFixed(8)}, ${JUPITER_CLOUD_FLOW.eddyLatitude.toFixed(8)}) * poles;
    return vec2(fract(uv.x), clamp(uv.y, 0.001, 0.999));
  }
  void main() {
    vec3 normal = normalize(vNormal);
    vec3 clouds;
    if (uReady) {
      clouds = texture2D(uMap, cloudCoordinate(vUv)).rgb;
      clouds = pow(clouds, vec3(1.04)) * vec3(1.12, 1.025, 0.91);
    } else {
      float latitude = vLocal.y;
      vec2 flowing = cloudCoordinate(vUv);
      vec3 flowDirection = vec3(cos(flowing.x * 6.28318), flowing.y * 2.0 - 1.0, sin(flowing.x * 6.28318));
      float turbulence = terrain(flowDirection * vec3(11.0, 3.5, 11.0));
      float bands = sin(latitude * 42.0 + turbulence * 4.3)
        + sin(latitude * 83.0 + turbulence * 3.0) * 0.28;
      clouds = mix(vec3(0.32, 0.19, 0.105), vec3(0.79, 0.72, 0.59),
        smoothstep(-1.0, 0.65, bands));
      clouds *= 0.79 + turbulence * 0.33;
    }
    float sun = dot(normal, uSun);
    float illumination = pow(max(sun, 0.0), 0.78);
    float shadow = 1.0;
    for (int i = 0; i < 4; i++) {
      vec3 towardMoon = uMoons[i] - vWorld;
      float ahead = dot(towardMoon, uSun);
      float distanceToRay = length(towardMoon - uSun * ahead);
      if (ahead > 0.0) shadow *= mix(0.32, 1.0,
        smoothstep(uRadii[i] * 0.65, uRadii[i] * 1.18, distanceToRay));
    }
    vec3 color = clouds * (0.006 + illumination * 1.13 * shadow);
    // The night side grades into space; it carries no luminous outline.
    color += vec3(0.003, 0.005, 0.010) * smoothstep(-0.5, 0.1, sun);
    gl_FragColor = vec4(color, 1.0);
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
  }
`;

const moonFragment = /* glsl */ `
  uniform float uKind;
  uniform vec3 uSun;
  varying vec2 vUv;
  varying vec3 vLocal, vWorld, vNormal;
  ${noiseShader}
  void main() {
    vec3 p = vLocal;
    float broad = terrain(p * 5.5 + uKind * 11.3);
    float fine = terrain(p * 33.0);
    vec3 surface;
    if (uKind < 0.5) {
      surface = mix(vec3(0.30, 0.17, 0.045), vec3(0.86, 0.69, 0.32),
        smoothstep(0.29, 0.68, broad));
      surface = mix(surface, vec3(0.29, 0.075, 0.025),
        smoothstep(0.66, 0.76, terrain(p * 17.0)) * 0.75);
    } else if (uKind < 1.5) {
      float crack = abs(sin((p.x + terrain(p * 6.0) * 0.44) * 43.0)
        + sin((p.y + p.z * 0.7) * 31.0));
      surface = mix(vec3(0.39, 0.24, 0.15), vec3(0.82, 0.81, 0.72),
        smoothstep(0.035, 0.13, crack));
      surface *= 0.82 + broad * 0.26;
    } else if (uKind < 2.5) {
      surface = mix(vec3(0.15, 0.125, 0.095), vec3(0.59, 0.53, 0.40),
        smoothstep(0.33, 0.67, broad));
      surface += smoothstep(0.69, 0.77, fine) * vec3(0.16, 0.16, 0.14);
    } else {
      surface = mix(vec3(0.105, 0.09, 0.075), vec3(0.29, 0.265, 0.22), broad);
      float craters = terrain(p * 46.0);
      surface += smoothstep(0.66, 0.74, craters) * 0.30;
      surface *= 0.74 + fine * 0.50;
    }
    surface *= 0.82 + fine * 0.32;
    float sun = max(dot(normalize(vNormal), uSun), 0.0);
    gl_FragColor = vec4(surface * (0.009 + pow(sun, 0.83) * 1.18), 1.0);
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
  }
`;

interface Visitor {
  group: THREE.Group;
  glint: THREE.Sprite;
}

/** No second animation loop: the Atmosphere host owns elapsed time and motion. */
export function createJupiterOrbitScene(context: AtmosphereSceneContext): AtmosphereScene {
  const renderer = new THREE.WebGLRenderer({ canvas: context.canvas, antialias: true, alpha: false });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.12;
  const scene = new THREE.Scene();
  scene.background = new THREE.Color("#02040a");
  const camera = new THREE.OrthographicCamera(-10, 10, 6, -6, 0.1, 150);
  camera.position.set(0, 0, 35);
  const geometries = new Set<THREE.BufferGeometry>();
  const materials = new Set<THREE.Material>();
  const textures = new Set<THREE.Texture>();
  const geometry = <T extends THREE.BufferGeometry>(value: T): T => { geometries.add(value); return value; };
  const material = <T extends THREE.Material>(value: T): T => { materials.add(value); return value; };
  const texture = <T extends THREE.Texture>(value: T): T => { textures.add(value); return value; };
  const random = makeJupiterRandom(context.seed);
  let destroyed = false;
  let reducedMotion = context.reducedMotion;
  let halfWidth = 10;
  let pointerX = 0;
  let pointerY = 0;
  let encounterWindow = -1;
  let encounter: JupiterEncounter | null = null;
  // Construction is the sole entropy read. Nothing is persisted or timed by wall clock.
  const salt = new Uint32Array(1);
  globalThis.crypto?.getRandomValues(salt);
  const sessionSalt = salt[0];
  const sun = new THREE.Vector3(-0.72, 0.43, 0.57).normalize();

  const skyMap = texture(new THREE.Texture());
  skyMap.colorSpace = THREE.SRGBColorSpace;
  skyMap.wrapS = THREE.RepeatWrapping;
  skyMap.minFilter = THREE.LinearMipmapLinearFilter;
  skyMap.anisotropy = Math.min(renderer.capabilities.getMaxAnisotropy(), 4);
  const skyMaterial = material(new THREE.ShaderMaterial({
    depthWrite: false,
    uniforms: { uSkyMap: { value: skyMap }, uSkyReady: { value: false } },
    vertexShader: `varying vec2 vSky; void main() { vSky = position.xy;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: /* glsl */ `
      uniform sampler2D uSkyMap;
      uniform bool uSkyReady;
      varying vec2 vSky;
      ${noiseShader}
      void main() {
        vec2 p = vSky;
        float cloud = terrain(vec3(p * vec2(0.22, 0.36), 3.1));
        float bandDistance = p.y - 1.8 - p.x * 0.28;
        float ribbon = exp(-pow((bandDistance + (cloud - 0.5) * 1.8) * 0.40, 2.0));
        float dust = terrain(vec3(p * 0.67, 8.2));
        float darkLane = smoothstep(0.34, 0.58, dust);
        vec3 color = vec3(0.0011, 0.0021, 0.0041);
        color += mix(vec3(0.010, 0.009, 0.013), vec3(0.019, 0.027, 0.044), cloud)
          * ribbon * darkLane;
        if (uSkyReady) {
          // Sample a spherical view toward the galactic plane, away from atlas poles.
          vec3 direction = normalize(vec3(p.x * 0.075 + p.y * 0.012, bandDistance * 0.11, 1.0));
          vec2 skyUv = vec2(0.52 + atan(direction.x, direction.z) / 6.283185,
            0.50 + asin(direction.y) / 3.141593);
          vec3 stars = texture2D(uSkyMap, skyUv).rgb;
          color += stars * vec3(1.12, 1.14, 1.24);
        }
        gl_FragColor = vec4(color, 1.0);
        #include <colorspace_fragment>
      }
    `,
  }));
  const dust = new THREE.Mesh(geometry(new THREE.PlaneGeometry(100, 60)), skyMaterial);
  dust.name = "Jupiter galactic sky";
  dust.position.z = -75;
  scene.add(dust);

  const starCount = JUPITER_SKY_STAR_COUNT;
  const starPositions = new Float32Array(starCount * 3);
  const starColors = new Float32Array(starCount * 3);
  const starSizes = new Float32Array(starCount);
  for (let i = 0; i < starCount; i++) {
    const x = (random() - 0.5) * 44;
    const galactic = i > starCount * 0.58;
    const y = galactic
      ? 1.8 + x * 0.28 + (random() + random() + random() - 1.5) * 3.8
      : (random() - 0.5) * 28;
    starPositions.set([x, y, -20 - random() * 43], i * 3);
    const tier = random();
    const brightness = tier > 0.994 ? 1.15 + random() * 0.6
      : 0.22 + Math.pow(random(), 2) * 0.65;
    const warmth = random();
    starColors.set([brightness * (0.65 + warmth * 0.40), brightness * 0.88, brightness * (1.1 - warmth * 0.38)], i * 3);
    starSizes[i] = tier > 0.994 ? 3.4 + random() * 1.9
      : tier > 0.88 ? 1.9 + random() * 1.2 : 0.95 + random() * 0.85;
  }
  const starGeometry = geometry(new THREE.BufferGeometry());
  starGeometry.setAttribute("position", new THREE.BufferAttribute(starPositions, 3));
  starGeometry.setAttribute("color", new THREE.BufferAttribute(starColors, 3));
  starGeometry.setAttribute("aSize", new THREE.BufferAttribute(starSizes, 1));
  const starMaterial = material(new THREE.ShaderMaterial({
    uniforms: { uDpr: { value: 1 } }, vertexColors: true, transparent: true,
    depthWrite: false, blending: THREE.AdditiveBlending,
    vertexShader: `attribute float aSize; uniform float uDpr; varying vec3 vColor;
      void main() { vColor = color; gl_PointSize = aSize * uDpr;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: `varying vec3 vColor; void main() {
      float radius = length(gl_PointCoord - 0.5) * 2.0;
      float core = exp(-radius * radius * 4.2) * (1.0 - smoothstep(0.6, 1.0, radius));
      gl_FragColor = vec4(vColor, core);
      #include <colorspace_fragment>
    }`,
  }));
  const stars = new THREE.Points(starGeometry, starMaterial);
  stars.name = "Jupiter stars";
  scene.add(stars);

  const system = new THREE.Group();
  system.name = "Jupiter system";
  system.position.set(3.75, -0.35, 0);
  system.rotation.z = -0.095;
  scene.add(system);
  const planetMap = texture(new THREE.Texture());
  planetMap.colorSpace = THREE.SRGBColorSpace;
  planetMap.wrapS = THREE.RepeatWrapping;
  planetMap.minFilter = THREE.LinearMipmapLinearFilter;
  planetMap.anisotropy = Math.min(renderer.capabilities.getMaxAnisotropy(), 8);
  const moonWorldPositions = JUPITER_MOONS.map(() => new THREE.Vector3());
  const planetMaterial = material(new THREE.ShaderMaterial({
    vertexShader: sphereVertex, fragmentShader: planetFragment,
    uniforms: {
      uMap: { value: planetMap }, uReady: { value: false }, uSun: { value: sun },
      uCloudTime: { value: 0 },
      uMoons: { value: moonWorldPositions }, uRadii: { value: JUPITER_MOONS.map(moon => moon.radius) },
    },
  }));
  const planet = new THREE.Mesh(geometry(new THREE.SphereGeometry(JUPITER_RADIUS, 128, 80)), planetMaterial);
  planet.name = "Jupiter";
  planet.rotation.y = -0.92;
  system.add(planet);
  const atmosphere = new THREE.Mesh(geometry(new THREE.SphereGeometry(JUPITER_RADIUS * 1.0055, 96, 64)), material(new THREE.ShaderMaterial({
    vertexShader: sphereVertex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: { uSun: { value: sun } },
    fragmentShader: /* glsl */ `
      uniform vec3 uSun; varying vec3 vWorld, vNormal;
      void main() {
        vec3 normal = normalize(vNormal);
        float edge = pow(1.0 - max(dot(normal, normalize(cameraPosition - vWorld)), 0.0), 7.0);
        float lit = smoothstep(-0.10, 0.7, dot(normal, uSun));
        vec3 color = mix(vec3(0.20, 0.38, 0.65), vec3(0.68, 0.76, 0.83), lit);
        gl_FragColor = vec4(color, edge * lit * 0.28);
        #include <colorspace_fragment>
      }
    `,
  })));
  atmosphere.name = "Jupiter atmosphere";
  system.add(atmosphere);
  const moons = JUPITER_MOONS.map((moon, index) => {
    const mesh = new THREE.Mesh(geometry(new THREE.SphereGeometry(moon.radius, 48, 32)), material(new THREE.ShaderMaterial({
      vertexShader: sphereVertex, fragmentShader: moonFragment,
      uniforms: { uKind: { value: index }, uSun: { value: sun } },
    })));
    mesh.name = moon.name;
    mesh.position.set(...jupiterMoonPosition(index, 0));
    system.add(mesh);
    return mesh;
  });

  scene.add(new THREE.AmbientLight(0x8292ad, 0.085));
  const sunlight = new THREE.DirectionalLight(0xffeed2, 3.4);
  sunlight.position.copy(sun).multiplyScalar(30);
  scene.add(sunlight);
  const gold = material(new THREE.MeshStandardMaterial({ color: 0x96783c, metalness: 0.78, roughness: 0.43 }));
  const silver = material(new THREE.MeshStandardMaterial({ color: 0xaaa9a0, metalness: 0.79, roughness: 0.35 }));
  const dark = material(new THREE.MeshStandardMaterial({ color: 0x292b2b, metalness: 0.55, roughness: 0.69 }));
  const black = material(new THREE.MeshStandardMaterial({ color: 0x030507, metalness: 0.32, roughness: 0.28 }));
  const addMesh = (parent: THREE.Object3D, shape: THREE.BufferGeometry, finish: THREE.Material, x = 0, y = 0, z = 0) => {
    const mesh = new THREE.Mesh(geometry(shape), finish);
    mesh.position.set(x, y, z);
    parent.add(mesh);
    return mesh;
  };
  const beam = (parent: THREE.Object3D, from: [number, number, number], to: [number, number, number], radius = 0.012) => {
    const a = new THREE.Vector3(...from), b = new THREE.Vector3(...to), direction = b.clone().sub(a);
    const mesh = addMesh(parent, new THREE.CylinderGeometry(radius, radius, direction.length(), 6), silver);
    mesh.position.copy(a).add(b).multiplyScalar(0.5);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.normalize());
  };
  const dish = (parent: THREE.Object3D, radius: number) => {
    const profile: THREE.Vector2[] = [];
    for (let i = 0; i <= 14; i++) {
      const r = (i / 14) * radius;
      profile.push(new THREE.Vector2(r, (r * r) / (radius * 2.6)));
    }
    const dishMaterial = material(new THREE.MeshStandardMaterial({ color: 0xb9b7a8, metalness: 0.71, roughness: 0.39, side: THREE.DoubleSide }));
    const mesh = addMesh(parent, new THREE.LatheGeometry(profile, 48), dishMaterial, 0, 0.12);
    for (let i = 0; i < 3; i++) {
      const angle = i * Math.PI * 2 / 3;
      beam(parent, [Math.cos(angle) * radius * 0.88, 0.39, Math.sin(angle) * radius * 0.88], [0, 0.73, 0], 0.009);
    }
    addMesh(parent, new THREE.CylinderGeometry(0.022, 0.04, 0.16, 8), silver, 0, 0.74);
    return mesh;
  };
  const glowPixels = new Uint8Array(32 * 32 * 4);
  for (let y = 0; y < 32; y++) for (let x = 0; x < 32; x++) {
    const radius = Math.hypot(x - 15.5, y - 15.5) / 15.5;
    const offset = (y * 32 + x) * 4;
    glowPixels.set([255, 238, 202, Math.round(Math.pow(Math.max(0, 1 - radius), 3) * 255)], offset);
  }
  const glintTexture = texture(new THREE.DataTexture(glowPixels, 32, 32));
  glintTexture.needsUpdate = true;
  const makeVisitor = (kind: JupiterEncounterKind): Visitor => {
    const group = new THREE.Group();
    group.name = `Jupiter ${kind}`;
    if (kind === "monolith") {
      addMesh(group, new THREE.BoxGeometry(0.19, 0.82, 0.046), black);
    } else {
      dish(group, kind === "pioneer" ? 0.43 : 0.47);
      addMesh(group, new THREE.CylinderGeometry(0.19, 0.21, 0.28, kind === "pioneer" ? 6 : 10), gold, 0, -0.05);
      if (kind === "pioneer") {
        for (const direction of [-1, 1]) {
          beam(group, [direction * 0.13, -0.15, 0], [direction * 0.91, -0.40, 0.08]);
          const rtg = addMesh(group, new THREE.CylinderGeometry(0.07, 0.07, 0.26, 8), dark, direction * 0.9, -0.4, 0.08);
          rtg.rotation.z = Math.PI / 2;
          for (let fin = 0; fin < 4; fin++) addMesh(group, new THREE.BoxGeometry(0.025, 0.18, 0.16), dark, direction * 0.9 + (fin - 1.5) * 0.055, -0.4, 0.08);
        }
        beam(group, [0.05, -0.1, 0], [0.18, -1.13, 0.1], 0.007);
      } else {
        beam(group, [-0.12, -0.12, 0], [-1.10, -0.33, 0.12]);
        beam(group, [0.12, -0.12, 0], [0.88, -0.10, 0.05]);
        addMesh(group, new THREE.BoxGeometry(0.27, 0.15, 0.20), dark, 0.92, -0.1, 0.05);
        for (let i = 0; i < 3; i++) addMesh(group, new THREE.CylinderGeometry(0.075, 0.075, 0.18, 8), dark, -0.70 - i * 0.18, -0.31, 0.12).rotation.z = Math.PI / 2;
        beam(group, [0, -0.14, 0], [0.22, -1.42, -0.08], 0.006);
      }
    }
    const glint = new THREE.Sprite(material(new THREE.SpriteMaterial({
      map: glintTexture, color: 0xffe7be, transparent: true, opacity: 0,
      blending: THREE.AdditiveBlending, depthWrite: false,
    })));
    glint.position.set(0.23, 0.24, 0.25);
    glint.scale.setScalar(0.19);
    group.add(glint);
    group.visible = false;
    group.position.z = 15;
    group.scale.setScalar(kind === "monolith" ? 0.63 : 0.58);
    scene.add(group);
    return { group, glint };
  };
  const visitors: Record<JupiterEncounterKind, Visitor> = {
    pioneer: makeVisitor("pioneer"), voyager: makeVisitor("voyager"), monolith: makeVisitor("monolith"),
  };
  const visitorList = Object.values(visitors);
  const moonCoordinates: [number, number, number] = [0, 0, 0];

  function render() { if (!destroyed) renderer.render(scene, camera); }
  const loadMap = (url: string, map: THREE.Texture, ready: { value: boolean }) => {
    const image = new Image();
    image.onload = () => {
      if (destroyed) return;
      map.image = image;
      map.needsUpdate = true;
      ready.value = true;
      image.onload = null;
      image.onerror = null;
      // Local maps refine the still frame even when Motion is off.
      render();
    };
    image.onerror = () => {
      image.onload = null;
      image.onerror = null;
      image.removeAttribute("src");
      if (!destroyed) render();
    };
    image.src = url;
    return image;
  };
  const mapImages = [
    loadMap(jupiterTextureUrl, planetMap, planetMaterial.uniforms.uReady),
    loadMap(starfieldTextureUrl, skyMap, skyMaterial.uniforms.uSkyReady),
  ];

  const updateMoonWorld = () => {
    system.updateMatrixWorld(true);
    for (let index = 0; index < moons.length; index++) {
      moons[index].getWorldPosition(moonWorldPositions[index]);
    }
  };
  updateMoonWorld();
  return {
    resize(viewport: AtmosphereViewport) {
      if (destroyed) return;
      const size = jupiterRenderSize(viewport.width, viewport.height, viewport.devicePixelRatio);
      renderer.setPixelRatio(size.dpr);
      renderer.setSize(size.width, size.height, false);
      starMaterial.uniforms.uDpr.value = size.dpr;
      const aspect = Math.max(1, viewport.width) / Math.max(1, viewport.height);
      halfWidth = 6 * aspect;
      camera.left = -halfWidth;
      camera.right = halfWidth;
      camera.updateProjectionMatrix();
      system.position.x = aspect < 0.8 ? 4.35 : Math.min(5.2, halfWidth * 0.39);
      updateMoonWorld();
    },
    update(frame: AtmosphereFrame) {
      if (destroyed || reducedMotion) return;
      const elapsed = Math.max(0, frame.elapsed);
      planet.rotation.y = -0.92 + elapsed * 0.00135;
      planetMaterial.uniforms.uCloudTime.value = elapsed;
      for (let index = 0; index < moons.length; index++) {
        jupiterMoonPosition(index, elapsed, moonCoordinates);
        moons[index].position.set(moonCoordinates[0], moonCoordinates[1], moonCoordinates[2]);
        moons[index].rotation.y = elapsed * 0.004 + index;
      }
      const ease = 1 - Math.exp(-Math.min(frame.delta, 0.05) * 1.4);
      pointerX += (frame.pointer.x - pointerX) * ease;
      pointerY += (frame.pointer.y - pointerY) * ease;
      camera.position.set(pointerX * 0.18, -pointerY * 0.12, 35);
      camera.lookAt(0, 0, 0);
      updateMoonWorld();
      const windowIndex = Math.floor(elapsed / JUPITER_ENCOUNTER_WINDOW_SECONDS);
      if (windowIndex !== encounterWindow) {
        encounterWindow = windowIndex;
        encounter = jupiterEncounterForWindow(context.seed, sessionSalt, windowIndex);
      }
      for (let index = 0; index < visitorList.length; index++) visitorList[index].group.visible = false;
      const progress = encounter ? (elapsed - encounter.start) / encounter.duration : -1;
      if (encounter && progress >= 0 && progress <= 1) {
        const visitor = visitors[encounter.kind];
        visitor.group.visible = true;
        visitor.group.position.set(
          (progress * 2 - 1) * (halfWidth + 2.4) * encounter.direction,
          encounter.height - progress * 1.1,
          15,
        );
        visitor.group.rotation.set(0.56, -0.48 + progress * 0.38, -0.30 + progress * 0.17);
        visitor.glint.material.opacity = jupiterEncounterGlint(progress) * (encounter.kind === "monolith" ? 0.20 : 0.72);
      }
    },
    setReducedMotion(value) { reducedMotion = value; },
    render,
    dispose() {
      if (destroyed) return;
      destroyed = true;
      for (const image of mapImages) {
        image.onload = null;
        image.onerror = null;
        image.removeAttribute("src");
      }
      for (const map of textures) map.image = null;
      for (const value of geometries) value.dispose();
      for (const value of materials) value.dispose();
      for (const value of textures) value.dispose();
      renderer.dispose();
    },
  };
}
