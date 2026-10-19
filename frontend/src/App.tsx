import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';

// Dedicated Pages
import { DashboardPage } from './pages/DashboardPage';
import { VerifyPage } from './pages/VerifyPage';
import { VerificationResultPage } from './pages/VerificationResultPage';
import { ChatPage } from './pages/ChatPage';
import { KnowledgeBasePage } from './pages/KnowledgeBasePage';
import { HistoryPage } from './pages/HistoryPage';
import { ReportsPage } from './pages/ReportsPage';
import { ModelLeaderboardPage } from './pages/ModelLeaderboardPage';
import { SettingsPage } from './pages/SettingsPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { SignupPage, LoginPage } from './pages/SignupPage';
import { TermsPage } from './pages/TermsPage';
import { PrivacyPolicyPage } from './pages/PrivacyPolicyPage';
import { LoadingScreen } from './components/common/LoadingScreen';

import { 
  initialUserSettings, 
  weeklyChartData, 
  monthlyChartData, 
  initialVerifications, 
  initialDocuments, 
  initialConversations, 
  initialProviders, 
  initialNotifications,
  initialLeaderboard
} from './data/mockBackendData';
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

export default function App() {
  const [userSettings, setUserSettings] = useState<UserSettings>(initialUserSettings);
  const [verifications, setVerifications] = useState<VerificationRecord[]>(initialVerifications);
  const [documents, setDocuments] = useState<KnowledgeDocument[]>(initialDocuments);
  const [conversations, setConversations] = useState<Conversation[]>(initialConversations);
  const [providers, setProviders] = useState<AIProvider[]>(initialProviders);
  const [notifications, setNotifications] = useState<NotificationItem[]>(initialNotifications);
  const [searchQuery, setSearchQuery] = useState('');

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

  const handleDeleteDocument = async (docId: string) => {
    try {
      await knowledgeApi.deleteDocument(docId);
    } catch {}
    setDocuments(prev => prev.filter(d => d.id !== docId));
  };

  const handleAddConversation = (conv: Conversation) => {
    setConversations(prev => [conv, ...prev]);
  };

  const handleUpdateConversation = (conv: Conversation) => {
    setConversations(prev => prev.map(c => c.id === conv.id ? conv : c));
  };

  const handleToggleProvider = (provId: string) => {
    setProviders(prev => prev.map(p => {
      if (p.id === provId) {
        return {
          ...p,
          status: p.status === 'Connected' ? 'Not Connected' : 'Connected'
        };
      }
      return p;
    }));
  };

  const handleSaveProviderKey = (
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
  ) => {
    providersApi.saveKey(provId, {
      api_key: data.apiKey,
      base_url: data.baseUrl,
      organization_id: data.organizationId,
      key_label: data.keyLabel,
    }).catch(() => {});

    setProviders(prev => {
      const exists = prev.some(p => p.id === provId);
      if (exists) {
        return prev.map(p => {
          if (p.id === provId) {
            return {
              ...p,
              status: 'Connected',
              configuredAt: 'Just now',
              ...data,
            };
          }
          return p;
        });
      } else {
        const newProv: AIProvider = {
          id: provId,
          name: data.name || 'Custom 3rd Party LLM',
          category: data.category || 'cloud',
          status: 'Connected',
          models: data.models && data.models.length > 0 ? data.models : ['Custom Model v1'],
          configuredAt: 'Just now',
          keyMasked: data.keyMasked,
          apiKey: data.apiKey,
          baseUrl: data.baseUrl,
          organizationId: data.organizationId,
          keyLabel: data.keyLabel,
        };
        return [...prev, newProv];
      }
    });

    const provName = data.name || providers.find(p => p.id === provId)?.name || 'Provider';
    const notif: NotificationItem = {
      id: `notif-${Date.now()}`,
      title: `${provName} API Key Linked`,
      description: `3rd-party LLM key linked to project VerifAI Intelligence Lab. Models are now active.`,
      timestamp: 'Just now',
      read: false,
      type: 'system',
      link: '/settings/providers'
    };
    setNotifications(prev => [notif, ...prev]);
  };

  const handleUnlinkProvider = (provId: string) => {
    providersApi.unlinkKey(provId).catch(() => {});
    setProviders(prev => prev.map(p => {
      if (p.id === provId) {
        return {
          ...p,
          status: 'Not Connected',
          apiKey: undefined,
          keyMasked: undefined,
          configuredAt: undefined,
        };
      }
      return p;
    }));
  };

  const handleClearHistory = () => {
    historyApi.purgeUserData().catch(() => {});
    setVerifications([]);
    setConversations([]);
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

  // Validate session on mount
  React.useEffect(() => {
    const token = getAuthToken();
    if (token) {
      authApi.getMe().then(user => {
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
        authApi.logout();
        setIsAuthenticated(false);
      }).finally(() => {
        setIsInitializing(false);
      });
    } else {
      setIsAuthenticated(false);
      const timer = setTimeout(() => setIsInitializing(false), 200);
      return () => clearTimeout(timer);
    }
  }, []);

  // Synchronize authenticated user data and backend resources
  React.useEffect(() => {
    if (isAuthenticated) {
      historyApi.listVerifications({ limit: 50 }).then(res => {
        if (res.items && res.items.length > 0) {
          setVerifications(res.items);
        }
      }).catch(() => {});

      knowledgeApi.listDocuments().then(docs => {
        if (docs && docs.length > 0) {
          setDocuments(docs);
        }
      }).catch(() => {});

      providersApi.listProviders().then(provs => {
        if (provs && provs.length > 0) {
          setProviders(provs);
        }
      }).catch(() => {});

      chatApi.listConversations({ limit: 50 }).then(res => {
        if (res.items && res.items.length > 0) {
          const mapped = res.items.map(c => ({
            id: c.id,
            title: c.title,
            updatedAt: new Date(c.updated_at).toLocaleDateString(),
            messageCount: c.message_count,
            models: ['GPT-4o', 'Claude 3.5', 'Gemini 1.5'],
            messages: [],
          }));
          setConversations(mapped);
        }
      }).catch(() => {});
    }
  }, [isAuthenticated]);

  const handleAuthSuccess = (userData: { fullName: string; email: string }) => {
    try {
      localStorage.setItem('verifai_authenticated', 'true');
    } catch {}
    setIsAuthenticated(true);
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

  if (isInitializing) {
    return <LoadingScreen message="Initializing VerifAI Console" />;
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
          <Routes>
          {/* Public Authentication Pages: Entry screen on root '/' */}
          <Route 
            path="/" 
            element={
              isAuthenticated ? (
                <Navigate to="/dashboard" replace />
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
            path="/login" 
            element={
              isAuthenticated ? (
                <Navigate to="/dashboard" replace />
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
                <Navigate to="/dashboard" replace />
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
                <Navigate to="/dashboard" replace />
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
                  notifications={notifications}
                  onMarkAllNotificationsRead={handleMarkAllNotificationsRead}
                  searchQuery={searchQuery}
                  onSearchChange={setSearchQuery}
                  theme={activeTheme}
                  onToggleTheme={handleToggleTheme}
                  onLogout={handleLogout}
                />
              ) : (
                <Navigate to="/" replace />
              )
            }
          >

          {/* 1. Dashboard Workspace */}
          <Route 
            path="/dashboard" 
            element={
              <DashboardPage
                verifications={verifications}
                weeklyChartData={weeklyChartData}
                monthlyChartData={monthlyChartData}
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
            path="/chat" 
            element={
              <ChatPage
                conversations={conversations}
                onAddConversation={handleAddConversation}
                onUpdateConversation={handleUpdateConversation}
                providers={providers}
                theme={activeTheme}
              />
            } 
          />
          <Route 
            path="/chat/:conversationId" 
            element={
              <ChatPage
                conversations={conversations}
                onAddConversation={handleAddConversation}
                onUpdateConversation={handleUpdateConversation}
                providers={providers}
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
                weeklyChartData={weeklyChartData}
                monthlyChartData={monthlyChartData}
                theme={activeTheme}
              />
            } 
          />
          <Route 
            path="/reports/models" 
            element={
              <ModelLeaderboardPage
                leaderboardData={initialLeaderboard}
                theme={activeTheme}
              />
            } 
          />
          <Route 
            path="/leaderboard" 
            element={
              <ModelLeaderboardPage
                leaderboardData={initialLeaderboard}
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
                onToggleProvider={handleToggleProvider}
                onSaveProviderKey={handleSaveProviderKey}
                onUnlinkProvider={handleUnlinkProvider}
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
                onToggleProvider={handleToggleProvider}
                onSaveProviderKey={handleSaveProviderKey}
                onUnlinkProvider={handleUnlinkProvider}
                onClearHistory={handleClearHistory}
                theme={activeTheme}
              />
            } 
          />

          </Route>

          {/* Dedicated Preview & Diagnostic Routes */}
          <Route path="/loading" element={<LoadingScreen />} />
          <Route path="/404" element={<NotFoundPage isAuthenticated={isAuthenticated} />} />

          {/* Global Catch-all 404 Route */}
          <Route path="*" element={<NotFoundPage isAuthenticated={isAuthenticated} />} />
        </Routes>
      </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}
