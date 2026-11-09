import { useEffect, useState } from 'react';
import { ArrowUpRight, Menu, X } from 'lucide-react';

interface GlassNavProps { isAuthenticated: boolean; }

const links = [
  { label: 'Difference', href: '#difference' },
  { label: 'Benefits', href: '#benefits' },
  { label: 'Consensus', href: '#consensus' },
  { label: 'Approach', href: '#approach' },
] as const;

/** Custom verification mark: an open evidence frame and a decisive check. */
export function VerifAIMark({ size = 42 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <path d="M24 3.8 42.2 14v20L24 44.2 5.8 34V14L24 3.8Z" stroke="currentColor" strokeWidth="2.4" strokeLinejoin="round" />
      <path d="M12.7 24.6 20.8 32.4 35.8 15.5" stroke="#39FF88" strokeWidth="4.4" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M24 3.8 42.2 14" stroke="#39FF88" strokeWidth="2.4" strokeLinecap="round" />
    </svg>
  );
}

export function GlassNav({ isAuthenticated }: GlassNavProps) {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState('#top');
  const launchPath = isAuthenticated ? '/dashboard' : '/login';

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
      const ids = ['#difference', '#benefits', '#consensus', '#approach'];
      let next = '#top';
      for (const id of ids) {
        const section = document.querySelector(id);
        if (section && section.getBoundingClientRect().top <= window.innerHeight * 0.38) next = id;
      }
      setActive(next);

    };
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false); };
    handleScroll();
    window.addEventListener('scroll', handleScroll, { passive: true });
    window.addEventListener('keydown', onKey);
    return () => { window.removeEventListener('scroll', handleScroll); window.removeEventListener('keydown', onKey); };
  }, []);

  return (
    <header className={'vi-nav vm-nav' + (scrolled || open ? ' is-scrolled' : '')}>
      <div className="vi-nav-inner vm-nav-inner">
        <a href="#top" className="vi-wordmark vm-wordmark" onClick={() => setOpen(false)} aria-label="VerifAI home">
          <span className="vm-logo-mark"><VerifAIMark size={37}/></span>
          <span className="vm-wordmark-text">Verif<span>AI</span></span>
        </a>
        <nav className="vi-nav-links vm-nav-links" aria-label="Landing page">
          {links.map(link => (
            <a key={link.href} className={active === link.href ? 'is-active' : ''} href={link.href}>
              {link.label}
            </a>
          ))}
        </nav>
        <div className="vi-nav-actions vm-nav-actions">
          {!isAuthenticated && <a className="vi-nav-signin" href="/login">Sign in</a>}
          <a className="vi-nav-cta vm-nav-cta" href={launchPath}>
            {isAuthenticated ? 'Workspace' : 'Get started'}
            <ArrowUpRight size={17} strokeWidth={1.8} aria-hidden="true" />
          </a>
        </div>
        <button className="vi-nav-menu vm-nav-toggle" type="button" onClick={() => setOpen(v=>!v)}
          aria-label={open?'Close navigation':'Open navigation'} aria-expanded={open} aria-controls="vi-mobile-navigation">
          {open ? <X size={23}/> : <Menu size={23}/>}
        </button>
      </div>
      {open && (
        <nav className="vi-nav-mobile vm-nav-mobile" id="vi-mobile-navigation" aria-label="Mobile landing navigation">
          {links.map(link=>(
            <a key={link.href} href={link.href} onClick={()=>setOpen(false)}>{link.label}<ArrowUpRight size={17}/></a>
          ))}
          <a className="vi-nav-mobile-launch" href={launchPath} onClick={()=>setOpen(false)}>
            {isAuthenticated ? 'Open workspace' : 'Get started'} <ArrowUpRight size={17}/>
          </a>
        </nav>
      )}
    </header>
  );
}
