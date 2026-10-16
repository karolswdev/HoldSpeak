import * as THREE from "three";
import type {
  AtmosphereFrame, AtmosphereScene, AtmosphereSceneContext, AtmosphereViewport,
} from "./atmosphereRuntime";
import { createOrbitalSky } from "./orbitalSky";
import {
  SATURN_RADIUS, SATURN_OBLATENESS, SATURN_RING_INNER, SATURN_RING_OUTER,
  SATURN_CASSINI_INNER, SATURN_CASSINI_OUTER, SATURN_MOONS,
  saturnMoonPosition, saturnFraming, saturnRenderSize,
} from "./saturnOrbitModel";

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

// The same radial ice profile drives the visible rings and their shadow.
const ringProfileShader = /* glsl */ `
  float ringDensity(float r) {
    float inner = smoothstep(${SATURN_RING_INNER.toFixed(3)}, 4.18, r);
    float outer = 1.0 - smoothstep(7.60, ${SATURN_RING_OUTER.toFixed(3)}, r);
    float cRing = 0.19 + 0.06 * sin(r * 24.0) + 0.04 * sin(r * 57.0);
    float bRing = 0.82 + 0.10 * sin(r * 16.0) + 0.04 * sin(r * 41.0);
    float aRing = 0.57 + 0.13 * sin(r * 21.0) + 0.05 * sin(r * 63.0);
    float density = mix(cRing, bRing, smoothstep(4.94, 5.08, r));
    density = mix(density, aRing, smoothstep(6.55, 6.78, r));
    float cassini = smoothstep(${SATURN_CASSINI_INNER.toFixed(3)}, 6.50, r)
      * (1.0 - smoothstep(6.73, ${SATURN_CASSINI_OUTER.toFixed(3)}, r));
    float encke = smoothstep(7.415, 7.43, r) * (1.0 - smoothstep(7.455, 7.47, r));
    density *= (1.0 - cassini * 0.988) * (1.0 - encke * 0.91);
    // Filter the narrowest ice layers in screen space to avoid phone shimmer.
    float footprint = fwidth(r);
    density += (sin(r * 128.0) * 0.055 * exp(-footprint * 128.0)
      + sin(r * 309.0) * 0.032 * exp(-footprint * 309.0)) * (1.0 - cassini);
    return clamp(density * inner * outer, 0.0, 0.98);
  }
`;

const sphereVertex = /* glsl */ `
  uniform float uOblateness;
  varying vec3 vLocal, vWorld, vNormal;
  void main() {
    vLocal = normalize(position);
    vWorld = (modelMatrix * vec4(position, 1.0)).xyz;
    // The globe's nonuniform scale needs the inverse normal stretch.
    vec3 corrected = normal / vec3(1.0, uOblateness * uOblateness, 1.0);
    vNormal = normalize(mat3(modelMatrix) * corrected);
    gl_Position = projectionMatrix * viewMatrix * vec4(vWorld, 1.0);
  }
`;

const planetFragment = /* glsl */ `
  uniform vec3 uSun, uLocalSun;
  uniform float uCloudTime;
  varying vec3 vLocal, vWorld, vNormal;
  ${noiseShader}
  ${ringProfileShader}
  void main() {
    float latitude = vLocal.y;
    float jet = sin(latitude * 27.0) * 0.014 * sin(uCloudTime * 0.0031);
    float longitude = atan(vLocal.z, vLocal.x) + jet;
    vec3 flowing = vec3(cos(longitude), latitude * 0.57, sin(longitude));
    float cloud = terrain(flowing * vec3(15.0, 7.0, 15.0)
      + vec3(uCloudTime * 0.00065, 0.0, 0.0));
    float band = sin(latitude * 46.0 + cloud * 1.4) * 0.46
      + sin(latitude * 91.0 + cloud * 2.2) * 0.18
      + sin(latitude * 17.0 - 0.7) * 0.32;
    vec3 surface = mix(vec3(0.52, 0.37, 0.18), vec3(0.92, 0.82, 0.59),
      smoothstep(-0.95, 0.9, band));
    surface = mix(surface, vec3(0.76, 0.70, 0.53), smoothstep(0.70, 0.96, abs(latitude)) * 0.64);
    surface *= 0.93 + cloud * 0.11;
    // Intersect the sunlight ray with the equatorial ring plane.
    vec3 p = vLocal * vec3(${SATURN_RADIUS.toFixed(3)}, ${(SATURN_RADIUS * SATURN_OBLATENESS).toFixed(3)}, ${SATURN_RADIUS.toFixed(3)});
    float shadow = 1.0;
    float planeDistance = -p.y / uLocalSun.y;
    if (planeDistance > 0.0) {
      vec3 hit = p + uLocalSun * planeDistance;
      shadow = 1.0 - ringDensity(length(hit.xz)) * 0.79;
    }
    float sunlight = dot(normalize(vNormal), uSun);
    float lit = pow(max(sunlight, 0.0), 0.77);
    vec3 color = surface * (0.009 + lit * 1.15 * shadow);
    // A restrained reflected fill gives shape to the dark hemisphere.
    color += vec3(0.008, 0.010, 0.014) * smoothstep(-0.5, 0.0, sunlight);
    gl_FragColor = vec4(color, 1.0);
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
  }
`;

const ringVertex = /* glsl */ `
  varying vec2 vRing;
  void main() {
    vRing = position.xz;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;
const ringFragment = /* glsl */ `
  uniform vec3 uLocalSun;
  varying vec2 vRing;
  ${ringProfileShader}
  void main() {
    float r = length(vRing);
    float density = ringDensity(r);
    if (density < 0.002) discard;
    vec3 p = vec3(vRing.x, 0.0, vRing.y);
    // Closest sunlight approach to the oblate globe, in unit-sphere space.
    vec3 radii = vec3(${SATURN_RADIUS.toFixed(3)}, ${(SATURN_RADIUS * SATURN_OBLATENESS).toFixed(3)}, ${SATURN_RADIUS.toFixed(3)});
    vec3 origin = p / radii, ray = uLocalSun / radii;
    float approach = -dot(origin, ray) / dot(ray, ray);
    float shadow = 1.0;
    if (approach > 0.0) {
      float distanceToGlobe = length(origin + ray * approach);
      shadow = mix(0.065, 1.0, smoothstep(0.98, 1.04, distanceToGlobe));
    }
    float ice = 0.5 + 0.5 * sin(r * 38.0 + sin(r * 10.0) * 0.5);
    vec3 color = mix(vec3(0.43, 0.35, 0.23), vec3(0.88, 0.81, 0.64), ice * 0.65 + density * 0.35);
    float azimuth = dot(normalize(p), normalize(vec3(uLocalSun.x, 0.0, uLocalSun.z)));
    float light = (0.61 + abs(uLocalSun.y) * 0.37) * (0.92 + azimuth * 0.08);
    color *= light * shadow;
    // C-ring light passes through; denser ice remains softly opaque.
    float alpha = 1.0 - exp(-density * 2.4);
    gl_FragColor = vec4(color, alpha);
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
  }
`;

const moonFragment = /* glsl */ `
  uniform vec3 uSun;
  uniform float uKind;
  varying vec3 vLocal, vWorld, vNormal;
  ${noiseShader}
  void main() {
    float broad = terrain(vLocal * 8.0), fine = terrain(vLocal * 42.0);
    vec3 surface;
    if (uKind < 0.5) {
      // Titan's thick haze suppresses sharp surface contrast.
      surface = mix(vec3(0.48, 0.23, 0.055), vec3(0.85, 0.58, 0.22), broad * 0.55 + 0.34);
    } else {
      float crack = abs(sin(vLocal.x * 29.0 + broad * 5.0) + sin(vLocal.z * 37.0));
      surface = mix(vec3(0.42, 0.58, 0.66), vec3(0.86, 0.92, 0.93), smoothstep(0.02, 0.18, crack));
      surface *= 0.86 + fine * 0.2;
    }
    float light = pow(max(dot(normalize(vNormal), uSun), 0.0), uKind < 0.5 ? 0.65 : 0.83);
    gl_FragColor = vec4(surface * (0.014 + light * 1.22), 1.0);
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
  }
`;

/** The Atmosphere host owns animation, elapsed time and hidden-page suspension. */
export function createSaturnOrbitScene(context: AtmosphereSceneContext): AtmosphereScene {
  const renderer = new THREE.WebGLRenderer({ canvas: context.canvas, antialias: true, alpha: false });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.1;
  const scene = new THREE.Scene();
  scene.background = new THREE.Color("#02040a");
  const camera = new THREE.OrthographicCamera(-10, 10, 6, -6, 0.1, 150);
  camera.position.set(0, 0, 35);
  const geometries = new Set<THREE.BufferGeometry>();
  const materials = new Set<THREE.Material>();
  const geometry = <T extends THREE.BufferGeometry>(value: T): T => { geometries.add(value); return value; };
  const material = <T extends THREE.Material>(value: T): T => { materials.add(value); return value; };
  let destroyed = false, reducedMotion = context.reducedMotion;
  let pointerX = 0, pointerY = 0;
  function render() { if (!destroyed) renderer.render(scene, camera); }
  const sky = createOrbitalSky(scene, context.seed, render);
  const system = new THREE.Group();
  system.name = "Saturn system";
  system.position.set(1.5, -0.35, 0);
  system.rotation.set(0.41, 0, -0.23);
  scene.add(system);
  const sun = new THREE.Vector3(-0.65, 0.55, 0.52).normalize();
  const localSun = sun.clone().applyQuaternion(system.quaternion.clone().invert());
  const planetMaterial = material(new THREE.ShaderMaterial({
    vertexShader: sphereVertex, fragmentShader: planetFragment,
    uniforms: {
      uOblateness: { value: SATURN_OBLATENESS }, uCloudTime: { value: 0 },
      uSun: { value: sun }, uLocalSun: { value: localSun.clone() },
    },
  }));
  const planet = new THREE.Mesh(geometry(new THREE.SphereGeometry(SATURN_RADIUS, 112, 72)), planetMaterial);
  planet.name = "Saturn";
  planet.scale.y = SATURN_OBLATENESS;
  system.add(planet);
  const ringGeometry = geometry(new THREE.RingGeometry(SATURN_RING_INNER, SATURN_RING_OUTER, 256, 1));
  ringGeometry.rotateX(-Math.PI / 2);
  const rings = new THREE.Mesh(ringGeometry, material(new THREE.ShaderMaterial({
    vertexShader: ringVertex, fragmentShader: ringFragment,
    uniforms: { uLocalSun: { value: localSun } },
    transparent: true, depthWrite: false, side: THREE.DoubleSide,
  })));
  rings.name = "Saturn rings";
  system.add(rings);
  const moons = SATURN_MOONS.map((moon, index) => {
    const mesh = new THREE.Mesh(geometry(new THREE.SphereGeometry(moon.radius, 48, 32)), material(new THREE.ShaderMaterial({
      vertexShader: sphereVertex, fragmentShader: moonFragment,
      uniforms: { uOblateness: { value: 1 }, uSun: { value: sun }, uKind: { value: index } },
    })));
    mesh.name = moon.name;
    mesh.position.set(...saturnMoonPosition(index, 0));
    system.add(mesh);
    return mesh;
  });
  const haze = new THREE.Mesh(geometry(new THREE.SphereGeometry(SATURN_MOONS[0].radius * 1.065, 48, 32)), material(new THREE.ShaderMaterial({
    vertexShader: sphereVertex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: { uOblateness: { value: 1 }, uSun: { value: sun } },
    fragmentShader: /* glsl */ `
      uniform vec3 uSun; varying vec3 vLocal, vWorld, vNormal;
      void main() {
        vec3 normal = normalize(vNormal);
        float rim = pow(1.0 - abs(dot(normal, normalize(cameraPosition - vWorld))), 2.8);
        float sunlight = smoothstep(-0.25, 0.7, dot(normal, uSun));
        gl_FragColor = vec4(vec3(0.62, 0.31, 0.075), rim * sunlight * 0.28);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }
    `,
  })));
  haze.name = "Titan haze";
  moons[0].add(haze);
  const moonCoordinates: [number, number, number] = [0, 0, 0];
  const spinAxis = new THREE.Vector3(0, 1, 0);
  return {
    resize(viewport: AtmosphereViewport) {
      if (destroyed) return;
      const size = saturnRenderSize(viewport.width, viewport.height, viewport.devicePixelRatio);
      renderer.setPixelRatio(size.dpr);
      renderer.setSize(size.width, size.height, false);
      sky.setDpr(size.dpr);
      const framing = saturnFraming(viewport.width, viewport.height);
      camera.left = -framing.halfWidth; camera.right = framing.halfWidth;
      camera.top = framing.halfHeight; camera.bottom = -framing.halfHeight;
      camera.updateProjectionMatrix();
      system.position.set(framing.x, framing.y, 0);
    },
    update(frame: AtmosphereFrame) {
      if (destroyed || reducedMotion) return;
      const elapsed = Math.max(0, frame.elapsed);
      planet.rotation.y = elapsed * 0.0011;
      planetMaterial.uniforms.uCloudTime.value = elapsed;
      // Cloud coordinates rotate with the globe, so transform the light back.
      planetMaterial.uniforms.uLocalSun.value.copy(localSun)
        .applyAxisAngle(spinAxis, -planet.rotation.y);
      for (let index = 0; index < moons.length; index++) {
        saturnMoonPosition(index, elapsed, moonCoordinates);
        moons[index].position.set(...moonCoordinates);
        moons[index].rotation.y = elapsed * 0.003 + index;
      }
      const ease = 1 - Math.exp(-Math.min(Math.max(frame.delta, 0), 0.05) * 1.4);
      pointerX += (frame.pointer.x - pointerX) * ease;
      pointerY += (frame.pointer.y - pointerY) * ease;
      camera.position.set(pointerX * 0.13, -pointerY * 0.09, 35);
      camera.lookAt(0, 0, 0);
    },
    setReducedMotion(value) { reducedMotion = value; },
    render,
    dispose() {
      if (destroyed) return;
      destroyed = true;
      sky.dispose();
      for (const value of geometries) value.dispose();
      for (const value of materials) value.dispose();
      renderer.dispose();
    },
  };
}
