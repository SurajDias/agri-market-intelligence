import React, { useRef, useState } from 'react';
import './ChromaCard.css';

export interface ChromaCardProps {
  children: React.ReactNode;
  className?: string;
  glowColor?: string; // default agricultural green rgba
}

const ChromaCard: React.FC<ChromaCardProps> = ({
  children,
  className = '',
}) => {
  const cardRef = useRef<HTMLDivElement | null>(null);
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    cardRef.current.style.setProperty('--mouse-x', `${x}px`);
    cardRef.current.style.setProperty('--mouse-y', `${y}px`);
  };

  return (
    <div
      ref={cardRef}
      className={`chroma-card ${isHovered ? 'chroma-card--hovered' : ''} ${className}`}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="chroma-card__border-glow" aria-hidden="true" />
      <div className="chroma-card__spotlight" aria-hidden="true" />
      <div className="chroma-card__content">{children}</div>
    </div>
  );
};

export default ChromaCard;
