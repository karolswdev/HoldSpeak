import { Reflector } from "three/addons/objects/Reflector.js";
import { Room, THREE } from "./sceneKit";

/** A real interior reflection blended over the view, with local ownership. */
export function createTrainGlass(room: Room) {
  const geometry = new THREE.PlaneGeometry(1.63, 0.99);
  const pane = new Reflector(geometry, {
    textureWidth: 512, textureHeight: 320, multisample: 0, clipBias: 0.001,
    color: 0xd5dfdf,
    shader: {
      name: "Night Train Fresnel glass",
      uniforms: { tDiffuse: { value: null }, color: { value: null }, textureMatrix: { value: null } },
      vertexShader: /* glsl */ `
        uniform mat4 textureMatrix;
        varying vec4 vReflection;
        varying vec3 vWorld, vNormal;
        void main() {
          vReflection = textureMatrix * vec4(position, 1.0);
          vWorld = (modelMatrix * vec4(position, 1.0)).xyz;
          vNormal = normalize(mat3(modelMatrix) * normal);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: /* glsl */ `
        uniform sampler2D tDiffuse;
        varying vec4 vReflection;
        varying vec3 vWorld, vNormal;
        void main() {
          vec3 reflection = texture2DProj(tDiffuse, vReflection).rgb;
          float facing = max(0.0, dot(normalize(vNormal), normalize(cameraPosition - vWorld)));
          float fresnel = 0.045 + 0.18 * pow(1.0 - facing, 5.0);
          gl_FragColor = vec4(reflection, fresnel);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
        }
      `,
    },
  });
  pane.name = "Night Train reflective window";
  pane.position.set(0, 1.42, -1.345);
  const material = pane.material as THREE.ShaderMaterial;
  material.transparent = true;
  material.depthWrite = false;
  pane.castShadow = false;
  pane.receiveShadow = false;
  room.root.add(room.moving(pane));
  // Millimetre beads and short faint trails, on the glass rather than in space.
  const rainMaterial = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false,
    uniforms: { uTime: { value: 0 } },
    vertexShader: `varying vec2 vUv; void main() {
      vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }`,
    fragmentShader: /* glsl */ `
      uniform float uTime;
      varying vec2 vUv;
      float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
      void main() {
        vec2 grid = vUv * vec2(76.0, 42.0);
        vec2 cell = floor(grid), p = fract(grid) - 0.5;
        float seed = hash(cell);
        p.x -= (hash(cell + 3.1) - 0.5) * 0.5;
        p.y -= sin(uTime * (0.024 + seed * 0.016) + seed * 19.0) * 0.16;
        float radius = length(p / vec2(0.055, 0.11));
        float bead = (1.0 - smoothstep(0.48, 1.0, radius)) * step(0.89, seed);
        float trail = (1.0 - smoothstep(0.008, 0.026, abs(p.x)))
          * smoothstep(0.02, 0.06, p.y) * (1.0 - smoothstep(0.17, 0.38, p.y))
          * step(0.972, seed);
        float alpha = bead * 0.10 + trail * 0.055;
        if (alpha < 0.003) discard;
        gl_FragColor = vec4(vec3(0.46, 0.60, 0.68), alpha);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }
    `,
  });
  const rain = room.moving(room.mesh(new THREE.PlaneGeometry(1.61, 0.97), rainMaterial, [0, 1.42, -1.331]));
  rain.name = "Night Train glass droplets";
  let disposed = false;
  return {
    update(elapsed: number) {
      if (!disposed) rainMaterial.uniforms.uTime.value = Math.max(0, elapsed);
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      pane.removeFromParent();
      rain.removeFromParent();
      // Reflector.dispose owns the material and render target, not its geometry.
      pane.dispose();
      geometry.dispose();
    },
  };
}
