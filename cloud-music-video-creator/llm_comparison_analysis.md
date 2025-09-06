# LLM FFmpeg Command Generation Comparison

**Source**: `vintage_dreamy_30s.md` specification  
**Task**: Generate FFmpeg commands for 30-second vintage → dreamy blur music video  
**Date**: Session analysis

## Sonnet vs FastTrack (Haiku) Analysis

### Command Approach Comparison

| Aspect | Sonnet 4 | FastTrack (Haiku) |
|--------|----------|-------------------|
| **Strategy** | Multi-step process (4 commands) | Single complex filter graph |
| **File handling** | Creates intermediate files | All-in-one processing |
| **Complexity** | Modular, easy to debug | More complex but efficient |
| **Processing time** | Longer (multiple passes) | Faster (single pass) |

### Effects Implementation Quality

#### Vintage Effects (Segment 1)

**Sonnet**:
```bash
colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131,hue=s=0.6,noise=alls=20:allf=t,vignette=PI/6
```

**FastTrack**:
```bash
colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131:0:0:0:0:1,curves=all='0/0.05 0.5/0.45 1/0.95',noise=alls=20:allf=t+u,vignette=angle=PI/4:mode=forward:eval=frame
```

**Analysis**: 
- ✅ Both use correct sepia colorchannelmixer values
- ✅ FastTrack adds sophisticated curves adjustment
- ✅ FastTrack has more advanced vignette configuration
- ✅ Sonnet simpler but effective approach

#### Dreamy Effects (Segment 2) 

**Sonnet**:
```bash
gblur=sigma=3:steps=1,eq=brightness=0.1:contrast=0.9,boxblur=luma_radius=1:luma_power=0.5,fade=t=out:st=13:d=2
```

**FastTrack**:
```bash
gblur=sigma=3:steps=1,eq=brightness=0.1:saturation=0.8,gblur=sigma=1.5:steps=1,fade=t=out:st=13:d=2:color=black
```

**Analysis**:
- ✅ Both use gblur with sigma=3
- ✅ Both apply brightness boost
- 🔄 Sonnet uses boxblur + contrast adjustment
- 🔄 FastTrack uses dual gblur + saturation adjustment
- ✅ FastTrack explicitly sets fade color to black

### Technical Implementation

#### Resolution & Format Handling

**Sonnet**:
```bash
-r 25 -s 1920x1080
```

**FastTrack**:
```bash
scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1:black,fps=25
```

**Analysis**:
- ❌ Sonnet: Basic approach, may not handle aspect ratio correctly
- ✅ FastTrack: Sophisticated scaling with aspect ratio preservation and padding

#### Audio Processing

**Sonnet**:
```bash
[1:a]volume=0.7,afade=t=in:st=0:d=1,afade=t=out:st=28.5:d=1.5[a]
```

**FastTrack**:
```bash
[1:a]volume=0.7,afade=t=in:st=0:d=1,afade=t=out:st=28.5:d=1.5[audio_out]
```

**Analysis**:
- ✅ Identical approach - both correctly calculated fade timing

## Strengths & Weaknesses

### Sonnet Strengths:
- 🎯 **Clear step-by-step process** - easy to understand and debug
- 🛠️ **Modular approach** - can test each segment individually
- 📚 **Detailed documentation** - explains each filter choice
- 🔧 **Alternative approaches** - provides both multi-step and single command

### Sonnet Weaknesses:
- ⏰ **Less efficient** - multiple FFmpeg invocations
- 💾 **More disk usage** - creates intermediate files
- 🔍 **Basic scaling** - doesn't handle aspect ratio edge cases

### FastTrack Strengths:
- ⚡ **High efficiency** - single pass processing
- 🎨 **Sophisticated effects** - advanced curves and vignette settings
- 📐 **Professional scaling** - proper aspect ratio handling
- 🔄 **Resource efficient** - no intermediate files

### FastTrack Weaknesses:
- 🧩 **Complex debugging** - harder to isolate issues in single command
- 📖 **Less explanation** - fewer details about filter choices

## Prompt Optimization Insights

### What Works Well for Both:
1. ✅ **Clear specification format** - MD structure is LLM-friendly
2. ✅ **Technical requirements** - specific resolution, timing, codec details
3. ✅ **Effect descriptions** - "vintage sepia", "dreamy blur" translate well
4. ✅ **Timing precision** - beat-based timing works for both LLMs

### Sonnet-Specific Optimizations:
- 📋 Ask for **multiple approaches** (step-by-step + single command)
- 🔍 Request **detailed explanations** of filter choices
- 🧪 Ask for **debugging-friendly** modular commands

### FastTrack-Specific Optimizations:
- ⚡ Emphasize **efficiency** and single-pass processing
- 🎨 Request **advanced filter techniques** 
- 📐 Specify **professional video handling** requirements

## Recommended Approach

**For Production**: Use **FastTrack's single command approach** for efficiency
**For Development**: Use **Sonnet's modular approach** for testing and iteration
**For Best Results**: Combine FastTrack's advanced effects with Sonnet's documentation clarity

## Command Quality Scores

| Criteria | Sonnet | FastTrack | Winner |
|----------|---------|-----------|--------|
| **Correctness** | 9/10 | 9/10 | Tie |
| **Efficiency** | 6/10 | 9/10 | FastTrack |
| **Sophistication** | 7/10 | 9/10 | FastTrack |
| **Debuggability** | 9/10 | 6/10 | Sonnet |
| **Documentation** | 10/10 | 7/10 | Sonnet |
| **Production Ready** | 8/10 | 9/10 | FastTrack |

**Overall**: Both LLMs successfully generated working FFmpeg commands from the MD specification, with complementary strengths for different use cases.