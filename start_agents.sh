#!/bin/bash
# start_agents_tmux.sh

SESSION="agentic-ai"

# Create new tmux session
tmux new-session -d -s $SESSION

# Window 0: MCP Server
tmux rename-window -t $SESSION:0 'MCP'
tmux send-keys -t $SESSION:0 'python src/mcp_server.py' C-m

# Window 1: Agent Server
tmux new-window -t $SESSION:1 -n 'Agent'
tmux send-keys -t $SESSION:1 'sleep 5 && python src/a2a_1_starlette.py' C-m

# Window 2: Client
tmux new-window -t $SESSION:2 -n 'Client'
tmux send-keys -t $SESSION:2 'sleep 10 && python src/client.py' C-m

# Attach to session
tmux attach-session -t $SESSION