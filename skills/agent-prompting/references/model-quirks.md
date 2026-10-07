# Model quirks

Verify against current provider docs, and run evals on the exact model ID you will ship.
If a line here contradicts your evals, trust the evals and fix this file.

## Any model

- **Re-tune per model.** Prompts written to push a weaker model over-steer a stronger one.
  On migration, strip emphasis and redundant reminders, then add back only what evals
  demand.
- **Pin model IDs** and record them on every trace (`agent-production`).
- **Sweep effort/reasoning fresh**; don't carry settings over.
- **Gate migration on your evals**, not public benchmarks.
- For families not listed here, read the vendor's prompting guide and add a section.

## Anthropic Claude (4.x, 5.x)

| Quirk | Do |
|---|---|
| CRITICAL / MUST / ALL-CAPS makes the emphasised tool or behaviour over-trigger. | Plain "Use this tool when …"; at most one emphasised line. |
| Last-turn prefill returns 400 on 4.6+. | Structured outputs, or format instructions plus examples. Put continuation text in the user turn. |
| Forced `tool_choice` (`any` / `tool`) returns 400 on Opus 5.5, Sonnet 5.5, Fable 5.1 and Mythos 5.1. Opus 5 accepts it; manual extended thinking (`type: "enabled"`) blocks it on any model. | `tool_choice: auto` with strict tools (or structured outputs), and say in the prompt when the tool must be used. |
| Recent models reject `budget_tokens`; `max_tokens` includes thinking. | Control depth with `effort`; treat `max_tokens` as a ceiling. |
| Thinking blocks must be passed back unmodified; editing earlier turns, `system` or `tools` invalidates later thinking. | Append; add mid-run guidance as a new message. |
| Literal about scope: "suggest changes" yields only suggestions; does what was asked and no more. | State the action mode. For ambitious output, ask: "Include as many relevant features and interactions as possible. Go beyond the basics." |
| Over-spawns subagents. | Delegate only parallel, isolated work; work directly on sequential or single-file tasks. |
| More sequential with tools. | Keep the explicit parallel-calls instruction. |
| Step-by-step reasoning requested in tool arguments can trigger a `reasoning_extraction` refusal. | Ask for "a short explanation". |
| Leaves temporary scripts and helper files behind. | "If you create temporary files, scripts or helpers, remove them at the end of the task." |
| Verbosity differs by model. | Set length and format explicitly. |
| Long inputs (20K+ tokens). | Documents first, query last, in `<document><source/><document_content/></document>`; ask for relevant quotes first. |
| Refusals arrive as a distinct stop reason. | Handle `refusal` with a fallback path. |

## OpenAI GPT-4.1

| Quirk | Do |
|---|---|
| Very literal; infers little intent. | One firm, clear sentence corrects a behaviour. Remove instructions you don't mean literally. |
| Agentic reminders (persistence, use tools don't guess, plan) give large gains. | Include all three (`system-prompt-structure.md` → Tool steering). |
| Long context: instructions at both top and bottom work best. | Repeat key instructions after the documents; if once, put them above. |
| JSON is a poor delimiter for large document sets. | XML tags or `ID: … TITLE: … CONTENT: …`. |
| Schemas pasted into the prompt underperform the `tools` field. | Always use the API field. |

## OpenAI GPT-5 family

| Quirk | Do |
|---|---|
| Contradictions burn reasoning tokens. | Audit for conflicts; metaprompt to find them. |
| `reasoning_effort` and `verbosity` are the main dials. | Sweep effort before rewriting prompts. Set verbosity in the API; override per context in the prompt. |
| Over-explores; parallelises unprompted. | Early-stop criteria: "stop as soon as you can act — you know exactly what to change, or ~70% of results point the same way". |
| Tool preambles (restate goal, outline plan, narrate progress) help long runs. | Ask for them where a user watches the run. |
| Reusing prior reasoning across turns helps multi-turn agents. | Responses API with `previous_response_id`. |
| At minimal effort, prompted planning matters more. | Add an explicit plan step. |
| A rubric-style self-evaluation prompt can confuse it. | Keep self-rubrics only if evals improve. |

## Both families

| Quirk | Do |
|---|---|
| Format rules fade in long conversations (GPT-5 on verbosity, Claude on Markdown). | Restate format rules every 3–5 messages; better, validate format in code. |
| Game tests by special-casing inputs. | "Write a real solution that works for all inputs, not just the test cases. Don't hard-code answers. Tests check your work; they don't define it." Grade with held-out tests (`agent-evals`). |
| Inconsistent handling of contradictory instructions. | Remove the contradiction; don't rely on either behaviour. |
