import React, { useState, useRef, useEffect } from 'react';

const BeforeAfterSlider = ({ before, after, width }) => {
  const [sliderPosition, setSliderPosition] = useState(50);
  const containerRef = useRef(null);
  const isDraggingRef = useRef(false);

  const handleMouseDown = () => {
    isDraggingRef.current = true;
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  const handleMouseMove = (e) => {
    if (!isDraggingRef.current || !containerRef.current) return;
    
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
    const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
    
    setSliderPosition(percentage);
  };

  const handleTouchMove = (e) => {
    if (!containerRef.current) return;
    
    const touch = e.touches[0];
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(touch.clientX - rect.left, rect.width));
    const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
    
    setSliderPosition(percentage);
  };

  useEffect(() => {
    document.addEventListener('mouseup', handleMouseUp);
    return () => {
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  return (
    <div 
      ref={containerRef}
      style={{ 
        position: 'relative', 
        width: width || '100%', 
        overflow: 'hidden',
        userSelect: 'none'
      }}
      onMouseMove={handleMouseMove}
      onTouchMove={handleTouchMove}
    >
      {/* After image (full width) */}
      <div style={{ position: 'absolute', width: '100%', height: '100%' }}>
        <img src={after} alt="After" style={{ width: '100%', display: 'block' }} />
      </div>
      
      {/* Before image (clipped) */}
      <div 
        style={{ 
          position: 'absolute', 
          width: `${sliderPosition}%`, 
          height: '100%',
          overflow: 'hidden'
        }}
      >
        <img src={before} alt="Before" style={{ width: '100%', display: 'block' }} />
      </div>
      
      {/* Slider control */}
      <div 
        style={{ 
          position: 'absolute',
          left: `calc(${sliderPosition}% - 1px)`,
          top: 0,
          bottom: 0,
          width: '2px',
          backgroundColor: 'white',
          cursor: 'ew-resize',
          boxShadow: '0 0 5px rgba(0,0,0,0.5)'
        }}
        onMouseDown={handleMouseDown}
        onTouchStart={handleMouseDown}
      >
        <div 
          style={{
            position: 'absolute',
            left: '-10px',
            top: 'calc(50% - 10px)',
            width: '20px',
            height: '20px',
            borderRadius: '50%',
            backgroundColor: 'white',
            border: '2px solid white',
            boxShadow: '0 0 5px rgba(0,0,0,0.5)'
          }}
        />
      </div>
    </div>
  );
};

export default BeforeAfterSlider;
