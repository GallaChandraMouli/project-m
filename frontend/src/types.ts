export interface User {
  id: string;
  email: string;
  role: 'consumer' | 'provider' | 'admin';
  created_at: string;
}

export interface Wallet {
  id: string;
  balance_credits: number;
  locked_credits: number;
  available_credits: number;
  updated_at: string;
  recent_transactions: Transaction[];
}

export interface Transaction {
  id: string;
  type: string;
  amount: number;
  reference_id?: string;
  description?: string;
  created_at: string;
}

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  is_active: boolean;
  last_used_at?: string;
  created_at: string;
}

export interface ApiKeyCreatedResponse {
  id: string;
  name: string;
  key_prefix: string;
  raw_api_key: string;
  created_at: string;
}

export interface NodeModel {
  id: string;
  model_name: string;
  price_per_million_prompt: number;
  price_per_million_completion: number;
  is_active: boolean;
}

export interface GpuNode {
  id: string;
  name: string;
  gpu_name: string;
  vram_mb: number;
  status: 'online' | 'offline' | 'busy';
  tokens_per_sec_benchmark: number;
  node_token: string;
  last_heartbeat?: string;
  created_at: string;
  models: NodeModel[];
}

export interface MarketplaceModel {
  model_name: string;
  active_providers_count: number;
  min_prompt_price: number;
  min_completion_price: number;
  avg_tokens_per_sec: number;
}

export interface InferenceJob {
  id: string;
  model_name: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_cost: number;
  provider_cut: number;
  platform_cut: number;
  latency_ms: number;
  status: string;
  created_at: string;
}

export interface AdminStats {
  total_users: number;
  online_nodes: number;
  total_nodes: number;
  total_jobs: number;
  total_tokens_processed: number;
  platform_revenue_credits: number;
}
