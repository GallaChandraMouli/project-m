import React, { useState, useEffect } from 'react';
import { Key, Plus, Trash2, Copy, Check, Terminal, Wallet as WalletIcon, History, ExternalLink, Code } from 'lucide-react';
import { ApiKey, Wallet, InferenceJob } from '../types';
import { getApiKeys, createApiKey, revokeApiKey, getConsumerWallet, claimFaucet, getUsageHistory, API_BASE } from '../api';

interface ConsumerViewProps {
  wallet: Wallet | null;
  onRefreshWallet: () => void;
  onOpenAuth: () => void;
  isAuthenticated: boolean;
}

export const ConsumerView: React.FC<ConsumerViewProps> = ({
  wallet,
  onRefreshWallet,
  onOpenAuth,
  isAuthenticated,
}) => {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [usageJobs, setUsageJobs] = useState<InferenceJob[]>([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [createdKeyRaw, setCreatedKeyRaw] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState(false);
  const [activeCodeTab, setActiveCodeTab] = useState<'python' | 'curl' | 'node'>('python');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      loadData();
    }
  }, [isAuthenticated]);

  const loadData = async () => {
    try {
      const [keys, jobs] = await Promise.all([getApiKeys(), getUsageHistory()]);
      setApiKeys(keys);
      setUsageJobs(jobs);
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyName.trim()) return;
    setLoading(true);
    try {
      const res = await createApiKey(newKeyName.trim());
      setCreatedKeyRaw(res.raw_api_key);
      setNewKeyName('');
      loadData();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRevokeKey = async (id: string) => {
    if (!confirm('Are you sure you want to revoke this API key? External apps using it will lose access.')) return;
    try {
      await revokeApiKey(id);
      loadData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(true);
    setTimeout(() => setCopiedKey(false), 2000);
  };

  if (!isAuthenticated) {
    return (
      <div className="py-24 text-center max-w-md mx-auto px-4">
        <Key className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-white">Developer & Consumer Portal</h2>
        <p className="text-sm text-slate-400 mt-2">
          Connect your account to generate API keys, claim test credits, and inspect request ledgers.
        </p>
        <button
          onClick={onOpenAuth}
          className="mt-6 px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 font-bold text-black text-sm shadow-lg shadow-emerald-500/25"
        >
          Sign In / Create Account
        </button>
      </div>
    );
  }

  const sampleKey = apiKeys[0]?.key_prefix ? `${apiKeys[0].key_prefix}...` : 'nx-live-your-api-key';

  const codeSnippets = {
    python: `from openai import OpenAI

client = OpenAI(
    base_url="${API_BASE}/v1",
    api_key="${createdKeyRaw || sampleKey}"
)

response = client.chat.completions.create(
    model="llama3:8b",
    messages=[{"role": "user", "content": "Explain decentralized AI in one paragraph."}],
    stream=True
)

for chunk in response:
    print(chunk.choices[0].delta.content or "", end="")`,
    curl: `curl ${API_BASE}/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer ${createdKeyRaw || sampleKey}" \\
  -d '{
    "model": "llama3:8b",
    "messages": [{"role": "user", "content": "Hello NexusCompute"}],
    "stream": true
  }'`,
    node: `import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "${API_BASE}/v1",
  apiKey: "${createdKeyRaw || sampleKey}",
});

const stream = await client.chat.completions.create({
  model: "llama3:8b",
  messages: [{ role: "user", content: "Hello!" }],
  stream: true,
});

for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content || "");
}`,
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
      {/* Top Ledger & Wallet Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-3xl bg-white/[0.02] border border-white/10 shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Usable Balance</span>
            <WalletIcon className="w-5 h-5 text-emerald-400" />
          </div>
          <div className="my-4">
            <div className="text-3xl font-extrabold text-white font-mono">
              ${(wallet?.balance_credits || 0).toFixed(4)}
            </div>
            <div className="text-xs text-slate-400 mt-1">Prepaid compute credits</div>
          </div>
          <button
            onClick={async () => {
              await claimFaucet();
              onRefreshWallet();
            }}
            className="w-full py-2 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded-xl text-xs font-semibold transition-all"
          >
            + Claim $25.00 Testnet Credits
          </button>
        </div>

        <div className="p-6 rounded-3xl bg-white/[0.02] border border-white/10 shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Escrow Holds</span>
            <div className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
          </div>
          <div className="my-4">
            <div className="text-3xl font-extrabold text-cyan-300 font-mono">
              ${(wallet?.locked_credits || 0).toFixed(4)}
            </div>
            <div className="text-xs text-slate-400 mt-1">Active in-flight streaming holds</div>
          </div>
          <div className="text-xs text-slate-400">Released or settled upon stream completion.</div>
        </div>

        <div className="p-6 rounded-3xl bg-white/[0.02] border border-white/10 shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Requests</span>
            <History className="w-5 h-5 text-slate-400" />
          </div>
          <div className="my-4">
            <div className="text-3xl font-extrabold text-white font-mono">{usageJobs.length}</div>
            <div className="text-xs text-slate-400 mt-1">Completed inference queries</div>
          </div>
          <div className="text-xs text-slate-400">Verifiable token billing logs below.</div>
        </div>
      </div>

      {/* API Key Management */}
      <div className="p-8 rounded-3xl bg-white/[0.02] border border-white/10 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-xl font-bold text-white flex items-center space-x-2">
              <Key className="w-5 h-5 text-emerald-400" />
              <span>Inference API Keys</span>
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Use these standard OpenAI-compatible keys in your Python, LangChain, or Node.js applications.
            </p>
          </div>

          <form onSubmit={handleCreateKey} className="flex items-center space-x-2 w-full sm:w-auto">
            <input
              type="text"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              placeholder="e.g. My App Server"
              className="px-3.5 py-2 bg-black/40 border border-white/10 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            />
            <button
              type="submit"
              disabled={loading || !newKeyName.trim()}
              className="px-4 py-2 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-xl text-xs font-bold transition-all disabled:opacity-50 flex items-center space-x-1 whitespace-nowrap"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Create Key</span>
            </button>
          </form>
        </div>

        {/* Modal-style raw key alert if just created */}
        {createdKeyRaw && (
          <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/40 text-emerald-200 text-xs space-y-2">
            <div className="font-bold flex items-center space-x-1.5">
              <Check className="w-4 h-4 text-emerald-400" />
              <span>API Key Created Successfully!</span>
            </div>
            <p className="text-slate-300">
              Please copy this key now. For your security, it will not be displayed in full again:
            </p>
            <div className="flex items-center space-x-2 bg-black/60 p-2.5 rounded-xl border border-emerald-500/30 font-mono text-sm text-emerald-300">
              <span className="flex-1 overflow-x-auto">{createdKeyRaw}</span>
              <button
                onClick={() => handleCopy(createdKeyRaw)}
                className="p-1.5 bg-emerald-500/20 hover:bg-emerald-500/30 rounded-lg text-emerald-300 transition-colors"
              >
                {copiedKey ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>
          </div>
        )}

        {/* Active Keys Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="text-[10px] uppercase font-bold text-slate-500 border-b border-white/10">
              <tr>
                <th className="pb-3">Key Name</th>
                <th className="pb-3">Prefix</th>
                <th className="pb-3">Created</th>
                <th className="pb-3">Status</th>
                <th className="pb-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-sans">
              {apiKeys.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-slate-500">
                    No API keys created yet. Generate one above to access the API.
                  </td>
                </tr>
              ) : (
                apiKeys.map((k) => (
                  <tr key={k.id} className="hover:bg-white/[0.01]">
                    <td className="py-3 font-semibold text-white">{k.name}</td>
                    <td className="py-3 font-mono text-emerald-400">{k.key_prefix}...</td>
                    <td className="py-3 text-slate-400">{new Date(k.created_at).toLocaleDateString()}</td>
                    <td className="py-3">
                      <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        Active
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      <button
                        onClick={() => handleRevokeKey(k.id)}
                        className="p-1 text-slate-500 hover:text-red-400 transition-colors"
                        title="Revoke key"
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

      {/* Drop-in OpenAI SDK Code Integration */}
      <div className="p-8 rounded-3xl bg-white/[0.02] border border-white/10 shadow-xl space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold text-white flex items-center space-x-2">
              <Code className="w-5 h-5 text-cyan-400" />
              <span>Drop-in OpenAI SDK Compatibility</span>
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Simply set <code className="text-emerald-400">base_url="{API_BASE}/v1"</code> in your existing AI code.
            </p>
          </div>

          <div className="flex space-x-1 bg-white/5 p-1 rounded-xl">
            {(['python', 'curl', 'node'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveCodeTab(tab)}
                className={`px-3 py-1 rounded-lg text-xs font-mono font-medium transition-colors ${
                  activeCodeTab === tab ? 'bg-emerald-500/20 text-emerald-300' : 'text-slate-400 hover:text-white'
                }`}
              >
                {tab.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        <div className="relative rounded-2xl bg-black/60 border border-white/10 p-5 font-mono text-xs text-emerald-300 overflow-x-auto">
          <button
            onClick={() => handleCopy(codeSnippets[activeCodeTab])}
            className="absolute top-4 right-4 p-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
          >
            {copiedKey ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
          </button>
          <pre>{codeSnippets[activeCodeTab]}</pre>
        </div>
      </div>

      {/* Usage History Ledger */}
      <div className="p-8 rounded-3xl bg-white/[0.02] border border-white/10 shadow-xl space-y-4">
        <h3 className="text-xl font-bold text-white">Recent Inference Queries</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="text-[10px] uppercase font-bold text-slate-500 border-b border-white/10">
              <tr>
                <th className="pb-3">Job ID</th>
                <th className="pb-3">Model</th>
                <th className="pb-3">Prompt / Completion</th>
                <th className="pb-3">Latency</th>
                <th className="pb-3">Total Cost</th>
                <th className="pb-3 text-right">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-sans">
              {usageJobs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-slate-500">
                    No inference requests yet. Test in the Playground or send an API call!
                  </td>
                </tr>
              ) : (
                usageJobs.map((j) => (
                  <tr key={j.id} className="hover:bg-white/[0.01]">
                    <td className="py-3 font-mono text-slate-400">{j.id.slice(0, 12)}...</td>
                    <td className="py-3 font-semibold text-white">{j.model_name}</td>
                    <td className="py-3 font-mono text-slate-300">
                      {j.prompt_tokens}p + {j.completion_tokens}c
                    </td>
                    <td className="py-3 font-mono text-cyan-400">{j.latency_ms} ms</td>
                    <td className="py-3 font-mono text-emerald-400">${j.total_cost.toFixed(4)}</td>
                    <td className="py-3 text-right text-slate-400">
                      {new Date(j.created_at).toLocaleTimeString()}
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
