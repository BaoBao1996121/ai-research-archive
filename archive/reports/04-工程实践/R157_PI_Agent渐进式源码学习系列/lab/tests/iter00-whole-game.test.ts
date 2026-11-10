import assert from "node:assert/strict";
import test from "node:test";
import { runWholeGame } from "../src/whole-game.ts";

test("Iter00: one observable whole game crosses model, tool, and model again", async () => {
  const result = await runWholeGame();

  assert.equal(result.answer, "The answer is 42.");
  assert.equal(result.modelCalls, 2);
  assert.deepEqual(result.transcript.map((message) => message.role), [
    "user",
    "assistant",
    "toolResult",
    "assistant",
  ]);
  assert.deepEqual(result.trace, [
    "agent_start",
    "turn_start",
    "model:start",
    "model:toolcall_start",
    "model:toolcall_delta",
    "model:toolcall_end",
    "model:done",
    "message_end:assistant",
    "tool_execution_start:add",
    "tool_execution_end:add",
    "tool_batch_end",
    "message_end:toolResult",
    "turn_start",
    "model:start",
    "model:text_start",
    "model:text_delta",
    "model:text_end",
    "model:done",
    "message_end:assistant",
    "agent_end",
  ]);
});
