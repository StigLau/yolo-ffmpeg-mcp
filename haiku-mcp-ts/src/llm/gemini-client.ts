/**
 * Google Gemini Flash client implementation
 */

import { GoogleGenerativeAI } from '@google/generative-ai';
import { BaseLLMClient, LLMRequest, LLMResponse } from './types.js';
import type { ModelConfig } from '../config.js';

export class GeminiFlashClient extends BaseLLMClient {
  private genAI: GoogleGenerativeAI;
  private config: ModelConfig;
  
  // Pricing: $0.075 per 1M input tokens, $0.30 per 1M output tokens
  private static readonly INPUT_COST_PER_TOKEN = 0.000000075;
  private static readonly OUTPUT_COST_PER_TOKEN = 0.0000003;
  
  constructor(config: ModelConfig) {
    super();
    this.config = config;
    this.genAI = new GoogleGenerativeAI(config.api_key);
  }
  
  get provider(): string {
    return 'google';
  }
  
  get model(): string {
    return this.config.model;
  }
  
  async generate(request: LLMRequest): Promise<LLMResponse> {
    try {
      const model = this.genAI.getGenerativeModel({ 
        model: this.config.model,
        generationConfig: {
          maxOutputTokens: request.max_tokens || this.config.max_tokens,
          temperature: request.temperature || 0.1,
        },
      });
      
      // Build prompt with context
      let fullPrompt = `You are a technical assistant specialized in FFMPEG operations.
Generate concise, accurate responses focused on video processing tasks.
Keep responses under ${this.config.max_tokens} tokens. Focus on actionable technical details.

${request.prompt}`;
      
      if (request.context) {
        fullPrompt += `\n\nContext: ${JSON.stringify(request.context, null, 2)}`;
      }
      
      const result = await model.generateContent(fullPrompt);
      const response = await result.response;
      const content = response.text();
      
      // Estimate token usage (Gemini doesn't provide exact counts)
      const estimatedTokens = this.estimateTokens(content);
      const cost = this.estimateCost(estimatedTokens);
      
      return {
        content,
        tokens_used: estimatedTokens,
        model: this.config.model,
        cost_estimate: cost,
        success: true,
      };
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      
      return {
        content: '',
        tokens_used: 0,
        model: this.config.model,
        cost_estimate: 0,
        success: false,
        error: errorMessage,
      };
    }
  }
  
  estimateCost(tokens: number): number {
    // Rough estimate assuming 70% input, 30% output
    const inputTokens = Math.floor(tokens * 0.7);
    const outputTokens = Math.floor(tokens * 0.3);
    
    return (
      inputTokens * GeminiFlashClient.INPUT_COST_PER_TOKEN +
      outputTokens * GeminiFlashClient.OUTPUT_COST_PER_TOKEN
    );
  }
  
  private estimateTokens(text: string): number {
    // Rough estimation: ~1.3 tokens per word
    const words = text.split(/\s+/).length;
    return Math.ceil(words * 1.3);
  }
}