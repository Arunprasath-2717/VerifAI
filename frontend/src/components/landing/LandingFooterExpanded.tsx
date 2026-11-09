import { motion } from 'motion/react';
import { ArrowUpRight } from 'lucide-react';
import { VerifAIMark } from './GlassNav';

export function LandingFooterExpanded({ isAuthenticated }: { isAuthenticated: boolean }) {
  const launchPath = isAuthenticated ? '/dashboard' : '/login';
  return (
    <footer className="vi-footer vi-footer-expanded" id="site-footer">
      <div className="vi-container">
        <div className="vi-footer-main">
          <motion.div className="vi-footer-invite"
            initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.3 }} transition={{ duration: .65 }}>
            <h2>GO BEYOND<br /><span className="vi-footer-script">the answer.</span></h2>
            <p>Less blind confidence. More evidence you can actually inspect.</p>
            <a className="vi-button vi-button-light" href={launchPath}>Start verifying <ArrowUpRight size={20} strokeWidth={1.7} aria-hidden="true" /></a>
          </motion.div>
          <div className="vi-footer-side" aria-label="Footer information and navigation">
            <div className="vi-footer-links">
              <nav aria-label="Explore VerifAI">
                <h3>Explore</h3>
                <a href="#difference">The Difference</a>
                <a href="#benefits">Key Benefits</a>
                <a href="#consensus">Why Consensus Matters</a>
                <a href="#approach">Our Approach</a>
              </nav>
              <nav aria-label="Account and policies">
                <h3>More</h3>
                <a href={launchPath}>{isAuthenticated ? 'Open Workspace' : 'Get Started'}</a>
                {!isAuthenticated && <a href="/login">Sign In</a>}
                <a href="/privacy">Privacy Policy</a>
                <a href="/terms">Terms of Service</a>
              </nav>
            </div>
          </div>
        </div>
        <div className="vi-footer-bottom">
          <a href="#top" className="vi-footer-brand" aria-label="VerifAI, back to top"><VerifAIMark size={26} /> VERIFAI</a>
          <span>© {new Date().getFullYear()} VerifAI</span>
          <a href="#top" className="vi-footer-to-top">Back to top <ArrowUpRight size={15} strokeWidth={1.5} aria-hidden="true" /></a>
        </div>
      </div>
    </footer>
  );
}
