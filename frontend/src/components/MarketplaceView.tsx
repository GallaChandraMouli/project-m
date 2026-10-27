import React, { useState, useEffect } from 'react';
import { Search, Zap, Cpu, Server, Activity, ArrowRight, CheckCircle2, ChevronRight, Layers } from 'lucide-react';
import { MarketplaceModel } from '../types';
import { getMarketplaceModels, getModelProviders } from '../api';

interface MarketplaceViewProps {
  onSelectModel: (modelName: string) => void;
  onOpenAuth: () => void;
}

export const MarketplaceView: React.FC<MarketplaceViewProps> = ({ onSelectModel, onOpenAuth }) => {
  const [models, setModels] = useState<MarketplaceModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedModelProviders, setSelectedModelProviders] = useState<{ modelName: string; providers: any[] } | null>(null);

  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    setLoading(true);
    try {
      const data = await getMarketplaceModels();
      setModels(data);
    } catch (e) {
      console.error('Failed to load marketplace models:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleInspectProviders = async (modelName: string) => {
    try {
      const providers = await getModelProviders(modelName);
      setSelectedModelProviders({ modelName, providers });
    } catch (e) {
      console.error('Failed to fetch providers:', e);
    }
  };

  const filteredModels = models.filter((m) =>
    m.model_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-10 py-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-b from-white/[0.04] to-transparent border border-white/10 p-8 sm:p-12">
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/4 -mb-12 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-3xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold mb-6">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span>Open P2P Compute Mesh Active</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight leading-tight">
            Decentralized Open-Source <br />
            <span className="bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
              AI Inference Network
            </span>
          </h1>
          <p className="mt-4 text-base sm:text-lg text-slate-300 leading-relaxed">
            Directly connect to independent GPU providers running open weights (Llama 3, DeepSeek-R1, Mistral). Drop-in OpenAI API compatibility at up to 80% lower cost.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-4">
            <button
              onClick={() => onSelectModel(models[0]?.model_name || 'llama3:8b')}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-black font-bold text-sm shadow-lg shadow-emerald-500/25 transition-all flex items-center space-x-2"
            >
              <Zap className="w-4 h-4" />
              <span>Launch Playground</span>
            </button>
            <button
              onClick={onOpenAuth}
              className="px-6 py-3 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] text-white border border-white/10 font-semibold text-sm transition-all flex items-center space-x-2"
            >
              <Server className="w-4 h-4 text-emerald-400" />
              <span>Become a GPU Provider</span>
            </button>
          </div>
        </div>

        {/* Global Metric Cards */}
        <div className="mt-12 grid grid-cols-2 sm:grid-cols-4 gap-4 border-t border-white/10 pt-8">
          <div>
            <div className="text-2xl sm:text-3xl font-extrabold text-white font-mono">
              {models.reduce((acc, m) => acc + m.active_providers_count, 0)}
            </div>
            <div className="text-xs text-slate-400 mt-1 flex items-center space-x-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span>Active GPU Nodes</span>
            </div>
          </div>
          <div>
            <div className="text-2xl sm:text-3xl font-extrabold text-white font-mono">{models.length}</div>
            <div className="text-xs text-slate-400 mt-1 flex items-center space-x-1">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
              <span>Available Models</span>
            </div>
          </div>
          <div>
            <div className="text-2xl sm:text-3xl font-extrabold text-white font-mono">
              {models.length > 0
                ? (models.reduce((acc, m) => acc + m.avg_tokens_per_sec, 0) / models.length).toFixed(1)
                : '64.2'}
            </div>
            <div className="text-xs text-slate-400 mt-1">Avg Tokens / Sec</div>
          </div>
          <div>
            <div className="text-2xl sm:text-3xl font-extrabold text-emerald-400 font-mono">100%</div>
            <div className="text-xs text-slate-400 mt-1">OpenAI Compatible</div>
          </div>
        </div>
      </div>

      {/* Catalog Search & Filters */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Active Model Registry</h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time verified models routed across peer providers with automatic failover
          </p>
        </div>

        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3.5 top-3 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search models (e.g. llama3, deepseek)..."
            className="w-full pl-10 pr-4 py-2 bg-white/[0.03] border border-white/10 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors"
          />
        </div>
      </div>

      {/* Models Grid */}
      {loading ? (
        <div className="py-20 text-center text-slate-400">Loading active compute models...</div>
      ) : filteredModels.length === 0 ? (
        <div className="py-20 text-center rounded-2xl bg-white/[0.02] border border-white/5 p-8">
          <Layers className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-white">No models match your search</h3>
          <p className="text-xs text-slate-400 mt-1">
            Start a worker node using <code className="text-emerald-400">nexus-worker start</code> to register models!
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredModels.map((m) => (
            <div
              key={m.model_name}
              className="group relative rounded-2xl bg-white/[0.02] hover:bg-white/[0.04] border border-white/10 hover:border-emerald-500/40 p-6 transition-all duration-300 shadow-xl flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                    <Cpu className="w-4 h-4" />
                  </div>
                  <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-mono">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    <span>{m.active_providers_count} Provider{m.active_providers_count !== 1 ? 's' : ''}</span>
                  </div>
                </div>

                <h3 className="text-lg font-bold text-white group-hover:text-emerald-300 transition-colors">
                  {m.model_name}
                </h3>
                <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                  Open weights model served by verified distributed GPU rigs with real-time token streaming.
                </p>

                {/* Pricing & Speed Matrix */}
                <div className="mt-6 grid grid-cols-2 gap-3 p-3 rounded-xl bg-black/40 border border-white/5">
                  <div>
                    <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
                      Prompt Price
                    </span>
                    <div className="text-sm font-bold text-slate-200 font-mono mt-0.5">
                      ${m.min_prompt_price.toFixed(2)}
                      <span className="text-[10px] text-slate-400 font-normal"> / 1M</span>
                    </div>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
                      Completion
                    </span>
                    <div className="text-sm font-bold text-emerald-400 font-mono mt-0.5">
                      ${m.min_completion_price.toFixed(2)}
                      <span className="text-[10px] text-slate-400 font-normal"> / 1M</span>
                    </div>
                  </div>
                </div>

                <div className="mt-4 flex items-center justify-between text-xs text-slate-400">
                  <span className="flex items-center space-x-1">
                    <Activity className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Benchmark Speed:</span>
                  </span>
                  <span className="font-mono font-bold text-white">{m.avg_tokens_per_sec} tok/s</span>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-white/10 flex items-center justify-between gap-3">
                <button
                  onClick={() => handleInspectProviders(m.model_name)}
                  className="text-xs text-slate-400 hover:text-white flex items-center space-x-1 transition-colors"
                >
                  <span>View Rigs</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => onSelectModel(m.model_name)}
                  className="px-4 py-2 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-semibold flex items-center space-x-1.5 transition-all"
                >
                  <Zap className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Test Playground</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Provider Details Modal */}
      {selectedModelProviders && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="relative w-full max-w-2xl bg-[#0D131F] border border-white/10 rounded-2xl shadow-2xl p-6">
            <div className="flex items-center justify-between pb-4 border-b border-white/10">
              <div>
                <h3 className="text-lg font-bold text-white">
                  Active Providers for {selectedModelProviders.modelName}
                </h3>
                <p className="text-xs text-slate-400">
                  Discovered nodes currently routing inference for this model
                </p>
              </div>
              <button
                onClick={() => setSelectedModelProviders(null)}
                className="text-slate-400 hover:text-white text-xs px-2 py-1 rounded bg-white/5"
              >
                Close
              </button>
            </div>

            <div className="mt-4 space-y-3 max-h-96 overflow-y-auto">
              {selectedModelProviders.providers.length === 0 ? (
                <p className="text-xs text-slate-400 py-6 text-center">No individual nodes reporting right now.</p>
              ) : (
                selectedModelProviders.providers.map((p, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl bg-white/[0.02] border border-white/5 flex items-center justify-between"
                  >
                    <div>
                      <div className="text-sm font-bold text-white flex items-center space-x-2">
                        <span>{p.node_name}</span>
                        <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/15 text-emerald-300 font-mono">
                          {p.gpu_name}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400 mt-1">
                        VRAM: {p.vram_mb} MB | Speed: {p.tokens_per_sec} tok/s
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs font-mono font-bold text-emerald-400">
                        ${p.completion_price_m}/M
                      </div>
                      <div className="text-[10px] text-slate-500">completion price</div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
