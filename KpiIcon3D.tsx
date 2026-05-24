"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { useRef } from "react";
import * as THREE from "three";

interface ShapeProps {
  type: "box" | "torus" | "octahedron" | "sphere";
  color: string;
}

function RotatingShape({ type, color }: ShapeProps) {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((state, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.x += delta * 0.5;
      meshRef.current.rotation.y += delta * 0.8;
    }
  });

  return (
    <mesh ref={meshRef}>
      {type === "box" && <boxGeometry args={[1.5, 1.5, 1.5]} />}
      {type === "torus" && <torusGeometry args={[1.2, 0.4, 16, 32]} />}
      {type === "octahedron" && <octahedronGeometry args={[1.4, 0]} />}
      {type === "sphere" && <sphereGeometry args={[1.2, 16, 16]} />}
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={0.6}
        wireframe={type === "sphere"}
        roughness={0.2}
        metalness={0.8}
      />
    </mesh>
  );
}

export default function KpiIcon3D({ type, color }: ShapeProps) {
  return (
    <div className="w-12 h-12 pointer-events-none drop-shadow-[0_0_10px_rgba(255,255,255,0.1)]">
      <Canvas camera={{ position: [0, 0, 4] }} gl={{ alpha: true }}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1.5} />
        <RotatingShape type={type} color={color} />
      </Canvas>
    </div>
  );
}