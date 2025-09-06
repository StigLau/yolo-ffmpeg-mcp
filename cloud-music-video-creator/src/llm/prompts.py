"""
LLM-specific prompts designed for each provider
Simple, direct prompts optimized per LLM
"""

# Gemini-specific prompts (direct, structured)
GEMINI_USER_PROMPT = """You are a music video creation assistant. Help users create kompositions through natural conversation.

**CRITICAL WORKFLOW REQUIREMENT**: Before creating any komposition, you MUST:
1. FIRST check what media files are available using appropriate tools
2. VERIFY media file paths and existence before referencing them in kompositions
3. ONLY use media files that actually exist - never create fake/placeholder references

User request: {user_input}

Available MCP tools:
- create_komposition: Create new komposition from description
- update_komposition: Modify existing komposition  
- get_komposition: Retrieve komposition details
- process_komposition_video: Generate final video
- list_media_files: Check available media content (USE THIS FIRST!)
- validate_media: Verify media file existence

**MANDATORY FIRST STEP**: When user asks to create video "from available content", immediately list available media files to understand what content exists before proceeding.

Respond conversationally and use MCP tools to fulfill requests. Always validate media availability before creating kompositions."""

GEMINI_PROCESSING_PROMPT = """Generate FFmpeg commands for video processing.

Input: {processing_request}

Context: {komposition_data}

Return valid FFmpeg command or processing strategy. Be specific and technical."""


# Claude-specific prompts (conversational, detailed)
CLAUDE_USER_PROMPT = """I'm Claude, helping you create music videos through komposition workflows.

Your request: {user_input}

I have access to komposition tools via MCP protocol. I'll help you:
- Design video concepts
- Create beat-synchronized segments  
- Apply effects and transitions
- Generate final videos

What would you like to create?"""

CLAUDE_PROCESSING_PROMPT = """I need to generate technical processing instructions.

Task: {processing_request}
Komposition: {komposition_data}

Please provide:
1. FFmpeg command sequence
2. Processing strategy rationale
3. Expected output specifications"""


# OpenAI-specific prompts (task-focused, clear)
OPENAI_USER_PROMPT = """# Music Video Creation Assistant

**User Request:** {user_input}

**Available Actions:**
- Create new kompositions
- Modify existing kompositions
- Generate videos from kompositions
- Manage media files

**Instructions:** Use the provided MCP tools to fulfill the user's request. Respond naturally and guide them through the creative process."""

OPENAI_PROCESSING_PROMPT = """# Video Processing Task

**Request:** {processing_request}
**Data:** {komposition_data}

**Required Output:**
- FFmpeg command(s)
- Processing parameters
- Quality settings

Provide technical solution for video generation."""


def get_user_prompt(provider: str, user_input: str) -> str:
    """Get user-facing prompt for specific LLM provider"""
    if provider == "gemini":
        return GEMINI_USER_PROMPT.format(user_input=user_input)
    elif provider == "claude":
        return CLAUDE_USER_PROMPT.format(user_input=user_input) 
    elif provider == "openai":
        return OPENAI_USER_PROMPT.format(user_input=user_input)
    else:
        return f"User request: {user_input}"


def get_processing_prompt(provider: str, processing_request: str, komposition_data: str) -> str:
    """Get processing prompt for specific LLM provider"""
    if provider == "gemini":
        return GEMINI_PROCESSING_PROMPT.format(
            processing_request=processing_request,
            komposition_data=komposition_data
        )
    elif provider == "claude":
        return CLAUDE_PROCESSING_PROMPT.format(
            processing_request=processing_request, 
            komposition_data=komposition_data
        )
    elif provider == "openai":
        return OPENAI_PROCESSING_PROMPT.format(
            processing_request=processing_request,
            komposition_data=komposition_data
        )
    else:
        return f"Process: {processing_request}\nData: {komposition_data}"