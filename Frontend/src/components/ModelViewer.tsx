import { Suspense, useMemo, useRef } from 'react';
import { Canvas, useLoader } from '@react-three/fiber';
import { 
  OrbitControls, 
  Center, 
  Environment, 
  ContactShadows, 
  PerspectiveCamera,
  Float,
  BakeShadows
} from '@react-three/drei';
import * as THREE from 'three';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';
import { motion } from 'framer-motion';

interface ModelProps {
  url: string;
  viewMode: 'solid' | 'wireframe';
}

const Model = ({ url, viewMode }: ModelProps) => {
  const geometry = useLoader(STLLoader, url);
  const meshRef = useRef<THREE.Mesh>(null);

  // Compute normals and center the geometry if not already handled
  useMemo(() => {
    geometry.computeVertexNormals();
    geometry.center();
  }, [geometry]);

  return (
    <group>
      {/* Main Model */}
      <mesh 
        ref={meshRef} 
        geometry={geometry} 
        castShadow 
        receiveShadow
      >
        <meshPhysicalMaterial 
          color="#FF6B00"
          metalness={0.9}
          roughness={0.15}
          clearcoat={1}
          clearcoatRoughness={0.1}
          emissive="#FF6B00"
          emissiveIntensity={0.05}
          envMapIntensity={1.5}
          wireframe={viewMode === 'wireframe'}
        />
      </mesh>

      {/* Subtle Wireframe Overlay for "Technical" look - only show in solid mode */}
      {viewMode === 'solid' && (
        <mesh geometry={geometry}>
          <meshBasicMaterial 
            color="#ffffff" 
            wireframe 
            transparent 
            opacity={0.05} 
          />
        </mesh>
      )}
    </group>
  );
};

interface ModelViewerProps {
  fileUrl: string | null;
  viewMode: 'solid' | 'wireframe';
  isDarkMode: boolean;
}

const Scene = ({ fileUrl, viewMode, isDarkMode }: { fileUrl: string; viewMode: 'solid' | 'wireframe'; isDarkMode: boolean }) => {
  const controlsRef = useRef<any>(null);

  return (
    <>
      <PerspectiveCamera makeDefault position={[5, 5, 5]} fov={35} />
      <OrbitControls 
        ref={controlsRef}
        makeDefault 
        enableDamping 
        dampingFactor={0.1}
        minDistance={0.1}
        maxDistance={1000}
        zoomSpeed={1.5}
        target={[0, 0, 0]}
      />

      <color attach="background" args={[isDarkMode ? '#0a0a0a' : '#fafafa']} />
      
      <Suspense fallback={null}>
        <Center top onCentered={({ width, height, depth }) => {
          // Calculate the bounding sphere or max dimension to fit the camera
          const maxDim = Math.max(width, height, depth);
          const fov = 35;
          const distance = maxDim / (2 * Math.tan((fov * Math.PI) / 360)) * 1.5;
          
          if (controlsRef.current) {
            const camera = controlsRef.current.object;
            camera.position.set(distance, distance, distance);
            controlsRef.current.update();
          }
        }}>
          <Model url={fileUrl} viewMode={viewMode} />
        </Center>

        {/* Lighting Setup for "Premium Optics" */}
        <spotLight position={[10, 15, 10]} angle={0.3} penumbra={1} castShadow intensity={isDarkMode ? 2 : 1.5} shadow-bias={-0.0001} />
        <ambientLight intensity={isDarkMode ? 0.2 : 0.6} />
        <pointLight position={[-10, -10, -10]} color="#FF6B00" intensity={isDarkMode ? 1 : 0.5} />
        <pointLight position={[0, 10, 0]} intensity={isDarkMode ? 0.5 : 0.3} />
        
        {/* Ground & Shadows */}
        <ContactShadows 
          position={[0, -0.01, 0]} 
          opacity={isDarkMode ? 0.5 : 0.2} 
          scale={100} 
          blur={2.4} 
          far={4.5} 
        />
        
        <Environment preset="studio" />
        <BakeShadows />
      </Suspense>

      {/* Technical Grid */}
      <gridHelper 
        args={[2000, 500, isDarkMode ? '#222' : '#ddd', isDarkMode ? '#111' : '#eee']} 
        position={[0, -0.02, 0]} 
      />
    </>
  );
};

export const ModelViewer = ({ fileUrl, viewMode, isDarkMode }: ModelViewerProps) => {
  return (
    <motion.div 
      animate={{ backgroundColor: isDarkMode ? '#0a0a0a' : '#fafafa' }}
      transition={{ duration: 0.4, ease: "easeInOut" }}
      style={{ 
        width: '100%', 
        height: '100%', 
        position: 'relative'
      }}
    >
      {!fileUrl ? (
        <div style={{ 
          height: '100%', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          flexDirection: 'column',
          gap: '1rem'
        }}>
          <div style={{ 
            width: '2px', 
            height: '40px', 
            background: 'linear-gradient(to bottom, transparent, var(--primary-orange), transparent)' 
          }} />
          <p style={{ 
            letterSpacing: '4px', 
            textTransform: 'uppercase', 
            fontSize: '10px', 
            fontWeight: 800,
            color: isDarkMode ? '#444' : '#333' 
          }}>
            SYSTEM_IDLE: NO_ASSET
          </p>
        </div>
      ) : (
        <Canvas 
          shadows 
          gl={{ 
            antialias: true, 
            toneMapping: THREE.ACESFilmicToneMapping,
            outputColorSpace: THREE.SRGBColorSpace 
          }}
        >
          <Scene fileUrl={fileUrl} viewMode={viewMode} isDarkMode={isDarkMode} />
        </Canvas>
      )}
    </motion.div>
  );
};
