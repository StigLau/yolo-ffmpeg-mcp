# Request for Komposteur Claude: MCP Discovery Protocol

## 🎯 **SITUATION SUMMARY**

We have a **complete MCP-Komposteur integration** ready to deploy, blocked only on the discovery protocol:

### **✅ WHAT'S WORKING**
- **MCP Bridge**: `integration/komposteur/bridge/komposteur_bridge.py` successfully calls Komposteur v0.9.9-core JAR
- **Video Processing**: Our MCP server has proven video processing capabilities (21 MCP tools, beat-sync, effects)
- **Error Identified**: JAR tries to call Python MCP processor but fails with "Python subprocess returned error"
- **Architecture Perfect**: Natural Language → Komposition → MCP Video Processing → Final Video

### **❌ WHAT'S MISSING**
Komposteur v0.9.9-core JAR contains MCP discovery code that's **not in current source**. We need to understand how it finds/calls Python processors.

## 🔍 **CRITICAL QUESTIONS FOR KOMPOSTEUR CLAUDE**

### **1. Discovery Protocol**
- How does `findMcpPythonProcessor()` actually work?
- Does it look for specific filenames, environment variables, config files?
- Is there a registration mechanism or hardcoded paths?

### **2. Interface Specification**  
- What's the expected Python processor API/protocol?
- Arguments format: JSON file path, stdin data, command line args?
- Expected response format: stdout, return codes, file outputs?

### **3. Communication Method**
- Subprocess with arguments/stdin/stdout?
- Socket server that Komposteur connects to?  
- HTTP API endpoints?
- Py4J gateway integration?

### **4. Configuration & Setup**
- Required environment variables or config files?
- Working directory expectations?
- Specific Python executable requirements?

## 🚀 **READY TO IMPLEMENT**

Once we have the discovery protocol, implementation is straightforward:

```python
# Update our MCP processor to match Komposteur's expectations
def komposteur_mcp_processor(komposition_json):
    # Parse Komposteur's request format
    # Call our existing MCP video processing 
    # Return in expected format
    
# Test complete pipeline
"Create a 30-second music video" → Komposition JSON → Video Output
```

## 📋 **SPECIFIC REQUEST**

**Can you provide the MCP processor discovery protocol used by Komposteur v0.9.9-core?**

We have:
- ✅ Complete MCP video processing system (21 tools, effects, beat-sync)
- ✅ Working Komposteur bridge that calls the JAR
- ✅ Test framework and integration ready

We need:
- ❓ How Komposteur discovers Python MCP processors
- ❓ Expected interface/protocol for the Python processor
- ❓ Required setup/configuration

**Timeline: Once we have the protocol details, integration can be completed in ~30 minutes.**