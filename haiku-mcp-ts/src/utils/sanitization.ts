/**
 * Response sanitization utilities for token optimization
 */

export interface SanitizedResponse {
  sanitized_content: string;
  original_tokens: number;
  sanitized_tokens: number;
  reduction_percentage: number;
  metadata_removed: boolean;
}

export interface SanitizationConfig {
  strip_metadata: boolean;
  max_output_tokens: number;
  preserve_essential_fields: string[];
  aggressive_pruning: boolean;
}

/**
 * Estimate token count for text (rough approximation)
 */
export function estimateTokens(text: string): number {
  return Math.ceil(text.split(/\s+/).length * 1.3);
}

/**
 * Sanitize FFMPEG command outputs
 */
export function sanitizeFFMPEGOutput(output: string, config: SanitizationConfig): SanitizedResponse {
  const originalTokens = estimateTokens(output);
  
  if (!config.strip_metadata) {
    return {
      sanitized_content: output,
      original_tokens: originalTokens,
      sanitized_tokens: originalTokens,
      reduction_percentage: 0,
      metadata_removed: false,
    };
  }

  let sanitized = output;

  // Remove verbose FFMPEG metadata
  sanitized = sanitized.replace(/^ffmpeg version.*?\n/gm, '');
  sanitized = sanitized.replace(/^built with.*?\n/gm, '');
  sanitized = sanitized.replace(/^configuration:.*?\n/gm, '');
  sanitized = sanitized.replace(/^lib[a-z]+\s+\d+\.\s*\d+.*?\n/gm, '');
  
  // Remove stream mapping details
  sanitized = sanitized.replace(/^\s*Stream mapping:.*?\n/gm, '');
  sanitized = sanitized.replace(/^\s*Stream #\d+:\d+.*?\n/gm, '');
  
  // Keep only essential progress/error info
  const lines = sanitized.split('\n');
  const essential = lines.filter(line => {
    return (
      line.includes('error') ||
      line.includes('Error') ||
      line.includes('WARNING') ||
      line.includes('size=') ||
      line.includes('time=') ||
      line.includes('fps=') ||
      line.trim().length < 50
    );
  });
  
  sanitized = essential.join('\n');
  
  const sanitizedTokens = estimateTokens(sanitized);
  const reduction = ((originalTokens - sanitizedTokens) / originalTokens) * 100;

  return {
    sanitized_content: sanitized,
    original_tokens: originalTokens,
    sanitized_tokens: sanitizedTokens,
    reduction_percentage: Math.round(reduction * 100) / 100,
    metadata_removed: true,
  };
}

/**
 * Sanitize YouTube download outputs
 */
export function sanitizeYouTubeOutput(output: string, config: SanitizationConfig): SanitizedResponse {
  const originalTokens = estimateTokens(output);
  
  if (!config.strip_metadata) {
    return {
      sanitized_content: output,
      original_tokens: originalTokens,
      sanitized_tokens: originalTokens,
      reduction_percentage: 0,
      metadata_removed: false,
    };
  }

  let sanitized = output;

  // Remove verbose format listings
  sanitized = sanitized.replace(/^format code\s+extension\s+resolution.*?\n/gm, '');
  sanitized = sanitized.replace(/^\d+\s+[a-z0-9]+\s+\d+x\d+.*?\n/gm, '');
  
  // Remove detailed download progress
  sanitized = sanitized.replace(/^\[download\]\s+\d+\.\d+%.*?\n/gm, '');
  sanitized = sanitized.replace(/^\[download\]\s+Downloaded.*?\n/gm, '');
  
  // Keep only essential info
  const lines = sanitized.split('\n');
  const essential = lines.filter(line => {
    const trimmed = line.trim();
    return (
      trimmed.includes('Downloading') ||
      trimmed.includes('ERROR') ||
      trimmed.includes('error') ||
      trimmed.includes('WARNING') ||
      trimmed.includes('has already been downloaded') ||
      trimmed.includes('Destination:') ||
      trimmed.length < 100
    );
  });
  
  sanitized = essential.slice(0, 10).join('\n'); // Max 10 essential lines
  
  const sanitizedTokens = estimateTokens(sanitized);
  const reduction = ((originalTokens - sanitizedTokens) / originalTokens) * 100;

  return {
    sanitized_content: sanitized,
    original_tokens: originalTokens,
    sanitized_tokens: sanitizedTokens,
    reduction_percentage: Math.round(reduction * 100) / 100,
    metadata_removed: true,
  };
}

/**
 * Sanitize JSON metadata responses
 */
export function sanitizeJSONMetadata(jsonStr: string, config: SanitizationConfig): SanitizedResponse {
  const originalTokens = estimateTokens(jsonStr);
  
  if (!config.strip_metadata) {
    return {
      sanitized_content: jsonStr,
      original_tokens: originalTokens,
      sanitized_tokens: originalTokens,
      reduction_percentage: 0,
      metadata_removed: false,
    };
  }

  try {
    const obj = JSON.parse(jsonStr);
    
    // Keep only essential fields
    const essential: Record<string, any> = {};
    
    for (const field of config.preserve_essential_fields) {
      if (obj[field] !== undefined) {
        essential[field] = obj[field];
      }
    }
    
    // Always preserve error information
    if (obj.error) essential.error = obj.error;
    if (obj.success !== undefined) essential.success = obj.success;
    if (obj.status) essential.status = obj.status;
    
    const sanitized = JSON.stringify(essential, null, config.aggressive_pruning ? 0 : 2);
    const sanitizedTokens = estimateTokens(sanitized);
    const reduction = ((originalTokens - sanitizedTokens) / originalTokens) * 100;

    return {
      sanitized_content: sanitized,
      original_tokens: originalTokens,
      sanitized_tokens: sanitizedTokens,
      reduction_percentage: Math.round(reduction * 100) / 100,
      metadata_removed: true,
    };
  } catch {
    // Not valid JSON, return original
    return {
      sanitized_content: jsonStr,
      original_tokens: originalTokens,
      sanitized_tokens: originalTokens,
      reduction_percentage: 0,
      metadata_removed: false,
    };
  }
}

/**
 * Generic response sanitizer with operation type detection
 */
export function sanitizeResponse(
  content: string, 
  operation: string, 
  config: SanitizationConfig
): SanitizedResponse {
  
  if (operation.includes('youtube') || operation.includes('download')) {
    return sanitizeYouTubeOutput(content, config);
  }
  
  if (operation.includes('ffmpeg') || operation.includes('video') || operation.includes('audio')) {
    return sanitizeFFMPEGOutput(content, config);
  }
  
  if (content.trim().startsWith('{') && content.trim().endsWith('}')) {
    return sanitizeJSONMetadata(content, config);
  }
  
  // Default: basic token limiting
  const originalTokens = estimateTokens(content);
  
  if (originalTokens <= config.max_output_tokens) {
    return {
      sanitized_content: content,
      original_tokens: originalTokens,
      sanitized_tokens: originalTokens,
      reduction_percentage: 0,
      metadata_removed: false,
    };
  }
  
  // Truncate to token limit
  const words = content.split(/\s+/);
  const targetWords = Math.floor(config.max_output_tokens / 1.3);
  const truncated = words.slice(0, targetWords).join(' ') + '...[truncated]';
  
  const sanitizedTokens = estimateTokens(truncated);
  const reduction = ((originalTokens - sanitizedTokens) / originalTokens) * 100;

  return {
    sanitized_content: truncated,
    original_tokens: originalTokens,
    sanitized_tokens: sanitizedTokens,
    reduction_percentage: Math.round(reduction * 100) / 100,
    metadata_removed: true,
  };
}