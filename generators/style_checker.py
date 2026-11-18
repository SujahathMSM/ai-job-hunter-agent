"""Deterministic check for wording that makes a CV or cover letter read as AI-generated.

Recruiters skim past stock phrases ("spearheaded", "results-driven", "I am writing to
express my interest"), stacks of buzzword adjectives, and bullets that all open with
the same verb. These are style problems, not factual ones: they are reported
separately from fact-check flags and never lower the grounding score.

Phrases that already appear in the candidate's own profile are not flagged: the
goal is to avoid wording the drafter introduced, not to rewrite the user's voice.
"""
import re
from collections import Counter
from typing import Dict, List, Optional

# phrase regex -> plain-language suggestion
STOCK_PHRASES: Dict[str, str] = {
    r"spearhead(?:ed|ing|s)?": "say what you did: 'led', 'started', 'built'",
    r"leverag(?:e|ed|es|ing)": "use 'used' or name what you did with it",
    r"utili[sz](?:e|ed|es|ing|ation)": "use 'use' / 'used'",
    r"results[- ]driven": "drop it and show a result instead",
    r"dynamic (?:professional|individual|team player)": "drop it",
    r"passionate about": "show the interest through what you built",
    r"proven track record": "state the actual result",
    r"track record of": "state the actual result",
    r"synerg(?:y|ies|istic)": "say who worked together on what",
    r"seamless(?:ly)?": "say what actually got easier or faster",
    r"cutting[- ]edge": "name the technology",
    r"state[- ]of[- ]the[- ]art": "name the technology",
    r"best[- ]in[- ]class": "drop it",
    r"world[- ]class": "drop it",
    r"game[- ]chang(?:er|ing)": "drop it",
    r"detail[- ]oriented": "show it with an example",
    r"self[- ]starter": "show it with an example",
    r"go[- ]getter": "drop it",
    r"think(?:ing)? outside the box": "describe the idea",
    r"hit the ground running": "say what you can start on",
    r"thought leader(?:ship)?": "drop it",
    r"value[- ]add(?:ed)?": "say what the value was",
    r"wealth of (?:experience|knowledge)": "say how many years, doing what",
    r"highly motivated": "drop it",
    r"strong work ethic": "drop it",
    r"fast[- ]paced environment": "describe the actual pace or scale",
    r"ever[- ]evolving": "drop it",
    r"in today'?s [a-z\- ]{0,30}(?:landscape|world|market)": "drop the opener",
    r"delve(?:d|s)? into": "use 'worked on' or 'studied'",
    r"testament to": "drop it",
    r"tapestry": "drop it",
    r"harness(?:ed|ing)? the power": "say what you used",
    r"i am writing to express my (?:strong )?interest": "open with why this company or role",
    r"i am (?:thrilled|excited|delighted) to apply": "open with why this company or role",
    r"please find (?:attached|enclosed)": "drop it; the CV is attached anyway",
}

# Buzzword adjectives that, stacked three or more in a row, read as generated filler.
BUZZ_ADJECTIVES = [
    "innovative", "scalable", "robust", "high-performance", "high-performing", "efficient",
    "reliable", "dynamic", "cutting-edge", "seamless", "modern", "comprehensive", "holistic",
    "strategic", "impactful", "agile", "secure", "resilient",
]
_ADJ = "(?:" + "|".join(re.escape(a) for a in BUZZ_ADJECTIVES) + ")"
_STACK_RE = re.compile(rf"\b{_ADJ}(?:\s*,\s*|\s+and\s+|,\s*and\s+){_ADJ}(?:(?:\s*,\s*|\s+and\s+|,\s*and\s+){_ADJ})+\b", re.I)

_COMPILED = [(re.compile(rf"\b{pat}\b", re.I), tip) for pat, tip in STOCK_PHRASES.items()]

# Plain-language list of the phrases, for drafting prompts.
PROMPT_AVOID_LIST = (
    "spearheaded, leveraged, utilized, results-driven, passionate about, proven track record, "
    "synergy, seamless, cutting-edge, state-of-the-art, world-class, detail-oriented, self-starter, "
    "fast-paced environment, wealth of experience, highly motivated, delve, testament to, "
    "'I am writing to express my interest', 'I am excited to apply'"
)

STYLE_RULES_FOR_PROMPT = f"""HUMAN-SOUNDING WRITING RULES:
- Write the way the candidate would: plain, specific, concrete. Reuse their own phrasing from the profile where possible.
- Never use these stock phrases: {PROMPT_AVOID_LIST}.
- Don't stack buzzword adjectives ("innovative, scalable, robust solution"); name what was built instead.
- Vary bullet structure and length; don't start every bullet with the same verb or follow one fixed "verb + metric + impact" template.
- Cover letters: no generic opener; start with something specific to this company or role."""


def find_style_issues(sections: Dict[str, str], profile_corpus: str = "",
                      bullets: Optional[List[str]] = None) -> List[Dict[str, str]]:
    """Return style flags: {type, claim, section, detail}. profile_corpus is the
    lowercased profile text; phrases found there are treated as the user's own words."""
    corpus = (profile_corpus or "").lower()
    flags: List[Dict[str, str]] = []
    seen = set()

    def add(kind: str, claim: str, section: str, detail: str):
        key = (kind, claim.lower())
        if key not in seen:
            seen.add(key)
            flags.append({"type": kind, "claim": claim, "section": section, "detail": detail})

    for section, text in sections.items():
        if not text:
            continue
        for regex, tip in _COMPILED:
            for m in regex.finditer(text):
                phrase = m.group(0)
                if phrase.lower() in corpus:
                    continue
                add("ai_cliche", phrase, section, f"Stock phrase that reads as AI-written; {tip}.")
        for m in _STACK_RE.finditer(text):
            phrase = m.group(0)
            if phrase.lower() not in corpus:
                add("stacked_adjectives", phrase, section,
                    "Three or more buzzword adjectives in a row; name what was built instead.")

    openers = Counter()
    drafted = [b for b in (bullets or []) if str(b).strip().lower() not in corpus]
    for b in drafted:
        words = re.findall(r"[A-Za-z][A-Za-z\-]+", str(b))
        if words:
            openers[words[0].lower()] += 1
    for verb, count in openers.items():
        if count >= 3 and len(drafted) >= 4:
            add("repeated_opener", verb.capitalize(), "work bullets",
                f"{count} bullets start with '{verb.capitalize()}'; vary how bullets open.")
    return flags
