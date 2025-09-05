#!/bin/bash
# View Chat & FFmpeg Logs Helper Script

LOG_DIR="/tmp/kompo/cloud-music-video-creator/logs/interactions"

echo "🔍 Cloud Music Video Creator - Log Viewer"
echo "=========================================="

case "${1:-help}" in
    "recent")
        echo "📝 Most Recent Log Files:"
        ls -lt "$LOG_DIR" | head -10
        ;;
    
    "latest")
        latest_log=$(ls -t "$LOG_DIR"/*.json | head -1)
        echo "📖 Latest Log: $(basename "$latest_log")"
        echo "------------------------------------------"
        cat "$latest_log" | jq '.'
        ;;
    
    "ffmpeg")
        echo "⚙️ Recent FFmpeg Commands:"
        find "$LOG_DIR" -name "*.json" -exec jq -r '.interactions[] | select(.interaction_type=="ffmpeg_command") | "\(.timestamp): \(.content.command)"' {} \; | tail -5
        ;;
    
    "chat")
        echo "💬 Recent Chat Messages:"
        find "$LOG_DIR" -name "*.json" -exec jq -r '.interactions[] | select(.interaction_type=="user_message" or .interaction_type=="llm1_response") | "\(.timestamp) [\(.interaction_type)]: \(.content.message // .content.response)"' {} \; | tail -10
        ;;
    
    "session")
        if [ -z "$2" ]; then
            echo "❌ Please provide session ID: ./view_logs.sh session <session_id>"
            exit 1
        fi
        session_file="$LOG_DIR/$2.json"
        if [ -f "$session_file" ]; then
            echo "📁 Session Log: $2"
            echo "-------------------------"
            cat "$session_file" | jq '.'
        else
            echo "❌ Session not found: $2"
        fi
        ;;
    
    "tail")
        echo "📡 Real-time Log Monitoring (press Ctrl+C to exit)"
        echo "------------------------------------------------"
        # This would monitor the server output, but since it's running in background,
        # we'll show the most recent files being updated
        watch -n 1 "ls -lt '$LOG_DIR' | head -5"
        ;;
    
    "help"|*)
        echo "Usage: ./view_logs.sh [command]"
        echo ""
        echo "Commands:"
        echo "  recent  - List most recent log files"
        echo "  latest  - Show latest complete log file"
        echo "  ffmpeg  - Show recent FFmpeg commands"
        echo "  chat    - Show recent chat interactions"
        echo "  session <id> - Show specific session log"
        echo "  tail    - Monitor logs in real-time"
        echo ""
        echo "Examples:"
        echo "  ./view_logs.sh recent"
        echo "  ./view_logs.sh latest"
        echo "  ./view_logs.sh session 1cad1f56"
        ;;
esac