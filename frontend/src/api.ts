import { User, Wallet, ApiKey, ApiKeyCreatedResponse, GpuNode, MarketplaceModel, InferenceJob, AdminStats } from './types';

export const API_BASE = 'http://localhost:8000';

export function getAuthToken(): string | null {
  return localStorage.getItem('nexus_token');
}

export function setAuthToken(token: string) {
  localStorage.setItem('nexus_token', token);
}

export function removeAuthToken() {
  localStorage.removeItem('nexus_token');
  localStorage.removeItem('nexus_user');
}

export function getStoredUser(): User | null {
  const u = localStorage.getItem('nexus_user');
  return u ? JSON.parse(u) : null;
}

export function setStoredUser(user: User) {
  localStorage.setItem('nexus_user', JSON.stringify(user));
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || 'An unexpected error occurred');
  }

  return res.json();
}

// Auth APIs
export async function registerUser(email: string, password: string, role: string = 'consumer') {
  const data = await request<{ access_token: string; user_id: string; email: string; role: string }>('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, role }),
  });
  setAuthToken(data.access_token);
  const user: User = { id: data.user_id, email: data.email, role: data.role as any, created_at: new Date().toISOString() };
  setStoredUser(user);
  return user;
}

export async function loginUser(email: string, password: string) {
  const data = await request<{ access_token: string; user_id: string; email: string; role: string }>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  setAuthToken(data.access_token);
  const user: User = { id: data.user_id, email: data.email, role: data.role as any, created_at: new Date().toISOString() };
  setStoredUser(user);
  return user;
}

export async function getMe(): Promise<User> {
  return request<User>('/api/v1/auth/me');
}

// Consumer APIs
export async function getConsumerWallet(): Promise<Wallet> {
  return request<Wallet>('/api/v1/consumer/wallet');
}

export async function claimFaucet(): Promise<{ message: string; new_balance: number }> {
  return request<{ message: string; new_balance: number }>('/api/v1/consumer/wallet/faucet', { method: 'POST' });
}

export async function getApiKeys(): Promise<ApiKey[]> {
  return request<ApiKey[]>('/api/v1/consumer/api-keys');
}

export async function createApiKey(name: string): Promise<ApiKeyCreatedResponse> {
  return request<ApiKeyCreatedResponse>('/api/v1/consumer/api-keys', {
    method: 'POST',
    body: JSON.stringify({ name }),
  });
}

export async function revokeApiKey(keyId: string): Promise<{ message: string }> {
  return request<{ message: string }>(`/api/v1/consumer/api-keys/${keyId}`, { method: 'DELETE' });
}

export async function getUsageHistory(): Promise<InferenceJob[]> {
  return request<InferenceJob[]>('/api/v1/consumer/usage');
}

// Provider APIs
export async function getProviderNodes(): Promise<GpuNode[]> {
  return request<GpuNode[]>('/api/v1/provider/nodes');
}

export async function registerNode(name: string): Promise<GpuNode> {
  return request<GpuNode>('/api/v1/provider/nodes/register', {
    method: 'POST',
    body: JSON.stringify({ name }),
  });
}

export async function deleteNode(nodeId: string): Promise<{ message: string }> {
  return request<{ message: string }>(`/api/v1/provider/nodes/${nodeId}`, { method: 'DELETE' });
}

export async function configureNodeModel(nodeId: string, model_name: string, promptPrice: number, completionPrice: number) {
  return request(`/api/v1/provider/nodes/${nodeId}/models`, {
    method: 'POST',
    body: JSON.stringify({
      model_name,
      price_per_million_prompt: promptPrice,
      price_per_million_completion: completionPrice,
    }),
  });
}

export async function getProviderEarnings(): Promise<Wallet> {
  return request<Wallet>('/api/v1/provider/earnings');
}

// Marketplace APIs
export async function getMarketplaceModels(): Promise<MarketplaceModel[]> {
  return request<MarketplaceModel[]>('/api/v1/models');
}

export async function getModelProviders(modelName: string): Promise<any[]> {
  return request<any[]>(`/api/v1/models/${encodeURIComponent(modelName)}/providers`);
}

// Admin APIs
export async function getAdminStats(): Promise<AdminStats> {
  return request<AdminStats>('/api/v1/admin/stats');
}

export async function getAdminNodes(): Promise<any[]> {
  return request<any[]>('/api/v1/admin/nodes');
}

// Streaming Inference via /v1/chat/completions
export async function* streamChatInference(
  model: string,
  messages: { role: string; content: string }[],
  temperature: number = 0.7,
  max_tokens: number = 1024
): AsyncGenerator<string, void, unknown> {
  const token = getAuthToken();
  const res = await fetch(`${API_BASE}/v1/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      model,
      messages,
      temperature,
      max_tokens,
      stream: true,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Inference request failed');
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error('Failed to open readable stream');

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || !trimmed.startsWith('data: ')) continue;
      const dataStr = trimmed.slice(6);
      if (dataStr === '[DONE]') return;

      try {
        const parsed = JSON.parse(dataStr);
        if (parsed.error) throw new Error(parsed.error);
        const delta = parsed.choices?.[0]?.delta?.content;
        if (delta) yield delta;
      } catch (e) {
        if (e instanceof Error && e.message.includes('error')) throw e;
      }
    }
  }
}
