import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';

// Load screens only when their route is visited. In particular, the public
// landing page must not load charts, private workspaces, or auth images.
const LandingPage = React.lazy(() => import('./pages/LandingPage').then(m => ({ default: m.LandingPage })));
const AppShell = React.lazy(() => import('./components/layout/AppShell').then(m => ({ default: m.AppShell })));
const DashboardPage = React.lazy(() => import('./pages/DashboardPage').then(m => ({ default: m.DashboardPage })));
const VerifyPage = React.lazy(() => import('./pages/VerifyPage').then(m => ({ default: m.VerifyPage })));
const VerificationResultPage = React.lazy(() => import('./pages/VerificationResultPage').then(m => ({ default: m.VerificationResultPage })));
const ChatPage = React.lazy(() => import('./pages/ChatPage').then(m => ({ default: m.ChatPage })));
const KnowledgeBasePage = React.lazy(() => import('./pages/KnowledgeBasePage').then(m => ({ default: m.KnowledgeBasePage })));
const HistoryPage = React.lazy(() => import('./pages/HistoryPage').then(m => ({ default: m.HistoryPage })));
const ReportsPage = React.lazy(() => import('./pages/ReportsPage').then(m => ({ default: m.ReportsPage })));
const ModelLeaderboardPage = React.lazy(() => import('./pages/ModelLeaderboardPage').then(m => ({ default: m.ModelLeaderboardPage })));
const SettingsPage = React.lazy(() => import('./pages/SettingsPage').then(m => ({ default: m.SettingsPage })));
const NotFoundPage = React.lazy(() => import('./pages/NotFoundPage').then(m => ({ default: m.NotFoundPage })));
const LoginPage = React.lazy(() => import('./pages/SignupPage').then(m => ({ default: m.LoginPage })));
const SignupPage = React.lazy(() => import('./pages/SignupPage').then(m => ({ default: m.SignupPage })));
const TermsPage = React.lazy(() => import('./pages/TermsPage').then(m => ({ default: m.TermsPage })));
const PrivacyPolicyPage = React.lazy(() => import('./pages/PrivacyPolicyPage').then(m => ({ default: m.PrivacyPolicyPage })));


import { initialUserSettings } from './data/mockBackendData';
import { VerificationRecord, KnowledgeDocument, Conversation, AIProvider, UserSettings, NotificationItem } from './types';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider } from './context/AuthContext';
import { firebaseSignOut } from './lib/firebase';
import { 
  authApi, 
  dashboardApi, 
  verificationApi, 
  knowledgeApi, 
  chatApi, 
  providersApi, 
  historyApi,
  getAuthToken 
} from './api';

/** Return users to the protected destination they originally requested. */
function RedirectAfterLogin() {
  const location = useLocation();
  const requested = (location.state as { from?: unknown } | null)?.from;
  const safePath = typeof requested === 'string' &&
    /^\/(dashboard|chat|verify|verification|knowledge-base|history|reports|model-leaderboard|settings)(\/|$)/.test(requested)
    ? requested : '/dashboard';
  return <Navigate to={safePath} replace />;
}

export default function App() {
  const [userSettings, setUserSettings] = useState<UserSettings>(initialUserSettings);
  const [verifications, setVerifications] = useState<VerificationRecord[]>([]);
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [providers, setProviders] = useState<AIProvider[]>([]);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [resourceErrors, setResourceErrors] = useState<Record<string, string>>({});
  // Keep tested model lanes across /chat -> /chat/:conversationId remounts.
  // No API keys or provider credentials are stored in this state.
  const [chatSelectedModels, setChatSelectedModels] = useState<string[]>([]);
  const [chatTestedModels, setChatTestedModels] = useState<Record<string, 'working' | 'failed'>>({});


  // Handlers
  const handleAddVerification = (record: VerificationRecord) => {
    setVerifications(prev => [record, ...prev]);
    const notif: NotificationItem = {
      id: `notif-${Date.now()}`,
      title: `Verification completed: ${record.status}`,
      description: record.query,
      timestamp: 'Just now',
      read: false,
      type: 'verification',
      link: `/verification/${record.id}`
    };
    setNotifications(prev => [notif, ...prev]);
  };

  const handleAddDocument = (doc: KnowledgeDocument) => {
    setDocuments(prev => [doc, ...prev]);
  };

  // The child page performs the deletion; only remove it here on confirmed success.
  const handleDeleteDocument = (docId: string) => {
    setDocuments(prev => prev.filter(d => d.id !== docId));
  };

  const handleAddConversation = (conv: Conversation) => {
    setConversations(prev => [conv, ...prev.filter(c => c.id !== conv.id)]);
  };

  const handleUpdateConversation = (conv: Conversation) => {
    setConversations(prev => prev.some(c => c.id === conv.id)
      ? prev.map(c => c.id === conv.id ? conv : c)
      : [conv, ...prev]
    );
  };

  const handleDeleteConversation = async (conversationId: string): Promise<void> => {
    const result = await chatApi.deleteConversation(conversationId);
    if (!result.deleted) {
      throw new Error('The backend did not confirm chat deletion.');
    }
    setConversations(prev => prev.filter(conv => conv.id !== conversationId));
  };

  const handleSaveProviderKey = async (
    provId: string,
    data: {
      apiKey: string;
      keyMasked: string;
      baseUrl?: string;
      organizationId?: string;
      keyLabel?: string;
      name?: string;
      models?: string[];
      category?: 'cloud' | 'local' | 'router';
    }
  ): Promise<void> => {
    // Never mark a key as linked until the backend has encrypted and stored it.
    const saved = await providersApi.saveKey(provId, {
      api_key: data.apiKey,
      base_url: data.baseUrl,
      organization_id: data.organizationId,
      key_label: data.keyLabel,
      name: data.name,
      models: data.models,
      category: data.category,
    });
    setChatSelectedModels([]);
    setChatTestedModels({});
    setProviders(prev => {
      const existing = prev.find(p => p.id === provId);
      const confirmed = {
        ...existing,
        ...saved,
        // No raw key is ever retained in provider state.
        apiKey: undefined,
      } as AIProvider;
      return existing
        ? prev.map(p => p.id === provId ? confirmed : p)
        : [...prev, confirmed];
    });
    setNotifications(prev => [{
      id: `notif-${Date.now()}`,
      title: `${saved.name} API key saved`,
      description: 'Credential stored by the backend. Test the connection to verify access.',
      timestamp: 'Just now',
      read: false,
      type: 'system',
      link: '/settings/providers',
    }, ...prev]);
  };

  const refreshProviders = async (): Promise<void> => {
    const current = await providersApi.listProviders();
    setProviders(current);
  };

  const handleUnlinkProvider = async (provId: string): Promise<void> => {
    await providersApi.unlinkKey(provId);
    setChatSelectedModels([]);
    setChatTestedModels({});
    setProviders(prev => prev.map(p => p.id === provId
      ? { ...p, status: 'Not Connected', apiKey: undefined, keyMasked: undefined, configuredAt: undefined }
      : p));
  };

  const handleClearHistory = async (): Promise<void> => {
    const result = await historyApi.purgeUserData();
    if (!result.success) throw new Error(result.message || 'Unable to purge history.');
    setVerifications([]);
    setConversations([]);
    setDocuments([]);
  };

  const handleMarkAllNotificationsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const handleToggleTheme = () => {
    setUserSettings(prev => ({
      ...prev,
      appearance: {
        ...prev.appearance,
        theme: prev.appearance.theme === 'light' ? 'dark' : 'light'
      }
    }));
  };

  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    try {
      return localStorage.getItem('verifai_authenticated') === 'true' && Boolean(localStorage.getItem('verifai_token'));
    } catch {
      return false;
    }
  });

  const [isInitializing, setIsInitializing] = useState<boolean>(true);

  // Validate session on mount. Ignore a stale response if the user logs out
  // or switches accounts before the request finishes.
  React.useEffect(() => {
    let active = true;
    const token = getAuthToken();
    if (token) {
      authApi.getMe().then(user => {
        if (!active || getAuthToken() !== token) return;
        setIsAuthenticated(true);
        setUserSettings(prev => ({
          ...prev,
          profile: {
            ...prev.profile,
            fullName: user.username || user.full_name || prev.profile.fullName,
            email: user.email || prev.profile.email,
          }
        }));
      }).catch(() => {
        if (!active || getAuthToken() !== token) return;
        authApi.logout();
        setIsAuthenticated(false);
      }).finally(() => {
        if (active) setIsInitializing(false);
      });
    } else {
      setIsAuthenticated(false);
      const timer = setTimeout(() => {
        if (active) setIsInitializing(false);
      }, 200);
      return () => { active = false; clearTimeout(timer); };
    }
    return () => { active = false; };
  }, []);

  // Synchronize authenticated user data and backend resources.
  // Ignore late responses after logout or user changes; an old account must
  // never repopulate shared frontend state in another session.
  React.useEffect(() => {
    if (!isAuthenticated) return;
    let active = true;
    setResourceErrors({});
    const reportLoadError = (resource: string, err: unknown) => {
      if (!active) return;
      const detail = err instanceof Error ? err.message : 'Request failed';
      setResourceErrors(prev => ({
        ...prev,
        [resource]: `${resource} could not be loaded: ${detail}`,
      }));
    };
    historyApi.listVerifications({ limit: 50 })
      .then(res => { if (active) setVerifications(res.items ?? []); })
      .catch(err => reportLoadError('Verification history', err));

    knowledgeApi.listDocuments()
      .then(docs => { if (active) setDocuments(docs); })
      .catch(err => reportLoadError('Knowledge-base documents', err));

    providersApi.listProviders()
      .then(provs => { if (active) setProviders(provs); })
      .catch(err => reportLoadError('AI providers', err));

    chatApi.listConversations({ limit: 50 }).then(res => {
      if (!active) return;
      setConversations((res.items ?? []).map(c => ({
        id: c.id,
        title: c.title,
        updatedAt: new Date(c.updated_at).toLocaleDateString(),
        messageCount: c.message_count,
        models: [], // Summaries don't contain model selections.
        messages: [],
      })));
    }).catch(err => reportLoadError('Conversations', err));

    return () => { active = false; };
  }, [isAuthenticated]);

  const handleAuthSuccess = (userData: { fullName: string; email: string }) => {
    try {
      localStorage.setItem('verifai_authenticated', 'true');
    } catch {}
    setIsAuthenticated(true);
    setChatSelectedModels([]);
    setChatTestedModels({});
    setUserSettings(prev => ({
      ...prev,
      profile: {
        ...prev.profile,
        fullName: userData.fullName,
        email: userData.email,
      }
    }));
  };

  const handleLogout = () => {
    firebaseSignOut().catch(() => {});
    authApi.logout();
    setIsAuthenticated(false);
    setChatSelectedModels([]);
    setChatTestedModels({});
    setVerifications([]);
    setDocuments([]);
    setConversations([]);
    setProviders([]);
    setNotifications([]);
    setResourceErrors({});
  };

  // Synchronize document root with active theme
  React.useEffect(() => {
    const isDark = userSettings.appearance.theme === 'dark';
    if (isDark) {
      document.documentElement.classList.add('dark');
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      document.documentElement.setAttribute('data-theme', 'light');
    }
  }, [userSettings.appearance.theme]);

  const activeTheme: 'light' | 'dark' = userSettings.appearance.theme === 'dark' ? 'dark' : 'light';

  // Avoid displaying a fabricated full-screen loading experience during
  // session restoration. Routing starts once auth initialization completes.
  if (isInitializing) {
    return null;
  }

  return (
    <ThemeProvider 
      activeTheme={activeTheme} 
      onThemeChange={(newTheme) => {
        setUserSettings(prev => ({
          ...prev,
          appearance: {
            ...prev.appearance,
            theme: newTheme
          }
        }));
      }}
    >
      <AuthProvider>
        <BrowserRouter>
          <React.Suspense fallback={null}>
          <Routes>
          {/* Public marketing homepage; launch CTAs enter the existing auth/app flow. */}
          <Route path="/" element={<LandingPage isAuthenticated={isAuthenticated} />} />
          <Route 
            path="/login" 
            element={
              isAuthenticated ? (
                <RedirectAfterLogin />
              ) : (
                <LoginPage 
                  theme={activeTheme} 
                  onAuthSuccess={handleAuthSuccess} 
                  isAuthenticated={isAuthenticated}
                />
              )
            } 
          />
          <Route 
            path="/signup" 
            element={
              isAuthenticated ? (
                <RedirectAfterLogin />
              ) : (
                <SignupPage 
                  theme={activeTheme} 
                  onAuthSuccess={handleAuthSuccess} 
                  isAuthenticated={isAuthenticated}
                />
              )
            } 
          />
          <Route 
            path="/auth" 
            element={
              isAuthenticated ? (
                <RedirectAfterLogin />
              ) : (
                <LoginPage 
                  theme={activeTheme} 
                  onAuthSuccess={handleAuthSuccess} 
                  isAuthenticated={isAuthenticated}
                />
              )
            } 
          />

          {/* Public Legal Documents & Compliance Routes */}
          <Route 
            path="/terms" 
            element={<TermsPage theme={activeTheme} />} 
          />
          <Route 
            path="/privacy" 
            element={<PrivacyPolicyPage theme={activeTheme} />} 
          />

          {/* Main Authenticated Product Workspace Shell - Strict Auth Guard */}
          <Route
            element={
              isAuthenticated ? (
                <AppShell
                  userSettings={userSettings}
                  dataLoadErrors={Object.values(resourceErrors)}
                  notifications={notifications}
                  onMarkAllNotificationsRead={handleMarkAllNotificationsRead}
                  searchQuery={searchQuery}
                  onSearchChange={setSearchQuery}
                  theme={activeTheme}
                  onToggleTheme={handleToggleTheme}
                  onLogout={handleLogout}
                />
              ) : (
                <Navigate to="/login" state={{ from: window.location.pathname + window.location.search }} replace />
              )
            }
          >

          {/* 1. Dashboard Workspace */}
          <Route 
            path="/dashboard" 
            element={
              <DashboardPage
                verifications={verifications}
                userName={userSettings.profile.fullName}
                theme={activeTheme}
              />
            } 
          />

          {/* 2. Paste & Verify Workspace */}
          <Route 
            path="/verify" 
            element={
              <VerifyPage onAddVerification={handleAddVerification} theme={activeTheme} />
            } 
          />

          {/* 3. Verification Result Workspace */}
          <Route 
            path="/verification/:verificationId" 
            element={
              <VerificationResultPage verifications={verifications} theme={activeTheme} />
            } 
          />

          {/* 4. AI Chat Workspace */}
          <Route 
            path="/chat/:conversationId?"
            element={
              <ChatPage
                conversations={conversations}
                onAddConversation={handleAddConversation}
                onUpdateConversation={handleUpdateConversation}
                onProvidersChanged={refreshProviders}
                onDeleteConversation={handleDeleteConversation}
                selected={chatSelectedModels}
                setSelected={setChatSelectedModels}
                testedModels={chatTestedModels}
                setTestedModels={setChatTestedModels}
                theme={activeTheme}
              />
            } 
          />

          {/* 5. Knowledge Base Workspace */}
          <Route 
            path="/knowledge-base" 
            element={
              <KnowledgeBasePage
                documents={documents}
                onAddDocument={handleAddDocument}
                onDeleteDocument={handleDeleteDocument}
                theme={activeTheme}
              />
            } 
          />
          <Route 
            path="/knowledge-base/:documentId" 
            element={
              <KnowledgeBasePage
                documents={documents}
                onAddDocument={handleAddDocument}
                onDeleteDocument={handleDeleteDocument}
                theme={activeTheme}
              />
            } 
          />

          {/* 6. History Workspace */}
          <Route 
            path="/history" 
            element={
              <HistoryPage
                verifications={verifications}
                conversations={conversations}
                theme={activeTheme}
              />
            } 
          />

          {/* 7. Reports Workspace */}
          <Route 
            path="/reports" 
            element={
              <ReportsPage
                theme={activeTheme}
              />
            } 
          />
          <Route 
            path="/reports/models" 
            element={
              <ModelLeaderboardPage
                theme={activeTheme}
              />
            } 
          />
          <Route 
            path="/leaderboard" 
            element={
              <ModelLeaderboardPage
                theme={activeTheme}
              />
            } 
          />

          {/* 8. Settings Workspace */}
          <Route 
            path="/settings" 
            element={
              <SettingsPage
                userSettings={userSettings}
                onUpdateUserSettings={setUserSettings}
                providers={providers}
                onSaveProviderKey={handleSaveProviderKey}
                onUnlinkProvider={handleUnlinkProvider}
                onRefreshProviders={refreshProviders}
                onClearHistory={handleClearHistory}
                theme={activeTheme}
              />
            } 
          />
          <Route 
            path="/settings/:tab" 
            element={
              <SettingsPage
                userSettings={userSettings}
                onUpdateUserSettings={setUserSettings}
                providers={providers}
                onSaveProviderKey={handleSaveProviderKey}
                onUnlinkProvider={handleUnlinkProvider}
                onRefreshProviders={refreshProviders}
                onClearHistory={handleClearHistory}
                theme={activeTheme}
              />
            } 
          />

          </Route>

          {/* Diagnostic routes */}
          <Route path="/404" element={<NotFoundPage isAuthenticated={isAuthenticated} />} />

          {/* Global Catch-all 404 Route */}
          <Route path="*" element={<NotFoundPage isAuthenticated={isAuthenticated} />} />
        </Routes>
          </React.Suspense>
      </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}
