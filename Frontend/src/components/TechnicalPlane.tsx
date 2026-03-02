import { useMemo } from 'react';
import { motion } from 'framer-motion';

interface TechnicalPlaneProps {
  label: string;
  axis: [string, string];
  generated: boolean;
}

export const TechnicalPlane = ({ label, axis, generated }: TechnicalPlaneProps) => {
  const points = useMemo(() => {
    return Array.from({ length: 15 }).map((_, i) => ({
      x: Math.random() * 80 + 10,
      y: Math.random() * 80 + 10,
      id: i
    }));
  }, []);

  return (
    <div className="coord-plane">
      <span className="label-mini">{label} ({axis[0]}{axis[1]})</span>
      
      {/* Dynamic Coordinate Indicators */}
      <div style={{ position: 'absolute', bottom: '12px', right: '12px', fontSize: '9px', color: '#ccc', textAlign: 'right' }}>
        <p>RECON_ACC: 0.9982</p>
        <p>POINTS: 14,290</p>
      </div>

      <svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none">
        {generated && (
          <>
            {/* Draw procedural edges */}
            {points.map((p, i) => i < points.length - 1 && (
              <motion.line
                key={`line-${i}`}
                x1={p.x} y1={p.y} 
                x2={points[i+1].x} y2={points[i+1].y}
                stroke="var(--primary-orange)"
                strokeWidth="0.2"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 1, delay: i * 0.05 }}
              />
            ))}
            {/* Draw procedural points */}
            {points.map((p) => (
              <motion.circle 
                key={p.id}
                cx={p.x} cy={p.y} r="0.6" 
                fill="var(--text-main)"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 + Math.random() }}
              />
            ))}
          </>
        )}
      </svg>
    </div>
  );
};
