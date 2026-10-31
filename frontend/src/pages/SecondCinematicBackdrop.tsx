import { useEffect, useRef } from 'react';
import { motion, useTransform, type MotionValue } from 'motion/react';

interface SecondCinematicBackdropProps {
  progress: MotionValue<number>;
  reducedMotion: boolean;
}

/**
 * The second film has its own timeline and only exists inside section 3.
 * It cannot appear or advance while the user is still in section 2.
 */
export function SecondCinematicBackdrop({
  progress,
  reducedMotion,
}: SecondCinematicBackdropProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const y = useTransform(progress, [0, 1], ['0%', '-1%']);
  const scale = useTransform(progress, [0, 1], [1, 1.01]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || reducedMotion) return;
    let frame = 0;
    let lastUpdate = 0;
    let visible = false;
    const sync = (now: number) => {
      frame = 0;
      if (!visible || document.hidden || !Number.isFinite(video.duration)) return;
      if (now - lastUpdate < 48) return;
      lastUpdate = now;
      const position = Math.min(1, Math.max(0, progress.get()));
      const desiredTime = 0.04 + position * (video.duration - 0.12);
      if (!video.seeking && Math.abs(video.currentTime - desiredTime) > 0.055) {
        try { video.currentTime = desiredTime; } catch { /* Poster remains. */ }
      }
    };
    const schedule = () => { if (!frame) frame = requestAnimationFrame(sync); };
    const observer = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
      if (visible) schedule();
    }, {threshold: 0.01});
    observer.observe(video);
    const onMetadata = () => { video.pause(); schedule(); };
    const unsubscribe = progress.on('change', schedule);
    video.addEventListener('loadedmetadata', onMetadata);
    video.addEventListener('seeked', schedule);
    video.pause();
    if (video.readyState >= 1) schedule();
    return () => {
      unsubscribe();
      observer.disconnect();
      cancelAnimationFrame(frame);
      video.removeEventListener('loadedmetadata', onMetadata);
      video.removeEventListener('seeked', schedule);
      video.pause();
    };
  }, [progress, reducedMotion]);

  return (
    <div className="va-video-two-backdrop" aria-hidden="true">
      <motion.div className="va-video-two-media" style={reducedMotion ? undefined : {y, scale}}>
        {!reducedMotion && (
          <video
            ref={videoRef}
            className="va-video-two-film"
            poster="/landing/evidence-ocean-sequence-02-poster.jpg"
            preload="metadata"
            muted
            playsInline
            disablePictureInPicture
            tabIndex={-1}
          >
            <source src="/landing/evidence-ocean-sequence-02.mp4" type="video/mp4" />
          </video>
        )}
      </motion.div>
      <div className="va-video-two-grade" />
    </div>
  );
}
