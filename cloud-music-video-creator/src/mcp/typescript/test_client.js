#!/usr/bin/env node

const { spawn } = require('child_process');
const { createReadStream, createWriteStream } = require('fs');

async function testMCPServer() {
    console.log('🚀 Testing MCP Server...\n');
    
    // Start the MCP server
    const server = spawn('node', ['dist/server.js'], {
        stdio: ['pipe', 'pipe', 'pipe']
    });
    
    let responseBuffer = '';
    
    server.stdout.on('data', (data) => {
        responseBuffer += data.toString();
    });
    
    server.stderr.on('data', (data) => {
        console.error('Server stderr:', data.toString());
    });
    
    // Test 1: List available tools
    console.log('📋 Test 1: Listing available tools...');
    const listToolsRequest = JSON.stringify({
        jsonrpc: '2.0',
        id: 1,
        method: 'tools/list',
        params: {}
    }) + '\n';
    
    server.stdin.write(listToolsRequest);
    
    // Wait for response
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    if (responseBuffer.includes('tools')) {
        console.log('✅ Tools list received');
        // Parse and show available tools
        try {
            const response = JSON.parse(responseBuffer.trim());
            if (response.result && response.result.tools) {
                console.log(`   Found ${response.result.tools.length} tools:`);
                response.result.tools.forEach(tool => {
                    console.log(`   - ${tool.name}: ${tool.description}`);
                });
            }
        } catch (e) {
            console.log('   Raw response:', responseBuffer);
        }
    } else {
        console.log('❌ No tools response received');
        console.log('Response buffer:', responseBuffer);
    }
    
    // Test 2: Create a komposition
    console.log('\n🎵 Test 2: Creating a komposition...');
    responseBuffer = ''; // Clear buffer
    
    const createKompositionRequest = JSON.stringify({
        jsonrpc: '2.0',
        id: 2,
        method: 'tools/call',
        params: {
            name: 'create_komposition',
            arguments: {
                title: 'Test Vintage Music Video',
                description: '30 second vintage music video with nice vibe',
                user_id: 'test_user_123',
                bpm: 120,
                duration_seconds: 30,
                visual_concept: 'vintage aesthetic with warm colors'
            }
        }
    }) + '\n';
    
    server.stdin.write(createKompositionRequest);
    
    // Wait for response
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    if (responseBuffer.includes('result')) {
        console.log('✅ Komposition created successfully');
        try {
            const response = JSON.parse(responseBuffer.trim());
            if (response.result && response.result.content) {
                const komposition = JSON.parse(response.result.content[0].text);
                console.log(`   ID: ${komposition.id}`);
                console.log(`   Title: ${komposition.title}`);
                console.log(`   BPM: ${komposition.bpm}`);
                console.log(`   Duration: ${komposition.duration_seconds}s`);
                console.log(`   Status: ${komposition.status}`);
            }
        } catch (e) {
            console.log('   Raw response:', responseBuffer);
        }
    } else {
        console.log('❌ Komposition creation failed');
        console.log('Response buffer:', responseBuffer);
    }
    
    // Test 3: List user kompositions
    console.log('\n📝 Test 3: Listing user kompositions...');
    responseBuffer = ''; // Clear buffer
    
    const listKompositionsRequest = JSON.stringify({
        jsonrpc: '2.0',
        id: 3,
        method: 'tools/call',
        params: {
            name: 'list_user_kompositions',
            arguments: {
                user_id: 'test_user_123'
            }
        }
    }) + '\n';
    
    server.stdin.write(listKompositionsRequest);
    
    // Wait for response
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    if (responseBuffer.includes('result')) {
        console.log('✅ Komposition list retrieved');
        try {
            const response = JSON.parse(responseBuffer.trim());
            if (response.result && response.result.content) {
                const kompositions = JSON.parse(response.result.content[0].text);
                console.log(`   Found ${kompositions.length} komposition(s)`);
                kompositions.forEach((k, i) => {
                    console.log(`   ${i + 1}. ${k.title} (${k.id})`);
                });
            }
        } catch (e) {
            console.log('   Raw response:', responseBuffer);
        }
    } else {
        console.log('❌ Komposition list failed');
        console.log('Response buffer:', responseBuffer);
    }
    
    console.log('\n🎯 MCP Server test completed');
    server.kill();
}

testMCPServer().catch(console.error);