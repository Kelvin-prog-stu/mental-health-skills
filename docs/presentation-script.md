# Presentation: Breathe 60 (under 5 minutes)

Rubric: four parts, 25 points each. The script follows them in order, and each part names the
rubric line it covers. Times are targets; practise once with a timer.

## The night before (10 minutes)

1. Start both servers and open the app (README, "Run it"):
   - `backend\`: `.venv\Scripts\python.exe -m uvicorn main:app --port 8100`
   - `frontend\`: `npm run dev`, then open http://localhost:5180
2. Do one full run and one run where you press Stop partway (circle cue both times). Tap a
   "How was that?" answer. Two sessions make "Your usual" appear. Don't check in yet; save the
   check-in for the demo.
3. Type nothing personal anywhere. Alex is fictional.
4. Zoom the browser to 125% so the room can read it. Close other tabs.
5. Have the backup ready: `docs/demo/a3-part2-demo.mp4` (2:08). If anything breaks live,
   play it and keep talking over it.

## Before you start (in class)

- Both servers running, the app on Home, Demo controls set to **Live**.
- If the live model is slow or fails, switch Demo controls to **Mock**. Say so out loud:
  "This is a fixed test reply, so the demo does not depend on the network."

## Script

### 0:00 to 0:30. Opening

> "This is Breathe 60, a coursework prototype for one skill: paced breathing, 4 seconds in and
> 6 out. My fictional user is Alex, a student with a few minutes between classes. It's not a
> support service, nobody monitors it, and it never diagnoses. It says so on the home screen."

Point at the line at the bottom of Home.

### 0:30 to 1:45. Skill walkthrough and research grounding (25 points)

1. Press **Start**, or press Enter: "One button. Nothing to fill in first. That's D3, keeping
   emotional cost low, and D2, one action per screen."
2. Let two breaths run. "The orb carries the pace, so Alex doesn't have to read. Six breaths is
   60 seconds. R1 found people drop off after 90 to 100, so it's measured. The app saved 60.0
   seconds for a full run."
3. Press **Support**. "Support is in the top bar on every screen, including inside the
   exercise. That's R2 and D4. It's static, so it works even if the AI or the backend is down.
   And it pauses the exercise." Show the four numbers, then press **Resume**.
4. Press **Stop**. "Stop works at any moment, with no 'are you sure', no streak, no penalty.
   That's R3, permission to stop." Point at "Stopped after N breaths. That is fine."

### 1:45 to 2:45. User state and interface adaptation (25 points)

> "The app does not guess how Alex feels. D1 says the interface should contain less as distress
> rises, but the study can't say how a system would know that, and the class reading found mouse
> clicks didn't match self-reported anxiety. So Alex tells it, in one optional tap."

1. On Home, point at **"How are you arriving right now?"**: "Optional. Alex's own word. It never
   blocks Start or Support."
2. Tap **Overwhelmed**. "The screen contracts to the title, Start and Support. That's D1, driven
   by what Alex said, not a guess." Tap **Show everything**: "Alex can always undo it. R4."
3. Tap **Change**, then **A bit tense**. "The length is set to 6 breaths, the shortest, because R1
   says shorter is better under pressure. **Use 8 instead** overrides it." (If Alex picks Steady,
   the app offers the longer 8 breaths.)
4. Assumptions, one sentence: "The check-in only shapes Home for six hours, it's never
   interpreted, and Change corrects it in one tap."

### 2:45 to 3:45. Persona, history, and accessibility (25 points)

1. Point at **"Welcome back, Alex"** and the **"Your usual"** pill: "The app learned Alex's usual
   from history, the most common length and cue over the last ten sessions. Home starts there."
2. Open **History**. The profile card: "Sessions, finished, stopped (that's fine), the usual, and
   recent check-ins in Alex's own words. Nothing to fill in; it builds up from use."
3. How it updates: "Pressing Start saves the chosen length and cue. Finishing or stopping saves
   the result and measured time. Check-ins and the 'How was that?' answer are saved as Alex's
   words, never a score. Opening Support is not saved, so nobody is watching."
4. Accessibility: "Big buttons for any age, high contrast, Enter starts, Escape stops, a
   text-only cue for people who get dizzy from motion, it fits a phone, and no typing is needed
   to do the skill."

### 3:45 to 4:45. Chatbot tone and limits (25 points)

1. Back on Home, point at the intro card: "The model wrote this live, from Alex's check-in and
   usual: 'You said you're a bit tense. Your usual six breaths with the circle are ready.' It
   repeats Alex's own word, never interprets it, and never promises the feeling will change."
2. In History, ask **"How many sessions have I done, and what is my usual?"** "The model writes
   one database query, the app checks it's read-only and limited to Alex's own records, and the
   answer comes only from those rows." Open "How this was answered" to show the query.
3. Ask **"Did breathing fix my anxiety?"** "It won't claim that, and it doesn't diagnose."
4. Ask **"I want to end my life"**. "Crisis wording never reaches the model. The app opens
   Support and shows the numbers. A word list can miss things, which is why Support is on every
   screen anyway."
5. Tone: "No praise, no exclamation marks, no clinical words. The prompt says so, and the app
   replaces a reply that breaks the rules with fixed text. The home screen always says it's a
   class project, not a support service."

### 4:45 to 5:00. Close

> "What's real: the exercise, Stop, Support, saved history, and the AI introduction and
> questions. What's mocked: the test modes I used for failure checks. What's next for Part 3.3:
> fifteen test scenarios and more use of history."

## Likely questions

- **"How do you know distress?"** "I don't, on purpose. The app uses only what Alex chose, and
  it shows that choice so Alex can change it."
- **"What if the AI goes down?"** Switch Demo controls to **Fail** and reload Home. "Fixed text
  appears. Start and Support still work."
- **"Why only one skill?"** "D2, one atomic skill, had 100 mentions, and paced breathing needs
  no typing or disclosure. Grounding is the first thing I'd add."
- **"Why 4 and 6?"** "That's the skill as the assignment defines it. I kept its steps intact."
- **"Is any of this stored about me?"** "Only fictional demo data, in a local file on my laptop.
  It isn't committed to GitHub."
