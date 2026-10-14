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
| 5 | `Review.dc.html` | Monthly marks per principle (in line / drift), decisions with reason and outcome, add an outcome inline, "Practise this moment" on a drift |
| 2d | `LendTerms.dc.html` | Lend with terms: amount within your own limit, return date (one date or two parts), a written-agreement message to copy into LINE, reminders that Ethics drafts and you send, and the step if it's late, chosen in advance |
| 6 | `Practice.dc.html` | Practice sessions: 3–4 minute rehearsals built from your ledger, charter, calendar and drifts. You write your line and tick your own checklist; an optional sample line is shown as "one way, not the right way". Nothing is scored |

## Getting money back (lending flow)

Ethics can't make anyone repay. It makes the conditions for repayment explicit, so the follow-up is about the money, not the person:

1. **Limit first.** The amount is checked against your own principle (e.g. ¥10,000 per person at a time).
2. **Terms before money moves.** A return date, or two smaller parts, which the borrower can propose.
3. **In writing.** A drafted message asks for a reply of "OK", and you mark it agreed. Send the money by bank transfer or PayPay so Cost records it.
4. **Reminders.** Ethics drafts reminders for 3 days before, the day itself, and 3 days after. You send them; Ethics never contacts anyone.
5. **Late step decided in advance:** ask once for a new date, pause further lending, or close it as a gift.
6. **Older open loans** get their own conversation. "Ask for money back" in Practice rehearses it, and the Ledger links to it.

Entry points: after **Decide** on a lending option (A/B) → Lend with terms. After a declining option (C/D) → Practice.
The Ledger row "Agree a plan for the ¥55,000" → Practice. Today → Practice card. Review drift → Practise this moment.

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
