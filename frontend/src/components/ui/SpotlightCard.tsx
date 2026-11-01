/**
 * SpotlightCard — ReactBits/CultUI-inspired mouse-tracking spotlight overlay
 * Tracks cursor position and renders a radial gradient that follows the pointer.
 * Pairs with CSS classes from ReactBitsAnimations.css.
 */
import React, { useRef, useState, useCallback } from 'react';

interface SpotlightCardProps {
  children: React.ReactNode;
  className?: string;
  spotlightColor?: string;
  spotlightSize?: number;
  /** Extra CSS classes only applied on hover */
  hoverClassName?: string;
  onClick?: (e: React.MouseEvent<HTMLDivElement>) => void;
  style?: React.CSSProperties;
}

export const SpotlightCard: React.FC<SpotlightCardProps> = ({
  children,
  className = '',
  spotlightColor,
  spotlightSize = 650,
  hoverClassName = '',
  onClick,
  style = {},
}) => {
  const divRef = useRef<HTMLDivElement>(null);
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!divRef.current) return;
    const rect = divRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    divRef.current.style.setProperty('--spotlight-x', `${x}px`);
    divRef.current.style.setProperty('--spotlight-y', `${y}px`);
  }, []);

  const handleMouseEnter = useCallback(() => {
    if (divRef.current) {
      divRef.current.style.setProperty('--spotlight-opacity', '1');
    }
    setIsHovered(true);
  }, []);

  const handleMouseLeave = useCallback(() => {
    if (divRef.current) {
      divRef.current.style.setProperty('--spotlight-opacity', '0');
    }
    setIsHovered(false);
  }, []);

  const combinedStyle: React.CSSProperties = {
    ...style,
    ...(spotlightColor ? { '--spotlight-color': spotlightColor } as React.CSSProperties : {}),
    ...(spotlightSize !== 650 ? { '--spotlight-size': `${spotlightSize}px` } as React.CSSProperties : {}),
  };

  return (
    <div
      ref={divRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      className={`spotlight-card ${className} ${isHovered ? hoverClassName : ''}`}
      style={combinedStyle}
    >
      {children}
    </div>
  );
};

export default SpotlightCard;
