import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { MarketplaceView } from './components/MarketplaceView';
import { PlaygroundView } from './components/PlaygroundView';
import { ConsumerView } from './components/ConsumerView';
import { ProviderView } from './components/ProviderView';
import { AdminView } from './components/AdminView';
import { AuthModal } from './components/AuthModal';
import { User, Wallet } from './types';
import { getStoredUser, getConsumerWallet, removeAuthToken, claimFaucet } from './api';

export function App() {
  const [currentView, setCurrentView] = useState<'marketplace' | 'playground' | 'consumer' | 'provider' | 'admin'>('marketplace');
  const [user, setUser] = useState<User | null>(getStoredUser());
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [selectedPlaygroundModel, setSelectedPlaygroundModel] = useState('llama3:8b');

  useEffect(() => {
    if (user) {
      refreshWallet();
    }
  }, [user]);

  const refreshWallet = async () => {
    try {
      const w = await getConsumerWallet();
      setWallet(w);
    } catch (e) {
      console.error(e);
    }
  };

  const handleLogout = () => {
    removeAuthToken();
    setUser(null);
    setWallet(null);
    setCurrentView('marketplace');
  };

  const handleClaimFaucet = async () => {
    try {
      await claimFaucet();
      await refreshWallet();
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleSelectModelFromMarketplace = (modelName: string) => {
    setSelectedPlaygroundModel(modelName);
    setCurrentView('playground');
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#080B11] text-slate-100">
      <Navbar
        currentView={currentView}
        setCurrentView={setCurrentView}
        user={user}
        wallet={wallet}
        onOpenAuth={() => setIsAuthModalOpen(true)}
        onLogout={handleLogout}
        onClaimFaucet={handleClaimFaucet}
      />

      <main className="flex-1">
        {currentView === 'marketplace' && (
          <MarketplaceView
            onSelectModel={handleSelectModelFromMarketplace}
            onOpenAuth={() => setIsAuthModalOpen(true)}
          />
        )}
        {currentView === 'playground' && (
          <PlaygroundView
            initialModel={selectedPlaygroundModel}
            onOpenAuth={() => setIsAuthModalOpen(true)}
            isAuthenticated={!!user}
          />
        )}
        {currentView === 'consumer' && (
          <ConsumerView
            wallet={wallet}
            onRefreshWallet={refreshWallet}
            onOpenAuth={() => setIsAuthModalOpen(true)}
            isAuthenticated={!!user}
          />
        )}
        {currentView === 'provider' && (
          <ProviderView
            onOpenAuth={() => setIsAuthModalOpen(true)}
            isAuthenticated={!!user}
          />
        )}
        {currentView === 'admin' && <AdminView />}
      </main>

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onSuccess={(u) => {
          setUser(u);
          refreshWallet();
        }}
      />
    </div>
  );
}

export default App;
