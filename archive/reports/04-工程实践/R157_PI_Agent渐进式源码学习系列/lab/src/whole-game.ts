import { runAgentLoop } from "./agent-loop.ts";
import { ScriptedModel } from "./scripted-model.ts";
import { createToolBatchExecutor, type AgentTool } from "./tool-pipeline.ts";
import type { AssistantMessage, Message } from "./types.ts";

export type WholeGameResult = {
  answer: string;
  transcript: Message[];
  trace: string[];
  modelCalls: number;
};

export async function runWholeGame(): Promise<WholeGameResult> {
  const trace: string[] = [];
  const request: AssistantMessage = {
    role: "assistant",
    content: [{ type: "toolCall", id: "call-add", name: "add", arguments: { a: 20, b: 22 } }],
    stopReason: "toolUse",
  };
  const answer: AssistantMessage = {
    role: "assistant",
    content: [{ type: "text", text: "The answer is 42." }],
    stopReason: "stop",
  };
  const model = new ScriptedModel([request, answer]);
  const add: AgentTool<{ a: number; b: number }> = {
    name: "add",
    description: "Add two numbers",
    validate(input) {
      const { a, b } = input as { a?: unknown; b?: unknown };
      if (typeof a !== "number" || typeof b !== "number") throw new Error("a and b must be numbers");
      return { a, b };
    },
    async execute({ a, b }) {
      return { text: String(a + b) };
    },
  };
  const executeTools = createToolBatchExecutor([add], {
    onEvent: (event) => {
      trace.push(`${event.type}:${event.toolName}`);
    },
  });
  const result = await runAgentLoop({
    model,
    messages: [{ role: "user", content: "What is 20 + 22?" }],
    tools: [{ name: add.name, description: add.description }],
    executeTools,
    onEvent(event) {
      if (event.type === "model_event") trace.push(`model:${event.event.type}`);
      else if (event.type === "message_end") trace.push(`message_end:${event.message.role}`);
      else trace.push(event.type);
    },
  });
  const finalMessage = result.messages.at(-1);
  const text = finalMessage?.role === "assistant"
    ? finalMessage.content.find((block) => block.type === "text")?.text ?? ""
    : "";

  return { answer: text, transcript: result.messages, trace, modelCalls: model.calls.length };
}
