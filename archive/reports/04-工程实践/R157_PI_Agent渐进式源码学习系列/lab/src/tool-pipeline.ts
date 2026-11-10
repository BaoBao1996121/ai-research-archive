import type { ToolBatchExecutor } from "./agent-loop.ts";
import type { ToolCall, ToolResultMessage } from "./types.ts";

export type ToolOutput = {
  text: string;
  terminate?: boolean;
};

export type AgentTool<TArgs = unknown> = {
  name: string;
  description: string;
  prepareArguments?: (input: unknown) => unknown;
  validate: (input: unknown) => TArgs;
  execute: (args: TArgs) => Promise<ToolOutput>;
  executionMode?: "parallel" | "sequential";
};

export type ToolExecutionEvent =
  | { type: "tool_execution_start"; toolCallId: string; toolName: string; args: unknown }
  | { type: "tool_execution_end"; toolCallId: string; toolName: string; isError: boolean };

export type ToolPipelineOptions = {
  mode?: "parallel" | "sequential";
  beforeToolCall?: (input: { call: ToolCall; args: unknown }) => Promise<{ block?: boolean; reason?: string } | void>;
  afterToolCall?: (input: { call: ToolCall; output: ToolOutput; isError: boolean }) => Promise<ToolOutput | void>;
  revalidateAfterBeforeHook?: boolean;
  onEvent?: (event: ToolExecutionEvent) => void | Promise<void>;
};

export type ToolBatchResult = {
  results: ToolResultMessage[];
  events: ToolExecutionEvent[];
  completionOrder: string[];
};

export async function executeToolBatch(
  calls: ToolCall[],
  tools: AgentTool<any>[],
  options: ToolPipelineOptions = {},
): Promise<ToolBatchResult> {
  const events: ToolExecutionEvent[] = [];
  const completionOrder: string[] = [];
  const emit = async (event: ToolExecutionEvent): Promise<void> => {
    events.push(event);
    await options.onEvent?.(event);
  };
  type Prepared = { call: ToolCall; tool: AgentTool<any>; args: unknown };
  type Finalized = { call: ToolCall; output: ToolOutput; isError: boolean };

  const prepare = async (toolCall: ToolCall): Promise<Prepared | Finalized> => {
    await emit({
      type: "tool_execution_start",
      toolCallId: toolCall.id,
      toolName: toolCall.name,
      args: toolCall.arguments,
    });
    try {
      const tool = tools.find((candidate) => candidate.name === toolCall.name);
      if (!tool) throw new Error(`Tool ${toolCall.name} not found`);
      const prepared = tool.prepareArguments?.(toolCall.arguments) ?? toolCall.arguments;
      let args = tool.validate(prepared);
      const before = await options.beforeToolCall?.({ call: toolCall, args });
      if (before?.block) throw new Error(before.reason || "Tool execution was blocked");
      if (options.revalidateAfterBeforeHook) args = tool.validate(args);
      return { call: toolCall, tool, args };
    } catch (error) {
      return {
        call: toolCall,
        output: { text: error instanceof Error ? error.message : String(error) },
        isError: true,
      };
    }
  };

  const execute = async (prepared: Prepared): Promise<Finalized> => {
    let output: ToolOutput;
    let isError = false;
    try {
      output = await prepared.tool.execute(prepared.args);
    } catch (error) {
      output = { text: error instanceof Error ? error.message : String(error) };
      isError = true;
    }
    try {
      const after = await options.afterToolCall?.({ call: prepared.call, output, isError });
      if (after) output = after;
    } catch (error) {
      output = { text: error instanceof Error ? error.message : String(error) };
      isError = true;
    }
    return { call: prepared.call, output, isError };
  };

  const finalize = async (finalized: Finalized): Promise<ToolResultMessage> => {
    completionOrder.push(finalized.call.id);
    await emit({
      type: "tool_execution_end",
      toolCallId: finalized.call.id,
      toolName: finalized.call.name,
      isError: finalized.isError,
    });
    return {
      role: "toolResult",
      toolCallId: finalized.call.id,
      toolName: finalized.call.name,
      content: [{ type: "text", text: finalized.output.text }],
      isError: finalized.isError,
    };
  };

  const forceSequential = options.mode === "sequential" || calls.some((toolCall) =>
    tools.find((tool) => tool.name === toolCall.name)?.executionMode === "sequential"
  );
  let results: ToolResultMessage[];
  if (forceSequential) {
    results = [];
    for (const toolCall of calls) {
      const prepared = await prepare(toolCall);
      const finalized = "tool" in prepared ? await execute(prepared) : prepared;
      results.push(await finalize(finalized));
    }
  } else {
    const entries: Array<ToolResultMessage | (() => Promise<ToolResultMessage>)> = [];
    for (const toolCall of calls) {
      const prepared = await prepare(toolCall);
      if ("tool" in prepared) {
        entries.push(async () => finalize(await execute(prepared)));
      } else {
        entries.push(await finalize(prepared));
      }
    }
    results = await Promise.all(entries.map((entry) => typeof entry === "function" ? entry() : entry));
  }

  return { results, events, completionOrder };
}

export function createToolBatchExecutor(tools: AgentTool<any>[], options: ToolPipelineOptions = {}): ToolBatchExecutor {
  return async (calls) => (await executeToolBatch(calls, tools, options)).results;
}
