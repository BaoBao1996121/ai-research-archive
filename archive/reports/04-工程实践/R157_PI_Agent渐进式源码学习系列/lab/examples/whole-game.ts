import { runWholeGame } from "../src/whole-game.ts";

const result = await runWholeGame();

console.log(`Answer: ${result.answer}`);
console.log(`Model calls: ${result.modelCalls}`);
console.log("\nObservable trace:");
for (const [index, event] of result.trace.entries()) {
  console.log(`${String(index + 1).padStart(2, "0")}  ${event}`);
}

