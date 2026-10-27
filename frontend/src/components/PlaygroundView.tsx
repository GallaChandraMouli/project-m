import React, { useState, useRef, useEffect } from 'react';
import { Send, Zap, RotateCcw, Cpu, Sparkles, Sliders, Clock, Activity, Coins } from 'lucide-react';
import { streamChatInference, getMarketplaceModels } from '../api';
import { MarketplaceModel } from '../types';

interface Message {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

interface PlaygroundViewProps {
  initialModel?: string;
  onOpenAuth: () => void;
  isAuthenticated: boolean;
}

export const PlaygroundView: React.FC<PlaygroundViewProps> = ({
  initialModel = 'llama3:8b',
  onOpenAuth,
  isAuthenticated,
}) => {
  const [models, setModels] = useState<MarketplaceModel[]>([]);
  const [selectedModel, setSelectedModel] = useState(initialModel);
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(512);
  const [systemPrompt, setSystemPrompt] = useState('You are a helpful, concise AI assistant running on a decentralized GPU network.');
  const [inputPrompt, setInputPrompt] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Hello! I am running on a decentralized open-source GPU node. How can I help you today?',
    },
  ]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Streaming Telemetry Metrics
  const [tokenCount, setTokenCount] = useState(0);
  const [latencyMs, setLatencyMs] = useState(0);
  const [tokensPerSec, setTokensPerSec] = useState(0);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getMarketplaceModels().then((data) => {
      setModels(data);
      if (data.length > 0 && !data.some((m) => m.model_name === selectedModel)) {
        setSelectedModel(data[0].model_name);
      }
    });
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputPrompt.trim() || isStreaming) return;

    if (!isAuthenticated) {
      onOpenAuth();
      return;
    }

    const userMsg: Message = { role: 'user', content: inputPrompt };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setInputPrompt('');
    setError(null);
    setIsStreaming(true);

    // Telemetry tracking
    const startTime = performance.now();
    let currentTokens = 0;

    // Placeholder for streaming assistant response
    setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);

    try {
      const apiMessages = [
        ...(systemPrompt ? [{ role: 'system', content: systemPrompt }] : []),
        ...updatedMessages.filter((m) => m.role !== 'system'),
      ];

      const stream = streamChatInference(selectedModel, apiMessages, temperature, maxTokens);

      for await (const chunk of stream) {
        currentTokens += 1;
        setTokenCount(currentTokens);

        const elapsed = (performance.now() - startTime) / 1000;
        if (elapsed > 0.1) {
          setTokensPerSec(Number((currentTokens / elapsed).toFixed(1)));
        }

        setMessages((prev) => {
          const next = [...prev];
          const last = next[next.length - 1];
          if (last && last.role === 'assistant') {
            last.content += chunk;
          }
          return next;
        });
      }

      setLatencyMs(Math.round(performance.now() - startTime));
    } catch (err: any) {
      setError(err.message || 'Inference error');
      setMessages((prev) => {
        const next = [...prev];
        const last = next[next.length - 1];
        if (last && last.role === 'assistant' && !last.content) {
          next.pop(); // Remove empty placeholder
        }
        return next;
      });
    } finally {
      setIsStreaming(false);
    }
  };

  const handleReset = () => {
    setMessages([
      {
        role: 'assistant',
        content: 'Conversation reset. Ready for a new prompt!',
      },
    ]);
    setTokenCount(0);
    setLatencyMs(0);
    setTokensPerSec(0);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 h-[calc(100vh-6rem)] flex flex-col lg:flex-row gap-6">
      {/* Left Chat Window */}
      <div className="flex-1 flex flex-col bg-white/[0.02] border border-white/10 rounded-3xl overflow-hidden shadow-2xl backdrop-blur-xl">
        {/* Chat Header & Telemetry Bar */}
        <div className="px-6 py-4 border-b border-white/10 bg-black/20 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <div className="text-sm font-bold text-white flex items-center space-x-2">
                <span>{selectedModel}</span>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              </div>
              <div className="text-[11px] text-slate-400">Direct streaming via active provider pool</div>
            </div>
          </div>

          {/* Real-time Telemetry HUD */}
          <div className="flex items-center space-x-4 text-xs font-mono">
            <div className="flex items-center space-x-1.5 text-slate-300 bg-white/5 px-2.5 py-1 rounded-lg">
              <Activity className="w-3.5 h-3.5 text-cyan-400" />
              <span>{tokensPerSec || '--'} tok/s</span>
            </div>
            <div className="flex items-center space-x-1.5 text-slate-300 bg-white/5 px-2.5 py-1 rounded-lg">
              <Clock className="w-3.5 h-3.5 text-emerald-400" />
              <span>{latencyMs ? `${latencyMs}ms` : '--'}</span>
            </div>
            <div className="flex items-center space-x-1.5 text-slate-300 bg-white/5 px-2.5 py-1 rounded-lg">
              <Coins className="w-3.5 h-3.5 text-yellow-400" />
              <span>{tokenCount} tokens</span>
            </div>
            <button
              onClick={handleReset}
              title="Reset Chat"
              className="p-1.5 text-slate-400 hover:text-white rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Message Stream Scroll Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {error && (
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs flex items-center justify-between">
              <span>{error}</span>
              {!isAuthenticated && (
                <button onClick={onOpenAuth} className="underline font-bold ml-2">
                  Sign in
                </button>
              )}
            </div>
          )}

          {messages.map((m, idx) => (
            <div
              key={idx}
              className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
            >
              <div
                className={`max-w-[85%] sm:max-w-[75%] rounded-2xl p-4 text-sm leading-relaxed ${
                  m.role === 'user'
                    ? 'bg-emerald-500/15 border border-emerald-500/30 text-white rounded-br-none shadow-lg shadow-emerald-500/5'
                    : 'bg-white/[0.04] border border-white/10 text-slate-200 rounded-bl-none shadow-md'
                }`}
              >
                <div className="text-[10px] uppercase font-bold text-slate-400 mb-1 tracking-wider">
                  {m.role === 'user' ? 'You' : `${selectedModel} (Provider)`}
                </div>
                <div className="whitespace-pre-wrap font-sans">{m.content || (isStreaming ? '...' : '')}</div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <form onSubmit={handleSend} className="p-4 border-t border-white/10 bg-black/30 flex items-center gap-3">
          <input
            type="text"
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            disabled={isStreaming}
            placeholder={
              isAuthenticated
                ? 'Type your message or prompt here...'
                : 'Please connect/login to execute inference...'
            }
            className="flex-1 bg-white/[0.04] border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isStreaming || !inputPrompt.trim()}
            className="p-3 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-black font-bold rounded-xl shadow-lg shadow-emerald-500/20 disabled:opacity-40 transition-all flex items-center justify-center"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>

      {/* Right Parameter Drawer */}
      <div className="w-full lg:w-80 bg-white/[0.02] border border-white/10 rounded-3xl p-6 flex flex-col justify-between backdrop-blur-xl space-y-6">
        <div className="space-y-6">
          <div className="flex items-center space-x-2 pb-4 border-b border-white/10">
            <Sliders className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-bold text-white tracking-wide">Inference Settings</h3>
          </div>

          {/* Model Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-2">Model</label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
            >
              {models.length > 0 ? (
                models.map((m) => (
                  <option key={m.model_name} value={m.model_name} className="bg-slate-900 text-white">
                    {m.model_name} ({m.active_providers_count} nodes)
                  </option>
                ))
              ) : (
                <option value="llama3:8b">llama3:8b</option>
              )}
            </select>
          </div>

          {/* Temperature Slider */}
          <div>
            <div className="flex justify-between text-xs text-slate-300 mb-1.5">
              <span className="font-semibold">Temperature</span>
              <span className="font-mono text-emerald-400">{temperature}</span>
            </div>
            <input
              type="range"
              min="0"
              max="1.5"
              step="0.05"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              className="w-full accent-emerald-500 h-1.5 bg-white/10 rounded-lg cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 mt-1">
              <span>Precise</span>
              <span>Creative</span>
            </div>
          </div>

          {/* Max Tokens Slider */}
          <div>
            <div className="flex justify-between text-xs text-slate-300 mb-1.5">
              <span className="font-semibold">Max Tokens</span>
              <span className="font-mono text-emerald-400">{maxTokens}</span>
            </div>
            <input
              type="range"
              min="64"
              max="2048"
              step="64"
              value={maxTokens}
              onChange={(e) => setMaxTokens(parseInt(e.target.value))}
              className="w-full accent-emerald-500 h-1.5 bg-white/10 rounded-lg cursor-pointer"
            />
          </div>

          {/* System Prompt */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">System Prompt</label>
            <textarea
              rows={3}
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              className="w-full bg-black/40 border border-white/10 rounded-xl p-3 text-xs text-slate-300 placeholder-slate-600 focus:outline-none focus:border-emerald-500 resize-none"
            />
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-black/40 border border-white/5 text-[11px] text-slate-400 space-y-1.5">
          <div className="font-bold text-white flex items-center space-x-1.5">
            <Cpu className="w-3.5 h-3.5 text-emerald-400" />
            <span>Smart Routing</span>
          </div>
          <p>
            Requests are automatically routed to the lowest-cost, lowest-latency online provider. If a provider drops, the coordinator auto-retries on a backup node.
          </p>
        </div>
      </div>
    </div>
  );
};
