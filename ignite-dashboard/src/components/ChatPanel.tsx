'use client';

import { useRef, useEffect, useState } from 'react';
import { useChatStore, validateChatMessage } from '@/stores/chatStore';
import { useA2AChat } from '@/hooks/useA2AChat';
import { Panel } from '@/components/ui/Panel';
import { config, AGENT_NODES } from '@/lib/config';
import { ChatMessage } from '@/lib/types';

/** Agent nodes that support chat (exclude MCP servers) */
const CHAT_AGENTS = AGENT_NODES.filter((node) => node.type !== 'mcp');

/** Get the agent URL from config based on agent ID */
function getAgentUrl(agentId: string): string {
  const agent = AGENT_NODES.find((n) => n.id === agentId);
  if (agent) return agent.url;
  return config.ORCHESTRATOR_URL;
}

export function ChatPanel() {
  const {
    histories,
    activeAgent,
    isPending,
    addMessage,
    setActiveAgent,
    setPending,
  } = useChatStore();

  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const agentUrl = getAgentUrl(activeAgent);
  const { sendMessage } = useA2AChat(agentUrl);

  const messages = histories[activeAgent] || [];

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    const text = inputValue;

    // Reject empty/whitespace-only messages silently
    if (!validateChatMessage(text)) {
      return;
    }

    const trimmedText = text.trim();

    // Add user message to store
    const userMessage: ChatMessage = {
      id: crypto.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`,
      role: 'user',
      content: trimmedText,
      timestamp: Date.now(),
      status: 'sent',
    };
    addMessage(activeAgent, userMessage);
    setInputValue('');
    setPending(true);

    try {
      const responseText = await sendMessage(trimmedText);

      // Add agent response to store
      const agentName = CHAT_AGENTS.find((a) => a.id === activeAgent)?.name ?? 'Agent';
      const agentMessage: ChatMessage = {
        id: crypto.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`,
        role: 'agent',
        content: responseText,
        agentName,
        timestamp: Date.now(),
        status: 'sent',
      };
      addMessage(activeAgent, agentMessage);
    } catch (error: unknown) {
      const errorText =
        error instanceof Error ? error.message : 'An unknown error occurred';

      // Add error message to store
      const errorMessage: ChatMessage = {
        id: crypto.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`,
        role: 'agent',
        content: errorText,
        timestamp: Date.now(),
        status: 'error',
        error: errorText,
      };
      addMessage(activeAgent, errorMessage);
    } finally {
      setPending(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const isSendDisabled = isPending || !validateChatMessage(inputValue);

  return (
    <Panel className="flex flex-col h-full overflow-hidden">
      {/* Panel Title */}
      <h2 className="text-sm font-semibold text-accent-cyan mb-2">Agent Chat</h2>

      {/* Agent Tabs */}
      <div className="flex gap-1 mb-3 border-b border-white/10 pb-2">
        {CHAT_AGENTS.map((agent) => (
          <button
            key={agent.id}
            onClick={() => setActiveAgent(agent.id)}
            className={`px-3 py-1.5 text-xs rounded-t transition-colors ${
              activeAgent === agent.id
                ? 'bg-accent-cyan/20 text-accent-cyan border-b-2 border-accent-cyan'
                : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
            }`}
          >
            {agent.name}
          </button>
        ))}
      </div>

      {/* Message Area */}
      <div className="flex-1 overflow-y-auto space-y-3 min-h-0 pr-1">
        {messages.length === 0 && (
          <p className="text-gray-500 text-xs text-center mt-8">
            Send a message to start chatting with {CHAT_AGENTS.find((a) => a.id === activeAgent)?.name ?? 'the agent'}.
          </p>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {/* Loading indicator */}
        {isPending && (
          <div className="flex items-start gap-2">
            <div className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 max-w-[80%]">
              <div className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-accent-cyan rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 bg-accent-cyan rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 bg-accent-cyan rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="mt-3 flex gap-2 items-end border-t border-white/10 pt-3">
        <textarea
          ref={inputRef}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message..."
          disabled={isPending}
          rows={1}
          className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-100 placeholder-gray-500 resize-none focus:outline-none focus:border-accent-cyan/50 disabled:opacity-50 disabled:cursor-not-allowed"
        />
        <button
          onClick={handleSend}
          disabled={isSendDisabled}
          className="px-4 py-2 bg-accent-cyan/20 text-accent-cyan text-sm font-medium rounded-lg border border-accent-cyan/30 hover:bg-accent-cyan/30 transition-colors disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-accent-cyan/20"
        >
          Send
        </button>
      </div>
    </Panel>
  );
}

/** Individual message bubble component */
function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';
  const isError = message.status === 'error';

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="bg-accent-cyan/20 border border-accent-cyan/30 rounded-lg px-3 py-2 max-w-[80%]">
          <p className="text-sm text-gray-100 whitespace-pre-wrap break-words">
            {message.content}
          </p>
          <span className="text-[10px] text-gray-500 mt-1 block text-right">
            {formatTime(message.timestamp)}
          </span>
        </div>
      </div>
    );
  }

  // Agent message
  return (
    <div className="flex justify-start">
      <div
        className={`rounded-lg px-3 py-2 max-w-[80%] ${
          isError
            ? 'bg-red-500/10 border border-red-500/30'
            : 'bg-white/5 border border-white/10'
        }`}
      >
        {/* Agent attribution */}
        {message.agentName && !isError && (
          <div className="flex items-center gap-1.5 mb-1">
            <span className="w-4 h-4 rounded-full bg-accent-cyan/30 flex items-center justify-center text-[8px] text-accent-cyan font-bold">
              {message.agentName.charAt(0)}
            </span>
            <span className="text-[10px] text-accent-cyan font-medium">
              {message.agentName}
            </span>
          </div>
        )}

        {isError && (
          <div className="flex items-center gap-1.5 mb-1">
            <span className="w-4 h-4 rounded-full bg-red-500/30 flex items-center justify-center text-[8px] text-red-400 font-bold">
              !
            </span>
            <span className="text-[10px] text-red-400 font-medium">Error</span>
          </div>
        )}

        <p
          className={`text-sm whitespace-pre-wrap break-words ${
            isError ? 'text-red-300' : 'text-gray-100'
          }`}
        >
          {message.content}
        </p>
        <span className="text-[10px] text-gray-500 mt-1 block">
          {formatTime(message.timestamp)}
        </span>
      </div>
    </div>
  );
}

/** Format timestamp to HH:mm */
function formatTime(timestamp: number): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
