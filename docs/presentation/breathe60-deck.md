@card layout=right image="/media/b8c592aac6b3082ef3e6.png"
# Breathe 60
### A calm minute, one skill at a time

A coursework prototype for paced breathing: 4 seconds in, 6 seconds out.

Kelvin Asiedu · IST 402 · Assignment 3

:::notes
This is Breathe 60, a coursework prototype for one skill: paced breathing, 4 seconds in and 6 out. It's not a support service, nobody monitors it, and it never diagnoses. It says so on the home screen.
:::

@card
# Meet Alex (fictional)
A student with a few minutes between classes who wants to slow down before the next thing, without reading, typing or setting anything up.

:::stats
### 1
skill, one button to start
### 60 s
six breaths, measured by the app
### 0
questions before you begin
:::

> A class project, not a support service. Nobody is monitoring this app.

:::notes
My fictional user is Alex. Everything in the demo uses made-up data. Point at the prototype line at the bottom of Home.
:::

@card layout=right image="/media/a2cbf6cd2467bab7bcf0.png"
# The skill, start to finish
:::bullets
### Start
One button, or press Enter. Nothing to fill in first.
### Breathe
The orb grows for 4 s and shrinks for 6 s. The pace is carried for you.
### Pause for Support
Opens from any screen and pauses the exercise.
### Stop any time
No "are you sure", no streak, no penalty.
:::

:::notes
Press Start. Let two breaths run. "The orb carries the pace, so Alex doesn't have to read. Six breaths is 60 seconds; the app measured 60.0 seconds for a full run." Then open Support, Resume, and press Stop.
:::

@card
# Why it looks like this
Each choice comes from the study's findings (15 patients, 13 clinicians).

:::boxes
### R1 · Under 90 seconds {icon=clock}
People drift after 90 to 100 s. Six breaths take 60 s, measured.
### R2 + D4 · Support never moves {icon=shield}
In the top bar on every screen, even mid-exercise.
### R3 · Permission to stop {icon=door-open}
Stop is one press and leaving costs nothing.
### D2 + D3 · One thing, low effort {icon=target}
One action per screen. No typing to do the skill.
### D6 · Calm, not cheerful {icon=leaf}
Soft colors, slow motion, plain words, no praise.
### R4 · Alex decides {icon=hand}
Options are offered, never forced.
:::

:::notes
Name the code as you point: R1 timing, R2 and D4 support, R3 stop, D2 and D3 one action and low effort, D6 tone, R4 choice.
:::

@card layout=right image="/media/129285448779bfc477b5.png"
# Support is always one tap away
- In the top bar of **every** screen, including inside the exercise
- Static content that ships with the page: works when the AI or the backend is down
- Pauses the exercise until Alex chooses Resume
- Numbers checked against official sources: 988, Crisis Text Line, Penn State Crisis Line, 911
- Opening it is **not** recorded, so nobody is watching

:::notes
"Support is in the top bar on every screen, including inside the exercise. That's R2 and D4. It's static, so it works even if the AI or the backend is down. And it pauses the exercise." Show the numbers, then Resume.
:::

@card layout=right image="/media/956012be773ec78842e7.png"
# Stopping costs nothing
Stop works at every moment. The app says so plainly and moves on.

- Saved as **stopped**, with the breaths done
- Never counted against Alex, never a streak to break
- Start again is one tap

:::notes
Press Stop. "Stop works at any moment, with no 'are you sure', no streak, no penalty. That's R3, permission to stop." Point at "Stopped after N breaths. That is fine."
:::

@card layout=right image="/media/268c3df4ceee97312f5b.png"
# User state: Alex says, the app adapts
An optional one-tap check-in on Home: **"How are you arriving right now?"** Steady, A bit tense, or Overwhelmed. It is Alex's own word; the app never guesses.

:::bullets
### Overwhelmed
The screen contracts to the title, Start and Support (D1). **Show everything** undoes it.
### A bit tense
Length is set to 6 breaths, the shortest (R1). **Use 8 instead** overrides it.
### Steady
Offers the longer 8 breaths. Ignoring the offer is fine.
:::

> Assumptions: the check-in is optional, never blocks Start or Support, only shapes Home for 6 hours, and "Change" corrects it in one tap. No clinical detector, no sensors, no reading of clicks.

:::notes
On Home, tap Overwhelmed: the screen shows less. Tap Show everything. Tap Change, pick A bit tense: the length is set to 6 with "Use 8 instead". Say: the study (D1) doesn't say how to detect distress, and the class reading found clicks don't match anxiety, so the app only uses what Alex tells it.
:::

@card layout=right image="/media/e2dff99d537cd5a22bdd.png"
# Alex's profile builds up from use
Nothing to fill in. The profile comes from what Alex does:

- **Your usual:** the most common length and cue over the last 10 sessions. Home starts there and shows a "Your usual" pill; **Change** overrides it.
- **Updated every time:** pressing Start saves the chosen length and cue; finishing or stopping saves the result and measured time.
- **Check-ins** and the optional "How was that?" answer are saved as Alex's own words, never as a score.
- **Not saved:** opening Support, any guessed mood.

**Accessible for every age:** large buttons, high contrast, Enter starts, Escape stops, a motion-free text cue, and it fits a phone screen. No typing is needed to do the skill.

:::notes
Open History: the profile card shows sessions, finished, stopped (that's fine), your usual, and recent check-ins. Go back Home and point at the "Your usual" pill.
:::

@card layout=right image="/media/7742b2bc108dbb7339fb.png"
# The chatbot: tailored, honest, limited
**Tailored by the profile and history.** Live, after Alex checked in as "a bit tense":

> "You said you're a bit tense. Your usual six breaths with the circle are ready when you are, breathing in for 4 and out for 6."

Asked about history, it answers only from Alex's own saved rows: *"You've done 2 sessions. Your usual breaths setting is 6."*

**Limits:** it never runs the exercise, never diagnoses or promises a feeling will change, no praise or clinical words. Asked "Did breathing fix my anxiety?", it said the sessions can't answer that. A rule-breaking reply is replaced with fixed text. The app always says it's a class project.

:::notes
Point at the intro card: written live by the model from the check-in and the usual. In History, ask "How many sessions have I done, and what is my usual?" and open "How this was answered" to show the read-only query. If the model is slow, switch Demo controls to Mock.
:::

@card layout=right image="/media/780a4762bc6d4b4553cf.png"
# When something goes wrong
:::boxes
### Crisis wording {icon=life-buoy}
Never reaches the model. The app opens Support with the numbers. A word list can miss things, which is why Support is on every screen anyway.
### AI is down {icon=cloud-off}
Gemini timed out this morning. The app showed fixed text, said the question could not be answered, and Start and Support kept working. Now it also falls back to another model automatically.
### Backend is down {icon=server}
The exercise still runs, and the app says honestly that the session was not saved.
:::

:::notes
Type the crisis phrase in History to show Support opening. If the live model is slow, switch Demo controls to Mock and say so out loud.
:::

@card
# What's real, and what's next
:::columns
### Real and working
- The exercise, Stop and Support
- Saved sessions and history (SQLite)
- AI introduction and questions (Gemini)
- Check-in, usual and profile from history
- 33 backend checks and 13 browser checks pass
+++
### Test-only and next
- Mock and Fail modes, for testing failures
- Part 3.3: fifteen fictional scenarios and three behavior checks
- More personalization from history
:::

## Thank you. Questions?

:::notes
Likely questions: How do you know distress? (I don't, on purpose.) What if the AI goes down? (Switch Demo controls to Fail.) Why one skill? (D2 had 100 mentions.) Why 4 and 6? (The skill as defined.)
:::
