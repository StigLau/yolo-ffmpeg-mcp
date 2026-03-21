# Video Effects Implementation Plan
*Based on Gemini LLM Research Analysis*

## Overview

After reviewing the comprehensive Gemini research on video effects and transitions, this document provides a focused implementation plan that aligns with our current FFMPEG MCP architecture and user needs.

## Key Research Insights 

### What We Agree With
1. **Professional "Looks" are Recipes**: Complex chained effects, not single filters - aligns perfectly with our komposition system
2. **FFMPEG Foundation is Powerful**: 80%+ of desired effects achievable with pure FFMPEG 
3. **Preset-Driven API**: Abstract complexity behind simple high-level parameters
4. **Phased Implementation**: Start with pure FFMPEG, then add permissive libraries
5. **Licensing is Critical**: Avoid GPL (Frei0r), prefer Apache/LGPL (OpenCV, VapourSynth)

### What Needs Adaptation
1. **3-Phase Timeline**: Compress to 2 phases for faster delivery
2. **LUT Workflow**: Simplify haldclut implementation for our use case  
3. **GPU Requirements**: Defer complex 3D transitions, focus on CPU-efficient effects
4. **User Interface**: Research assumes GUI - we're LLM-first via MCP

## Recommended Implementation Plan

### Phase 1: Core Effects Foundation (Pure FFMPEG)
**Timeline**: 2-3 weeks  
**Risk**: Low  
**Dependencies**: None (existing FFMPEG)

#### 1.1 Color & Tone Operations
```python
# New MCP Tools to Implement
apply_color_grade(file_id: str, preset: str, intensity: float = 1.0)
apply_curves(file_id: str, preset: str, custom_points: str = None)
apply_lut(file_id: str, lut_name: str, intensity: float = 1.0)
```

**Presets to Include:**
- **Color Grade**: `vintage`, `bleach_bypass`, `film_noir`, `warm_seventies`, `cool_scifi`, `horror_desaturated`
- **Curves**: `s_curve_contrast`, `film_emulation`, `bright_highlights`, `crushed_blacks`
- **Built-in LUTs**: `kodak_5218`, `fuji_8551`, `arri_alexa_rec709`

**FFMPEG Implementation:**
```bash
# Vintage Look Chain
-vf "eq=saturation=0.85:contrast=1.1,curves=preset=vintage,colorbalance=shadows=0.2"

# Film Noir 
-vf "eq=saturation=0.1:contrast=2.0,curves=all='0/0 0.3/0.1 0.7/0.9 1/1'"
```

#### 1.2 Stylistic Effects
```python
# New MCP Tools
apply_stylistic_effect(file_id: str, effect: str, intensity: float = 1.0)
```

**Effects to Include:**
- **VHS Look**: `scale + eq + noise + gblur` chain
- **80s Neon Glow**: `split + rgbashift + gblur + blend` complex filter
- **Film Grain**: `geq + blend` with luma masking
- **Gaussian Blur**: Simple `gblur` with intensity mapping
- **Chromatic Aberration**: `rgbashift` for glitch transitions

#### 1.3 Enhanced Transitions
```python  
# Extend existing transition system
add_transition_effect(video1_id: str, video2_id: str, transition: str, duration: float, easing: str = "linear")
```

**New Transition Types:**
- **All xfade options**: `wipeleft`, `wiperight`, `wipeup`, `wipedown`, `diagtl`, `radial`, `horzopen`
- **Custom timing**: Support for offset and duration control
- **Blend modes**: `screen`, `multiply`, `overlay` for creative transitions

### Phase 2: Advanced Effects & Optimization (2-4 weeks)  
**Risk**: Medium  
**Dependencies**: Custom FFMPEG build consideration

#### 2.1 Preset Engine Architecture
```python
# Advanced preset system
class EffectPreset:
    name: str
    category: str  # "color", "stylistic", "blur", "distortion"
    filter_chain: List[FilterStep]
    parameters: Dict[str, ParameterDef]
    
load_effect_presets()  # Load from JSON configuration
get_available_presets(category: str = None) -> List[str]
```

#### 2.2 Effect Chaining & Recipes
```python
# Multi-effect application
batch_apply_effects(file_id: str, effects_chain: List[EffectStep]) -> str
create_effect_recipe(name: str, effects_chain: List[EffectStep]) -> str
apply_effect_recipe(file_id: str, recipe_name: str, intensity: float = 1.0) -> str
```

**Popular Recipes to Include:**
- **"Social Media Ready"**: brightness + saturation + slight blur + crop to 9:16
- **"Cinematic Grade"**: color balance + curves + film grain + vignette  
- **"Retro Vibe"**: VHS effect + warm color cast + slight distortion
- **"Professional Polish"**: color correction + subtle sharpen + noise reduction

#### 2.3 Content-Aware Effects (OpenCV Integration)
*If resources allow - can be Phase 3*
```python
# Intelligent effects based on content analysis  
apply_face_blur(file_id: str, blur_intensity: float = 0.5) -> str
apply_object_tracking_effect(file_id: str, object_type: str, effect: str) -> str
auto_color_correct(file_id: str, reference_skin_tone: bool = True) -> str
```

## Integration with Current Codebase

### 1. Extend FFMPEG Wrapper (`src/ffmpeg_wrapper.py`)
```python
# Add to FFMPEGWrapper class
def build_color_grade_command(self, preset: str, intensity: float) -> List[str]:
    """Build filter chain for color grading presets"""
    
def build_stylistic_effect_command(self, effect: str, intensity: float) -> List[str]:
    """Build complex filter chains for stylistic effects"""
    
def build_multi_effect_chain(self, effects: List[EffectStep]) -> str:
    """Build filter_complex for chained effects"""
```

### 2. New Effect Processor (`src/effect_processor.py`)
```python
class EffectProcessor:
    """Handles all video effects and presets"""
    
    def __init__(self, ffmpeg_wrapper: FFMPEGWrapper):
        self.ffmpeg = ffmpeg_wrapper
        self.presets = self.load_presets()
    
    async def apply_preset(self, file_id: str, preset_name: str, **params) -> str:
        """Apply predefined effect preset"""
        
    async def apply_effect_chain(self, file_id: str, chain: List[EffectStep]) -> str:
        """Apply multiple effects in sequence"""
```

### 3. Preset Configuration (`presets/effects.json`)
```json
{
  "color_grades": {
    "vintage": {
      "description": "Warm, nostalgic 70s film look",
      "filter_chain": "eq=saturation=0.85:contrast=1.1,curves=preset=vintage",
      "parameters": {
        "intensity": {"min": 0.0, "max": 2.0, "default": 1.0}
      }
    },
    "film_noir": {
      "filter_chain": "eq=saturation=0.1:contrast=2.0,curves=all='0/0 0.3/0.1 0.7/0.9 1/1'",
      "parameters": {
        "intensity": {"min": 0.0, "max": 1.5, "default": 1.0}
      }
    }
  },
  "stylistic_effects": {
    "vhs_look": {
      "filter_chain": "scale=640:480,setsar=1,eq=saturation=0.85:contrast=1.1,noise=alls=7,gblur=sigma=0.4",
      "performance": "medium"
    },
    "neon_glow": {
      "filter_complex": "[0:v]split=2[base][glow];[glow]rgbashift=rh=5:bh=-5,gblur=sigma=20[processed];[base][processed]blend=all_mode=screen",
      "performance": "slow"
    }
  }
}
```

### 4. New MCP Tools in `src/server.py`
```python
@mcp.tool()
async def apply_color_grade(file_id: str, preset: str, intensity: float = 1.0) -> Dict[str, Any]:
    """Apply professional color grading preset"""

@mcp.tool() 
async def apply_stylistic_effect(file_id: str, effect: str, intensity: float = 1.0) -> Dict[str, Any]:
    """Apply stylistic visual effect"""

@mcp.tool()
async def batch_apply_effects(file_id: str, effects_chain: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Apply multiple effects in sequence"""

@mcp.tool()
async def get_available_effects(category: str = None) -> Dict[str, Any]:
    """List available effects and presets"""
```

## File Structure Changes

```
src/
├── effect_processor.py          # NEW: Core effects engine
├── preset_manager.py           # NEW: Preset loading and management  
├── ffmpeg_wrapper.py           # EXTEND: Add effect commands
└── server.py                   # EXTEND: Add effect MCP tools

presets/
├── effects.json                # NEW: Effect definitions
├── luts/                       # NEW: LUT files
│   ├── kodak_5218.png
│   ├── fuji_8551.png
│   └── arri_alexa_rec709.png
└── recipes/                    # NEW: Multi-effect recipes
    ├── social_media.json
    ├── cinematic.json
    └── retro.json

tests/
├── test_effect_processor.py    # NEW: Effect testing
└── test_presets.py            # NEW: Preset validation
```

## Implementation Priorities

### High Priority (Phase 1)
1. **Color grading suite** - Professional baseline requirement
2. **Basic stylistic effects** - VHS, film grain, blur - high user demand  
3. **Enhanced transitions** - Expand beyond basic dissolve/fade
4. **Preset system foundation** - Architecture for future expansion

### Medium Priority (Phase 2)  
1. **Effect chaining** - Professional workflow support
2. **Recipe system** - Popular effect combinations
3. **Performance optimization** - GPU acceleration consideration
4. **LUT integration** - Professional color workflow

### Lower Priority (Future)
1. **OpenCV integration** - Content-aware effects  
2. **3D transitions** - GPU-based complex transitions
3. **Custom FFMPEG build** - Eased transitions
4. **Real-time preview** - Effect parameter tuning

## Risk Assessment

### Low Risk ✅
- Pure FFMPEG implementations
- Preset system architecture  
- Effect chaining logic
- JSON-based configuration

### Medium Risk ⚠️  
- Complex filter_complex chains
- Performance with multiple effects
- Custom FFMPEG build decision
- OpenCV integration complexity

### High Risk ❌
- GPU-based 3D transitions
- GPL-licensed libraries (Frei0r)
- Real-time processing requirements
- Custom shader development

## Success Metrics

1. **20+ professional effects** available through MCP
2. **Sub-30 second processing** for standard effects on 1080p/30s video
3. **Zero licensing issues** - only permissive licenses
4. **Seamless LLM integration** - natural language effect application
5. **Professional output quality** - broadcast-ready results

This implementation plan provides a clear path to dramatically expand our video effects capabilities while maintaining our core strengths in intelligent, LLM-driven video processing.