import React, { createContext, useContext, useEffect, useState } from 'react';

export type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  isDark: boolean;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType>({
  theme: 'light',
  isDark: false,
  toggleTheme: () => {},
  setTheme: () => {},
});

interface ThemeProviderProps {
  children: React.ReactNode;
  initialTheme?: Theme;
  activeTheme?: Theme;
  onThemeChange?: (theme: Theme) => void;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ 
  children, 
  initialTheme = 'light',
  activeTheme,
  onThemeChange,
}) => {
  const [internalTheme, setInternalTheme] = useState<Theme>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('verifai-theme') as Theme;
      if (saved === 'dark' || saved === 'light') return saved;
    }
    return activeTheme || initialTheme;
  });

  // Effective theme prioritizes controlled activeTheme if supplied
  const effectiveTheme: Theme = activeTheme !== undefined ? activeTheme : internalTheme;
  const isDark = effectiveTheme === 'dark';

  useEffect(() => {
    const root = document.documentElement;
    if (isDark) {
      root.classList.add('dark');
      root.setAttribute('data-theme', 'dark');
      root.style.colorScheme = 'dark';
    } else {
      root.classList.remove('dark');
      root.setAttribute('data-theme', 'light');
      root.style.colorScheme = 'light';
    }
    try {
      localStorage.setItem('verifai-theme', effectiveTheme);
    } catch {
      // ignore
    }
  }, [effectiveTheme, isDark]);

  const toggleTheme = () => {
    const nextTheme: Theme = effectiveTheme === 'light' ? 'dark' : 'light';
    setInternalTheme(nextTheme);
    if (onThemeChange) {
      onThemeChange(nextTheme);
    }
  };

  const setTheme = (newTheme: Theme) => {
    setInternalTheme(newTheme);
    if (onThemeChange) {
      onThemeChange(newTheme);
    }
  };

  return (
    <ThemeContext.Provider value={{ theme: effectiveTheme, isDark, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => useContext(ThemeContext);
