const { CommunicationInterface } = require('../communication_interface');

const DEFAULT_OPTIONS = {
  model: 'claude-3-haiku-20240307',
  maxTokens: 300,
  systemPrompt: 'You are a concise assistant.',
};

function createMockClaudeClient(responses) {
  const calls = [];
  return {
    calls,
    messages: {
      create: async (input) => {
        calls.push(input);
        const response = responses.shift();
        if (!response) {
          throw new Error('Unexpected Claude SDK call with no remaining mock response');
        }
        return response;
      },
    },
  };
}

describe('CommunicationInterface (Claude transport)', () => {
  it('forwards user prompts through the Claude SDK', async () => {
    const mockClient = createMockClaudeClient([
      {
        id: 'msg_123',
        content: [{ type: 'text', text: 'Hello from Claude!' }],
        stop_reason: 'end_turn',
      },
    ]);

    const comms = new CommunicationInterface({
      client: mockClient,
      model: DEFAULT_OPTIONS.model,
      maxTokens: DEFAULT_OPTIONS.maxTokens,
      systemPrompt: DEFAULT_OPTIONS.systemPrompt,
    });

    const reply = await comms.sendMessage({
      conversationId: 'conv-1',
      message: 'Hello Claude, are you there?',
    });

    expect(mockClient.calls.length).toBe(1);
    expect(mockClient.calls[0]).toEqual({
      model: DEFAULT_OPTIONS.model,
      max_tokens: DEFAULT_OPTIONS.maxTokens,
      system: DEFAULT_OPTIONS.systemPrompt,
      messages: [
        {
          role: 'user',
          content: [{ type: 'text', text: 'Hello Claude, are you there?' }],
        },
      ],
    });

    expect(reply.id).toBe('msg_123');
    expect(reply.text).toBe('Hello from Claude!');
    expect(reply.conversationId).toBe('conv-1');
    expect(reply.raw).toBeTruthy();
  });

  it('preserves conversation history for follow-up turns', async () => {
    const mockClient = createMockClaudeClient([
      {
        id: 'msg_first',
        content: [{ type: 'text', text: 'Hi! I am Claude.' }],
        stop_reason: 'end_turn',
      },
      {
        id: 'msg_second',
        content: [{ type: 'text', text: 'I am doing well, thanks!' }],
        stop_reason: 'end_turn',
      },
    ]);

    const comms = new CommunicationInterface({
      client: mockClient,
      model: DEFAULT_OPTIONS.model,
      maxTokens: DEFAULT_OPTIONS.maxTokens,
      systemPrompt: DEFAULT_OPTIONS.systemPrompt,
    });

    await comms.sendMessage({
      conversationId: 'conv-2',
      message: 'Hello Claude!',
    });

    const followUp = await comms.sendMessage({
      conversationId: 'conv-2',
      message: 'How are you today?',
    });

    expect(mockClient.calls.length).toBe(2);
    expect(mockClient.calls[1].messages).toEqual([
      {
        role: 'user',
        content: [{ type: 'text', text: 'Hello Claude!' }],
      },
      {
        role: 'assistant',
        content: [{ type: 'text', text: 'Hi! I am Claude.' }],
      },
      {
        role: 'user',
        content: [{ type: 'text', text: 'How are you today?' }],
      },
    ]);

    expect(followUp.id).toBe('msg_second');
    expect(followUp.text).toBe('I am doing well, thanks!');
  });

  it('rejects when Claude does not return text content', async () => {
    const mockClient = createMockClaudeClient([
      {
        id: 'msg_no_text',
        content: [{ type: 'tool_use', name: 'some_tool', input: {} }],
        stop_reason: 'tool_use',
      },
    ]);

    const comms = new CommunicationInterface({
      client: mockClient,
      model: DEFAULT_OPTIONS.model,
      maxTokens: DEFAULT_OPTIONS.maxTokens,
      systemPrompt: DEFAULT_OPTIONS.systemPrompt,
    });

    await expectAsync(
      comms.sendMessage({
        conversationId: 'conv-3',
        message: 'Please respond in plain text.',
      }),
    ).toBeRejectedWithError(/Claude response did not include text content/i);
  });
});

