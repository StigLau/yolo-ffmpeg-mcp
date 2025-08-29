/**
 * LLM client types and interfaces
 */

export interface LLMResponse {
  content: string;
  tokens_used: number;
  model: string;
  cost_estimate: number;
  success: boolean;
  error?: string;
}

export interface LLMRequest {
  prompt: string;
  context?: Record<string, unknown>;
  max_tokens?: number;
  temperature?: number;
}

export interface TokenUsage {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
}

export interface CostEstimate {
  input_cost: number;
  output_cost: number;
  total_cost: number;
}

export abstract class BaseLLMClient {
  abstract generate(request: LLMRequest): Promise<LLMResponse>;
  abstract estimateCost(tokens: number): number;
  abstract get provider(): string;
  abstract get model(): string;
}