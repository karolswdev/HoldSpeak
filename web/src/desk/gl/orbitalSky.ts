import * as THREE from "three";
import starfieldTextureUrl from "./textures/jupiter-starfield.jpg";

export const ORBITAL_SKY_STAR_COUNT = 18_000;

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

/** Local galactic map and seeded stars; the caller owns camera and rendering. */
export function createOrbitalSky(scene: THREE.Scene, seed: number, onReady: () => void): {
  setDpr(dpr: number): void;
  dispose(): void;
} {
  let destroyed = false;
  let state = seed >>> 0;
  const random = () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 0x100000000;
  };
  const geometries: THREE.BufferGeometry[] = [];
  const materials: THREE.Material[] = [];
  const textures: THREE.Texture[] = [];
  const geometry = <T extends THREE.BufferGeometry>(value: T): T => { geometries.push(value); return value; };
  const material = <T extends THREE.Material>(value: T): T => { materials.push(value); return value; };
  const texture = <T extends THREE.Texture>(value: T): T => { textures.push(value); return value; };
  const skyMap = texture(new THREE.Texture());
  skyMap.colorSpace = THREE.SRGBColorSpace;
  skyMap.wrapS = THREE.RepeatWrapping;
  skyMap.minFilter = THREE.LinearMipmapLinearFilter;
  skyMap.anisotropy = 4;
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
  dust.name = "Orbital galactic sky";
  dust.position.z = -75;
  scene.add(dust);

  const starCount = ORBITAL_SKY_STAR_COUNT;
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
  stars.name = "Orbital stars";
  scene.add(stars);

  const image = new Image();
  image.onload = () => {
    if (destroyed) return;
    skyMap.image = image;
    skyMap.needsUpdate = true;
    skyMaterial.uniforms.uSkyReady.value = true;
    image.onload = null;
    image.onerror = null;
    onReady();
  };
  image.onerror = () => {
    if (destroyed) return;
    image.onload = null;
    image.onerror = null;
    image.removeAttribute("src");
    onReady();
  };
  image.src = starfieldTextureUrl;
  return {
    setDpr(dpr) {
      if (!destroyed) starMaterial.uniforms.uDpr.value = Math.min(Math.max(dpr || 1, 1), 1.5);
    },
    dispose() {
      if (destroyed) return;
      destroyed = true;
      image.onload = null;
      image.onerror = null;
      image.removeAttribute("src");
      scene.remove(dust, stars);
      skyMap.image = null;
      for (const value of geometries) value.dispose();
      for (const value of materials) value.dispose();
      for (const value of textures) value.dispose();
    },
  };
}
