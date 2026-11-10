export type StopReason = "pending" | "stop" | "length" | "toolUse" | "error" | "aborted";

export type TextContent = {
  type: "text";
  text: string;
};

export type ToolCall = {
  type: "toolCall";
  id: string;
  name: string;
  arguments: unknown;
};

export type UserMessage = {
  role: "user";
  content: string;
};

export type AssistantMessage = {
  role: "assistant";
  content: Array<TextContent | ToolCall>;
  stopReason: StopReason;
  errorMessage?: string;
};

export type ToolResultMessage = {
  role: "toolResult";
  toolCallId: string;
  toolName: string;
  content: TextContent[];
  isError: boolean;
};

export type Message = UserMessage | AssistantMessage | ToolResultMessage;

export type ModelContext = {
  systemPrompt?: string;
  messages: Message[];
  tools?: Array<{ name: string; description: string }>;
};

export type ModelEvent =
  | { type: "start"; partial: AssistantMessage }
  | { type: "text_start"; contentIndex: number; partial: AssistantMessage }
  | { type: "text_delta"; contentIndex: number; delta: string; partial: AssistantMessage }
  | { type: "text_end"; contentIndex: number; content: string; partial: AssistantMessage }
  | { type: "toolcall_start"; contentIndex: number; partial: AssistantMessage }
  | { type: "toolcall_delta"; contentIndex: number; delta: string; partial: AssistantMessage }
  | { type: "toolcall_end"; contentIndex: number; toolCall: ToolCall; partial: AssistantMessage }
  | { type: "done"; reason: "stop" | "length" | "toolUse"; message: AssistantMessage }
  | { type: "error"; reason: "error" | "aborted"; error: AssistantMessage };

export interface ModelAdapter {
  stream(context: Readonly<ModelContext>): AsyncIterable<ModelEvent>;
}

