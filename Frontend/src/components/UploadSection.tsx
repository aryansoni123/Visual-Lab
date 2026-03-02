import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileImage, Box, CheckCircle2, X, ArrowRight } from 'lucide-react';

interface UploadSectionProps {
  onImagesUpload: (files: File[]) => void;
  onStlUpload: (file: File) => void;
  isProcessing: boolean;
}

export const UploadSection = ({ onImagesUpload, onStlUpload, isProcessing }: UploadSectionProps) => {
  const [images, setImages] = useState<File[]>([]);
  const [stlFile, setStlFile] = useState<File | null>(null);
  
  const imageInputRef = useRef<HTMLInputElement>(null);
  const stlInputRef = useRef<HTMLInputElement>(null);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files).slice(0, 3);
      setImages(selectedFiles);
      onImagesUpload(selectedFiles);
    }
  };

  const handleStlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setStlFile(e.target.files[0]);
      onStlUpload(e.target.files[0]);
    }
  };

  const removeImage = (index: number) => {
    const newImages = images.filter((_, i) => i !== index);
    setImages(newImages);
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', padding: '4rem 0' }}>
      {/* 2D Image Upload Section */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        style={{ 
          background: 'var(--bg-white)', 
          padding: '2.5rem', 
          borderRadius: '24px', 
          boxShadow: 'var(--shadow-md)',
          border: '1px solid var(--border-color)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
          <div style={{ background: 'rgba(255, 107, 0, 0.1)', padding: '0.75rem', borderRadius: '12px' }}>
            <FileImage color="var(--primary-orange)" size={24} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', marginBottom: '0.25rem' }}>Source Images</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Upload 3 reference images for processing</p>
          </div>
        </div>

        <div 
          onClick={() => imageInputRef.current?.click()}
          style={{ 
            border: '2px dashed var(--border-color)', 
            borderRadius: '16px', 
            padding: '3rem 2rem', 
            textAlign: 'center',
            cursor: 'pointer',
            transition: 'all 0.2s ease'
          }}
          onMouseOver={(e) => e.currentTarget.style.borderColor = 'var(--primary-orange)'}
          onMouseOut={(e) => e.currentTarget.style.borderColor = 'var(--border-color)'}
        >
          <Upload size={32} color="var(--text-muted)" style={{ marginBottom: '1rem' }} />
          <p style={{ fontWeight: 500 }}>Click to upload images</p>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>PNG, JPG up to 10MB each</p>
          <input 
            type="file" 
            multiple 
            accept="image/*" 
            ref={imageInputRef} 
            onChange={handleImageChange} 
            style={{ display: 'none' }} 
          />
        </div>

        <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
          <AnimatePresence>
            {images.map((file, idx) => (
              <motion.div 
                key={idx}
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.8, opacity: 0 }}
                style={{ position: 'relative', width: '80px', height: '80px' }}
              >
                <img 
                  src={URL.createObjectURL(file)} 
                  alt="preview" 
                  style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '8px' }} 
                />
                <button 
                  onClick={() => removeImage(idx)}
                  style={{ 
                    position: 'absolute', 
                    top: '-8px', 
                    right: '-8px', 
                    background: '#000', 
                    color: '#fff', 
                    borderRadius: '50%', 
                    width: '20px', 
                    height: '20px', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center' 
                  }}
                >
                  <X size={12} />
                </button>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </motion.div>

      {/* STL Upload Section */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ delay: 0.1 }}
        style={{ 
          background: 'var(--bg-white)', 
          padding: '2.5rem', 
          borderRadius: '24px', 
          boxShadow: 'var(--shadow-md)',
          border: '1px solid var(--border-color)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
          <div style={{ background: 'rgba(255, 107, 0, 0.1)', padding: '0.75rem', borderRadius: '12px' }}>
            <Box color="var(--primary-orange)" size={24} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.25rem', marginBottom: '0.25rem' }}>3D Model Asset</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Upload the target STL file</p>
          </div>
        </div>

        {!stlFile ? (
          <div 
            onClick={() => stlInputRef.current?.click()}
            style={{ 
              border: '2px dashed var(--border-color)', 
              borderRadius: '16px', 
              padding: '3rem 2rem', 
              textAlign: 'center',
              cursor: 'pointer'
            }}
          >
            <Upload size={32} color="var(--text-muted)" style={{ marginBottom: '1rem' }} />
            <p style={{ fontWeight: 500 }}>Click to upload STL</p>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>STL files only</p>
            <input 
              type="file" 
              accept=".stl" 
              ref={stlInputRef} 
              onChange={handleStlChange} 
              style={{ display: 'none' }} 
            />
          </div>
        ) : (
          <div style={{ 
            background: 'var(--bg-off-white)', 
            padding: '2rem', 
            borderRadius: '16px', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between' 
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <CheckCircle2 color="#10B981" />
              <div>
                <p style={{ fontWeight: 600 }}>{stlFile.name}</p>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Ready for visualization</p>
              </div>
            </div>
            <button 
              onClick={() => setStlFile(null)}
              style={{ color: 'var(--text-muted)' }}
            >
              <X size={20} />
            </button>
          </div>
        )}

        <button 
          disabled={images.length < 3 || !stlFile || isProcessing}
          style={{ 
            width: '100%', 
            marginTop: '2rem', 
            padding: '1rem', 
            background: images.length >= 3 && stlFile ? 'var(--primary-orange)' : '#ccc', 
            color: '#fff', 
            borderRadius: '12px', 
            fontWeight: 600,
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            gap: '0.5rem'
          }}
        >
          {isProcessing ? 'Processing...' : 'Generate 3D Assets'}
          <ArrowRight size={18} />
        </button>
      </motion.div>
    </div>
  );
};
