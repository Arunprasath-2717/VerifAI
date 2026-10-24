/**
 * TiltCard — CultUI/Aceternity-inspired 3D tilt hover effect.
 * Tracks cursor position and applies rotateX/rotateY transforms for a
 * natural-feeling depth effect that resets smoothly on mouse leave.
 */
import React, { useRef, useState, useCallback } from 'react';

interface TiltCardProps {
  children: React.ReactNode;
  className?: string;
  /** Maximum tilt angle in degrees (default: 4) */
  maxTilt?: number;
  /** Scale on hover (default: 1.02) */
  hoverScale?: number;
  /** Perspective distance in px (default: 1200) */
  perspective?: number;
  /** Transition speed in ms (default: 400) */
  speed?: number;
  onClick?: (e: React.MouseEvent<HTMLDivElement>) => void;
  style?: React.CSSProperties;
}

export const TiltCard: React.FC<TiltCardProps> = ({
  children,
  className = '',
  maxTilt = 4,
  hoverScale = 1.02,
  perspective = 1200,
  speed = 400,
  onClick,
  style = {},
}) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const [transform, setTransform] = useState('');
  const [isHovered, setIsHovered] = useState(false);
  const requestRef = useRef<number>(0);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;

    // Cancel any pending animation frame
    if (requestRef.current) {
      cancelAnimationFrame(requestRef.current);
    }

    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    // Calculate rotation: Y axis based on horizontal position, X axis on vertical
    const rotateY = ((x - centerX) / centerX) * maxTilt;
    const rotateX = -((y - centerY) / centerY) * maxTilt;

    requestRef.current = requestAnimationFrame(() => {
      setTransform(
        `perspective(${perspective}px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) scale3d(${hoverScale}, ${hoverScale}, ${hoverScale})`
      );
    });
  }, [maxTilt, hoverScale, perspective]);

  const handleMouseEnter = useCallback(() => {
    setIsHovered(true);
  }, []);

  const handleMouseLeave = useCallback(() => {
    setIsHovered(false);
    setTransform('');
    if (requestRef.current) {
      cancelAnimationFrame(requestRef.current);
    }
  }, []);

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      className={className}
      style={{
        ...style,
        transform: isHovered ? transform : 'perspective(1200px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)',
        transition: `transform ${speed}ms cubic-bezier(0.03, 0.98, 0.52, 0.99)`,
        transformStyle: 'preserve-3d',
        willChange: isHovered ? 'transform' : 'auto',
      }}
    >
      {children}
    </div>
  );
};

export default TiltCard;
