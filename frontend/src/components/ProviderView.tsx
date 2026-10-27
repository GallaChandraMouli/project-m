import React, { useState, useEffect } from 'react';
import { Terminal, Cpu, Plus, Trash2, DollarSign, Activity, Check, Copy, RefreshCw, Layers } from 'lucide-react';
import { GpuNode, Wallet } from '../types';
import { getProviderNodes, registerNode, deleteNode, configureNodeModel, getProviderEarnings } from '../api';

interface ProviderViewProps {
  onOpenAuth: () => void;
  isAuthenticated: boolean;
}

export const ProviderView: React.FC<ProviderViewProps> = ({ onOpenAuth, isAuthenticated }) => {
  const [nodes, setNodes] = useState<GpuNode[]>([]);
  const [earnings, setEarnings] = useState<Wallet | null>(null);
  const [newNodeName, setNewNodeName] = useState('');
  const [justRegisteredNode, setJustRegisteredNode] = useState<GpuNode | null>(null);
  const [copiedToken, setCopiedToken] = useState(false);
  const [loading, setLoading] = useState(false);

  // Model Pricing Configuration Modal State
  const [editingNodeId, setEditingNodeId] = useState<string | null>(null);
  const [modelName, setModelName] = useState('llama3:8b');
  const [promptPrice, setPromptPrice] = useState(0.20);
  const [completionPrice, setCompletionPrice] = useState(0.40);

  useEffect(() => {
    if (isAuthenticated) {
      loadData();
    }
  }, [isAuthenticated]);

  const loadData = async () => {
    try {
      const [nodeList, earn] = await Promise.all([getProviderNodes(), getProviderEarnings()]);
      setNodes(nodeList);
      setEarnings(earn);
    } catch (e) {
      console.error(e);
    }
  };

  const handleRegisterNode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNodeName.trim()) return;
    setLoading(true);
    try {
      const node = await registerNode(newNodeName.trim());
      setJustRegisteredNode(node);
      setNewNodeName('');
      loadData();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteNode = async (nodeId: string) => {
    if (!confirm('Are you sure you want to remove this node from your account?')) return;
    try {
      await deleteNode(nodeId);
      loadData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleSaveModelPrice = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingNodeId) return;
    try {
      await configureNodeModel(editingNodeId, modelName, promptPrice, completionPrice);
      setEditingNodeId(null);
      loadData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedToken(true);
    setTimeout(() => setCopiedToken(false), 2000);
  };

  if (!isAuthenticated) {
    return (
      <div className="py-24 text-center max-w-md mx-auto px-4">
        <Cpu className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-white">GPU Provider Portal</h2>
        <p className="text-sm text-slate-400 mt-2">
          Monetize your GPU servers and local Ollama / vLLM instances by providing inference to the network.
        </p>
        <button
          onClick={onOpenAuth}
          className="mt-6 px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 font-bold text-black text-sm shadow-lg shadow-emerald-500/25"
        >
          Sign In as Provider
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
      {/* Earnings Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-3xl bg-white/[0.02] border border-white/10 shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Accumulated Earnings</span>
            <DollarSign className="w-5 h-5 text-emerald-400" />
          </div>
          <div className="my-4">
            <div className="text-3xl font-extrabold text-emerald-400 font-mono">
              ${(earnings?.balance_credits || 0).toFixed(4)}
            </div>
            <div className="text-xs text-slate-400 mt-1">Net yield from serving token inference</div>
          </div>
          <div className="text-xs text-slate-500">90% of all customer token charges credited directly.</div>
        </div>

        <div className="p-6 rounded-3xl bg-white/[0.02] border border-white/10 shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Rigs</span>
            <Activity className="w-5 h-5 text-cyan-400" />
          </div>
          <div className="my-4">
            <div className="text-3xl font-extrabold text-white font-mono">
              {nodes.filter((n) => n.status === 'online').length} / {nodes.length}
            </div>
            <div className="text-xs text-slate-400 mt-1">Nodes currently connected via WSS</div>
          </div>
          <div className="text-xs text-slate-500">Outbound WebSockets require 0 port forwarding.</div>
        </div>

        <div className="p-6 rounded-3xl bg-white/[0.02] border border-white/10 shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Verification Status</span>
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
          </div>
          <div className="my-4">
            <div className="text-lg font-bold text-white">Automated Probing</div>
            <div className="text-xs text-slate-400 mt-1">Synthetic benchmarks measure real tok/s</div>
          </div>
          <div className="text-xs text-slate-500">Fastest nodes receive higher routing priority.</div>
        </div>
      </div>

      {/* Nodes Management Section */}
      <div className="p-8 rounded-3xl bg-white/[0.02] border border-white/10 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-xl font-bold text-white flex items-center space-x-2">
              <Terminal className="w-5 h-5 text-emerald-400" />
              <span>Registered Compute Nodes</span>
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Add a node, install the lightweight daemon, and connect your GPU or local Ollama engine.
            </p>
          </div>

          <form onSubmit={handleRegisterNode} className="flex items-center space-x-2 w-full sm:w-auto">
            <input
              type="text"
              value={newNodeName}
              onChange={(e) => setNewNodeName(e.target.value)}
              placeholder="e.g. RTX-4090-Homelab"
              className="px-3.5 py-2 bg-black/40 border border-white/10 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            />
            <button
              type="submit"
              disabled={loading || !newNodeName.trim()}
              className="px-4 py-2 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-xl text-xs font-bold transition-all disabled:opacity-50 flex items-center space-x-1 whitespace-nowrap"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Node</span>
            </button>
          </form>
        </div>

        {/* Quick Launch Instruction Banner when a node is registered */}
        {justRegisteredNode && (
          <div className="p-5 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-xs space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-bold text-white text-sm">
                Node '{justRegisteredNode.name}' Registered! Start your worker daemon:
              </span>
              <button
                onClick={() => setJustRegisteredNode(null)}
                className="text-slate-400 hover:text-white text-xs"
              >
                Dismiss
              </button>
            </div>
            <div className="bg-black/60 p-3 rounded-xl border border-white/10 font-mono text-emerald-300 flex items-center justify-between">
              <span>python worker/nexus_worker/cli.py start --token {justRegisteredNode.node_token}</span>
              <button
                onClick={() =>
                  handleCopy(`python worker/nexus_worker/cli.py start --token ${justRegisteredNode.node_token}`)
                }
                className="p-1.5 bg-emerald-500/20 hover:bg-emerald-500/30 rounded-lg text-emerald-300 transition-colors ml-2"
              >
                {copiedToken ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
            <p className="text-slate-400">
              The worker connects outbound via WebSocket. No static IP or firewall port forwarding needed.
            </p>
          </div>
        )}

        {/* Nodes Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="text-[10px] uppercase font-bold text-slate-500 border-b border-white/10">
              <tr>
                <th className="pb-3">Node Name</th>
                <th className="pb-3">Hardware / GPU</th>
                <th className="pb-3">Status</th>
                <th className="pb-3">Speed Benchmark</th>
                <th className="pb-3">Worker Token</th>
                <th className="pb-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-sans">
              {nodes.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500">
                    No GPU nodes registered yet. Add a node above to start earning!
                  </td>
                </tr>
              ) : (
                nodes.map((n) => (
                  <tr key={n.id} className="hover:bg-white/[0.01]">
                    <td className="py-3.5 font-bold text-white flex items-center space-x-2">
                      <span
                        className={`w-2 h-2 rounded-full ${
                          n.status === 'online'
                            ? 'bg-emerald-400 shadow-[0_0_8px_#10b981]'
                            : 'bg-slate-600'
                        }`}
                      />
                      <span>{n.name}</span>
                    </td>
                    <td className="py-3.5">
                      <div className="text-slate-200 font-medium">{n.gpu_name}</div>
                      <div className="text-[10px] text-slate-500">{n.vram_mb} MB VRAM</div>
                    </td>
                    <td className="py-3.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider ${
                          n.status === 'online'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : 'bg-white/5 text-slate-400'
                        }`}
                      >
                        {n.status}
                      </span>
                    </td>
                    <td className="py-3.5 font-mono text-cyan-400 font-semibold">
                      {n.tokens_per_sec_benchmark ? `${n.tokens_per_sec_benchmark} tok/s` : 'Unbenchmarked'}
                    </td>
                    <td className="py-3.5 font-mono text-slate-400">
                      <div className="flex items-center space-x-1.5">
                        <span>{n.node_token.slice(0, 14)}...</span>
                        <button
                          onClick={() => handleCopy(n.node_token)}
                          className="p-1 hover:text-emerald-400 text-slate-500 transition-colors"
                          title="Copy token"
                        >
                          <Copy className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                    <td className="py-3.5 text-right space-x-2">
                      <button
                        onClick={() => setEditingNodeId(n.id)}
                        className="px-2.5 py-1 bg-white/5 hover:bg-white/10 text-slate-300 rounded-lg text-[11px] font-medium transition-colors"
                      >
                        Configure Pricing
                      </button>
                      <button
                        onClick={() => handleDeleteNode(n.id)}
                        className="p-1.5 text-slate-500 hover:text-red-400 transition-colors"
                        title="Delete node"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Model Pricing Configuration Modal */}
      {editingNodeId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="relative w-full max-w-md bg-[#0D131F] border border-white/10 rounded-2xl shadow-2xl p-6">
            <h3 className="text-lg font-bold text-white mb-2">Configure Model Inference Price</h3>
            <p className="text-xs text-slate-400 mb-6">
              Set custom rates per 1M tokens. You receive 90% of all generated revenue directly.
            </p>

            <form onSubmit={handleSaveModelPrice} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Model Name</label>
                <input
                  type="text"
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  placeholder="e.g. llama3:8b"
                  className="w-full px-3 py-2 bg-black/40 border border-white/10 rounded-xl text-xs text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Prompt Price ($ / 1M)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={promptPrice}
                    onChange={(e) => setPromptPrice(parseFloat(e.target.value))}
                    className="w-full px-3 py-2 bg-black/40 border border-white/10 rounded-xl text-xs text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Completion Price ($ / 1M)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={completionPrice}
                    onChange={(e) => setCompletionPrice(parseFloat(e.target.value))}
                    className="w-full px-3 py-2 bg-black/40 border border-white/10 rounded-xl text-xs text-white"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end space-x-2 pt-4">
                <button
                  type="button"
                  onClick={() => setEditingNodeId(null)}
                  className="px-4 py-2 bg-white/5 hover:bg-white/10 text-slate-300 rounded-xl text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-black font-bold rounded-xl text-xs"
                >
                  Save Model Pricing
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
