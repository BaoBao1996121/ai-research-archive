import assert from "node:assert/strict";
import test from "node:test";
import { runAgentLoop } from "../src/agent-loop.ts";
import { ScriptedModel } from "../src/scripted-model.ts";
import type { AssistantMessage, ToolResultMessage } from "../src/types.ts";

const answer = (text: string): AssistantMessage => ({
  role: "assistant",
  content: [{ type: "text", text }],
  stopReason: "stop",
});

test("Iter02: no tool call means one model turn and stop", async () => {
  const model = new ScriptedModel([answer("hello")]);
  const result = await runAgentLoop({
    model,
    messages: [{ role: "user", content: "hi" }],
  });

  assert.equal(result.reason, "stop");
  assert.deepEqual(result.messages.map((message) => message.role), ["user", "assistant"]);
  assert.equal(model.calls.length, 1);
});

test("Iter02: a tool result is fed back before the next model turn", async () => {
  const toolRequest: AssistantMessage = {
    role: "assistant",
    content: [{ type: "toolCall", id: "call-1", name: "add", arguments: { a: 20, b: 22 } }],
    stopReason: "toolUse",
  };
  const model = new ScriptedModel([toolRequest, answer("42")]);
  const executed: string[] = [];
  const executeTools = async (): Promise<ToolResultMessage[]> => {
    executed.push("call-1");
    return [{
      role: "toolResult",
      toolCallId: "call-1",
      toolName: "add",
      content: [{ type: "text", text: "42" }],
      isError: false,
    }];
  };

  const result = await runAgentLoop({
    model,
    messages: [{ role: "user", content: "20 + 22?" }],
    executeTools,
  });

  assert.deepEqual(executed, ["call-1"]);
  assert.equal(model.calls.length, 2);
  assert.deepEqual(model.calls[1].messages.map((message) => message.role), ["user", "assistant", "toolResult"]);
  assert.deepEqual(result.messages.map((message) => message.role), ["user", "assistant", "toolResult", "assistant"]);
});

test("Iter02: length-truncated tool arguments fail closed", async () => {
  const truncated: AssistantMessage = {
    role: "assistant",
    content: [{ type: "toolCall", id: "call-cut", name: "write", arguments: { path: "important.txt" } }],
    stopReason: "length",
  };
  const model = new ScriptedModel([truncated, answer("I will retry safely")]);
  let executions = 0;

  const result = await runAgentLoop({
    model,
    messages: [{ role: "user", content: "write the report" }],
    executeTools: async () => {
      executions += 1;
      return [];
    },
  });

  const toolResult = result.messages.find((message) => message.role === "toolResult");
  assert.equal(executions, 0);
  assert.equal(toolResult?.isError, true);
  assert.match(toolResult?.content[0].text ?? "", /token limit|truncated/i);
  assert.equal(model.calls.length, 2);
});
