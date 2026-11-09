import { useEffect, useRef } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import './ScrollBits.css';

gsap.registerPlugin(ScrollTrigger);

interface ScrollFloatProps {
  children: string;
  className?: string;
  splitBy?: 'chars' | 'words';
  direction?: 'up' | 'down';
  stagger?: number;
  distance?: number;
}

/**
 * Editorial adaptation of React Bits ScrollFloat.
 * Inline rather than another heading, so the original accessible h2 and
 * mixed-font italic emphasis remain intact.
 */
export function ScrollFloat({
  children, className = '', splitBy = 'words', direction = 'up',
  stagger = 0.065, distance = 52,
}: ScrollFloatProps) {
  const element = useRef<HTMLSpanElement>(null);
  const words = children.split(/(\s+)/);
  useEffect(() => {
    const node = element.current;
    if (!node || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const targets = gsap.utils.toArray<HTMLElement>(
      node.querySelectorAll(splitBy === 'words' ? '.vr-scroll-bit-word' : '.vr-scroll-bit-char')
    );
    // Only set hidden/translated states when JS animation is actually mounted.
    const context = gsap.context(() => {
      gsap.fromTo(targets,
        { autoAlpha: 0, yPercent: direction === 'up' ? distance : -distance },
        {
          autoAlpha: 1, yPercent: 0, duration: .8, ease: 'power3.out',
          stagger, overwrite: 'auto',
          scrollTrigger: { trigger: node, start: 'top 88%', once: true }
        });
    }, node);
    return () => context.revert();
  }, [children, splitBy, direction, stagger, distance]);
  return (
    <span ref={element} className={`vr-scroll-float ${className}`}>
      {words.map((word, wi) => /^\s+$/.test(word)
        ? <span key={wi} className="vr-scroll-bit-space">{word}</span>
        : <span className="vr-scroll-bit-word" key={wi}>
            {splitBy === 'chars' ? Array.from(word).map((char, ci) =>
              <span className="vr-scroll-bit-char" key={ci}>{char}</span>) : word}
          </span>)}
    </span>
  );
}
