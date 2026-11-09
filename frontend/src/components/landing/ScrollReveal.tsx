import { useEffect, useRef } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import './ScrollBits.css';

gsap.registerPlugin(ScrollTrigger);

interface ScrollRevealProps {
  children: string;
  className?: string;
  stagger?: number;
  duration?: number;
  baseOpacity?: number;
}

/** Accessible word-based interpretation of React Bits ScrollReveal.
 * Uses a restrained enter-once fade instead of scroll scrubbing body copy. */
export function ScrollReveal({
  children, className = '', stagger = .042, duration = .7, baseOpacity = .22,
}: ScrollRevealProps) {
  const node = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    const element = node.current;
    if (!element || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const pieces = gsap.utils.toArray<HTMLElement>(element.querySelectorAll('.vr-scroll-reveal-word'));
    const context = gsap.context(() => {
      gsap.fromTo(pieces,
        { opacity: baseOpacity, y: 6 },
        {
          opacity: 1, y: 0, duration, stagger, ease: 'power2.out',
          scrollTrigger: { trigger: element, start: 'top 90%', once: true },
        });
    }, element);
    return () => context.revert();
  }, [children, duration, stagger, baseOpacity]);
  return (
    <span ref={node} className={`vr-scroll-reveal ${className}`} aria-label={children}>
      <span className="vr-scroll-reveal-content" aria-hidden="true">
        {children.split(/(\s+)/).map((word, i) => /^\s+$/.test(word)
          ? <span key={i}>{word}</span>
          : <span key={i} className="vr-scroll-reveal-word">{word}</span>)}
      </span>
    </span>
  );
}
