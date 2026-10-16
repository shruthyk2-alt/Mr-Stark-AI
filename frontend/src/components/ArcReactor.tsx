import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { sound } from '../services/sound';

interface ArcReactorProps {
  size?: number;
  state?: 'idle' | 'listening' | 'thinking' | 'speaking' | 'error';
  interactive?: boolean;
  onClick?: () => void;
  className?: string;
}

export const ArcReactor: React.FC<ArcReactorProps> = ({
  size = 220,
  state = 'idle',
  interactive = true,
  onClick,
  className = '',
}) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const stateRef = useRef(state);
  stateRef.current = state;

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
    camera.position.z = 5.2;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(size, size);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.4;
    container.appendChild(renderer.domElement);

    // 2. Lighting
    const ambientLight = new THREE.AmbientLight(0x0a1628, 1.5);
    scene.add(ambientLight);

    const coreLight = new THREE.PointLight(0x00f0ff, 3.5, 15);
    coreLight.position.set(0, 0, 1.2);
    scene.add(coreLight);

    const backRimLight = new THREE.PointLight(0x0088ff, 2, 10);
    backRimLight.position.set(0, 0, -2);
    scene.add(backRimLight);

    // 3. Reactor Assembly Group
    const reactorGroup = new THREE.Group();
    scene.add(reactorGroup);

    // Outer Palladium / Titanium Rim
    const outerRingGeo = new THREE.TorusGeometry(1.8, 0.12, 16, 64);
    const darkMetalMat = new THREE.MeshStandardMaterial({
      color: 0x1e293b,
      metalness: 0.9,
      roughness: 0.25,
    });
    const outerRing = new THREE.Mesh(outerRingGeo, darkMetalMat);
    reactorGroup.add(outerRing);

    // Segmented Outer Casing Ring
    const casingRingGeo = new THREE.TorusGeometry(1.55, 0.08, 16, 64);
    const casingRing = new THREE.Mesh(casingRingGeo, darkMetalMat);
    reactorGroup.add(casingRing);

    // Inner Glowing Cyan Energy Ring
    const glowRingGeo = new THREE.TorusGeometry(1.4, 0.09, 16, 64);
    const cyanGlowMat = new THREE.MeshStandardMaterial({
      color: 0x00f0ff,
      emissive: 0x00e5ff,
      emissiveIntensity: 2.2,
      roughness: 0.1,
    });
    const glowRing = new THREE.Mesh(glowRingGeo, cyanGlowMat);
    reactorGroup.add(glowRing);

    // 10 Electromagnetic Copper Coils spaced radially
    const coilsGroup = new THREE.Group();
    const coilGeo = new THREE.BoxGeometry(0.18, 0.38, 0.26);
    const copperMat = new THREE.MeshStandardMaterial({
      color: 0xd97706,
      metalness: 0.85,
      roughness: 0.3,
      emissive: 0x78350f,
      emissiveIntensity: 0.4,
    });

    const coilCount = 10;
    for (let i = 0; i < coilCount; i++) {
      const angle = (i / coilCount) * Math.PI * 2;
      const coil = new THREE.Mesh(coilGeo, copperMat);
      coil.position.x = Math.cos(angle) * 1.4;
      coil.position.y = Math.sin(angle) * 1.4;
      coil.rotation.z = angle;
      coilsGroup.add(coil);
    }
    reactorGroup.add(coilsGroup);

    // Inner Core Group (Rotates independently)
    const innerCoreGroup = new THREE.Group();
    reactorGroup.add(innerCoreGroup);

    // Inner Triangular Palladium Frame
    const triPoints: THREE.Vector3[] = [];
    const triRadius = 0.85;
    for (let i = 0; i < 3; i++) {
      const angle = (i / 3) * Math.PI * 2 - Math.PI / 2;
      triPoints.push(new THREE.Vector3(Math.cos(angle) * triRadius, Math.sin(angle) * triRadius, 0.1));
    }
    triPoints.push(triPoints[0]); // close loop
    const triLineGeo = new THREE.BufferGeometry().setFromPoints(triPoints);
    const triLineMat = new THREE.LineBasicMaterial({ color: 0x00f0ff, linewidth: 3 });
    const triLine = new THREE.Line(triLineGeo, triLineMat);
    innerCoreGroup.add(triLine);

    // Central Unibeam Core (Glow Sphere)
    const centerSphereGeo = new THREE.SphereGeometry(0.42, 32, 32);
    const centerSphereMat = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      emissive: 0x00f0ff,
      emissiveIntensity: 3.5,
      roughness: 0.0,
      metalness: 0.1,
    });
    const centerSphere = new THREE.Mesh(centerSphereGeo, centerSphereMat);
    innerCoreGroup.add(centerSphere);

    // Holographic Energy Particles
    const particleCount = 75;
    const particleGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      const angle = Math.random() * Math.PI * 2;
      const radius = 0.35 + Math.random() * 1.35;
      positions[i * 3] = Math.cos(angle) * radius;
      positions[i * 3 + 1] = Math.sin(angle) * radius;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 0.4;
    }
    particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const particleMat = new THREE.PointsMaterial({
      color: 0x38bdf8,
      size: 0.05,
      transparent: true,
      opacity: 0.85,
      blending: THREE.AdditiveBlending,
    });
    const particles = new THREE.Points(particleGeo, particleMat);
    reactorGroup.add(particles);

    // 4. Animation Loop
    let animId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();
      const currentState = stateRef.current;

      // Base rotation
      let baseSpeed = 0.35;
      let innerSpeed = -0.7;
      let intensityMultiplier = 1.0;

      if (currentState === 'thinking') {
        baseSpeed = 1.8;
        innerSpeed = -3.2;
        intensityMultiplier = 1.5 + Math.sin(elapsed * 12) * 0.4;
      } else if (currentState === 'listening') {
        baseSpeed = 0.8;
        innerSpeed = -1.2;
        intensityMultiplier = 1.3 + Math.sin(elapsed * 6) * 0.3;
      } else if (currentState === 'speaking') {
        baseSpeed = 0.9;
        innerSpeed = -1.4;
        intensityMultiplier = 1.4 + Math.sin(elapsed * 16) * 0.5;
      } else if (currentState === 'error') {
        baseSpeed = 0.2;
        innerSpeed = -0.2;
        cyanGlowMat.emissive.setHex(0xef4444);
        coreLight.color.setHex(0xef4444);
      } else {
        // idle
        cyanGlowMat.emissive.setHex(0x00e5ff);
        coreLight.color.setHex(0x00f0ff);
        intensityMultiplier = 1.0 + Math.sin(elapsed * 2.2) * 0.2;
      }

      reactorGroup.rotation.z += 0.005 * baseSpeed;
      innerCoreGroup.rotation.z += 0.008 * innerSpeed;
      particles.rotation.z -= 0.004 * baseSpeed;

      // Pulse breathing
      cyanGlowMat.emissiveIntensity = 2.0 * intensityMultiplier;
      centerSphereMat.emissiveIntensity = 3.2 * intensityMultiplier;
      coreLight.intensity = 3.2 * intensityMultiplier;

      renderer.render(scene, camera);
    };

    animate();

    // 5. Cleanup
    return () => {
      cancelAnimationFrame(animId);
      renderer.dispose();
      outerRingGeo.dispose();
      glowRingGeo.dispose();
      casingRingGeo.dispose();
      coilGeo.dispose();
      centerSphereGeo.dispose();
      particleGeo.dispose();
      darkMetalMat.dispose();
      cyanGlowMat.dispose();
      copperMat.dispose();
      centerSphereMat.dispose();
      particleMat.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [size]);

  const handleClick = () => {
    sound.playPulse();
    if (onClick) onClick();
  };

  return (
    <div
      ref={mountRef}
      onClick={interactive ? handleClick : undefined}
      className={`relative inline-flex items-center justify-center cursor-pointer transition-transform duration-300 hover:scale-105 active:scale-95 ${className}`}
      title="STARK ARC REACTOR MK VII // Click to pulse"
    >
      {/* Outer ambient glow ring */}
      <div
        className="absolute inset-0 rounded-full pointer-events-none"
        style={{
          boxShadow:
            state === 'error'
              ? '0 0 35px rgba(239, 68, 68, 0.45)'
              : '0 0 35px rgba(0, 240, 255, 0.35)',
        }}
      />
    </div>
  );
};
