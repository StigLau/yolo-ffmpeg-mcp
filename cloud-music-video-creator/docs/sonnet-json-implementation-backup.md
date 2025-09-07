# Sonnet JSON Implementation Backup

**Date**: 2025-09-07  
**Context**: Sonnet was creating JSON kompositions instead of markdown format. This document preserves the JSON-based approach for potential future use.

## Current Sonnet Behavior (JSON-based)

Sonnet is currently returning responses in JSON format like:

```json
{
  "response_type": "initial_greeting",
  "message": "Hello! I see we have some media content available to work with:\n\n1. Audio: 'Subnautic Measures.flac' (27.1MB)\n2. Video: 'JJVtt947FfI_136.mp4' (16.4MB)\n\nWould you like to create a music video using these files?",
  "komposition": {
    "name": "New Music Video Komposition",
    "parameters": {
      "duration": 30,
      "bpm": 120,
      "resolution": "1920x1080",
      "style": "Ready for customization"
    },
    "segments": [
      {
        "id": 1,
        "name": "Opening",
        "duration": 10,
        "source": null,
        "effects": null,
        "transition": null
      },
      {
        "id": 2,
        "name": "Middle", 
        "duration": 10,
        "source": null,
        "effects": null,
        "transition": null
      },
      {
        "id": 3,
        "name": "Finale",
        "duration": 10,
        "source": null,
        "effects": null,
        "transition": null
      }
    ],
    "technical_specifications": {
      "format": "MP4",
      "codec": "H.264/AAC", 
      "quality": "CRF 23"
    }
  }
}
```

## Current Response Parsing Logic

The system has enhanced parsing in `src/llm_service.py` that handles multiple JSON formats:

```python
# Handle different response formats
response_text = ""
komposition = parsed.get("komposition")

# Try different field names for response text
if "response" in parsed:
    response_text = parsed["response"]
elif "message" in parsed:
    response_text = parsed["message"]
elif "conversation" in parsed and parsed["conversation"]:
    # Handle Gemini conversation format
    for msg in parsed["conversation"]:
        if msg.get("speaker") == "assistant":
            response_text = msg.get("message", "")
            break
elif "messages" in parsed and parsed["messages"]:
    # Handle Gemini messages format
    for msg in parsed["messages"]:
        if msg.get("role") == "assistant":
            response_text = msg.get("content", "")
            break

# If still no response text found and there's text before JSON, use that
if not response_text and json_start > 0:
    text_before_json = llm_response[:json_start].strip()
    # Remove markdown code block indicators
    text_before_json = text_before_json.replace("```json", "").replace("```", "").strip()
    if text_before_json:
        response_text = text_before_json
        logger.info(f"Using text before JSON as response: {len(response_text)} chars")
```

## Issues with JSON Approach

1. **Validation Failure**: The validation system expects markdown format with patterns like:
   ```markdown
   ### Segment 1: Opening (0-10s)
   - **Source**: media_001 (JJVtt947FfI_136.mp4)
   ```

2. **Processing Pipeline**: The Haiku MCP processor expects markdown kompositions, not JSON structures

3. **File References**: JSON structure uses `"source": null` instead of specific file references that validation can check

## Transition Plan

**Next Steps**: 
1. Update Sonnet prompts to generate markdown instead of JSON
2. Keep JSON parsing as fallback for other providers
3. Ensure markdown format includes actual file references like `media_001 (JJVtt947FfI_136.mp4)`

## Files Modified for JSON Support

- `src/llm_service.py`: Enhanced response parsing
- `src/llm/prompts.py`: Sonnet prompts (to be updated for markdown)
- `web/chat.html`: UI expects both response text and komposition fields

This backup preserves the JSON implementation work in case we need to revert or support both formats in the future.