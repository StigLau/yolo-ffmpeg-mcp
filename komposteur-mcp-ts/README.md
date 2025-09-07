# Komposteur MCP Server

TypeScript MCP server that wraps the [Komposteur](https://github.com/StigLau/komposteur) uberjar to provide LLMs with music video creation capabilities.

## Features

- **YouTube Download**: Download videos using Komposteur's YouTube integration
- **Kompost.json Processing**: Process music video compositions from JSON files
- **S3 Operations**: Upload and download media files via S3
- **Status Monitoring**: Check system status and JAR availability

## Quick Start

```bash
# Setup project
make setup

# Start development server
make dev

# Test JAR functionality
make validate-jar
```

## Development

```bash
# Watch for changes
make watch

# Run tests
make test

# Build for production
make build
```

## MCP Tools

The server provides these tools for LLM integration:

- `komposteur_youtube_download` - Download videos from YouTube
- `komposteur_process_composition` - Process kompost.json files
- `komposteur_s3_upload` - Upload files to S3
- `komposteur_s3_download` - Download files from S3
- `komposteur_status` - Get system status

## Configuration

The server automatically detects Komposteur JAR in this order:
1. Local development: `~/.m2/repository/no/lau/kompost/mcp/uber-kompost-1.0.0-shaded.jar`
2. Fallback: `./lib/komposteur-uber.jar`

## Architecture

- **TypeScript MCP Server**: Handles LLM communication
- **JAR Manager**: Manages Komposteur JAR execution
- **Operations Layer**: Wraps Komposteur functionality
- **Type Safety**: Full TypeScript definitions

See `CLAUDE.md` for detailed development guidelines.