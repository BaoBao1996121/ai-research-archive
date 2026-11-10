import type {
  Message,
  ModelAdapter,
  ModelEvent,
  ToolCall,
  ToolResultMessage,
} from "./types.ts";

export type ToolBatchExecutor = (calls: ToolCall[]) => Promise<ToolResultMessage[]>;

export type AgentEvent =
  | { type: "agent_start" }
  | { type: "turn_start"; turn: number }
  | { type: "model_event"; event: ModelEvent }
  | { type: "message_end"; message: Message }
  | { type: "tool_batch_end"; results: ToolResultMessage[] }
  | { type: "agent_end"; reason: "stop" | "error" | "maxTurns"; messages: Message[] };

export type RunAgentOptions = {
  model: ModelAdapter;
  messages: Message[];
  systemPrompt?: string;
  tools?: Array<{ name: string; description: string }>;
  executeTools?: ToolBatchExecutor;
  maxTurns?: number;
  onEvent?: (event: AgentEvent) => void | Promise<void>;
};

export type AgentRunResult = {
  messages: Message[];
  events: AgentEvent[];
  reason: "stop" | "error" | "maxTurns";
};

export async function runAgentLoop(options: RunAgentOptions): Promise<AgentRunResult> {
  const messages = [...options.messages];
  const events: AgentEvent[] = [];
  const maxTurns = options.maxTurns ?? 8;
  const emit = async (event: AgentEvent): Promise<void> => {
    events.push(event);
    await options.onEvent?.(event);
  };
  const finish = async (reason: AgentRunResult["reason"]): Promise<AgentRunResult> => {
    await emit({ type: "agent_end", reason, messages: [...messages] });
    return { messages, events, reason };
  };

  await emit({ type: "agent_start" });
  for (let turn = 1; turn <= maxTurns; turn += 1) {
    await emit({ type: "turn_start", turn });
    let assistantMessage;
    for await (const event of options.model.stream({
      systemPrompt: options.systemPrompt,
      messages,
      tools: options.tools,
    })) {
      await emit({ type: "model_event", event });
      if (event.type === "done") assistantMessage = event.message;
      if (event.type === "error") assistantMessage = event.error;
    }
    if (!assistantMessage) throw new Error("Model stream ended without done or error");

    messages.push(assistantMessage);
    await emit({ type: "message_end", message: assistantMessage });
    if (assistantMessage.stopReason === "error" || assistantMessage.stopReason === "aborted") {
      return finish("error");
    }

    const calls = assistantMessage.content.filter((block) => block.type === "toolCall");
    if (calls.length === 0) return finish("stop");
    const results = assistantMessage.stopReason === "length"
      ? calls.map((call) => ({
          role: "toolResult" as const,
          toolCallId: call.id,
          toolName: call.name,
          content: [{
            type: "text" as const,
            text: "Tool call was not executed: the token limit may have truncated its arguments.",
          }],
          isError: true,
        }))
      : options.executeTools
        ? await options.executeTools(calls)
        : calls.map((call) => ({
          role: "toolResult" as const,
          toolCallId: call.id,
          toolName: call.name,
          content: [{ type: "text" as const, text: `No executor for tool ${call.name}` }],
          isError: true,
        }));
    messages.push(...results);
    await emit({ type: "tool_batch_end", results });
    for (const result of results) await emit({ type: "message_end", message: result });
  }
  return finish("maxTurns");
}
