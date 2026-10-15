# Ethics app — chat memory

A record of the design conversation for the **Ethics** app, kept so a later session can carry on from here.

## Links and files

- Design canvas (private): https://claude.ai/artifact/8nbimY9Qtct9LXtN1P3kKw
- Repo: `celeritas7/temp`, branch `ccr-2d7674e7-y6vxua`, folder `ethics/`
  - `ethics/DESIGN.md`: the spec
  - `ethics/screens/*.dc.html`: one file per screen; `ethics/screens/canvas.json` lays them out on the canvas

## Who it's for

- A solo engineer living alone in Japan, working at an engineering company, in shared or rented housing.
- The app belongs to a personal app system, as a team in the Psychology department (crown level).
- **Akatsuki** is the integration broker. Ethics reads facts through it (calendar, Cost money data, contacts, location) and stores no raw data of its own.
- **Neurology** is the sister app. It flags believing things too easily and copying others under influence. Ethics must never become an authority to obey.
- **Cost** is the app that holds money lent and owed.

## Core rules (from the brief)

1. Assess situations, never people's character. Never label anyone as bad or untrustworthy; state facts such as "repayment has not happened on the last 3 loans".
2. Always offer options (2–4), never a verdict. Each option shows which values it honours, which it costs, and the likely outcome.
3. The user's own stated values are the only standard. If none applies, say so and ask for a new principle.
4. Fast: a check takes under a minute on a phone.
5. Every judgement shows its reasoning and can be overridden.

## Style decisions

- A clinical instrument look, not wellness. Near-black `#0C0C0E`, surface `#141417`.
- Muted gold accent `#C9A54A`. Neurology signals use violet `#A396E6`.
- IBM Plex Sans for UI text, IBM Plex Mono for facts, dates and amounts.
- No praise, guilt or ethics scores. Drift is a neutral hollow mark, never red.
- The user's Design System artifact was empty, so the look was built from the brief.

## Screens built (9 artboards, 390×844, all clickable)

| # | File | What it does |
| --- | --- | --- |
| 1 | `Main.dc.html` | Today: requests awaiting an answer, pending decisions, commitments due soon, a Practice card |
| 2a | `DecisionCheck.dc.html` | One-line situation, who is involved, stakes chips, facts from Akatsuki, elapsed timer |
| 2b | `DecisionOptions.dc.html` | Values touched with a "why" and "Doesn't apply here"; options A–D (unranked, none preselected); one-line reason + Decide; then Lend with terms (A/B) or Practice (C/D) |
| 2c | `Uncovered.dc.html` | "Your charter doesn't cover this": write a principle, or see options with consequences only; Neurology signal shown as information only |
| 2d | `LendTerms.dc.html` | Lend with terms: amount within your own limit, return date or two parts, written agreement drafted for LINE, reminders, the step if it's late chosen in advance |
| 3 | `Charter.dc.html` | 8 principles in the user's words, with versions, edit history and the decisions where each applied |
| 4 | `Ledger.dc.html` | Promises, what I owe, what I lent (from Cost); filter; link to rehearse asking for the ¥55,000 back |
| 5 | `Review.dc.html` | Monthly in-line/drift marks per principle; decisions with reason and outcome; "Practise this moment" on a drift |
| 6 | `Practice.dc.html` | Rehearsal sessions of 3–4 minutes with self-ticked checklists, unscored |

## Charter used as sample data

The user gave the first four. The last four were added by Claude as placeholders and should be replaced with the user's own wording.

1. I don't judge people.
2. I tell the truth when asked directly.
3. I pay my fair share of a shared mistake.
4. My employer's IP stays with my employer.
5. *(placeholder)* I lend only what I can afford not to get back. (v2 adds: ¥10,000 per person at a time.)
6. *(placeholder)* I keep a promise, or release it early and plainly.
7. *(placeholder)* I follow work rules even when no one checks.
8. *(placeholder)* I don't accept gifts that come with a request attached.

## Sample scenarios and placeholder names

- **Recruiter:** Ms. Mori asks the user to withdraw from today's 14:00 interview at Kōbe Seiki, which the user confirmed on 2 Oct.
- **Cleaning fee:** ¥18,000 was charged to Daichi; the user's fair share is still pending.
- **Loan request:** Kenji asks for ¥30,000. Three earlier loans (¥15,000 on 12 Mar, ¥20,000 on 3 Jun, ¥20,000 on 2 Aug), ¥55,000 in total, have not been returned.
- **Work event:** drinking pressure at the year-end party, Fri 23 Oct, in Umeda. This is the "not covered" case.
- **Resume:** which tools built at former employer Hoshino Kōgyō can be included.

All names, dates and amounts are placeholders.

## Second request: practice sessions and getting money back

The user asked for ways to improve, through practice sessions, and for lending to come with a way to get the money back.

- **Lend with terms** cannot force anyone to repay. It sets the conditions before any money moves:
  - The amount stays within the user's own limit.
  - A return date is set, or two smaller parts; the borrower can pick the date.
  - A written "OK" is asked for in a LINE message.
  - The money goes by bank transfer or PayPay, so Cost has a record.
  - Reminders go 3 days before, on the day, and 3 days after. Ethics drafts them; the user sends them.
  - The step if it's late is chosen in advance: ask once for a new date, pause further lending, or close it as a gift.
- **Practice** sessions, each built from the user's own data:
  - Ask for money back (Kenji's ¥55,000)
  - Set terms before lending
  - Say no once, plainly
  - Hold your limit under group pressure (party, 23 Oct)
  - Answer a direct question truthfully (from the 18 Sep drift)
- In a session the user writes their own line and ticks their own checklist. The sample line is labelled "one way to say it, not the right way".
- "Personality session" was taken to mean these practice sessions. Ask the user if they meant something else.

## Open items

- Replace the four placeholder principles and the sample names with real ones.
- Confirm what "personality session" was meant to cover.
- The canvas is private; share it from its Share menu if others need it.
- The screens have not been opened or rendered to check how they look.
