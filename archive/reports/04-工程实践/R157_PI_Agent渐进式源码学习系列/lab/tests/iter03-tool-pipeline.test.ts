import assert from "node:assert/strict";
import test from "node:test";
import { executeToolBatch, type AgentTool } from "../src/tool-pipeline.ts";
import type { ToolCall } from "../src/types.ts";

const call = (id: string, name: string, args: unknown): ToolCall => ({
  type: "toolCall",
  id,
  name,
  arguments: args,
});

test("Iter03: invalid arguments never execute; thrown tool errors become messages", async () => {
  let invalidExecutions = 0;
  const positive: AgentTool<{ value: number }> = {
    name: "positive",
    description: "Accept a positive number",
    validate(input) {
      const value = (input as { value?: unknown }).value;
      if (typeof value !== "number" || value <= 0) throw new Error("value must be positive");
      return { value };
    },
    async execute() {
      invalidExecutions += 1;
      return { text: "unreachable" };
    },
  };
  const explode: AgentTool = {
    name: "explode",
    description: "Throw on purpose",
    validate: (input) => input,
    async execute() {
      throw new Error("boom");
    },
  };

  const batch = await executeToolBatch(
    [call("bad", "positive", { value: -1 }), call("boom", "explode", {})],
    [positive, explode],
  );

  assert.equal(invalidExecutions, 0);
  assert.deepEqual(batch.results.map((result) => result.toolCallId), ["bad", "boom"]);
  assert.deepEqual(batch.results.map((result) => result.isError), [true, true]);
  assert.match(batch.results[0].content[0].text, /positive/);
  assert.match(batch.results[1].content[0].text, /boom/);
});

test("Iter03: parallel completion may reorder, but model-facing results do not", async () => {
  const delay = (milliseconds: number) => new Promise((resolve) => setTimeout(resolve, milliseconds));
  const makeTool = (name: string, milliseconds: number): AgentTool => ({
    name,
    description: name,
    validate: (input) => input,
    async execute() {
      await delay(milliseconds);
      return { text: name };
    },
  });

  const batch = await executeToolBatch(
    [call("slow", "slow", {}), call("fast", "fast", {})],
    [makeTool("slow", 30), makeTool("fast", 1)],
  );

  assert.deepEqual(batch.completionOrder, ["fast", "slow"]);
  assert.deepEqual(batch.results.map((result) => result.toolCallId), ["slow", "fast"]);
});

test("Iter03: one sequential tool forces the whole batch to run serially", async () => {
  let active = 0;
  let maxActive = 0;
  const makeTool = (name: string, executionMode?: "sequential"): AgentTool => ({
    name,
    description: name,
    executionMode,
    validate: (input) => input,
    async execute() {
      active += 1;
      maxActive = Math.max(maxActive, active);
      await new Promise((resolve) => setTimeout(resolve, 10));
      active -= 1;
      return { text: name };
    },
  });

  await executeToolBatch(
    [call("first", "first", {}), call("second", "second", {})],
    [makeTool("first", "sequential"), makeTool("second")],
  );

  assert.equal(maxActive, 1);
});

test("Iter03: Pi-faithful hooks can mutate validated args; hardening can revalidate", async () => {
  let executions = 0;
  const numberTool: AgentTool<{ value: number }> = {
    name: "number",
    description: "Needs a number",
    validate(input) {
      const value = (input as { value?: unknown }).value;
      if (typeof value !== "number") throw new Error("value must remain a number");
      return { value };
    },
    async execute(args) {
      executions += 1;
      return { text: String(args.value) };
    },
  };
  const mutateAfterValidation = async ({ args }: { args: unknown }) => {
    (args as { value: unknown }).value = "corrupted";
  };

  const faithful = await executeToolBatch(
    [call("faithful", "number", { value: 1 })],
    [numberTool],
    { beforeToolCall: mutateAfterValidation },
  );
  const hardened = await executeToolBatch(
    [call("hardened", "number", { value: 1 })],
    [numberTool],
    { beforeToolCall: mutateAfterValidation, revalidateAfterBeforeHook: true },
  );

  assert.equal(faithful.results[0].isError, false);
  assert.equal(hardened.results[0].isError, true);
  assert.equal(executions, 1);
});
