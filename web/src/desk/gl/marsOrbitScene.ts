import * as THREE from "three";
import marsTextureUrl from "./textures/mars-viking.jpg";
import type { AtmosphereScene, AtmosphereSceneContext } from "./atmosphereRuntime";
import { MARS_MOONS, MARS_RADIUS, marsMoonPosition, marsRenderSize } from "./marsOrbitModel";
import { createOrbitalSky } from "./orbitalSky";

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
  float terrain(vec3 p) { return noise(p) * 0.58 + noise(p * 2.03) * 0.27 + noise(p * 4.07) * 0.15; }
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
  uniform vec3 uSun, uMoons[2];
  uniform float uRadii[2];
  varying vec2 vUv;
  varying vec3 vLocal, vWorld, vNormal;
  ${noiseShader}
  void main() {
    vec3 surface;
    if (uReady) {
      surface = texture2D(uMap, vUv).rgb * vec3(1.20, 0.94, 0.82);
    } else {
      float rock = terrain(vLocal * 6.0);
      float detail = terrain(vLocal * 38.0);
      surface = mix(vec3(0.16, 0.075, 0.043), vec3(0.68, 0.32, 0.14), smoothstep(0.26, 0.73, rock));
      surface *= 0.78 + detail * 0.40;
      float cap = smoothstep(0.965, 0.995, abs(vLocal.y) + (rock - 0.5) * 0.028);
      surface = mix(surface, vec3(0.80, 0.79, 0.76), cap);
    }
    vec3 normal = normalize(vNormal);
    float light = dot(normal, uSun);
    float illumination = pow(max(light, 0.0), 0.76);
    float shadow = 1.0;
    for (int i = 0; i < 2; i++) {
      vec3 towardMoon = uMoons[i] - vWorld;
      float ahead = dot(towardMoon, uSun);
      float distanceToRay = length(towardMoon - uSun * ahead);
      if (ahead > 0.0) shadow *= mix(0.24, 1.0,
        smoothstep(uRadii[i] * 0.55, uRadii[i] * 1.20, distanceToRay));
    }
    vec3 color = surface * (0.007 + illumination * 1.16 * shadow);
    color += vec3(0.0015, 0.0020, 0.0035) * smoothstep(-0.35, 0.12, light);
    gl_FragColor = vec4(color, 1.0);
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
  }
`;
const moonFragment = /* glsl */ `
  uniform vec3 uSun;
  uniform float uKind;
  varying vec3 vLocal, vWorld, vNormal;
  ${noiseShader}
  float crater(vec3 p, vec3 centre, float radius) {
    float d = length(p - normalize(centre)) / radius;
    return -0.23 * exp(-d * d * 5.0) + 0.13 * exp(-pow((d - 0.82) * 7.0, 2.0));
  }
  void main() {
    vec3 p = normalize(vLocal);
    float broad = terrain(p * 7.0 + uKind * 13.0);
    float fine = terrain(p * 43.0);
    float relief = crater(p, vec3(-0.3, 0.2, 1.0), 0.42)
      + crater(p, vec3(0.7, -0.4, 0.6), 0.22)
      + crater(p, vec3(-0.5, -0.7, 0.5), 0.17)
      + crater(p, vec3(0.3, 0.8, -0.5), 0.25)
      + crater(p, vec3(-0.8, 0.1, -0.6), 0.18);
    vec3 surface = mix(vec3(0.15, 0.14, 0.13), vec3(0.49, 0.46, 0.41), broad);
    surface *= 0.82 + fine * 0.35 + relief;
    float light = pow(max(dot(normalize(vNormal), uSun), 0.0), 0.82);
    gl_FragColor = vec4(surface * (0.018 + light * 1.25), 1.0);
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
  }
`;

/** Irregular relief normalized to the physical equivalent-volume body radius. */
function moonGeometry(radius: number, kind: number): THREE.SphereGeometry {
  const geometry = new THREE.SphereGeometry(radius, 56, 40);
  const positions = geometry.getAttribute("position");
  const direction = new THREE.Vector3();
  const craters = [
    { centre: new THREE.Vector3(-0.3, 0.2, 1).normalize(), radius: 0.40, depth: 0.13 },
    { centre: new THREE.Vector3(0.7, -0.4, 0.6).normalize(), radius: 0.23, depth: 0.065 },
    { centre: new THREE.Vector3(-0.5, -0.7, 0.5).normalize(), radius: 0.18, depth: 0.045 },
  ];
  for (let i = 0; i < positions.count; i++) {
    direction.fromBufferAttribute(positions, i).normalize();
    let relief = 1 + Math.sin(direction.x * 7 + kind) * Math.sin(direction.y * 9 + direction.z * 5) * 0.036
      + Math.sin(direction.z * 16 + direction.x * 4) * 0.014;
    for (const crater of craters) {
      const d = direction.distanceTo(crater.centre) / crater.radius;
      relief += -crater.depth * Math.exp(-d * d * 4.5)
        + crater.depth * 0.34 * Math.exp(-Math.pow((d - 0.85) * 6, 2));
    }
    positions.setXYZ(i, direction.x * radius * relief * (kind === 0 ? 1.25 : 1.13),
      direction.y * radius * relief * (kind === 0 ? 0.83 : 0.94), direction.z * radius * relief * 0.94);
  }
  // SphereGeometry duplicates the longitude seam and poles. Weld their positions
  // exactly before measuring the closed surface, including float32 roundoff.
  const columns = geometry.parameters.widthSegments + 1;
  for (let row = 0; row <= geometry.parameters.heightSegments; row++) {
    const first = row * columns;
    const isPole = row === 0 || row === geometry.parameters.heightSegments;
    for (let column = isPole ? 1 : columns - 1; column < columns; column++) {
      positions.setXYZ(first + column, positions.getX(first), positions.getY(first), positions.getZ(first));
    }
  }
  const indices = geometry.index!;
  const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3();
  let signedVolume = 0;
  for (let i = 0; i < indices.count; i += 3) {
    a.fromBufferAttribute(positions, indices.getX(i));
    b.fromBufferAttribute(positions, indices.getX(i + 1));
    c.fromBufferAttribute(positions, indices.getX(i + 2));
    signedVolume += a.dot(b.cross(c)) / 6;
  }
  const targetVolume = 4 * Math.PI * radius ** 3 / 3;
  const scale = Math.cbrt(targetVolume / Math.abs(signedVolume));
  geometry.scale(scale, scale, scale);
  geometry.computeVertexNormals();
  return geometry;
}

/** The shared Atmosphere host supplies all time, visibility and motion control. */
export function createMarsOrbitScene(context: AtmosphereSceneContext): AtmosphereScene {
  const renderer = new THREE.WebGLRenderer({ canvas: context.canvas, antialias: true, alpha: false });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.12;
  const scene = new THREE.Scene();
  scene.background = new THREE.Color("#02040a");
  const camera = new THREE.OrthographicCamera(-10, 10, 6, -6, 0.1, 150);
  camera.position.set(0, 0, 35);
  let destroyed = false, reducedMotion = context.reducedMotion;
  let pointerX = 0, pointerY = 0;
  const geometries: THREE.BufferGeometry[] = [];
  const materials: THREE.Material[] = [];
  const geometry = <T extends THREE.BufferGeometry>(value: T): T => { geometries.push(value); return value; };
  const material = <T extends THREE.Material>(value: T): T => { materials.push(value); return value; };
  function render() { if (!destroyed) renderer.render(scene, camera); }
  const sky = createOrbitalSky(scene, context.seed, render);
  const system = new THREE.Group();
  system.name = "Mars system";
  system.position.set(3.75, -0.55, 0);
  system.rotation.z = -0.12;
  scene.add(system);
  const sun = new THREE.Vector3(-0.72, 0.43, 0.57).normalize();
  const planetMap = new THREE.Texture();
  planetMap.colorSpace = THREE.SRGBColorSpace;
  planetMap.wrapS = THREE.RepeatWrapping;
  planetMap.minFilter = THREE.LinearMipmapLinearFilter;
  planetMap.anisotropy = Math.min(renderer.capabilities.getMaxAnisotropy(), 8);
  const moonWorldPositions = MARS_MOONS.map(() => new THREE.Vector3());
  const planetMaterial = material(new THREE.ShaderMaterial({
    vertexShader: sphereVertex, fragmentShader: planetFragment,
    uniforms: { uMap: { value: planetMap }, uReady: { value: false }, uSun: { value: sun },
      uMoons: { value: moonWorldPositions }, uRadii: { value: MARS_MOONS.map(moon => moon.radius) } },
  }));
  const planet = new THREE.Mesh(geometry(new THREE.SphereGeometry(MARS_RADIUS, 128, 80)), planetMaterial);
  planet.name = "Mars";
  planet.rotation.y = -0.42;
  system.add(planet);
  const atmosphere = new THREE.Mesh(geometry(new THREE.SphereGeometry(MARS_RADIUS * 1.003, 96, 64)), material(new THREE.ShaderMaterial({
    vertexShader: sphereVertex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: { uSun: { value: sun } },
    fragmentShader: /* glsl */ `
      uniform vec3 uSun; varying vec3 vWorld, vNormal;
      void main() {
        vec3 normal = normalize(vNormal);
        float edge = pow(1.0 - max(dot(normal, normalize(cameraPosition - vWorld)), 0.0), 10.0);
        float lit = smoothstep(-0.05, 0.65, dot(normal, uSun));
        gl_FragColor = vec4(vec3(0.26, 0.40, 0.59), edge * lit * 0.14);
        #include <colorspace_fragment>
      }
    `,
  })));
  atmosphere.name = "Mars atmosphere";
  system.add(atmosphere);
  const moons = MARS_MOONS.map((moon, index) => {
    const mesh = new THREE.Mesh(geometry(moonGeometry(moon.radius, index)), material(new THREE.ShaderMaterial({
      vertexShader: sphereVertex, fragmentShader: moonFragment,
      uniforms: { uSun: { value: sun }, uKind: { value: index } },
    })));
    mesh.name = moon.name;
    mesh.position.set(...marsMoonPosition(index, 0));
    mesh.rotation.set(0.12, index * 0.7, -0.15);
    system.add(mesh);
    return mesh;
  });
  const updateMoonWorld = () => {
    system.updateMatrixWorld(true);
    moons.forEach((moon, index) => moon.getWorldPosition(moonWorldPositions[index]));
  };
  updateMoonWorld();
  const image = new Image();
  image.onload = () => {
    if (destroyed) return;
    planetMap.image = image;
    planetMap.needsUpdate = true;
    planetMaterial.uniforms.uReady.value = true;
    image.onload = null;
    image.onerror = null;
    render();
  };
  image.onerror = () => {
    if (destroyed) return;
    image.onload = null;
    image.onerror = null;
    image.removeAttribute("src");
    render();
  };
  image.src = marsTextureUrl;
  const coordinates: [number, number, number] = [0, 0, 0];
  return {
    resize(viewport) {
      if (destroyed) return;
      const size = marsRenderSize(viewport.width, viewport.height, viewport.devicePixelRatio);
      renderer.setPixelRatio(size.dpr);
      renderer.setSize(size.width, size.height, false);
      sky.setDpr(size.dpr);
      const aspect = Math.max(1, viewport.width) / Math.max(1, viewport.height);
      const halfHeight = Math.max(6, 6.2 / aspect);
      const halfWidth = halfHeight * aspect;
      camera.left = -halfWidth; camera.right = halfWidth;
      camera.top = halfHeight; camera.bottom = -halfHeight;
      camera.updateProjectionMatrix();
      system.position.x = aspect < 0.8 ? 0.35 : Math.min(4.3, halfWidth * 0.39);
      system.position.y = aspect < 0.8 ? -0.4 : -0.55;
      updateMoonWorld();
    },
    update(frame) {
      if (destroyed || reducedMotion) return;
      const elapsed = Math.max(0, frame.elapsed);
      planet.rotation.y = -0.42 + elapsed * 0.0012;
      moons.forEach((moon, index) => {
        moon.position.set(...marsMoonPosition(index, elapsed, coordinates));
        moon.rotation.y = index * 0.7 + elapsed * (index === 0 ? 0.007 : 0.003);
      });
      const ease = 1 - Math.exp(-Math.max(0, Math.min(frame.delta, 0.05)) * 1.4);
      pointerX += (frame.pointer.x - pointerX) * ease;
      pointerY += (frame.pointer.y - pointerY) * ease;
      camera.position.set(pointerX * 0.12, -pointerY * 0.08, 35);
      camera.lookAt(0, 0, 0);
      updateMoonWorld();
    },
    setReducedMotion(value) { reducedMotion = value; },
    render,
    dispose() {
      if (destroyed) return;
      destroyed = true;
      image.onload = null; image.onerror = null;
      image.removeAttribute("src");
      planetMap.image = null;
      sky.dispose();
      for (const value of geometries) value.dispose();
      for (const value of materials) value.dispose();
      planetMap.dispose();
      renderer.dispose();
    },
  };
}
