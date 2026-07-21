import { describe, it, expect, beforeEach } from 'vitest';
import { useChatStore, validateChatMessage } from '@/stores/chatStore';
import { ChatMessage } from '@/lib/types';

function createMessage(overrides: Partial<ChatMessage> = {}): ChatMessage {
  return {
    id: `msg-${Date.now()}-${Math.random()}`,
    role: 'user',
    content: 'Hello',
    timestamp: Date.now(),
    status: 'sent',
    ...overrides,
  };
}

describe('chatStore', () => {
  beforeEach(() => {
    useChatStore.setState({
      histories: {},
      activeAgent: 'orchestrator',
      isPending: false,
    });
  });

  describe('initial state', () => {
    it('should have empty histories', () => {
      const state = useChatStore.getState();
      expect(state.histories).toEqual({});
    });

    it('should have activeAgent set to orchestrator', () => {
      const state = useChatStore.getState();
      expect(state.activeAgent).toBe('orchestrator');
    });

    it('should have isPending set to false', () => {
      const state = useChatStore.getState();
      expect(state.isPending).toBe(false);
    });
  });

  describe('addMessage', () => {
    it('should add a message to a new agent history', () => {
      const msg = createMessage({ content: 'Hello agent' });
      useChatStore.getState().addMessage('orchestrator', msg);

      const state = useChatStore.getState();
      expect(state.histories['orchestrator']).toHaveLength(1);
      expect(state.histories['orchestrator'][0]).toEqual(msg);
    });

    it('should append messages to existing agent history', () => {
      const msg1 = createMessage({ id: '1', content: 'First' });
      const msg2 = createMessage({ id: '2', content: 'Second' });

      useChatStore.getState().addMessage('orchestrator', msg1);
      useChatStore.getState().addMessage('orchestrator', msg2);

      const state = useChatStore.getState();
      expect(state.histories['orchestrator']).toHaveLength(2);
      expect(state.histories['orchestrator'][0].id).toBe('1');
      expect(state.histories['orchestrator'][1].id).toBe('2');
    });

    it('should maintain separate histories per agent', () => {
      const msg1 = createMessage({ id: '1', content: 'To orchestrator' });
      const msg2 = createMessage({ id: '2', content: 'To research' });

      useChatStore.getState().addMessage('orchestrator', msg1);
      useChatStore.getState().addMessage('research-agent', msg2);

      const state = useChatStore.getState();
      expect(state.histories['orchestrator']).toHaveLength(1);
      expect(state.histories['research-agent']).toHaveLength(1);
      expect(state.histories['orchestrator'][0].id).toBe('1');
      expect(state.histories['research-agent'][0].id).toBe('2');
    });

    it('should enforce max 200 messages per agent', () => {
      // Add 200 messages
      for (let i = 0; i < 200; i++) {
        useChatStore.getState().addMessage('orchestrator', createMessage({ id: `msg-${i}` }));
      }

      expect(useChatStore.getState().histories['orchestrator']).toHaveLength(200);

      // Add the 201st message
      useChatStore.getState().addMessage('orchestrator', createMessage({ id: 'msg-200' }));

      const history = useChatStore.getState().histories['orchestrator'];
      expect(history).toHaveLength(200);
      // Oldest message (msg-0) should be removed
      expect(history[0].id).toBe('msg-1');
      // Newest message should be at the end
      expect(history[199].id).toBe('msg-200');
    });
  });

  describe('setActiveAgent', () => {
    it('should update the active agent', () => {
      useChatStore.getState().setActiveAgent('research-agent');
      expect(useChatStore.getState().activeAgent).toBe('research-agent');
    });

    it('should allow setting back to orchestrator', () => {
      useChatStore.getState().setActiveAgent('research-agent');
      useChatStore.getState().setActiveAgent('orchestrator');
      expect(useChatStore.getState().activeAgent).toBe('orchestrator');
    });
  });

  describe('setPending', () => {
    it('should set isPending to true', () => {
      useChatStore.getState().setPending(true);
      expect(useChatStore.getState().isPending).toBe(true);
    });

    it('should set isPending to false', () => {
      useChatStore.getState().setPending(true);
      useChatStore.getState().setPending(false);
      expect(useChatStore.getState().isPending).toBe(false);
    });
  });
});

describe('validateChatMessage', () => {
  it('should accept a normal message', () => {
    expect(validateChatMessage('Hello, world!')).toBe(true);
  });

  it('should accept a single character message', () => {
    expect(validateChatMessage('a')).toBe(true);
  });

  it('should accept a message with leading/trailing whitespace if trimmed content is valid', () => {
    expect(validateChatMessage('  hello  ')).toBe(true);
  });

  it('should reject an empty string', () => {
    expect(validateChatMessage('')).toBe(false);
  });

  it('should reject a whitespace-only string', () => {
    expect(validateChatMessage('   ')).toBe(false);
  });

  it('should reject tabs and newlines only', () => {
    expect(validateChatMessage('\t\n\r')).toBe(false);
  });

  it('should accept a message at exactly 10,000 characters', () => {
    const msg = 'a'.repeat(10000);
    expect(validateChatMessage(msg)).toBe(true);
  });

  it('should reject a message exceeding 10,000 characters after trimming', () => {
    const msg = 'a'.repeat(10001);
    expect(validateChatMessage(msg)).toBe(false);
  });

  it('should reject a message that is over 10,000 chars after trimming whitespace', () => {
    const msg = '  ' + 'a'.repeat(10001) + '  ';
    expect(validateChatMessage(msg)).toBe(false);
  });

  it('should accept a message that is under 10,000 chars after trimming whitespace', () => {
    const msg = '  ' + 'a'.repeat(9998) + '  ';
    expect(validateChatMessage(msg)).toBe(true);
  });
});
