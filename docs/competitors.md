# Prior art: similar apps

Date: 2026-10-31
Purpose: learn from existing apps and shape design rules. This is not a market
analysis. Dhadkan is a portfolio project focused on engineering quality, so
this document stays short.

Legend: "observed" means I installed and used the app myself. "reported"
means it comes from an article or forum and is not verified by me.

## Apps reviewed

| App | Evidence | Offline | Sources cited | Heart attack + CPR | Hindi / Indian numbers | CPR metronome | Notes |
|---|---|---|---|---|---|---|---|
| Revive CPR | observed | No | not checked | CPR and AED guidance; reported: heart attack vs cardiac arrest content, AED locator | not checked | No | Easy interface, audio-visual guidance, built with cardiologists (reported) |
| First Aid (EXACT NAME AND PUBLISHER TO CONFIRM) | observed | not checked | not checked | broad first aid | language barrier | not checked | Very broad content, low rating |
| My SOS Family | observed | not checked | n/a | alerts emergency contacts only | not checked | n/a | Solves a different problem (alerting), complements Dhadkan |
| Rays First Aid CPR | reported (listicle) | reported: yes | not checked | CPR | not checked | not checked | Not tested |
| CPR Coach (MVP) | reported (Team-BHP forum) | not checked | not checked | CPR | reported: Hindi + 5 other languages | not checked | Solo-built, deterministic flow, no AI in the instructions |

## Findings (observed by me)

**Revive CPR**
- Strengths: solid project, easy-to-understand interface, audio-visual effects.
- Audio and visuals are sometimes out of sync.
- No metronome.
- Uses a 15-20 second video, with no imagery.
- Does not work offline.

**First Aid app**
- Strengths: has everything, literally.
- Low rating overall.
- Users describe it as a learning platform more than an emergency tool.
- Steps are shown one slide at a time, which is slow.
- Cluttered.
- Language barrier.

**My SOS Family**
- Sends an alert to emergency contacts. It does not tell a bystander what to do.

## Design rules taken from this

| Weakness seen | Dhadkan design rule |
|---|---|
| Audio and visuals drift apart | Schedule metronome audio and visuals from one Web Audio clock, not setInterval |
| No metronome | Metronome with the rate read from the content file (value and source) |
| Video only, no imagery | Simple static diagrams we draw ourselves; no video |
| Needs internet | Offline-first PWA, tested in airplane mode on a real phone |
| Cluttered, slow, one slide per step | Emergency mode: one screen, big buttons, 3 taps or fewer to CPR. Learning content kept out of the emergency path |
| Language barrier | English first, then Hindi and Marathi (Movement 6) |

## Feature triage (from my suggestions list)

| Idea | Decision |
|---|---|
| Offline application | Build (v1) |
| Metronome | Build (v1) |
| Voice-guided, spoken step prompts | Build (v1), text always shown as fallback |
| Rescuer-switch timer | Build (v1); interval comes from a sourced content value |
| Bundled emergency numbers | India only for v1; structure allows more later |
| Accelerometer rate feedback | v2, experimental; depth cannot be measured reliably |
| Practice mode with score | v2 |
| Post-event reports for paramedics | Excluded: needs stored personal data |

See ADR 0003 for the reasoning.

## How Dhadkan differs (claims I can prove)

- Open-source code and content.
- Every protocol step carries a source and page reference, enforced by schema
  validation and CI.
- Visible review status and open questions per protocol.
- Risk-awareness module using Indian data (IDRS, NFHS-5).
- Fully offline, with a metronome driven by sourced values.

Not claiming: first app, only offline app, or best app.

## To verify later (optional, keep it short)

- [ ] Confirm the exact name and publisher of the First Aid app above.
- [ ] Revive CPR: sources cited? Languages? Offline claim still true?
- [ ] Rays First Aid CPR and CPR Coach: install and fill the "not checked" cells.
