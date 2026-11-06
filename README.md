# GenAI-Engineer---Content-Systems

# Self-Evaluating Lesson Generator (Intro to RAG)

An agentic loop that **writes** a beginner lesson, **judges** it with hard pass/fail checks, and **rewrites** it until it passes (max 3 attempts).

Target learner: 12th-grade graduate from India, non-English-medium, zero AI background.

## How it works

```
topic -> WRITER -> EDITOR (8 pass/fail checks) -> all pass? -> save lesson
                      |  fail
                      +-- send reasons back to WRITER (max 2 retries)
```

- **Writer**: one model call that writes the lesson from the fact sheet.
- **Editor**: a separate model call plus plain-code checks. It never writes, it only judges.
- **Rejection log**: `rejection_log.json` records what failed on each attempt.
- **Memory**: `lessons_learned.json` counts failures across runs. The top 3 are added to the next writer prompt (self-evolving).

## The 8 checks (no partial credit)

| Type | Check |
|------|-------|
| Code | Average sentence length is 15 words or fewer |
| Code | All 5 headings present (What is it, Why it matters, How it works, Example, Recap) |
| Model | `grounded`: matches the fact sheet |
| Model | `jargon_defined`: every term explained on first use |
| Model | `analogy`: one real-life analogy |
| Model | `example`: one worked example |
| Model | `flow`: problem, idea, steps, example, recap |
| Model | `beginner_level`: understandable with zero background |

## Design choices

- **Separate editor**: a writer that grades itself tends to approve itself.
- **Fact sheet**: the editor checks claims against my own facts, not its memory.
- **Code + model checks**: code checks are cheap and cannot be argued with.
- **Retry cap**: the loop always ends, so cost is predictable.
- **Memory**: repeated failures improve future prompts, not just retries.

## Setup

1. Install Python 3.10+
2. `pip install google-genai`
3. Get a free key at https://aistudio.google.com/apikey
4. Set it (Windows Command Prompt): `set GEMINI_API_KEY=your_key`
   (Mac/Linux: `export GEMINI_API_KEY=your_key`)

## Run

```
python main.py
```

Press Enter for the default topic. Outputs: `lesson.md`, `rejection_log.json`, `lessons_learned.json`.

**Demo of the evaluator catching an error** (plants a false sentence on attempt 1):

```
set BREAK=1
python main.py
```

## Files

- `main.py`: the whole loop
- `fact_sheet.txt`: true statements about RAG used for grounding
