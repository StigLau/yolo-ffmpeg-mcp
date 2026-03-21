/**
 * Anthropic Claude Haiku client implementation
 */

import Anthropic from '@anthropic-ai/sdk';
import { BaseLLMClient, LLMRequest, LLMResponse } from './types.js';
import type { ModelConfig } from '../config.js';

export class HaikuClient extends BaseLLMClient {
  private client: Anthropic;
  private config: ModelConfig;
  
  // Pricing: $0.25 per 1M input tokens, $1.25 per 1M output tokens
  private static readonly INPUT_COST_PER_TOKEN = 0.00000025;
  private static readonly OUTPUT_COST_PER_TOKEN = 0.00000125;
  
  constructor(config: ModelConfig) {
    super();
    this.config = config;
    this.client = new Anthropic({
      apiKey: config.api_key,
    });
  }
  
  get provider(): string {
    return 'anthropic';
  }
  
  get model(): string {
    return this.config.model;
  }
  
  async generate(request: LLMRequest): Promise<LLMResponse> {
    try {
      // Build enhanced system prompt for professional FFMPEG operations
      let systemPrompt = `You are a professional video processing specialist with deep FFMPEG expertise.

MUSIC VIDEO WORKFLOW CONTEXT:
- Primary use case: Create music videos by combining video sources with separate audio tracks
- Incoming video audio is generally ignored/dropped during processing
- Final audio comes from external sources (MP3/WAV files)
- Focus on video processing: visual effects, timing, transitions

REQUIREMENTS:
1. Generate specific FFMPEG commands with exact parameters
2. Use -an flag to drop audio when processing video-only operations
3. Add smooth video transitions and effects (fade, crossfade)
4. Optimize for video processing performance (skip audio filters when not needed)
5. Read and interpret FFMPEG logs for troubleshooting
6. Provide fallback strategies for common issues

RESPONSE FORMAT:
1. **Analysis**: Source file specifications
2. **Commands**: Exact FFMPEG syntax with parameters
3. **Validation**: Quality check procedures
4. **Troubleshooting**: Log analysis and error handling

TECHNICAL STANDARDS:
- Use specific filter syntax: -filter_complex "[0:v]fade=..."
- Include codec parameters: -c:v libx264 -preset medium
- Drop audio when not needed: -an
- Specify video transitions: fade, crossfade effects
- Focus on video quality and processing speed

Generate responses under ${this.config.max_tokens} tokens but prioritize technical completeness.`;
      
      if (request.context) {
        systemPrompt += `\n\nContext: ${JSON.stringify(request.context, null, 2)}`;
      }
      
      const message = await this.client.messages.create({
        model: this.config.model,
        max_tokens: request.max_tokens || this.config.max_tokens,
        system: systemPrompt,
        messages: [
          {
            role: 'user',
            content: request.prompt,
          },
        ],
      });
      
      const content = message.content[0];
      if (content.type !== 'text') {
        throw new Error('Expected text response from Claude');
      }
      
      const inputTokens = message.usage.input_tokens;
      const outputTokens = message.usage.output_tokens;
      const totalTokens = inputTokens + outputTokens;
      
      const cost = 
        inputTokens * HaikuClient.INPUT_COST_PER_TOKEN +
        outputTokens * HaikuClient.OUTPUT_COST_PER_TOKEN;
      
      return {
        content: content.text,
        tokens_used: totalTokens,
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
      inputTokens * HaikuClient.INPUT_COST_PER_TOKEN +
      outputTokens * HaikuClient.OUTPUT_COST_PER_TOKEN
    );
  }
}