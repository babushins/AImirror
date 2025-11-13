# utils/phrases.py
# Context-aware phrase generator with novelty protection.
#
# get_phrase({
#   "emotion": "happy|neutral|angry|sad|surprised",
#   "people": int|None,
#   "motion": float|None (0..1),
#   "tod": "morning|afternoon|evening|night",
#   "name": "Edgars"
# }) -> str

from __future__ import annotations
import random
from collections import deque
from typing import Dict, List, Optional

# ---------------- Module memory (prevents boring repeats) ----------------

_RECENT = deque(maxlen=24)     # recent fully-rendered phrases
_LAST_EMO = None               # last emotion we phrased for

def _novel(line: str) -> bool:
    return line not in _RECENT

def _remember(line: str) -> None:
    _RECENT.append(line)

# ---------------- Small libraries of mixable fragments -------------------

OPENERS = {
    "morning": [
        "Good morning", "Fresh start", "New day energy"
    ],
    "afternoon": [
        "Good afternoon", "Midday momentum", "Keeping pace"
    ],
    "evening": [
        "Good evening", "Winding down with focus", "Evening clarity"
    ],
    "night": [
        "Late but steady", "Quiet hours focus", "Night mode"
    ],
}

HAPPY = [
    "Love that vibe", "That smile suits you", "Nice energy",
    "Mood looks great", "Looking upbeat"
]

SURPRISED = [
    "Something unexpected?", "Caught off guard?", "Surprise face, huh?"
]

ANGRY = [
    "Anger is just energy", "Strong focus incoming", "Let’s channel it"
]

SAD = [
    "Let’s keep it gentle", "Small steps still count", "Steady and kind"
]

NEUTRAL = [
    "Ready when you are", "Calm and focused", "I’m with you"
]

ACTIONS = [
    "Want a {len}-minute focus block?",
    "Shall I set a {len}-minute timer?",
    "How about a tiny next step?",
    "Want a two-minute micro-plan?",
    "Prefer a quick summary of today?"
]

TAILS_PEOPLE = {
    0: ["It’s just us here.", "Room is all yours."],
    1: ["Looks like there’s someone with you.", "Seems you’re not alone."],
    "many": ["I see a busy background.", "Looks lively behind you."]
}

def _people_tail(people: Optional[int]) -> str:
    if people is None:
        return ""
    if people <= 0:
        return random.choice(TAILS_PEOPLE[0])
    if people == 1:
        return random.choice(TAILS_PEOPLE[1])
    return random.choice(TAILS_PEOPLE["many"])

def _motion_tail(motion: Optional[float]) -> str:
    if motion is None:
        return ""
    if motion > 0.22:
        return "Quite a bit of movement behind you."
    if motion > 0.12:
        return "Some activity in the background."
    if motion < 0.05:
        return "Background looks calm."
    return ""

def _choose_nonrepeat(cands: List[str]) -> str:
    # Prefer novel; fallback to anything if all seen
    novel = [c for c in cands if _novel(c)]
    return random.choice(novel if novel else cands)

def _emotion_bucket(em: Optional[str]) -> List[str]:
    if em == "happy": return HAPPY
    if em == "surprised": return SURPRISED
    if em == "angry": return ANGRY
    if em == "sad": return SAD
    return NEUTRAL

# ---------------- Public API ----------------

def get_phrase(ctx: Dict) -> str:
    """
    Build a fresh phrase from context and avoid repeating recent outputs.
    ctx keys: emotion, people, motion, tod, name
    """
    name = ctx.get("name") or "there"
    tod = ctx.get("tod") or "day"
    emotion = ctx.get("emotion") or "neutral"
    people = ctx.get("people")
    motion = ctx.get("motion")

    # light variety for timer length suggestions
    length = random.choice([10, 15, 20, 25])

    opener_pool = OPENERS.get(tod, ["Let's focus"])
    affect_pool = _emotion_bucket(emotion)

    opener = random.choice(opener_pool)
    affect = random.choice(affect_pool)
    action = random.choice(ACTIONS).format(len=length)

    tails = [ _people_tail(people), _motion_tail(motion) ]
    tails = [t for t in tails if t]  # drop empty

    # assemble 3–part message with mild shuffling for novelty
    parts = [
        f"{opener}, {name}.",
        f"{affect}.",
        f"{action}",
    ]
    # Occasionally change order of the middle bits
    if random.random() < 0.35:
        parts[1], parts[2] = parts[2], parts[1]

    if tails:
        parts.append(" ".join(tails))

    line = " ".join(parts)

    # Guard against trivial repetition
    if not _novel(line):
        # regenerate once with new draws
        opener = random.choice(opener_pool)
        affect = _choose_nonrepeat(affect_pool)
        action = random.choice(ACTIONS).format(len=length if random.random() < 0.5 else random.choice([12, 18, 30]))
        parts = [f"{opener}, {name}.", f"{affect}.", f"{action}"]
        if tails: parts.append(" ".join(tails))
        line = " ".join(parts)

    _remember(line)
    return line
