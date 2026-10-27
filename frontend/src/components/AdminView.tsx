import React, { useState, useEffect } from 'react';
import { Shield, Users, Server, Zap, Coins, Activity, RefreshCw } from 'lucide-react';
import { AdminStats } from '../types';
import { getAdminStats, getAdminNodes } from '../api';

export const AdminView: React.FC = () => {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [nodes, setNodes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    setLoading(true);
    try {
      const [s, n] = await Promise.all([getAdminStats(), getAdminNodes()]);
      setStats(s);
      setNodes(n);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center space-x-2">
            <Shield className="w-6 h-6 text-emerald-400" />
            <span>Network Health & Platform Oversight</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Global network telemetry, compute utilization, and platform fee settlement ledger
          </p>
        </div>

        <button
          onClick={loadAdminData}
          disabled={loading}
          className="px-3.5 py-2 bg-white/5 hover:bg-white/10 text-slate-300 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Telemetry</span>
        </button>
      </div>

      {/* Network Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <div className="p-6 rounded-3xl bg-white/[0.02] border border-white/10 shadow-xl">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase">Total Users</span>
            <Users className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold text-white font-mono mt-3">
            {stats?.total_users ?? '--'}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Consumers & Providers</div>
        </div>

        <div className="p-6 rounded-3xl bg-white/[0.02] border border-white/10 shadow-xl">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase">Online Nodes</span>
            <Server className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-extrabold text-white font-mono mt-3">
            {stats?.online_nodes ?? '--'}
            <span className="text-sm font-normal text-slate-500"> / {stats?.total_nodes ?? '--'}</span>
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Live WebSocket Uplinks</div>
        </div>

        <div className="p-6 rounded-3xl bg-white/[0.02] border border-white/10 shadow-xl">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase">Total Tokens</span>
            <Zap className="w-4 h-4 text-yellow-400" />
          </div>
          <div className="text-3xl font-extrabold text-white font-mono mt-3">
            {stats?.total_tokens_processed?.toLocaleString() ?? '--'}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Inference Volume Served</div>
        </div>

        <div className="p-6 rounded-3xl bg-white/[0.02] border border-white/10 shadow-xl">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase">Protocol Revenue</span>
            <Coins className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold text-emerald-400 font-mono mt-3">
            ${stats?.platform_revenue_credits?.toFixed(4) ?? '0.0000'}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">10% Platform Cut</div>
        </div>
      </div>

      {/* Real-time Connected Rigs Table */}
      <div className="p-8 rounded-3xl bg-white/[0.02] border border-white/10 shadow-xl space-y-4">
        <h3 className="text-lg font-bold text-white">Live Node Telemetry</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="text-[10px] uppercase font-bold text-slate-500 border-b border-white/10">
              <tr>
                <th className="pb-3">Node Name</th>
                <th className="pb-3">Operator Email</th>
                <th className="pb-3">Hardware Spec</th>
                <th className="pb-3">Status</th>
                <th className="pb-3">Benchmark Speed</th>
                <th className="pb-3 text-right">Last Heartbeat</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-sans">
              {nodes.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500">
                    No nodes connected to coordinator.
                  </td>
                </tr>
              ) : (
                nodes.map((n) => (
                  <tr key={n.id} className="hover:bg-white/[0.01]">
                    <td className="py-3.5 font-bold text-white flex items-center space-x-2">
                      <span
                        className={`w-2 h-2 rounded-full ${
                          n.status === 'online' ? 'bg-emerald-400' : 'bg-slate-600'
                        }`}
                      />
                      <span>{n.name}</span>
                    </td>
                    <td className="py-3.5 text-slate-400 font-mono">{n.provider_email}</td>
                    <td className="py-3.5">
                      <span className="font-semibold text-white">{n.gpu_name}</span>
                      <span className="text-slate-500 ml-1.5">({n.vram_mb} MB)</span>
                    </td>
                    <td className="py-3.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] uppercase font-semibold ${
                          n.status === 'online'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : 'bg-white/5 text-slate-400'
                        }`}
                      >
                        {n.status}
                      </span>
                    </td>
                    <td className="py-3.5 font-mono text-cyan-400">
                      {n.tokens_per_sec ? `${n.tokens_per_sec} tok/s` : '--'}
                    </td>
                    <td className="py-3.5 text-right font-mono text-slate-400">
                      {n.last_heartbeat ? new Date(n.last_heartbeat).toLocaleTimeString() : 'Never'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
