"""Facts, suggestions and reviewed tips for the reply after "How was that?".

Everything here is decided by the app, not the model. The model only puts the chosen facts,
the suggestion and the tips into plain sentences, so every number and recommendation it can
use is traceable to a saved row or to a source below.

Tips were read on the source pages on 2026-10-27. Only what the page says is kept, in my
wording, and each is shown with its source link. None of them is a promise of effect.
"""

from collections import Counter
from datetime import datetime, timedelta

TIPS_REVIEWED = "2026-10-27"

SOURCES = {
    "nhs": {
        "name": "NHS: Breathing exercises for stress",
        "url": "https://www.nhs.uk/mental-health/self-help/guides-tools-and-activities/breathing-exercises-for-stress/",
    },
    "cleveland": {
        "name": "Cleveland Clinic: Diaphragmatic breathing",
        "url": "https://my.clevelandclinic.org/health/articles/9445-diaphragmatic-breathing",
    },
    "balban": {
        "name": "Balban et al. (2023), Cell Reports Medicine",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC9873947",
    },
}

TIPS = {
    "nhs_minutes": ("nhs", "The NHS guide suggests keeping the breathing going for at least 5 minutes, as part of a daily routine."),
    "nhs_belly": ("nhs", "The NHS guide suggests breathing in through the nose and out through the mouth, letting the breath go as deep into the belly as is comfortable, without forcing it."),
    "cleveland_hands": ("cleveland", "Cleveland Clinic suggests one hand on the upper chest and one just below the ribs, keeping the chest hand as still as possible."),
    "cleveland_start_small": ("cleveland", "Cleveland Clinic suggests starting small and building up the time gradually."),
    "balban_daily": ("balban", "A small 2023 Stanford study had people do 5 minutes of slow breathing with long out-breaths every day for 4 weeks."),
}

DAILY_MINUTES_GUIDE = 5  # NHS: "at least 5 minutes"


def _local_day(iso: str | None) -> datetime | None:
    if not iso:
        return None
    return datetime.fromisoformat(iso).astimezone()


def _count(n: int, noun: str) -> str:
    return f"{n} {noun}" if n == 1 else f"{n} {noun}s"


def build(session: dict, rows: list[dict], usual: dict | None = None) -> dict:
    """`session` is this session (with its self_report); `rows` are the person's saved sessions,
    newest first, from the read-only query. Returns facts, one suggestion, tips and sources."""
    now = datetime.now().astimezone()
    today = [r for r in rows if (d := _local_day(r["started_at"])) and d.date() == now.date()]
    week = [r for r in rows if (d := _local_day(r["started_at"])) and d >= now - timedelta(days=7)]
    seconds_today = round(sum((r["exercise_ms"] or 0) for r in today) / 1000)
    minutes_today = round(seconds_today / 60, 1)
    completed = [r for r in rows if r["status"] == "completed"]
    answers = Counter(r["self_report"] for r in rows[:10] if r["self_report"])
    earlier_answers = Counter(r["self_report"] for r in rows[1:10] if r["self_report"])
    stopped_early = session["status"] == "stopped"
    completed_six = sum(1 for r in completed[:5] if r["planned_breaths"] == 6)

    # Fact sentences written by the app, so every count in them is right. The model must copy at
    # least one word for word instead of restating the numbers itself (it once turned "4 finished,
    # 1 stopped" into "5 completed out of 5").
    facts = [f"You have finished {len(completed)} of your {_count(len(rows), 'saved session')}."]
    if earlier_answers:
        top, count = earlier_answers.most_common(1)[0]
        facts.append(f"Before this one, you answered '{top.replace('_', ' ')}' {_count(count, 'time')}.")
    if seconds_today:
        facts.append(f"You have about {minutes_today} minutes of breathing saved today.")
    if usual:
        facts.append(f"Your usual is {usual['breaths']} breaths with the {usual['cue']} cue.")

    # One suggestion, chosen by fixed rules. Each one is something the app can really do.
    if stopped_early and session["planned_breaths"] == 8:
        suggestion = ("6 breaths is shorter if 8 felt long. The Pause button keeps your place if you need a moment.", {"label": "Try 6 breaths", "breaths": 6, "cue": session["cue"]})
        tip_ids = ["cleveland_start_small"]
    elif stopped_early:
        suggestion = ("The Pause button keeps your place if you need a moment, and the text cue is there if the circle is distracting.", None)
        tip_ids = ["cleveland_start_small", "nhs_belly"]
    elif session["planned_breaths"] == 6 and completed_six >= 2 and session["self_report"] != "a_bit_calmer":
        suggestion = ("8 breaths (80 seconds) is there if you want a little longer next time.", {"label": "Try 8 breaths", "breaths": 8, "cue": session["cue"]})
        tip_ids = ["nhs_belly", "cleveland_hands"]
    elif minutes_today < DAILY_MINUTES_GUIDE:
        left = max(1, round(DAILY_MINUTES_GUIDE - minutes_today))
        so_far = f"You have about {minutes_today} minutes today. " if seconds_today else ""
        suggestion = (f"{so_far}Starting again adds about one more minute; about {left} more minutes would reach "
                      f"the 5 minutes the NHS guide mentions, only if you want to.",
                      {"label": "Another round", "breaths": session["planned_breaths"], "cue": session["cue"]})
        tip_ids = ["nhs_minutes"]
    else:
        suggestion = ("Your usual setting is ready whenever you come back.", None)
        tip_ids = ["balban_daily"]

    tips = [{"id": t, "text": TIPS[t][1], "source": TIPS[t][0]} for t in tip_ids]
    return {
        "facts": facts,
        "suggestion": suggestion[0],
        "action": suggestion[1],
        "tips": tips,
        "sources": [SOURCES[s] for s in dict.fromkeys(t["source"] for t in tips)],
        "answers_last_10": dict(answers),
    }
