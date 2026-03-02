import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ModelViewer } from './components/ModelViewer';
import { TechnicalPlane } from './components/TechnicalPlane';
import { Image, Box, ArrowRight, Cpu, Database, Sun, Moon } from 'lucide-react';

type ViewType = 'front' | 'top' | 'side';

function App() {
  const [images, setImages] = useState<{ [key in ViewType]: File | null }>({
    front: null,
    top: null,
    side: null
  });
  const [stlUrl, setStlUrl] = useState<string | null>(null);
  const [isGenerated, setIsGenerated] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [viewMode, setViewMode] = useState<'solid' | 'wireframe'>('solid');
  const [isDarkMode, setIsDarkMode] = useState(true);

  const fileInputRefs = {
    front: useRef<HTMLInputElement>(null),
    top: useRef<HTMLInputElement>(null),
    side: useRef<HTMLInputElement>(null),
    stl: useRef<HTMLInputElement>(null)
  };

  const handleImageUpload = (view: ViewType, file: File) => {
    setImages(prev => ({ ...prev, [view]: file }));
  };

  const handleGenerate = () => {
    setIsProcessing(true);
    // Simulate generation delay
    setTimeout(() => {
      setIsProcessing(false);
      setIsGenerated(true);
    }, 2000);
  };

  const handleStlUpload = (file: File) => {
    const url = URL.createObjectURL(file);
    setStlUrl(url);
  };

  const isImagesReady = images.front && images.top && images.side;

  return (
    <div className="lab-container">
      {/* LEFT: CONTROLS */}
      <div className="control-panel">
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
          <div style={{ background: 'var(--primary-orange)', padding: '6px', borderRadius: '8px' }}>
            <Cpu color="#fff" size={20} />
          </div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.5px' }}>
            VISUAL_LAB<span style={{ fontWeight: 400, opacity: 0.5 }}>.io</span>
          </h1>
        </div>

        {/* Orthographic Views Container */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem', alignItems: 'center' }}>
            <h3 style={{ fontSize: '11px', fontWeight: 800, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '1px' }}>
              Reference Inputs
            </h3>
            {isGenerated && (
              <span style={{ fontSize: '10px', color: 'var(--primary-orange)', fontWeight: 700 }}>TECHNICAL PLOTTING ACTIVE</span>
            )}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {(['front', 'top', 'side'] as ViewType[]).map((view) => (
              <div key={view} className="upload-card" onClick={() => !isGenerated && fileInputRefs[view].current?.click()}>
                {isGenerated ? (
                  <TechnicalPlane 
                    label={view} 
                    axis={view === 'top' ? ['X', 'Y'] : view === 'front' ? ['Y', 'Z'] : ['X', 'Z']} 
                    generated={isGenerated} 
                  />
                ) : images[view] ? (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ width: '100%', height: '100%' }}>
                    <img 
                      src={URL.createObjectURL(images[view]!)} 
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
                      alt={view}
                    />
                    <span className="label-mini">{view} READY</span>
                  </motion.div>
                ) : (
                  <motion.div 
                    initial="initial"
                    whileHover="hover"
                    style={{ 
                      width: '100%', 
                      height: '100%', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      background: '#f2f2f2',
                      position: 'relative'
                    }}>
                    <motion.div 
                      variants={{
                        initial: { scale: 1, color: 'rgba(153, 153, 153, 0.3)', opacity: 1 },
                        hover: { scale: 1.1, color: 'var(--primary-orange)', opacity: 0.8 }
                      }}
                      transition={{ type: "spring", stiffness: 300, damping: 20 }}
                      style={{ 
                        fontSize: '32px', 
                        fontWeight: 900, 
                        letterSpacing: '6px',
                        userSelect: 'none',
                        textTransform: 'uppercase'
                      }}
                    >
                      {view}
                    </motion.div>
                  </motion.div>
                )}
                <input 
                  type="file" 
                  hidden 
                  ref={fileInputRefs[view]} 
                  onChange={(e) => e.target.files?.[0] && handleImageUpload(view, e.target.files[0])} 
                />
              </div>
            ))}
          </div>

          <AnimatePresence>
            {isImagesReady && !isGenerated && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                <button 
                  className="btn-generate"
                  onClick={handleGenerate}
                  disabled={isProcessing}
                >
                  {isProcessing ? 'SYNCHRONIZING...' : 'GENERATE 3D RECONSTRUCTION'}
                  {!isProcessing && <ArrowRight size={16} />}
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* RIGHT: VIEWPORT */}
      <div className="viewport-area" style={{ background: isDarkMode ? '#0a0a0a' : 'var(--bg-panel)' }}>
        {/* Floating Header */}
        <div style={{ 
          position: 'absolute', 
          top: '24px', 
          left: '24px', 
          right: '24px', 
          zIndex: 10, 
          display: 'flex', 
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
            <span style={{ 
              background: isDarkMode ? '#111' : '#fff', 
              color: isDarkMode ? '#fff' : '#111', 
              fontSize: '9px', 
              fontWeight: 900, 
              padding: '4px 8px', 
              borderRadius: '4px', 
              border: isDarkMode ? 'none' : '1px solid var(--border)',
              letterSpacing: '1px' 
            }}>
              PRIMARY_VIEWPORT
            </span>
            <div style={{ display: 'flex', gap: '1rem', color: 'var(--text-dim)', fontSize: '10px', fontWeight: 700 }}>
              <span 
                onClick={() => setViewMode('wireframe')}
                style={{ 
                  cursor: 'pointer', 
                  color: viewMode === 'wireframe' ? 'var(--primary-orange)' : (isDarkMode ? '#666' : 'var(--text-dim)') 
                }}
              >
                Wireframe
              </span>
              <span 
                onClick={() => setViewMode('solid')}
                style={{ 
                  cursor: 'pointer', 
                  color: viewMode === 'solid' ? 'var(--primary-orange)' : (isDarkMode ? '#666' : 'var(--text-dim)') 
                }}
              >
                Solid
              </span>
            </div>
          </div>
          
          {/* SUN/MOON SLIDER TOGGLE */}
          <div 
            onClick={() => setIsDarkMode(!isDarkMode)}
            style={{ 
              width: '70px',
              height: '35px',
              background: isDarkMode ? '#111' : '#fff',
              border: '1px solid var(--border)',
              borderRadius: '100px',
              padding: '4px',
              display: 'flex',
              alignItems: 'center',
              cursor: 'pointer',
              position: 'relative',
              transition: 'all 0.3s ease'
            }}
          >
            <motion.div
              animate={{ x: isDarkMode ? 35 : 0 }}
              transition={{ type: "spring", stiffness: 500, damping: 30 }}
              style={{
                width: '25px',
                height: '25px',
                background: isDarkMode ? 'var(--primary-orange)' : '#ffd700',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 2
              }}
            >
              {isDarkMode ? <Moon size={14} color="#fff" fill="#fff" /> : <Sun size={14} color="#fff" fill="#fff" />}
            </motion.div>
            <div style={{ 
              position: 'absolute', 
              inset: 0, 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center', 
              padding: '0 10px',
              opacity: 0.3
            }}>
              <Sun size={12} color={isDarkMode ? "#fff" : "var(--text-dim)"} />
              <Moon size={12} color={isDarkMode ? "#fff" : "var(--text-dim)"} />
            </div>
          </div>
        </div>

        <ModelViewer fileUrl={stlUrl} viewMode={viewMode} isDarkMode={isDarkMode} />

        {/* STL Upload Button - Floating */}
        {!isGenerated && (
          <div 
            style={{ 
              position: 'absolute', 
              bottom: '24px', 
              right: '24px', 
              zIndex: 10 
            }}
          >
             <motion.button 
               animate={{ 
                 backgroundColor: isDarkMode ? '#1a1a1a' : '#f5f5f5',
                 color: isDarkMode ? '#fff' : '#111',
                 borderColor: isDarkMode ? '#222' : '#ddd'
               }}
               transition={{ duration: 0.4, ease: "easeInOut" }}
               whileHover={{ scale: 1.05 }}
               whileTap={{ scale: 0.95 }}
               onClick={() => fileInputRefs.stl.current?.click()}
               style={{
                 border: '1px solid',
                 borderRadius: '12px',
                 padding: '12px 20px',
                 display: 'flex',
                 alignItems: 'center',
                 gap: '12px',
                 cursor: 'pointer',
                 fontSize: '11px',
                 fontWeight: 800,
                 textTransform: 'uppercase',
                 letterSpacing: '1.5px',
                 boxShadow: isDarkMode ? '0 8px 30px rgba(0,0,0,0.4)' : '0 8px 30px rgba(0,0,0,0.08)'
               }}
             >
               <Database size={16} color="var(--primary-orange)" />
               <span>Upload STL</span>
             </motion.button>
             <input 
                type="file" 
                hidden 
                accept=".stl"
                ref={fileInputRefs.stl} 
                onChange={(e) => e.target.files?.[0] && handleStlUpload(e.target.files[0])} 
              />
          </div>
        )}

        {!stlUrl && !isGenerated && (
          <div style={{ 
            position: 'absolute', 
            top: '50%', 
            left: '50%', 
            transform: 'translate(-50%, -50%)',
            textAlign: 'center'
          }}>
            <Box size={40} color="#ddd" style={{ marginBottom: '1.5rem' }} />
            <p style={{ fontSize: '11px', letterSpacing: '3px', textTransform: 'uppercase', color: 'var(--text-dim)', fontWeight: 800 }}>
              Awaiting Spatial Data
            </p>
          </div>
        )}

        {isProcessing && (
          <div style={{ 
            position: 'absolute', 
            inset: 0, 
            background: 'rgba(255,255,255,0.8)', 
            backdropFilter: 'blur(20px)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100
          }}>
             <motion.div 
               animate={{ rotate: 360 }} 
               transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
               style={{ marginBottom: '1rem' }}
             >
               <Cpu size={32} color="var(--primary-orange)" />
             </motion.div>
             <p style={{ fontSize: '12px', fontWeight: 800, letterSpacing: '2px' }}>CALCULATING GEOMETRY</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
