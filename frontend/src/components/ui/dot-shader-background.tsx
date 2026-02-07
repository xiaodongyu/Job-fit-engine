"use client";

import { useMemo, useEffect } from "react";
import { Canvas, ThreeEvent, useFrame, useThree } from "@react-three/fiber";
import { shaderMaterial, useTrailTexture } from "@react-three/drei";
import { useTheme } from "next-themes";
import * as THREE from "three";

const DotMaterial = shaderMaterial(
  {
    time: 0,
    resolution: new THREE.Vector2(),
    dotColor: new THREE.Color("#111827"),
    bgColor: new THREE.Color("#ffffff"),
    mouseTrail: null,
    render: 0,
    rotation: 0,
    gridSize: 60,
    dotOpacity: 0.08,
  },
  /* glsl */ `
    void main() {
      gl_Position = vec4(position.xy, 0.0, 1.0);
    }
  `,
  /* glsl */ `
    uniform float time;
    uniform int render;
    uniform vec2 resolution;
    uniform vec3 dotColor;
    uniform vec3 bgColor;
    uniform sampler2D mouseTrail;
    uniform float rotation;
    uniform float gridSize;
    uniform float dotOpacity;

    vec2 rotate(vec2 uv, float angle) {
        float s = sin(angle);
        float c = cos(angle);
        mat2 rotationMatrix = mat2(c, -s, s, c);
        return rotationMatrix * (uv - 0.5) + 0.5;
    }

    vec2 coverUv(vec2 uv) {
      vec2 s = resolution.xy / max(resolution.x, resolution.y);
      vec2 newUv = (uv - 0.5) * s + 0.5;
      return clamp(newUv, 0.0, 1.0);
    }

    float sdfCircle(vec2 p, float r) {
        return length(p - 0.5) - r;
    }

    void main() {
      vec2 screenUv = gl_FragCoord.xy / resolution;
      vec2 uv = coverUv(screenUv);

      vec2 rotatedUv = rotate(uv, rotation);

      // Create a grid
      vec2 gridUv = fract(rotatedUv * gridSize);
      vec2 gridUvCenterInScreenCoords = rotate((floor(rotatedUv * gridSize) + 0.5) / gridSize, -rotation);

      // Screen mask
      float screenMask = smoothstep(0.0, 1.0, 1.0 - uv.y);
      vec2 centerDisplace = vec2(0.7, 1.1);
      float circleMaskCenter = length(uv - centerDisplace);
      float circleMaskFromCenter = smoothstep(0.5, 1.0, circleMaskCenter);
      
      float combinedMask = screenMask * circleMaskFromCenter;
      float circleAnimatedMask = sin(time * 2.0 + circleMaskCenter * 10.0);

      // Mouse trail effect
      float mouseInfluence = texture2D(mouseTrail, gridUvCenterInScreenCoords).r;
      
      float scaleInfluence = max(mouseInfluence * 0.5, circleAnimatedMask * 0.3);

      // Create dots with animated scale, influenced by mouse
      float dotSize = min(pow(circleMaskCenter, 2.0) * 0.3, 0.3);
      float sdfDot = sdfCircle(gridUv, dotSize * (1.0 + scaleInfluence * 0.5));
      float smoothDot = smoothstep(0.05, 0.0, sdfDot);

      float opacityInfluence = max(mouseInfluence * 50.0, circleAnimatedMask * 0.5);
      vec3 composition = mix(bgColor, dotColor, smoothDot * combinedMask * dotOpacity * (1.0 + opacityInfluence));

      gl_FragColor = vec4(composition, 1.0);

      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }
  `
);

function Scene() {
  const size = useThree((s) => s.size);
  const viewport = useThree((s) => s.viewport);
  const { resolvedTheme } = useTheme();

  const rotation = 0.12;
  const gridSize = 90;

  const themeColors =
    resolvedTheme === "dark"
      ? { dotColor: "#FFFFFF", bgColor: "#0b0b0c", dotOpacity: 0.045 }
      : { dotColor: "#111827", bgColor: "#FFFFFF", dotOpacity: 0.075 };

  const [trail, onMove] = useTrailTexture({
    size: 512,
    radius: 0.1,
    maxAge: 400,
    interpolate: 1,
    ease: function easeInOutCirc(x) {
      return x < 0.5
        ? (1 - Math.sqrt(1 - Math.pow(2 * x, 2))) / 2
        : (Math.sqrt(1 - Math.pow(-2 * x + 2, 2)) + 1) / 2;
    },
  });

  const dotMaterial = useMemo(() => new DotMaterial(), []);

  useEffect(() => {
    dotMaterial.uniforms.dotColor.value.setHex(themeColors.dotColor.replace("#", "0x"));
    dotMaterial.uniforms.bgColor.value.setHex(themeColors.bgColor.replace("#", "0x"));
    dotMaterial.uniforms.dotOpacity.value = themeColors.dotOpacity;
  }, [resolvedTheme, dotMaterial, themeColors.bgColor, themeColors.dotColor, themeColors.dotOpacity]);

  useFrame((state) => {
    dotMaterial.uniforms.time.value = state.clock.elapsedTime;
  });

  const scale = Math.max(viewport.width, viewport.height) / 2;

  return (
    <mesh scale={[scale, scale, 1]} onPointerMove={(e: ThreeEvent<PointerEvent>) => onMove(e)}>
      <planeGeometry args={[2, 2]} />
      <primitive
        object={dotMaterial}
        resolution={[size.width * viewport.dpr, size.height * viewport.dpr]}
        rotation={rotation}
        gridSize={gridSize}
        mouseTrail={trail}
        render={0}
      />
    </mesh>
  );
}

export const DotScreenShader = ({
  eventSource,
}: {
  eventSource?: HTMLElement;
}) => {
  return (
    <Canvas
      className="h-full w-full pointer-events-none"
      eventSource={eventSource}
      eventPrefix="client"
      gl={{
        antialias: true,
        powerPreference: "high-performance",
        outputColorSpace: THREE.SRGBColorSpace,
        toneMapping: THREE.NoToneMapping,
      }}
    >
      <Scene />
    </Canvas>
  );
};

