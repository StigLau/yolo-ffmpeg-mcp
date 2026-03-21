# Haiku LLM Integration Architecture
**Native CLI Tools for Cost-Effective Video Processing**

## 🎯 **Executive Summary**

This document outlines the architecture for integrating Claude 3 Haiku LLM as specialized CLI tools to reduce video processing costs by **99.7%** while maintaining quality through intelligent Sonnet supervision.

**Key Benefits:**
- **Cost Reduction**: $125 → $0.19 per complex video workflow 
- **Speed Increase**: 2-3x faster for structured tasks
- **Quality Assurance**: Sonnet validation for creative decisions
- **Native CLI**: Simple deployment, no container complexity
- **Java Integration**: Seamless enterprise integration

## 📊 **Cost Analysis & Budget Recommendations**

### **Current Cost Structure**
Based on existing video processing workflows:
- Complex music video creation: **$125** (Sonnet-only)
- Simple JSON generation: **$3-5** (Sonnet-only) 
- Timing calculations: **$1-2** (Sonnet-only)
- Effect parameters: **$2-4** (Sonnet-only)

### **Haiku Cost Structure** 
- JSON generation: **$0.03** (12x cheaper than Sonnet)
- Timing calculations: **$0.01** (100x cheaper)
- Effect parameters: **$0.02** (100x cheaper)
- Video QC analysis: **$0.05** (25x cheaper)

### **Recommended Starting Budget**
**$5/day** - Conservative starting point to identify bottlenecks:
- **200 JSON generations** @ $0.03 = $6/day theoretical max
- **500 timing calculations** @ $0.01 = $5/day theoretical max
- Realistic mixed usage: ~$2-3/day actual consumption
- Leaves room for experimentation and Sonnet validation

**Budget Escalation Plan:**
- Week 1-2: $5/day (find issues, optimize prompts)
- Week 3-4: $10/day (scale successful patterns)
- Month 2+: $20-50/day (production workloads)

## 🏗️ **Native CLI Architecture**

### **Tool Suite Structure**
```
haiku-video-tools/
├── bin/
│   ├── haiku-komposition          # JSON generation from natural language
│   ├── haiku-timing               # BPM/beat calculations
│   ├── haiku-effects              # Effect parameter selection  
│   ├── haiku-files                # File path resolution
│   ├── haiku-qc                   # Video quality control
│   └── haiku-monitor              # Progress monitoring
├── lib/
│   ├── haiku-core.jar             # Java integration bridge
│   ├── prompts/                   # Optimized prompt templates
│   └── schemas/                   # JSON validation schemas
├── config/
│   ├── cost-limits.yml            # Budget controls
│   ├── quality-thresholds.yml     # Confidence scoring
│   └── timeout-settings.yml       # Based on existing timeout work
└── tests/
    ├── integration/               # End-to-end workflow tests
    └── validation/                # Quality validation tests
```

### **Command Examples**
```bash
# JSON komposition generation
./haiku-komposition \
  --input "12 segments, 4 beats each, 120 BPM, old school vibe, fade to white" \
  --template music_video \
  --bpm 120 \
  --output komposition.json \
  --confidence-threshold 0.8

# Beat timing calculations  
./haiku-timing \
  --duration 24 \
  --bpm 120 \
  --segments 12 \
  --beats-per-segment 4 \
  --output timing.json

# Effect parameters
./haiku-effects \
  --style "old school vibe" \
  --transitions "fade to white" \
  --intensity 0.8 \
  --output effects.json

# Video QC analysis
./haiku-qc \
  --input video.mp4 \
  --check-formats \
  --check-audio-sync \
  --check-resolution \
  --timeout 30s
```

## 🤖 **Haiku LLM Excellence Areas - Deep Analysis**

### **1. JSON Structure Generation** 💎 **PRIME CANDIDATE**

**Why Haiku Excels:**
- **Pattern Recognition**: Excellent at mapping natural language to structured schemas
- **Consistency**: Highly reliable for repetitive JSON generation tasks  
- **Speed**: 2-3x faster than Sonnet for structured data
- **Cost**: 12x cheaper than Sonnet ($0.00025 vs $0.003 per 1K tokens)

**Implementation Pattern:**
```bash
# Input: "Create music video with 12 segments, each 4 beats at 120 BPM, old school vibe"
# Output: Complete komposition.json with proper timing, effects, segments

./haiku-komposition \
  --input "YouTube shorts: Xjz9swW9Pg0, tNCPEtMqGcM, FrmUdNupdq4. Set 21 Rec 2.wav background music at 120 BPM. 12 segments × 4 beats. Old school vibe, fade to white transitions." \
  --output generated_komposition.json \
  --confidence-threshold 0.8

# Auto-generated output includes:
# - Proper BPM timing calculations
# - Segment structure with beat alignment
# - Effect parameters for "old school vibe"
# - Transition specifications
# - Audio integration settings
```

**Quality Assurance Integration:**
- Haiku confidence score < 0.8 → Escalate to Sonnet validation
- JSON schema validation (immediate)
- Technical feasibility check (Build Detective integration)
- Pattern learning from successful generations

### **2. Beat Timing Calculations** 🎵 **MATHEMATICAL EXCELLENCE**

**Current Problem from Documentation:**
Your `analyze_critical_findings.py` shows **critical timing issues**:
- MCP uniform division: `[0.0, 15.0, 30.0, 45.0]` (mathematical)
- Keyframe-aware timing: `[0.0, 5.29, 10.63, 15.96]` (content-aware)
- **29+ second differences** causing "completely different video content"

**Haiku Solution:**
```bash
# Beat-precise calculations
./haiku-timing \
  --total-duration 24s \
  --bpm 120 \
  --segments 12 \
  --beats-per-segment 4 \
  --alignment content-aware \
  --keyframe-analysis true

# Output: 
{
  "beat_boundaries": [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0],
  "timing_strategy": "beat_synchronized",
  "confidence": 0.95,
  "bpm_validation": "120 BPM confirmed",
  "total_beats": 48,
  "segment_timing": "mathematically_precise"
}
```

**Integration with Existing Timing Work:**
- Uses your existing `timeout_manager.py` patterns for reliability
- Integrates with `ProcessingTimeEstimator` for operation timeouts
- Leverages `TimingCalculator` from Komposteur for validation

### **3. Effect Parameter Selection** 🎨 **PATTERN MATCHING**

**Natural Language → Specific Parameters:**
```bash
./haiku-effects \
  --description "old school vibe with vintage look and fade to white between segments" \
  --output effects.json

# Generated output:
{
  "vintage_color_grading": {
    "warmth": 1.3,
    "saturation": 0.75,
    "grain_intensity": 0.4,
    "vignette": 0.2
  },
  "fade_transitions": {
    "type": "fade_to_color", 
    "color": "#FFFFFF",
    "duration": 0.5,
    "curve": "ease-in-out"
  },
  "old_school_effects": {
    "film_grain": true,
    "color_temperature": "warm",
    "contrast_boost": 0.3
  },
  "confidence": 0.87,
  "processing_cost": "$0.02"
}
```

### **4. File Path Resolution** 📁 **PERFECT MATCH**

**Fuzzy Matching Excellence:**
```bash
./haiku-files \
  --user-reference "Set 21 Rec 2.wav" \
  --available-files "$(cat available_files.json)" \
  --output file_mapping.json

# Output:
{
  "matched_file": {
    "user_input": "Set 21 Rec 2.wav",
    "resolved_id": "file_f2be678e", 
    "resolved_name": "Set 21 Rec 2.wav",
    "confidence": 0.99,
    "match_type": "exact_name"
  }
}
```

### **5. Video Quality Control** 📊 **NEW CAPABILITY**

**Based on Your Existing Video QC Work:**
From `MCP_KOMPOST_VIDEO_EVALUATION.md` and `KompostOutputValidator.java`, we have excellent QC foundation:

```bash
./haiku-qc \
  --input video.mp4 \
  --check-all \
  --timeout 30s

# QC Analysis Output:
{
  "format_analysis": {
    "codec": "h264",
    "profile": "High",  
    "pixel_format": "yuv420p",
    "compatibility": "universal",
    "assessment": "✅ macOS/Windows/browser compatible"
  },
  "audio_analysis": {
    "codec": "aac",
    "sample_rate": "48000",
    "channels": "stereo", 
    "sync_status": "✅ perfectly_synchronized",
    "duration_match": "✅ matches_video_duration"
  },
  "timing_analysis": {
    "beat_alignment": "✅ 120_BPM_synchronized",
    "segment_boundaries": "✅ precise_beat_boundaries", 
    "transition_timing": "✅ smooth_crossfades"
  },
  "quality_score": 0.94,
  "issues_found": [],
  "recommendations": [
    "Ready for production use",
    "Optimal for streaming platforms"
  ]
}
```

## 🔧 **Java Integration Bridge**

### **Service Layer Architecture**
```java
@Service
public class HaikuOrchestrationService {
    
    @Value("${haiku.daily.budget:5.00}")
    private double dailyBudget;
    
    @Value("${haiku.confidence.threshold:0.8}")  
    private double confidenceThreshold;
    
    @Autowired
    private HaikuCommandExecutor executor;
    
    @Autowired
    private SonnetValidationService sonnetValidator;
    
    public KompositionResult generateKomposition(String naturalLanguage, int bpm) {
        // 1. Check budget
        if (!budgetService.canAffordOperation("komposition", 0.03)) {
            throw new BudgetExceededException("Daily Haiku budget exceeded");
        }
        
        // 2. Execute Haiku
        CommandResult haikuResult = executor.executeCommand(
            "haiku-komposition",
            "--input", naturalLanguage,
            "--bpm", String.valueOf(bpm),
            "--confidence-threshold", String.valueOf(confidenceThreshold)
        );
        
        // 3. Quality assessment
        if (haikuResult.getConfidence() < confidenceThreshold) {
            logger.info("Haiku confidence {} below threshold, escalating to Sonnet", 
                       haikuResult.getConfidence());
            return sonnetValidator.enhanceKomposition(haikuResult, naturalLanguage);
        }
        
        // 4. Track costs and patterns
        usageTracker.recordSuccessfulGeneration(haikuResult);
        
        return haikuResult.toKompositionResult();
    }
}
```

### **Command Executor Implementation**
```java
@Component  
public class HaikuCommandExecutor {
    
    @Value("${haiku.tools.path:/opt/haiku-video-tools/bin}")
    private String toolsPath;
    
    public CommandResult executeCommand(String tool, String... args) {
        try {
            ProcessBuilder pb = new ProcessBuilder();
            List<String> command = new ArrayList<>();
            command.add(Paths.get(toolsPath, tool).toString());
            command.addAll(Arrays.asList(args));
            
            pb.command(command);
            pb.directory(new File(System.getProperty("user.dir")));
            
            Process process = pb.start();
            
            // Use existing timeout patterns from timeout_manager.py concepts
            boolean finished = process.waitFor(30, TimeUnit.SECONDS);
            if (!finished) {
                process.destroyForcibly();
                throw new HaikuTimeoutException("Command timed out after 30s");
            }
            
            String output = IOUtils.toString(process.getInputStream(), StandardCharsets.UTF_8);
            String error = IOUtils.toString(process.getErrorStream(), StandardCharsets.UTF_8);
            
            if (process.exitValue() != 0) {
                throw new HaikuExecutionException("Command failed: " + error);
            }
            
            return CommandResult.fromJson(output);
            
        } catch (Exception e) {
            throw new HaikuExecutionException("Failed to execute " + tool, e);
        }
    }
}
```

## 🧠 **Sonnet Supervision & Quality Framework**

### **Confidence-Based Escalation**
```java
public class QualityAssessmentFramework {
    
    public QualityReport assessHaikuOutput(HaikuResult result, String context) {
        List<QualityCheck> checks = Arrays.asList(
            // JSON Structure validation
            () -> validateJsonSchema(result.getJson()),
            
            // Technical feasibility (reuse Build Detective patterns)
            () -> validateTechnicalFeasibility(result),
            
            // Creative interpretation accuracy
            () -> assessCreativeInterpretation(result, context),
            
            // Timing/BPM calculation accuracy  
            () -> validateTimingCalculations(result),
            
            // File reference resolution accuracy
            () -> validateFileReferences(result)
        );
        
        QualityReport report = new QualityReport();
        for (QualityCheck check : checks) {
            CheckResult checkResult = check.execute();
            report.addCheck(checkResult);
        }
        
        // Calculate overall confidence
        double confidence = report.calculateOverallConfidence();
        
        if (confidence < 0.8) {
            // Escalate to Sonnet for validation/enhancement
            SonnetEnhancementResult enhancement = sonnetService.enhanceResult(result, context);
            report.setEscalated(true);
            report.setEnhancement(enhancement);
        }
        
        // Learn from successful patterns
        if (confidence > 0.9) {
            promptPatternService.reinforceSuccessfulPattern(result, context);
        }
        
        return report;
    }
}
```

### **Prompt Optimization Learning**
```java
@Service
public class HaikuPromptOptimizationService {
    
    public void learnFromSuccessfulPattern(HaikuResult result, String originalInput) {
        if (result.getConfidence() > 0.9) {
            PromptPattern successPattern = PromptPattern.builder()
                .inputKeywords(extractKeywords(originalInput))
                .outputStructure(analyzeOutputStructure(result))
                .confidence(result.getConfidence())
                .processingTime(result.getProcessingTime())
                .cost(result.getCost())
                .build();
                
            promptPatternRepository.save(successPattern);
            
            // Update prompt templates for similar future requests
            promptTemplateService.updateTemplate(
                result.getOperationType(), 
                successPattern
            );
        }
    }
    
    public void identifyImprovementArea(HaikuResult result, String originalInput) {
        if (result.getConfidence() < 0.6) {
            ImprovementArea area = ImprovementArea.builder()
                .inputPattern(originalInput)
                .failureType(result.getFailureType())
                .confidence(result.getConfidence())
                .errorMessages(result.getErrors())
                .build();
                
            improvementAreaRepository.save(area);
            
            // Flag for prompt engineering review
            notificationService.notifyPromptEngineers(area);
        }
    }
}
```

## ⏰ **Timeout Integration - Building on Existing Work**

**Based on Your `TIMEOUT_IMPLEMENTATION_SUMMARY.md`:**

### **Haiku-Specific Timeout Strategy**
```bash
# Haiku operations are much faster, different timeout strategy needed
./haiku-komposition \
  --input "complex music video description" \
  --timeout 10s \  # Much shorter than video processing (was 60s-30min)
  --fallback-to-sonnet \  # Auto-escalate on timeout
  --cleanup-on-failure

# Timeout calculation for Haiku vs. your existing video processing:
# - JSON generation: 2-5s (vs 30s+ for video processing)
# - Timing calculations: 1-2s (vs minutes for complex operations) 
# - Effect parameters: 3-5s (vs processing time)
# - QC analysis: 5-30s (depends on video size)
```

### **Integration with Existing Timeout Manager**
```python
# Reuse patterns from timeout_manager.py for Haiku operations
from .timeout_manager import timeout_manager

async def execute_haiku_operation(operation_type, args, timeout_override=None):
    # Much shorter timeouts for LLM operations vs video processing
    timeout_mapping = {
        'komposition': 10,  # vs 60-1800s for video processing
        'timing': 5,        # vs 30-600s for complex timing
        'effects': 8,       # vs processing time
        'qc': 30,          # vs validation time
        'files': 3         # vs file operation time
    }
    
    timeout = timeout_override or timeout_mapping.get(operation_type, 10)
    
    operation_id = f"haiku_{operation_type}_{int(time.time())}"
    
    try:
        result = await timeout_manager.execute_with_timeout(
            execute_haiku_command(operation_type, args),
            operation_id,
            timeout_seconds=timeout,
            cleanup_callback=lambda: cleanup_haiku_temp_files(operation_id)
        )
        return result
    except TimeoutError:
        # Auto-escalate to Sonnet if Haiku times out
        logger.warning(f"Haiku {operation_type} timed out, escalating to Sonnet")
        return await escalate_to_sonnet(operation_type, args)
```

## 📈 **Testing & Validation Strategy**

### **Integration Test Suite**
```bash
# End-to-end workflow test
./tests/test-haiku-workflow.sh

# Test sequence:
# 1. Natural language → Haiku komposition generation
# 2. Confidence assessment 
# 3. Sonnet validation (if needed)
# 4. JSON schema validation
# 5. Technical feasibility check
# 6. Cost tracking
# 7. Performance benchmarking
```

### **Quality Benchmarks**
- **Accuracy**: >90% for structured JSON tasks
- **Speed**: <10s for most operations (vs minutes for video processing)
- **Cost**: <$0.05 per operation (vs $3-125 for Sonnet-only)
- **Availability**: 99.5% uptime with fallback to Sonnet
- **Confidence**: >0.8 before auto-escalation

## 🚀 **Implementation Phases**

### **Phase 1: Foundation (Week 1-2)**
- [ ] Build native CLI tools for JSON generation
- [ ] Implement basic Java integration bridge
- [ ] Set up $5/day budget with monitoring
- [ ] Create basic timeout integration
- [ ] Test on simple komposition generation

### **Phase 2: Expansion (Week 3-4)** 
- [ ] Add timing calculation CLI tool
- [ ] Implement effect parameter selection
- [ ] Add Sonnet validation framework
- [ ] Create confidence scoring system
- [ ] Test on complex music video workflows

### **Phase 3: Quality Control (Week 5-6)**
- [ ] Build video QC CLI tool
- [ ] Integrate with existing validation framework
- [ ] Add file path resolution
- [ ] Implement prompt learning system
- [ ] Performance optimization

### **Phase 4: Production (Week 7-8)**
- [ ] Full integration testing
- [ ] Production deployment
- [ ] Budget scaling ($20-50/day)
- [ ] Documentation completion
- [ ] Team training

## 📊 **Future Work & Extensions**

**As noted in your requirements - documented for later:**

### **Advanced Timeout Management**
- Adaptive timeout learning from actual processing times
- Multi-tier timeout strategy (Haiku → Sonnet → Manual)
- Operation queueing for concurrent processing
- Resource-aware timeout adjustment

### **Enhanced QC Capabilities** 
- ML-based quality scoring beyond rule-based validation
- Automated issue detection and correction suggestions
- Integration with streaming platform requirements
- Real-time quality monitoring during processing

### **Cost Optimization**
- Dynamic model selection (Haiku vs Sonnet) based on complexity
- Bulk operation discounts and batching
- Cost prediction and budgeting tools
- ROI tracking and reporting

## 🎯 **Success Metrics**

### **Cost Metrics**
- **Target**: 99.7% cost reduction achieved ($125 → $0.19)
- **Budget adherence**: Stay within $5/day during testing
- **ROI**: Positive return within 30 days

### **Quality Metrics** 
- **Accuracy**: >95% for JSON generation tasks
- **Confidence**: >0.8 average confidence score
- **Escalation rate**: <20% requiring Sonnet validation

### **Performance Metrics**
- **Speed**: 3x faster than Sonnet-only approach  
- **Reliability**: 99.5% successful operation completion
- **Timeout reduction**: <1% timeout failures

### **Adoption Metrics**
- **CLI usage**: 50+ operations/day within first month
- **Java integration**: Seamless enterprise workflow integration
- **Developer satisfaction**: Positive feedback on simplicity and cost

---

This architecture provides a solid foundation for cost-effective video processing while maintaining the quality standards established in your existing video evaluation and validation framework. The native CLI approach ensures simplicity while the Java integration bridge provides enterprise-grade reliability and monitoring.