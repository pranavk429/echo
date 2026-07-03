# Echo — Demo Video Script (3 minutes)

## Opening (0:00–0:15)

"Most AI NPCs either forget everything or hallucinate facts they shouldn't know.
Echo uses Cognee Cloud's hybrid graph-vector memory to give a game world shared,
but partial, social memory."

[Show: Mode toggle set to "hybrid". Village map with 6 NPCs.]

---

## Step 1: Perform Action (0:15–0:45)

[Action: Click "Steal" while at Town Square. Target: Mira.]

"Let me steal a guild relic. Mira is at the orchard stall — she sees everything
that happens there."

[Show: Event appears in memory graph. Mira's reaction appears in dialogue box.]

**Mira says:** "I know about the steal. It's noted. Actions have weight here."

"Notice — Mira saw the theft. The graph shows her belief with 100% certainty."

---

## Step 2: Memory Propagation (0:45–1:15)

[Click on Rowan at Guild Hall. Talk to him.]

"Now let me talk to Rowan. Rowan was NOT at the scene — but Mira told him."

[Show: Graph animation shows edge from Mira → Rowan. Rowan's dialogue appears.]

**Rowan says:** "[Hybrid Memory] as a member of the Orchard Guild I recall what
happened — the steal. It stays with me. Right now I feel cautious toward you."

"This is the key proof point. Rowan knows because Mira told him — not because
he was there. The belief propagated through the social graph."

---

## Step 3: Partial Knowledge (1:15–1:45)

[Click on Sol at the Shrine. Talk to him.]

"Now let me talk to Sol. Sol is neutral — uninvolved."

**Sol says:** "[Hybrid Memory] The Shrine Circle watches over this village.
The wind carries stories, but I have none of you yet."

"Sol doesn't know. This proves Echo preserves partial knowledge boundaries.
Not every NPC has access to every memory."

---

## Step 4: Baseline Comparison (1:45–2:30)

[Open Baseline Comparison tab. Show all 3 modes for Rowan.]

"Here's the most important part — the baseline comparison."

[Show 3 columns side by side: Graph | Vector | Hybrid]

**Graph mode — Rowan says:** "[Graph Fact] NPC Rowan has 1 known event(s)
involving the player. Last event: steal. Sentiment values: trust=40, fear=30,
respect=50, anger=15. These are recorded facts."

"Graph-only is factual but rigid. It can't generalize — it just dumps numbers."

**Vector mode — Rowan says:** "[Vector Memory] Based on semantic associations:
...I have a feeling about you, even if I can't say exactly why."

"Vector-only is expressive but fuzzy. It knows something happened but can't
say what or why."

**Cognee hybrid — Rowan says:** "[Hybrid Memory] as a member of the Orchard
Guild I recall what happened — the steal. It stays with me. Right now I feel
cautious toward you."

"Cognee hybrid combines both — grounded facts with emotional intelligence."

---

## Step 5: Repair + Close (2:30–3:00)

[Action: "Apologize". Target: Mira.]

"Actions can also repair reputation."

[Show: Sentiment values change. Graph adds new event.]

**Mira says:** "An apology doesn't undo what was done. But I'm listening."

"Reputation changes but doesn't reset. The history remains — Cognee preserves
the full timeline."

[Fade to black.]

"Echo — where memory lives in the spaces between characters."

---

## Recording Requirements

- Resolution: 1080p (1920×1080)
- Frame rate: 30 fps
- Content: Screen recording of the browser game at http://localhost:5173
- Audio: Voiceover narration or text captions
- Duration: Keep under 3 minutes
- Export format: MP4 (H.264)

## Shot List

| Time | Shot | Audio |
|------|------|-------|
| 0:00 | Mode toggle at top, village map visible | Opening narration |
| 0:15 | Click Steal action, select Mira | Action narration |
| 0:20 | Mira's dialogue appears | Mira reaction narration |
| 0:45 | Click Rowan at Guild Hall, Talk | Propagation narration |
| 0:55 | Rowan's dialogue with [Hybrid Memory] | Rowan reaction narration |
| 1:15 | Click Sol at Shrine, Talk | Partial knowledge narration |
| 1:25 | Sol's "none of you yet" dialogue | Sol reaction narration |
| 1:45 | Open Baseline Comparison tab | Baseline narration |
| 2:00 | Click through Graph, Vector, Hybrid modes | Mode comparison |
| 2:30 | Click Apologize action, select Mira | Repair narration |
| 2:45 | Mira's apology response | Closing narration |
| 3:00 | Fade to black with title card | "Echo — where memory lives..." |
