import type { AssistantMessage, ModelAdapter, ModelContext, ModelEvent } from "./types.ts";

export class ScriptedModel implements ModelAdapter {
  readonly calls: ModelContext[] = [];
  private readonly responses: AssistantMessage[];

  constructor(responses: AssistantMessage[]) {
    this.responses = [...responses];
  }

  async *stream(context: Readonly<ModelContext>): AsyncIterable<ModelEvent> {
    const snapshot: ModelContext = { ...context, messages: [...context.messages] };
    if (context.tools) snapshot.tools = [...context.tools];
    this.calls.push(snapshot);
    const response = this.responses.shift();
    if (!response) throw new Error("ScriptedModel has no response left");

    let partial: AssistantMessage = { role: "assistant", content: [], stopReason: "pending" };
    yield { type: "start", partial };

    for (const [contentIndex, block] of response.content.entries()) {
      if (block.type === "text") {
        partial = { ...partial, content: [...partial.content, { type: "text", text: "" }] };
        yield { type: "text_start", contentIndex, partial };
        partial = { ...partial, content: [...partial.content.slice(0, -1), block] };
        yield { type: "text_delta", contentIndex, delta: block.text, partial };
        yield { type: "text_end", contentIndex, content: block.text, partial };
      } else {
        partial = { ...partial, content: [...partial.content, block] };
        yield { type: "toolcall_start", contentIndex, partial };
        yield { type: "toolcall_delta", contentIndex, delta: JSON.stringify(block.arguments), partial };
        yield { type: "toolcall_end", contentIndex, toolCall: block, partial };
      }
    }

    if (response.stopReason === "error" || response.stopReason === "aborted") {
      yield { type: "error", reason: response.stopReason, error: response };
      return;
    }
    if (response.stopReason === "pending") throw new Error("A final scripted response cannot be pending");
    yield { type: "done", reason: response.stopReason, message: response };
  }
}
