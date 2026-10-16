import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { sound } from '../services/sound';
import { RotateCw, ZoomIn, Eye, RotateCcw } from 'lucide-react';

interface ExosuitViewerProps {
  className?: string;
}

export const ExosuitViewer: React.FC<ExosuitViewerProps> = ({ className = '' }) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const [autoRotate, setAutoRotate] = useState<boolean>(true);
  const [cameraMode, setCameraMode] = useState<'default' | 'front' | 'side' | 'back' | 'zoom'>('default');

  const controlsRef = useRef<{
    setTargetPos: (x: number, y: number, z: number) => void;
    toggleRotate: () => void;
  }>({
    setTargetPos: () => {},
    toggleRotate: () => {},
  });

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || 380;
    const height = container.clientHeight || 340;

    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x060d1a, 0.04);

    const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100);
    const targetCameraPos = new THREE.Vector3(3.4, 0.9, 6.8);
    camera.position.copy(targetCameraPos);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.35;
    container.appendChild(renderer.domElement);

    // 2. Lighting Setup
    const ambientLight = new THREE.AmbientLight(0x1e293b, 1.8);
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0xfff5ea, 2.8);
    keyLight.position.set(5, 8, 5);
    scene.add(keyLight);

    const cyanRimLight = new THREE.DirectionalLight(0x00f0ff, 3.2);
    cyanRimLight.position.set(-6, 2, -4);
    scene.add(cyanRimLight);

    const underGlow = new THREE.PointLight(0x00f0ff, 1.5, 8);
    underGlow.position.set(0, -3.5, 0);
    scene.add(underGlow);

    // 3. Mark VII Exosuit Procedural Assembly
    const suit = new THREE.Group();
    scene.add(suit);
    suit.position.y = -0.3;

    // Materials
    const redMat = new THREE.MeshStandardMaterial({
      color: 0x991b1b, // Hot-rod crimson
      metalness: 0.85,
      roughness: 0.22,
    });

    const goldMat = new THREE.MeshStandardMaterial({
      color: 0xd97706, // Titanium gold
      metalness: 0.92,
      roughness: 0.2,
    });

    const titaniumMat = new THREE.MeshStandardMaterial({
      color: 0x1e293b, // Dark titanium joints
      metalness: 0.95,
      roughness: 0.35,
    });

    const cyanGlowMat = new THREE.MeshStandardMaterial({
      color: 0x00f0ff,
      emissive: 0x00f0ff,
      emissiveIntensity: 3.5,
      roughness: 0.05,
    });

    // Helper to build suit parts
    const addMesh = (geo: THREE.BufferGeometry, mat: THREE.Material, parent: THREE.Object3D, pos?: [number, number, number], rot?: [number, number, number]) => {
      const m = new THREE.Mesh(geo, mat);
      if (pos) m.position.set(...pos);
      if (rot) m.rotation.set(...rot);
      parent.add(m);
      return m;
    };

    // A. HELMET
    const helmetGroup = new THREE.Group();
    helmetGroup.position.set(0, 1.85, 0);
    suit.add(helmetGroup);

    // Cranium Dome
    const domeGeo = new THREE.SphereGeometry(0.38, 24, 24, 0, Math.PI * 2, 0, Math.PI * 0.7);
    addMesh(domeGeo, redMat, helmetGroup, [0, 0.05, 0]);

    // Faceplate (Gold)
    const faceplateGeo = new THREE.CylinderGeometry(0.28, 0.22, 0.45, 16, 1, false, Math.PI * 0.15, Math.PI * 0.7);
    addMesh(faceplateGeo, goldMat, helmetGroup, [0, -0.06, 0.16], [0, Math.PI * 0.65, 0]);

    // Eye Optics (Cyan emissive slits)
    const eyeGeo = new THREE.BoxGeometry(0.1, 0.025, 0.03);
    addMesh(eyeGeo, cyanGlowMat, helmetGroup, [-0.11, -0.02, 0.35], [0, 0.12, 0]);
    addMesh(eyeGeo, cyanGlowMat, helmetGroup, [0.11, -0.02, 0.35], [0, -0.12, 0]);

    // Jaw / Chin Guard
    const jawGeo = new THREE.BoxGeometry(0.24, 0.12, 0.28);
    addMesh(jawGeo, redMat, helmetGroup, [0, -0.24, 0.12]);

    // B. TORSO & CHEST
    const torsoGroup = new THREE.Group();
    torsoGroup.position.set(0, 0.95, 0);
    suit.add(torsoGroup);

    // Upper Chest Plates (Red)
    const chestUpperGeo = new THREE.BoxGeometry(0.9, 0.55, 0.55);
    addMesh(chestUpperGeo, redMat, torsoGroup, [0, 0.3, 0]);

    // Gold Pec Plates
    const pecGeo = new THREE.BoxGeometry(0.38, 0.35, 0.12);
    addMesh(pecGeo, goldMat, torsoGroup, [-0.22, 0.32, 0.26], [0, 0.1, 0]);
    addMesh(pecGeo, goldMat, torsoGroup, [0.22, 0.32, 0.26], [0, -0.1, 0]);

    // Chest Arc Reactor / Unibeam (Glowing cyan core)
    const unibeamCasingGeo = new THREE.CylinderGeometry(0.14, 0.14, 0.08, 24);
    addMesh(unibeamCasingGeo, titaniumMat, torsoGroup, [0, 0.32, 0.3], [Math.PI / 2, 0, 0]);

    const unibeamCoreGeo = new THREE.CylinderGeometry(0.1, 0.1, 0.09, 24);
    addMesh(unibeamCoreGeo, cyanGlowMat, torsoGroup, [0, 0.32, 0.31], [Math.PI / 2, 0, 0]);

    // Abdominal Segmented Armor
    for (let i = 0; i < 3; i++) {
      const abGeo = new THREE.BoxGeometry(0.68 - i * 0.06, 0.12, 0.44);
      addMesh(abGeo, i % 2 === 0 ? titaniumMat : goldMat, torsoGroup, [0, 0.0 - i * 0.14, 0.04]);
    }

    // Pelvis / Hip Armor (Red & Gold)
    const pelvisGeo = new THREE.BoxGeometry(0.72, 0.28, 0.46);
    addMesh(pelvisGeo, redMat, suit, [0, 0.35, 0]);

    // C. SHOULDERS & ARMS
    const leftArm = new THREE.Group();
    const rightArm = new THREE.Group();
    leftArm.position.set(-0.65, 1.25, 0);
    rightArm.position.set(0.65, 1.25, 0);
    suit.add(leftArm);
    suit.add(rightArm);

    // Pauldrons (Shoulder bells)
    const pauldronGeo = new THREE.SphereGeometry(0.24, 16, 16, 0, Math.PI, 0, Math.PI);
    addMesh(pauldronGeo, redMat, leftArm, [0, 0.05, 0], [0, 0, Math.PI / 2]);
    addMesh(pauldronGeo, redMat, rightArm, [0, 0.05, 0], [0, 0, -Math.PI / 2]);

    // Biceps (Gold)
    const bicepGeo = new THREE.CylinderGeometry(0.12, 0.11, 0.45, 16);
    addMesh(bicepGeo, goldMat, leftArm, [-0.05, -0.28, 0]);
    addMesh(bicepGeo, goldMat, rightArm, [0.05, -0.28, 0]);

    // Forearms (Red)
    const forearmGeo = new THREE.CylinderGeometry(0.13, 0.1, 0.48, 16);
    addMesh(forearmGeo, redMat, leftArm, [-0.05, -0.7, 0.02]);
    addMesh(forearmGeo, redMat, rightArm, [0.05, -0.7, 0.02]);

    // Repulsor Palms (Cyan glow discs)
    const repulsorGeo = new THREE.CylinderGeometry(0.06, 0.06, 0.03, 16);
    addMesh(repulsorGeo, cyanGlowMat, leftArm, [-0.05, -0.96, 0.04], [Math.PI / 2, 0, 0]);
    addMesh(repulsorGeo, cyanGlowMat, rightArm, [0.05, -0.96, 0.04], [Math.PI / 2, 0, 0]);

    // D. LEGS & BOOTS
    const leftLeg = new THREE.Group();
    const rightLeg = new THREE.Group();
    leftLeg.position.set(-0.25, 0.2, 0);
    rightLeg.position.set(0.25, 0.2, 0);
    suit.add(leftLeg);
    suit.add(rightLeg);

    // Thighs (Red / Gold plates)
    const thighGeo = new THREE.CylinderGeometry(0.18, 0.15, 0.65, 16);
    addMesh(thighGeo, redMat, leftLeg, [0, -0.35, 0]);
    addMesh(thighGeo, redMat, rightLeg, [0, -0.35, 0]);

    // Knee Guards (Gold)
    const kneeGeo = new THREE.BoxGeometry(0.18, 0.16, 0.12);
    addMesh(kneeGeo, goldMat, leftLeg, [0, -0.7, 0.14]);
    addMesh(kneeGeo, goldMat, rightLeg, [0, -0.7, 0.14]);

    // Calves & Shins (Red)
    const calfGeo = new THREE.CylinderGeometry(0.17, 0.13, 0.75, 16);
    addMesh(calfGeo, redMat, leftLeg, [0, -1.15, 0]);
    addMesh(calfGeo, redMat, rightLeg, [0, -1.15, 0]);

    // Boots (Titanium & Red with repulsor soles)
    const bootGeo = new THREE.BoxGeometry(0.22, 0.14, 0.44);
    addMesh(bootGeo, titaniumMat, leftLeg, [0, -1.55, 0.08]);
    addMesh(bootGeo, titaniumMat, rightLeg, [0, -1.55, 0.08]);

    const soleGlowGeo = new THREE.BoxGeometry(0.16, 0.02, 0.34);
    addMesh(soleGlowGeo, cyanGlowMat, leftLeg, [0, -1.63, 0.08]);
    addMesh(soleGlowGeo, cyanGlowMat, rightLeg, [0, -1.63, 0.08]);

    // Circular Holo Platform beneath the Suit
    const platRingGeo = new THREE.TorusGeometry(1.4, 0.02, 16, 64);
    const platRing = addMesh(platRingGeo, cyanGlowMat, scene, [0, -2.0, 0], [Math.PI / 2, 0, 0]);

    const platInnerGeo = new THREE.RingGeometry(0.2, 1.35, 32);
    const platInnerMat = new THREE.MeshBasicMaterial({
      color: 0x00f0ff,
      transparent: true,
      opacity: 0.12,
      side: THREE.DoubleSide,
    });
    addMesh(platInnerGeo, platInnerMat, scene, [0, -2.01, 0], [Math.PI / 2, 0, 0]);

    // 4. Mouse Orbit Interaction
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      const deltaX = e.clientX - prevMouseX;
      const deltaY = e.clientY - prevMouseY;
      suit.rotation.y += deltaX * 0.01;
      camera.position.y = Math.max(-1, Math.min(3.5, camera.position.y - deltaY * 0.01));
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const onMouseUp = () => {
      isDragging = false;
    };

    const domEl = renderer.domElement;
    domEl.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);

    // 5. Camera Control Logic
    controlsRef.current.setTargetPos = (x: number, y: number, z: number) => {
      targetCameraPos.set(x, y, z);
    };

    // 6. Animation Loop
    let animId: number;
    let isAutoRotating = true;

    controlsRef.current.toggleRotate = () => {
      isAutoRotating = !isAutoRotating;
      setAutoRotate(isAutoRotating);
    };

    const animate = () => {
      animId = requestAnimationFrame(animate);

      // Auto-rotation
      if (isAutoRotating && !isDragging) {
        suit.rotation.y += 0.007;
      }

      // Smooth camera interpolation
      camera.position.lerp(targetCameraPos, 0.05);
      camera.lookAt(0, 0.2, 0);

      // Pulse hologram ring
      platRing.rotation.z += 0.01;

      renderer.render(scene, camera);
    };

    animate();

    // 7. Cleanup
    return () => {
      cancelAnimationFrame(animId);
      domEl.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  const setView = (mode: 'default' | 'front' | 'side' | 'back' | 'zoom') => {
    sound.playClick();
    setCameraMode(mode);
    if (mode === 'front') {
      controlsRef.current.setTargetPos(0, 0.4, 6.5);
    } else if (mode === 'side') {
      controlsRef.current.setTargetPos(6.5, 0.4, 0);
    } else if (mode === 'back') {
      controlsRef.current.setTargetPos(0, 0.4, -6.5);
    } else if (mode === 'zoom') {
      controlsRef.current.setTargetPos(0, 1.1, 3.2); // focus on chest unibeam & helmet
    } else {
      // default
      controlsRef.current.setTargetPos(3.4, 0.9, 6.8);
    }
  };

  const handleToggleRotate = () => {
    sound.playClick();
    controlsRef.current.toggleRotate();
  };

  return (
    <div className={`relative flex flex-col bg-slate-950/70 border border-cyan-500/20 rounded-xl overflow-hidden backdrop-blur-md ${className}`}>
      {/* Top Header Badge */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-cyan-500/20 bg-slate-900/60">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
          <span className="font-orbitron text-xs font-semibold tracking-wider text-cyan-300">
            MARK VII // EXOSUIT TELEMETRY
          </span>
        </div>
        <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-500/40 text-cyan-400">
          ONLINE | 3D RENDER
        </span>
      </div>

      {/* 3D Canvas Canvas Container */}
      <div ref={mountRef} className="relative w-full h-[320px] cursor-grab active:cursor-grabbing flex items-center justify-center">
        {/* Holographic grid watermark overlay */}
        <div className="absolute inset-0 stark-holo-grid pointer-events-none opacity-20" />
        <div className="absolute top-2 left-3 pointer-events-none font-mono text-[9px] text-cyan-500/60">
          SYS::3D_RENDERER_ACTIVE<br />
          MESH::MK7_COMPOSITE_TITANIUM<br />
          DRAG TO ORBIT
        </div>
      </div>

      {/* Control Buttons Bar matching reference image */}
      <div className="grid grid-cols-6 gap-1 p-2 bg-slate-900/80 border-t border-cyan-500/20 text-[10px] font-mono text-cyan-300">
        <button
          onClick={() => setView('front')}
          className={`py-1 px-1 rounded text-center transition-all border ${
            cameraMode === 'front'
              ? 'bg-cyan-500/30 border-cyan-400 text-cyan-200'
              : 'bg-slate-950/60 border-cyan-500/20 hover:border-cyan-400/50 hover:bg-cyan-950/40'
          }`}
        >
          FRONT
        </button>
        <button
          onClick={() => setView('side')}
          className={`py-1 px-1 rounded text-center transition-all border ${
            cameraMode === 'side'
              ? 'bg-cyan-500/30 border-cyan-400 text-cyan-200'
              : 'bg-slate-950/60 border-cyan-500/20 hover:border-cyan-400/50 hover:bg-cyan-950/40'
          }`}
        >
          SIDE
        </button>
        <button
          onClick={() => setView('back')}
          className={`py-1 px-1 rounded text-center transition-all border ${
            cameraMode === 'back'
              ? 'bg-cyan-500/30 border-cyan-400 text-cyan-200'
              : 'bg-slate-950/60 border-cyan-500/20 hover:border-cyan-400/50 hover:bg-cyan-950/40'
          }`}
        >
          BACK
        </button>
        <button
          onClick={handleToggleRotate}
          className={`py-1 px-1 rounded text-center transition-all flex items-center justify-center space-x-0.5 border ${
            autoRotate
              ? 'bg-cyan-500/30 border-cyan-400 text-cyan-200'
              : 'bg-slate-950/60 border-cyan-500/20 hover:border-cyan-400/50 hover:bg-cyan-950/40'
          }`}
          title="Toggle Turntable Rotation"
        >
          <RotateCw className="w-2.5 h-2.5 inline mr-0.5" />
          <span>ROT</span>
        </button>
        <button
          onClick={() => setView('zoom')}
          className={`py-1 px-1 rounded text-center transition-all flex items-center justify-center space-x-0.5 border ${
            cameraMode === 'zoom'
              ? 'bg-cyan-500/30 border-cyan-400 text-cyan-200'
              : 'bg-slate-950/60 border-cyan-500/20 hover:border-cyan-400/50 hover:bg-cyan-950/40'
          }`}
          title="Zoom to Chest Unibeam"
        >
          <ZoomIn className="w-2.5 h-2.5 inline mr-0.5" />
          <span>ZOOM</span>
        </button>
        <button
          onClick={() => setView('default')}
          className={`py-1 px-1 rounded text-center transition-all flex items-center justify-center space-x-0.5 border ${
            cameraMode === 'default'
              ? 'bg-cyan-500/30 border-cyan-400 text-cyan-200'
              : 'bg-slate-950/60 border-cyan-500/20 hover:border-cyan-400/50 hover:bg-cyan-950/40'
          }`}
          title="Reset to Isometric View"
        >
          <RotateCcw className="w-2.5 h-2.5 inline mr-0.5" />
          <span>RESET</span>
        </button>
      </div>
    </div>
  );
};
