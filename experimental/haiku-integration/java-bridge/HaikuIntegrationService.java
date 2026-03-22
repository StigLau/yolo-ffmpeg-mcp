package no.lau.kompost.haiku;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Java service layer for Haiku LLM integration
 * Bridges Python CLI tools with Java enterprise systems
 */
public class HaikuIntegrationService {
    
    private static final Logger logger = LoggerFactory.getLogger(HaikuIntegrationService.class);
    
    private final Path cliToolsPath;
    private final ObjectMapper objectMapper;
    private final HaikuConfig config;
    
    public HaikuIntegrationService(HaikuConfig config) {
        this.config = config;
        this.cliToolsPath = Paths.get(config.getCliToolsPath());
        this.objectMapper = new ObjectMapper();
    }
    
    /**
     * Generate komposition asynchronously using Haiku LLM
     */
    public CompletableFuture<KompositionResult> generateKomposition(KompositionRequest request) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                logger.info("Generating komposition: prompt='{}', bpm={}", 
                          request.getPrompt(), request.getBpm());
                
                List<String> command = buildCommand(request);
                ProcessResult result = executeCommand(command, config.getTimeoutSeconds());
                
                if (result.getExitCode() == 0) {
                    return parseSuccessfulResult(result, request);
                } else {
                    logger.error("CLI command failed with exit code {}: {}", 
                               result.getExitCode(), result.getError());
                    return KompositionResult.failure(
                        "CLI execution failed: " + result.getError(),
                        result.getExitCode()
                    );
                }
                
            } catch (Exception e) {
                logger.error("Error generating komposition", e);
                return KompositionResult.failure("Internal error: " + e.getMessage(), -1);
            }
        });
    }
    
    /**
     * Get learning statistics
     */
    public CompletableFuture<LearningStats> getLearningStats() {
        return CompletableFuture.supplyAsync(() -> {
            try {
                List<String> command = List.of(
                    cliToolsPath.resolve("haiku-komposition").toString(),
                    "--learning-stats"
                );
                
                ProcessResult result = executeCommand(command, 10);
                
                if (result.getExitCode() == 0) {
                    return parseLearningStats(result.getOutput());
                } else {
                    logger.warn("Failed to get learning stats: {}", result.getError());
                    return LearningStats.empty();
                }
                
            } catch (Exception e) {
                logger.error("Error getting learning stats", e);
                return LearningStats.empty();
            }
        });
    }
    
    /**
     * Validate service health and connectivity
     */
    public HealthStatus checkHealth() {
        try {
            // Check if CLI tools are accessible
            Path haikuTool = cliToolsPath.resolve("haiku-komposition");
            if (!haikuTool.toFile().exists()) {
                return HealthStatus.unhealthy("Haiku CLI tool not found at: " + haikuTool);
            }
            
            // Test basic connectivity
            List<String> command = List.of(haikuTool.toString(), "--learning-stats");
            ProcessResult result = executeCommand(command, 5);
            
            if (result.getExitCode() == 0) {
                return HealthStatus.healthy("Haiku integration service operational");
            } else {
                return HealthStatus.degraded("CLI execution issues: " + result.getError());
            }
            
        } catch (Exception e) {
            logger.error("Health check failed", e);
            return HealthStatus.unhealthy("Health check exception: " + e.getMessage());
        }
    }
    
    private List<String> buildCommand(KompositionRequest request) {
        List<String> command = new ArrayList<>();
        command.add(cliToolsPath.resolve("haiku-komposition").toString());
        command.add("--input");
        command.add(request.getPrompt());
        command.add("--bpm");
        command.add(String.valueOf(request.getBpm()));
        command.add("--confidence-threshold");
        command.add(String.valueOf(request.getConfidenceThreshold()));
        
        if (request.getOutputFile() != null) {
            command.add("--output");
            command.add(request.getOutputFile().toString());
        }
        
        if (request.isSimulationMode()) {
            command.add("--simulation-mode");
        } else if (request.isApiMode()) {
            command.add("--api-mode");
        }
        
        return command;
    }
    
    private ProcessResult executeCommand(List<String> command, int timeoutSeconds) throws IOException, InterruptedException {
        logger.debug("Executing command: {}", String.join(" ", command));
        
        ProcessBuilder pb = new ProcessBuilder(command);
        pb.redirectErrorStream(true);
        
        Process process = pb.start();
        
        StringBuilder output = new StringBuilder();
        StringBuilder error = new StringBuilder();
        
        // Read output
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line).append("\n");
            }
        }
        
        // Wait for completion with timeout
        boolean finished = process.waitFor(timeoutSeconds, TimeUnit.SECONDS);
        
        if (!finished) {
            process.destroyForcibly();
            throw new RuntimeException("Process timed out after " + timeoutSeconds + " seconds");
        }
        
        return new ProcessResult(process.exitValue(), output.toString(), error.toString());
    }
    
    private KompositionResult parseSuccessfulResult(ProcessResult result, KompositionRequest request) {
        try {
            String output = result.getOutput();
            
            // Extract CLI Result JSON from output
            String cliResultPrefix = "🔧 CLI Result: ";
            int cliResultIndex = output.indexOf(cliResultPrefix);
            
            if (cliResultIndex == -1) {
                logger.warn("CLI result not found in output");
                return KompositionResult.failure("CLI result parsing failed", 0);
            }
            
            String jsonString = output.substring(cliResultIndex + cliResultPrefix.length()).trim();
            JsonNode resultNode = objectMapper.readTree(jsonString);
            
            // Load komposition file if specified
            JsonNode komposition = null;
            if (request.getOutputFile() != null) {
                komposition = objectMapper.readTree(request.getOutputFile().toFile());
            }
            
            return KompositionResult.success(
                komposition,
                resultNode.get("confidence").asDouble(),
                resultNode.get("cost").asDouble(),
                resultNode.get("processing_time").asDouble(),
                resultNode.get("escalation_needed").asBoolean(),
                output
            );
            
        } catch (Exception e) {
            logger.error("Error parsing CLI result", e);
            return KompositionResult.failure("Result parsing error: " + e.getMessage(), 0);
        }
    }
    
    private LearningStats parseLearningStats(String output) {
        try {
            // Parse learning statistics from output
            // This is a simple parser - could be enhanced for production
            
            int totalPatterns = parseStatValue(output, "Total patterns learned:");
            int totalSuccesses = parseStatValue(output, "Total successful kompositions:");
            double avgConfidence = parseStatDouble(output, "Average confidence:");
            
            return new LearningStats(totalPatterns, totalSuccesses, avgConfidence);
            
        } catch (Exception e) {
            logger.warn("Error parsing learning stats", e);
            return LearningStats.empty();
        }
    }
    
    private int parseStatValue(String output, String prefix) {
        try {
            int index = output.indexOf(prefix);
            if (index == -1) return 0;
            
            String line = output.substring(index + prefix.length()).split("\n")[0].trim();
            return Integer.parseInt(line);
        } catch (NumberFormatException e) {
            return 0;
        }
    }
    
    private double parseStatDouble(String output, String prefix) {
        try {
            int index = output.indexOf(prefix);
            if (index == -1) return 0.0;
            
            String line = output.substring(index + prefix.length()).split("\n")[0].trim();
            return Double.parseDouble(line);
        } catch (NumberFormatException e) {
            return 0.0;
        }
    }
    
    // Data classes
    
    public static class ProcessResult {
        private final int exitCode;
        private final String output;
        private final String error;
        
        public ProcessResult(int exitCode, String output, String error) {
            this.exitCode = exitCode;
            this.output = output;
            this.error = error;
        }
        
        public int getExitCode() { return exitCode; }
        public String getOutput() { return output; }
        public String getError() { return error; }
    }
    
    public static class KompositionRequest {
        private final String prompt;
        private final int bpm;
        private final double confidenceThreshold;
        private final Path outputFile;
        private final boolean simulationMode;
        private final boolean apiMode;
        
        public KompositionRequest(String prompt, int bpm, double confidenceThreshold, 
                                Path outputFile, boolean simulationMode, boolean apiMode) {
            this.prompt = prompt;
            this.bpm = bpm;
            this.confidenceThreshold = confidenceThreshold;
            this.outputFile = outputFile;
            this.simulationMode = simulationMode;
            this.apiMode = apiMode;
        }
        
        public String getPrompt() { return prompt; }
        public int getBpm() { return bpm; }
        public double getConfidenceThreshold() { return confidenceThreshold; }
        public Path getOutputFile() { return outputFile; }
        public boolean isSimulationMode() { return simulationMode; }
        public boolean isApiMode() { return apiMode; }
    }
    
    public static class KompositionResult {
        private final boolean success;
        private final JsonNode komposition;
        private final double confidence;
        private final double cost;
        private final double processingTime;
        private final boolean escalationNeeded;
        private final String rawOutput;
        private final String error;
        private final int exitCode;
        
        private KompositionResult(boolean success, JsonNode komposition, double confidence,
                                double cost, double processingTime, boolean escalationNeeded,
                                String rawOutput, String error, int exitCode) {
            this.success = success;
            this.komposition = komposition;
            this.confidence = confidence;
            this.cost = cost;
            this.processingTime = processingTime;
            this.escalationNeeded = escalationNeeded;
            this.rawOutput = rawOutput;
            this.error = error;
            this.exitCode = exitCode;
        }
        
        public static KompositionResult success(JsonNode komposition, double confidence,
                                              double cost, double processingTime, boolean escalationNeeded,
                                              String rawOutput) {
            return new KompositionResult(true, komposition, confidence, cost, processingTime,
                                       escalationNeeded, rawOutput, null, 0);
        }
        
        public static KompositionResult failure(String error, int exitCode) {
            return new KompositionResult(false, null, 0.0, 0.0, 0.0, false, null, error, exitCode);
        }
        
        // Getters
        public boolean isSuccess() { return success; }
        public JsonNode getKomposition() { return komposition; }
        public double getConfidence() { return confidence; }
        public double getCost() { return cost; }
        public double getProcessingTime() { return processingTime; }
        public boolean isEscalationNeeded() { return escalationNeeded; }
        public String getRawOutput() { return rawOutput; }
        public String getError() { return error; }
        public int getExitCode() { return exitCode; }
    }
    
    public static class LearningStats {
        private final int totalPatterns;
        private final int totalSuccesses;
        private final double averageConfidence;
        
        public LearningStats(int totalPatterns, int totalSuccesses, double averageConfidence) {
            this.totalPatterns = totalPatterns;
            this.totalSuccesses = totalSuccesses;
            this.averageConfidence = averageConfidence;
        }
        
        public static LearningStats empty() {
            return new LearningStats(0, 0, 0.0);
        }
        
        public int getTotalPatterns() { return totalPatterns; }
        public int getTotalSuccesses() { return totalSuccesses; }
        public double getAverageConfidence() { return averageConfidence; }
    }
    
    public static class HealthStatus {
        private final boolean healthy;
        private final String status;
        private final String message;
        
        private HealthStatus(boolean healthy, String status, String message) {
            this.healthy = healthy;
            this.status = status;
            this.message = message;
        }
        
        public static HealthStatus healthy(String message) {
            return new HealthStatus(true, "UP", message);
        }
        
        public static HealthStatus degraded(String message) {
            return new HealthStatus(true, "DEGRADED", message);
        }
        
        public static HealthStatus unhealthy(String message) {
            return new HealthStatus(false, "DOWN", message);
        }
        
        public boolean isHealthy() { return healthy; }
        public String getStatus() { return status; }
        public String getMessage() { return message; }
    }
    
    public static class HaikuConfig {
        private final String cliToolsPath;
        private final int timeoutSeconds;
        
        public HaikuConfig(String cliToolsPath, int timeoutSeconds) {
            this.cliToolsPath = cliToolsPath;
            this.timeoutSeconds = timeoutSeconds;
        }
        
        public String getCliToolsPath() { return cliToolsPath; }
        public int getTimeoutSeconds() { return timeoutSeconds; }
    }
}