
# Questions for the TypeScript MCP Server LLM

I am an AI assistant trying to interact with the `typescript-mcp` server. I have started the server, and now I need to write a client to communicate with it. Please provide the following information to help me write a `client.ts` script.

## 1. Connecting to the Server

I know the server uses `StdioServerTransport`. Please provide a TypeScript code snippet demonstrating how to use the `@modelcontextprotocol/sdk`'s `StdioClientTransport` to connect to the running server process.

## 2. Calling a Tool

I want to call the `system-health` tool. Please provide a TypeScript code snippet that shows how to:

*   Create a JSON-RPC request to call the `system-health` tool.
*   Send the request to the server.

## 3. Handling the Response

After sending the request, I need to read and parse the response from the server. Please provide a TypeScript code snippet that shows how to:

*   Read the JSON-RPC response from the server's `stdout`.
*   Parse the response to get the result of the `system-health` tool.

## 4. Compiling and Running the Client

Assuming I have a `client.ts` file with the code from the previous questions, please provide the exact shell commands to:

1.  Compile the `client.ts` file.
2.  Run the compiled client.

A complete, runnable example of a `client.ts` file that connects to the server, calls the `system-health` tool, and prints the response would be ideal.
