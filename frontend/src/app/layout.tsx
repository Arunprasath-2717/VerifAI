import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { ThemeProvider } from '@/components/ThemeProvider';
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Credence — AI Information Verification & Research Workspace',
  description: 'Examine AI-generated information, verify claims against authoritative peer-reviewed evidence, and conduct trustworthy AI conversations.',
  keywords: ['AI verification', 'fact checking', 'evidence inspection', 'trustworthy AI', 'academic research'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} min-h-screen flex flex-col bg-pastel-bg text-pastel-charcoal dark:bg-pastel-bg-dark dark:text-pastel-charcoal-light antialiased transition-colors duration-200`}>
        <ThemeProvider>
          {/* Skip link for accessibility */}
          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:p-3 focus:bg-pastel-lavender focus:text-white focus:rounded-lg focus:m-2"
          >
            Skip to main content
          </a>
          <Navbar />
          <div id="main-content" className="flex-1 flex flex-col">
            {children}
          </div>
          <Footer />
        </ThemeProvider>
      </body>
    </html>
  );
}
