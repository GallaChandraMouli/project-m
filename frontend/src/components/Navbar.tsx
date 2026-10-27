import React from 'react';
import { Cpu, Terminal, Shield, Zap, Wallet as WalletIcon, LogOut, User as UserIcon, PlusCircle } from 'lucide-react';
import { User, Wallet } from '../types';

interface NavbarProps {
  currentView: 'marketplace' | 'playground' | 'consumer' | 'provider' | 'admin';
  setCurrentView: (view: 'marketplace' | 'playground' | 'consumer' | 'provider' | 'admin') => void;
  user: User | null;
  wallet: Wallet | null;
  onOpenAuth: () => void;
  onLogout: () => void;
  onClaimFaucet: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentView,
  setCurrentView,
  user,
  wallet,
  onOpenAuth,
  onLogout,
  onClaimFaucet,
}) => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-white/10 bg-[#080B11]/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo */}
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setCurrentView('marketplace')}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 via-emerald-500 to-cyan-400 p-[1px] flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <div className="w-full h-full bg-[#0B0F17] rounded-xl flex items-center justify-center">
              <Cpu className="w-5 h-5 text-emerald-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                NexusCompute
              </span>
              <span className="px-1.5 py-0.5 text-[10px] uppercase tracking-wider font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-full">
                Testnet
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">Decentralized GPU Inference Mesh</p>
          </div>
        </div>

        {/* View Navigation */}
        <nav className="hidden md:flex items-center space-x-1 bg-white/[0.03] p-1 rounded-xl border border-white/5">
          <button
            onClick={() => setCurrentView('marketplace')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              currentView === 'marketplace'
                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            Marketplace
          </button>
          <button
            onClick={() => setCurrentView('playground')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center space-x-1.5 ${
              currentView === 'playground'
                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Zap className="w-3.5 h-3.5" />
            <span>Playground</span>
          </button>
          <button
            onClick={() => setCurrentView('consumer')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              currentView === 'consumer'
                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            Consumer API
          </button>
          <button
            onClick={() => setCurrentView('provider')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center space-x-1.5 ${
              currentView === 'provider'
                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>Provider Node</span>
          </button>
          <button
            onClick={() => setCurrentView('admin')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center space-x-1.5 ${
              currentView === 'admin'
                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Shield className="w-3.5 h-3.5" />
            <span>Admin</span>
          </button>
        </nav>

        {/* Right Section: Wallet & User */}
        <div className="flex items-center space-x-3">
          {user ? (
            <div className="flex items-center space-x-3">
              {/* Wallet pill */}
              <div className="flex items-center bg-white/[0.04] border border-white/10 rounded-xl px-3 py-1.5 space-x-2">
                <WalletIcon className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-xs font-mono font-semibold text-emerald-300">
                  ${(wallet?.balance_credits || 0).toFixed(2)}
                </span>
                <button
                  onClick={onClaimFaucet}
                  title="Claim $25.00 Test Credits"
                  className="text-[11px] bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 px-1.5 py-0.5 rounded flex items-center space-x-1 transition-colors"
                >
                  <PlusCircle className="w-3 h-3" />
                  <span>Faucet</span>
                </button>
              </div>

              {/* User email & logout */}
              <div className="flex items-center space-x-2">
                <div className="hidden sm:flex flex-col text-right">
                  <span className="text-xs font-medium text-slate-200">{user.email.split('@')[0]}</span>
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider">{user.role}</span>
                </div>
                <button
                  onClick={onLogout}
                  title="Logout"
                  className="p-2 rounded-lg bg-white/[0.03] hover:bg-red-500/10 text-slate-400 hover:text-red-400 border border-white/5 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={onOpenAuth}
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-black shadow-lg shadow-emerald-500/20 transition-all flex items-center space-x-1.5"
            >
              <UserIcon className="w-3.5 h-3.5" />
              <span>Connect / Login</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
