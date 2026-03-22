package no.lau.kompost.haiku.web;

import no.lau.kompost.haiku.HaikuIntegrationService;
import no.lau.kompost.haiku.HaikuIntegrationService.*;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import javax.validation.constraints.Max;
import javax.validation.constraints.Min;
import javax.validation.constraints.NotBlank;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.concurrent.CompletableFuture;

/**
 * REST API for Haiku LLM komposition generation
 * Enterprise endpoint for video komposition creation with budget controls
 */
@RestController
@RequestMapping("/api/v1/haiku")
public class HaikuRestController {
    
    private final HaikuIntegrationService haikuService;
    
    public HaikuRestController(HaikuIntegrationService haikuService) {
        this.haikuService = haikuService;
    }
    
    /**
     * Generate komposition from natural language prompt
     */
    @PostMapping("/komposition")
    public CompletableFuture<ResponseEntity<KompositionResponse>> generateKomposition(
            @Valid @RequestBody GenerateKompositionRequest request) {
        
        Path outputFile = null;
        if (request.getSaveToFile()) {
            outputFile = Paths.get("/tmp/komposition-" + System.currentTimeMillis() + ".json");
        }
        
        KompositionRequest serviceRequest = new KompositionRequest(
            request.getPrompt(),
            request.getBpm(),
            request.getConfidenceThreshold(),
            outputFile,
            request.isSimulationMode(),
            request.isApiMode()
        );
        
        return haikuService.generateKomposition(serviceRequest)
            .thenApply(result -> {
                if (result.isSuccess()) {
                    return ResponseEntity.ok(KompositionResponse.success(result));
                } else {
                    return ResponseEntity.status(500)
                        .body(KompositionResponse.error(result.getError()));
                }
            });
    }
    
    /**
     * Get learning statistics and pattern insights
     */
    @GetMapping("/learning/stats")
    public CompletableFuture<ResponseEntity<LearningStatsResponse>> getLearningStats() {
        return haikuService.getLearningStats()
            .thenApply(stats -> ResponseEntity.ok(new LearningStatsResponse(stats)));
    }
    
    /**
     * Health check endpoint
     */
    @GetMapping("/health")
    public ResponseEntity<HealthResponse> checkHealth() {
        HealthStatus status = haikuService.checkHealth();
        return ResponseEntity.ok(new HealthResponse(status));
    }
    
    // Request/Response DTOs
    
    public static class GenerateKompositionRequest {
        @NotBlank(message = "Prompt is required")
        private String prompt;
        
        @Min(value = 60, message = "BPM must be at least 60")
        @Max(value = 200, message = "BPM must not exceed 200")
        private int bpm = 120;
        
        @Min(value = 0.1, message = "Confidence threshold must be at least 0.1")
        @Max(value = 1.0, message = "Confidence threshold must not exceed 1.0")
        private double confidenceThreshold = 0.8;
        
        private boolean simulationMode = false;
        private boolean apiMode = false;
        private boolean saveToFile = false;
        
        // Getters and setters
        public String getPrompt() { return prompt; }
        public void setPrompt(String prompt) { this.prompt = prompt; }
        
        public int getBpm() { return bpm; }
        public void setBpm(int bpm) { this.bpm = bpm; }
        
        public double getConfidenceThreshold() { return confidenceThreshold; }
        public void setConfidenceThreshold(double confidenceThreshold) { 
            this.confidenceThreshold = confidenceThreshold; 
        }
        
        public boolean isSimulationMode() { return simulationMode; }
        public void setSimulationMode(boolean simulationMode) { 
            this.simulationMode = simulationMode; 
        }
        
        public boolean isApiMode() { return apiMode; }
        public void setApiMode(boolean apiMode) { this.apiMode = apiMode; }
        
        public boolean getSaveToFile() { return saveToFile; }
        public void setSaveToFile(boolean saveToFile) { this.saveToFile = saveToFile; }
    }
    
    public static class KompositionResponse {
        private boolean success;
        private KompositionData komposition;
        private double confidence;
        private double costUsd;
        private double processingTimeSeconds;
        private boolean escalationNeeded;
        private String error;
        
        public static KompositionResponse success(KompositionResult result) {
            KompositionResponse response = new KompositionResponse();
            response.success = true;
            response.komposition = new KompositionData(result.getKomposition());
            response.confidence = result.getConfidence();
            response.costUsd = result.getCost();
            response.processingTimeSeconds = result.getProcessingTime();
            response.escalationNeeded = result.isEscalationNeeded();
            return response;
        }
        
        public static KompositionResponse error(String error) {
            KompositionResponse response = new KompositionResponse();
            response.success = false;
            response.error = error;
            return response;
        }
        
        // Getters and setters
        public boolean isSuccess() { return success; }
        public void setSuccess(boolean success) { this.success = success; }
        
        public KompositionData getKomposition() { return komposition; }
        public void setKomposition(KompositionData komposition) { this.komposition = komposition; }
        
        public double getConfidence() { return confidence; }
        public void setConfidence(double confidence) { this.confidence = confidence; }
        
        public double getCostUsd() { return costUsd; }
        public void setCostUsd(double costUsd) { this.costUsd = costUsd; }
        
        public double getProcessingTimeSeconds() { return processingTimeSeconds; }
        public void setProcessingTimeSeconds(double processingTimeSeconds) { 
            this.processingTimeSeconds = processingTimeSeconds; 
        }
        
        public boolean isEscalationNeeded() { return escalationNeeded; }
        public void setEscalationNeeded(boolean escalationNeeded) { 
            this.escalationNeeded = escalationNeeded; 
        }
        
        public String getError() { return error; }
        public void setError(String error) { this.error = error; }
    }
    
    public static class KompositionData {
        private Object metadata;
        private Object segments;
        private Object audio;
        
        public KompositionData(com.fasterxml.jackson.databind.JsonNode jsonNode) {
            if (jsonNode != null) {
                try {
                    com.fasterxml.jackson.databind.ObjectMapper mapper = 
                        new com.fasterxml.jackson.databind.ObjectMapper();
                    
                    this.metadata = mapper.treeToValue(jsonNode.get("metadata"), Object.class);
                    this.segments = mapper.treeToValue(jsonNode.get("segments"), Object.class);
                    this.audio = mapper.treeToValue(jsonNode.get("audio"), Object.class);
                } catch (Exception e) {
                    // Fallback to raw JSON
                    this.metadata = jsonNode.get("metadata");
                    this.segments = jsonNode.get("segments");
                    this.audio = jsonNode.get("audio");
                }
            }
        }
        
        public Object getMetadata() { return metadata; }
        public void setMetadata(Object metadata) { this.metadata = metadata; }
        
        public Object getSegments() { return segments; }
        public void setSegments(Object segments) { this.segments = segments; }
        
        public Object getAudio() { return audio; }
        public void setAudio(Object audio) { this.audio = audio; }
    }
    
    public static class LearningStatsResponse {
        private int totalPatterns;
        private int totalSuccesses;
        private double averageConfidence;
        private String status;
        
        public LearningStatsResponse(LearningStats stats) {
            this.totalPatterns = stats.getTotalPatterns();
            this.totalSuccesses = stats.getTotalSuccesses();
            this.averageConfidence = stats.getAverageConfidence();
            this.status = stats.getTotalPatterns() > 0 ? "active" : "learning";
        }
        
        public int getTotalPatterns() { return totalPatterns; }
        public void setTotalPatterns(int totalPatterns) { this.totalPatterns = totalPatterns; }
        
        public int getTotalSuccesses() { return totalSuccesses; }
        public void setTotalSuccesses(int totalSuccesses) { this.totalSuccesses = totalSuccesses; }
        
        public double getAverageConfidence() { return averageConfidence; }
        public void setAverageConfidence(double averageConfidence) { 
            this.averageConfidence = averageConfidence; 
        }
        
        public String getStatus() { return status; }
        public void setStatus(String status) { this.status = status; }
    }
    
    public static class HealthResponse {
        private boolean healthy;
        private String status;
        private String message;
        private long timestamp;
        
        public HealthResponse(HealthStatus healthStatus) {
            this.healthy = healthStatus.isHealthy();
            this.status = healthStatus.getStatus();
            this.message = healthStatus.getMessage();
            this.timestamp = System.currentTimeMillis();
        }
        
        public boolean isHealthy() { return healthy; }
        public void setHealthy(boolean healthy) { this.healthy = healthy; }
        
        public String getStatus() { return status; }
        public void setStatus(String status) { this.status = status; }
        
        public String getMessage() { return message; }
        public void setMessage(String message) { this.message = message; }
        
        public long getTimestamp() { return timestamp; }
        public void setTimestamp(long timestamp) { this.timestamp = timestamp; }
    }
}