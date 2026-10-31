import { useEffect, useRef } from 'react';
import { motion, useTransform, type MotionValue } from 'motion/react';

interface CinematicScrollBackdropProps {
  progress: MotionValue<number>;
  reducedMotion: boolean;
}

/** Original ocean film: scroll-scrub exclusively within Section 3 (the pillar). */
export function CinematicScrollBackdrop({
  progress,
  reducedMotion,
}: CinematicScrollBackdropProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const mediaY = useTransform(progress, [0, 1], ['0%', '-1%']);
  const mediaScale = useTransform(progress, [0, 1], [1, 1.01]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || reducedMotion) return;
    let animationFrame = 0;
    let lastUpdate = 0;
    let visible = true;

    const updateFrame = (now: number) => {
      animationFrame = 0;
      if (!visible || document.hidden || !Number.isFinite(video.duration)) return;
      if (now - lastUpdate < 48) return;
      lastUpdate = now;
      const position = Math.min(1, Math.max(0, progress.get()));
      // Land on the last encoded frame (24 FPS) exactly as Section 3 ends.
      const lastFrameTime = Math.max(0, video.duration - 1 / 24);
      const desiredTime = Math.min(lastFrameTime, position * lastFrameTime);
      if (!video.seeking && Math.abs(video.currentTime - desiredTime) > 0.055) {
        try { video.currentTime = desiredTime; } catch { /* Retain the poster. */ }
      }
    };
    const schedule = () => {
      if (!animationFrame) animationFrame = requestAnimationFrame(updateFrame);
    };
    const onMetadata = () => {
      video.pause();
      schedule();
    };
    const observer = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
      if (visible) schedule();
    }, { threshold: 0.01 });
    observer.observe(video);
    const unsubscribe = progress.on('change', schedule);
    video.addEventListener('loadedmetadata', onMetadata);
    video.addEventListener('seeked', schedule);
    video.pause();
    if (video.readyState >= 1) schedule();
    return () => {
      unsubscribe();
      observer.disconnect();
      cancelAnimationFrame(animationFrame);
      video.removeEventListener('loadedmetadata', onMetadata);
      video.removeEventListener('seeked', schedule);
      video.pause();
    };
  }, [progress, reducedMotion]);

  return (
    <div className="va-cinema-backdrop" aria-hidden="true">
      <motion.div
        className="va-cinema-media"
        style={reducedMotion ? undefined : { y: mediaY, scale: mediaScale }}
      >
        {!reducedMotion && (
          <video
            ref={videoRef}
            className="va-cinema-film"
            poster="/landing/evidence-ocean-first-frame.jpg"
            preload="auto"
            muted
            playsInline
            disablePictureInPicture
            tabIndex={-1}
          >
            <source
              src="/landing/evidence-ocean-scroll-mobile.mp4"
              media="(max-width: 700px)"
              type="video/mp4"
            />
            <source src="/landing/evidence-ocean-scroll.mp4" type="video/mp4" />
          </video>
        )}
      </motion.div>
      <div className="va-cinema-grade" />
    </div>
  );
}
