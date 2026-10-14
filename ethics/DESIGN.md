# Ethics — design spec

Ethics is a team in the Psychology department (crown level) of the personal app system, alongside Neurology.
It helps act on your own stated values when a decision involves other people, money, honesty or obligations.
It does not supply a morality of its own.

Mockups: `screens/*.dc.html` (390×844 phone artboards; `screens/canvas.json` lays them out).

## What it owns, what it reads

| Ethics owns (stored) | Read live from Akatsuki (never stored) |
| --- | --- |
| Charter principles and their edit history | Calendar events |
| Decision records: situation line, people, stakes, values touched, options shown, choice, one-line reason, outcome | Money lent and owed (Cost) |
| Commitments (promises made) | Contacts |
| Value overrides ("doesn't apply here") | Location (e.g. last train home) |

Each fact shown on screen is labelled with its source and "read now, not kept".

## Rules, and where each screen enforces them

1. **Situations, not people.** The app has no field or label for a person's character. Facts are about the money or the request
   ("Repayment has not happened on the last 3 loans"). The check screen says "These describe the money, not the person".
2. **Options, not verdicts.** 2–4 options, each with *Honours / Costs / Likely* rows. They are listed in no particular order and none is preselected.
   "None of these — write my own option" is always offered.
3. **Your charter is the only standard.** Each value touched quotes your own wording and gives a one-line *Why*. You can set any value aside
   ("Doesn't apply here"), and the options update. If no principle applies, the check stops and says so (screen 2c). You can then write a
   principle or continue without one; without one, options show consequences only.
4. **Under a minute.** The check has two steps: one line plus chips, then pick and reason. An elapsed timer is always visible. People come from
   Contacts and money facts from Cost, so you type almost nothing.
5. **No authority.** No scores and no praise or guilt copy. Review shows marks for *in line* and *drift* in date order, with no percentages.
   A drift is shown with your reason at the time, the outcome, and any later edit to the principle.
6. **Neurology boundary.** Neurology signals (e.g. group pressure) appear in Neurology's violet. They are marked "information only" and never change the options.

## Screens

| # | Artboard | Purpose |
| --- | --- | --- |
| 1 | `Main.dc.html` | Today: requests awaiting your answer (with deadline and source fact), pending decision drafts, commitments due soon |
| 2a | `DecisionCheck.dc.html` | Describe: one line, who (Contacts), stakes (Money, Honesty, Work rules, Safety, A promise), facts read from Akatsuki |
| 2b | `DecisionOptions.dc.html` | Values touched with reasoning and override; options with trade-offs; reason + **Decide**; recorded state with undo and a 30-day outcome prompt |
| 2c | `Uncovered.dc.html` | No principle applies: shows which principles were checked and why each was ruled out, the Neurology signal, write a principle or continue without one |
| 3 | `Charter.dc.html` | Principles in your words, version, count of decisions, expandable edit history and examples |
| 4 | `Ledger.dc.html` | Promises, what I owe, what I lent and whether it came back (from Cost); filter All / Promises / I owe / Lent |
| 5 | `Review.dc.html` | Monthly marks per principle (in line / drift), decisions with reason and outcome, add an outcome inline |

## Visual system

- Ground `#0C0C0E`, surface `#141417`, hairline `#1F1F24`–`#3A3A40`. Same family as Neurology.
- Accent: muted gold `#C9A54A` (text on gold `#151107`). Neurology's signals use violet `#A396E6`.
- Ink `#ECEAE4`, secondary `#A9A69E`, tertiary `#8A877F`. All meet 4.5:1 on the ground.
- Drift is drawn as a neutral hollow square, never in red. Returned money is a muted green outline; unreturned money is neutral.
- Type: IBM Plex Sans for UI and IBM Plex Mono for facts, dates, amounts and labels. This gives a clinical, instrument-like feel.
- Touch targets are at least 44px, and tab bar items are 52px.

## Sample data covered

Recruiter withdrawal request (Today, Ledger promises) · cleaning-fee fair share (Today, Ledger, Charter examples) ·
repeat loan request (full Decision Check flow) · drinking pressure at a work event (uncovered flow) ·
resume and former employer's tools (Today draft, Charter IP principle, Review).
