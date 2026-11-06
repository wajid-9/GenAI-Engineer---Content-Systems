import json, os, re, time
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-3.8-flash"  # change if Google renames it


def ask(prompt):
    for i in range(5):
        try:
            return client.models.generate_content(model=MODEL, contents=prompt).text
        except genai.errors.ServerError:
            print("Model busy, waiting...")
            time.sleep(10 * (i + 1))
    raise SystemExit("Model still busy. Try again later.")


topic = input("Topic (Enter = Introduction to RAG): ") or "Introduction to RAG"
facts = open("fact_sheet.txt").read()
try:
    memory = json.load(open("lessons_learned.json"))
except FileNotFoundError:
    memory = {}

# Most common past failures get added to the writer's prompt (self-evolving part)
top = sorted(memory, key=memory.get, reverse=True)[:3]
tips = "Past common mistakes to avoid: " + ", ".join(top) if top else ""

LLM_CHECKS = {
    "grounded": "Every claim matches the FACT SHEET. Nothing false or invented.",
    "jargon_defined": "Every technical term is explained in simple words on first use.",
    "analogy": "Has one real-life analogy a student in India would know.",
    "example": "Has one concrete worked example with a question and answer.",
    "flow": "Order is: problem, idea, steps, example, recap.",
    "beginner_level": "A 12th-grade, non-English-medium student with zero background can follow it.",
}

log, feedback = [], ""
for attempt in range(1, 4):  # 1 first try + 2 retries, then stop
    lesson = ask(
        f"Write a beginner lesson on: {topic}.\n"
        "Use very simple English, short sentences (under 12 words), no idioms.\n"
        "Use these headings: What is it, Why it matters, How it works, Example, Recap.\n"
        f"Use only these facts:\n{facts}\n{tips}\n"
        f"Fix these problems from the last try: {feedback}"
    )
    if os.getenv("BREAK") and attempt == 1:  # demo: plant a wrong sentence
        lesson += "\nRAG retrains the model on your documents."

    fails = {}
    sentences = [s for s in re.split(r"[.!?]+", lesson) if s.strip()]
    avg = len(lesson.split()) / max(len(sentences), 1)
    if avg > 15:
        fails["short_sentences"] = f"Average sentence is {avg:.0f} words."
    for h in ["What is", "Why", "How", "Example", "Recap"]:
        if h.lower() not in lesson.lower():
            fails["missing_" + h] = "Section not found."

    checks = "\n".join(f"- {k}: {v}" for k, v in LLM_CHECKS.items())
    raw = ask(
        "You are a strict editor. For each check answer PASS or FAIL, no partial credit.\n"
        f"FACT SHEET:\n{facts}\nCHECKS:\n{checks}\nLESSON:\n{lesson}\n"
        'Reply ONLY as JSON: {"check_name": {"result": "PASS or FAIL", "reason": "one line"}}'
    )
    verdict = json.loads(re.search(r"\{.*\}", raw, re.S).group())
    for k, v in verdict.items():
        if v["result"] == "FAIL":
            fails[k] = v["reason"]

    log.append({"attempt": attempt, "failed_checks": fails})
    print(f"Attempt {attempt}: {len(fails)} failed -> {fails}")
    if not fails:
        break
    feedback = json.dumps(fails)
    for k in fails:
        memory[k] = memory.get(k, 0) + 1

open("lesson.md", "w").write(lesson)
json.dump(log, open("rejection_log.json", "w"), indent=2)
json.dump(memory, open("lessons_learned.json", "w"), indent=2)
print("Saved lesson.md, rejection_log.json, lessons_learned.json")
