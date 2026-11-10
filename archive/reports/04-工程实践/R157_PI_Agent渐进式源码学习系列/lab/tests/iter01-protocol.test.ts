import assert from "node:assert/strict";
import test from "node:test";
import { ScriptedModel } from "../src/scripted-model.ts";
import type { AssistantMessage, ModelEvent } from "../src/types.ts";

test("Iter01: one provider-neutral text trace has stable event boundaries", async () => {
  const response: AssistantMessage = {
    role: "assistant",
    content: [{ type: "text", text: "42" }],
    stopReason: "stop",
  };
  const model = new ScriptedModel([response]);
  const context = { systemPrompt: "Be exact", messages: [{ role: "user" as const, content: "6 * 7?" }] };
  const events: ModelEvent[] = [];

  for await (const event of model.stream(context)) events.push(event);

  assert.deepEqual(
    events.map((event) => event.type),
    ["start", "text_start", "text_delta", "text_end", "done"],
  );
  assert.equal(events[2].type === "text_delta" && events[2].delta, "42");
  assert.deepEqual(model.calls, [context]);
  assert.deepEqual(events.at(-1), { type: "done", reason: "stop", message: response });
});

test("Iter01: tool calls use the same event vocabulary for every provider", async () => {
  const response: AssistantMessage = {
    role: "assistant",
    content: [{ type: "toolCall", id: "call-1", name: "add", arguments: { a: 20, b: 22 } }],
    stopReason: "toolUse",
  };
  const events: ModelEvent[] = [];

  for await (const event of new ScriptedModel([response]).stream({ messages: [] })) events.push(event);

  assert.deepEqual(
    events.map((event) => event.type),
    ["start", "toolcall_start", "toolcall_delta", "toolcall_end", "done"],
  );
  assert.equal(events[2].type === "toolcall_delta" && events[2].delta, '{"a":20,"b":22}');
});
