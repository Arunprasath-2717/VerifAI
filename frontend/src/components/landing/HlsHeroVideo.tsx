import React, { useEffect, useRef, useState } from 'react';
import { Volume2, VolumeX } from 'lucide-react';

interface HlsHeroVideoProps {
  hlsSrc?: string;
  fallbackMp4?: string;
  poster?: string;
}

export function HlsHeroVideo({
  hlsSrc = 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8',
  fallbackMp4 = '/cinema/threshold-film.mp4',
  poster = '/cinema/threshold-poster.jpg',
}: HlsHeroVideoProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isMuted, setIsMuted] = useState(true);
  const [isVideoLoaded, setIsVideoLoaded] = useState(false);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    let hlsInstance: any = null;

    const playVideo = () => {
      video.play().catch(() => {
        // Autoplay might require mute
        video.muted = true;
        video.play().catch(() => {});
      });
    };

    const attachMp4Fallback = () => {
      if (!video) return;
      if (video.src !== fallbackMp4 && !video.currentSrc.includes(fallbackMp4)) {
        video.src = fallbackMp4;
        playVideo();
      }
    };

    // Check for native HLS support (Safari, iOS)
    if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = hlsSrc;
      video.addEventListener('loadedmetadata', () => {
        setIsVideoLoaded(true);
        playVideo();
      });
      video.addEventListener('error', attachMp4Fallback);
    } else {
      // Use HLS.js for other browsers
      const initHls = (HlsClass: any) => {
        if (!video || !HlsClass.isSupported()) {
          attachMp4Fallback();
          return;
        }

        try {
          const hls = new HlsClass({
            enableWorker: true,
            lowLatencyMode: true,
            backBufferLength: 60,
          });
          hlsInstance = hls;

          hls.loadSource(hlsSrc);
          hls.attachMedia(video);

          hls.on(HlsClass.Events.MANIFEST_PARSED, () => {
            setIsVideoLoaded(true);
            playVideo();
          });

          hls.on(HlsClass.Events.ERROR, (_event: any, data: any) => {
            if (data.fatal) {
              switch (data.type) {
                case HlsClass.ErrorTypes.NETWORK_ERROR:
                  hls.startLoad();
                  break;
                case HlsClass.ErrorTypes.MEDIA_ERROR:
                  hls.recoverMediaError();
                  break;
                default:
                  hls.destroy();
                  attachMp4Fallback();
                  break;
              }
            }
          });
        } catch {
          attachMp4Fallback();
        }
      };

      if (typeof window !== 'undefined' && (window as any).Hls) {
        initHls((window as any).Hls);
      } else {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/hls.js@1.5.17/dist/hls.min.js';
        script.async = true;
        script.onload = () => {
          if ((window as any).Hls) {
            initHls((window as any).Hls);
          } else {
            attachMp4Fallback();
          }
        };
        script.onerror = () => {
          attachMp4Fallback();
        };
        document.head.appendChild(script);
      }
    }

    const onPlay = () => setIsVideoLoaded(true);
    video.addEventListener('playing', onPlay);

    return () => {
      video.removeEventListener('playing', onPlay);
      video.removeEventListener('error', attachMp4Fallback);
      if (hlsInstance) {
        hlsInstance.destroy();
      }
    };
  }, [hlsSrc, fallbackMp4]);

  const toggleSound = () => {
    if (!videoRef.current) return;
    const nextMuted = !isMuted;
    videoRef.current.muted = nextMuted;
    setIsMuted(nextMuted);
  };

  return (
    <div className="absolute inset-0 w-full h-full overflow-hidden bg-black select-none pointer-events-none">
      {/* Video Element */}
      <video
        ref={videoRef}
        poster={poster}
        autoPlay
        loop
        muted={isMuted}
        playsInline
        preload="auto"
        className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-1000 ${
          isVideoLoaded ? 'opacity-85 scale-100' : 'opacity-40 scale-105'
        }`}
      >
        <source src={fallbackMp4} type="video/mp4" />
      </video>

      {/* Atmospheric Overlays */}
      {/* Bottom gradient fade for text legibility and seamless transition to page content */}
      <div
        className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent"
        aria-hidden="true"
      />

      {/* Left gradient fade for bottom-left hero typography */}
      <div
        className="absolute inset-0 bg-gradient-to-r from-black/85 via-black/45 to-transparent"
        aria-hidden="true"
      />

      {/* Top vignette for glassmorphic nav */}
      <div
        className="absolute top-0 inset-x-0 h-40 bg-gradient-to-b from-black/80 via-black/30 to-transparent"
        aria-hidden="true"
      />

      {/* Subtle modern grid mask */}
      <div
        className="absolute inset-0 opacity-[0.07] bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:24px_24px] pointer-events-none"
        aria-hidden="true"
      />

      {/* Interactive Sound Toggle (Bottom-Right) */}
      <div className="absolute bottom-8 right-6 sm:bottom-12 sm:right-10 z-30 pointer-events-auto">
        <button
          type="button"
          onClick={toggleSound}
          aria-label={isMuted ? 'Unmute background video' : 'Mute background video'}
          className="flex items-center gap-2 px-3.5 py-2 rounded-full bg-black/40 hover:bg-black/70 text-white/70 hover:text-white border border-white/10 backdrop-blur-md transition-all duration-200 text-xs tracking-wider uppercase font-medium hover:scale-105 active:scale-95"
        >
          {isMuted ? (
            <>
              <VolumeX className="w-3.5 h-3.5 text-neutral-400" />
              <span>Audio Off</span>
            </>
          ) : (
            <>
              <Volume2 className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
              <span className="text-emerald-300">Audio On</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
