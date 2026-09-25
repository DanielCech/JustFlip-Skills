---
name: justflip-create-flashcards
description: Create or modify importable JustFlip decks from CSV, TSV, pipe-delimited text, markdown notes, webpages, existing `.flashcards` JSON, or `.flashcards.zip` bundles. Use when asked to turn source material into app-importable flashcard decks for the JustFlip iOS app using the `flashcard-content` schema.
---

Create flashcard sets for the **JustFlip** app import format.

Read [reference.md](reference.md) and [interest_icons.md](interest_icons.md) before generating the final file so the JSON keys, version, icon choice, and ZIP layout match the app contract.

## Workflow

1. Identify the source type.
2. If modifying an existing file:
   - **`.flashcards` (JSON):** read the file directly and apply changes to the JSON structure.
   - **`.flashcards.zip`:** extract the ZIP to a temporary directory, read `content.json`, apply changes, then repackage using `scripts/build_flashcard_package.py` or `zip -r`.
3. Choose the simplest reliable path for new content:
   - Structured Q/A data in CSV, TSV, or `|`-delimited text: use `scripts/csv_to_flashcard.py`.
   - Markdown, notes, article text, or webpage content: read the source, extract the learning points yourself, then write the JSON manually.
4. Decide deck structure:
   - Use a single deck when the source is one coherent topic.
   - Use multi-deck JSON when the source naturally splits into sections, chapters, or categories.
5. Choose an interest icon:
   - For every newly created deck, proactively suggest an interest icon based on the subject. Give one primary suggestion and, when useful, up to two alternatives from [interest_icons.md].
   - Put the selected SF Symbol name in the top-level `interest_icon` field. Use the exact symbol name, not the display label or a Unicode emoji.
   - If the user does not choose among the suggestions, use the primary suggestion and mention it in the result summary. Do not use the generic `square.stack.3d.up` unless the subject is genuinely generic or no better match exists.
   - For an existing deck, preserve its current icon unless the user asks to change it. On re-import, JustFlip preserves an existing user-selected interest icon.
   - The catalog is the set currently shown by the app’s Create/Edit Interest picker; do not invent SF Symbol names outside it.
6. Set language tags:
   - Always include `q_lang` and `a_lang` on every card when the languages vary card-by-card.
   - Otherwise include `deck_q_lang` and `deck_a_lang` at deck level.
   - Use BCP 47 codes such as `en`, `cs`, `es`, `de`.
7. Add spoken variants:
   - A `{spoken form}` hint only works when it **directly follows a host**: inline
     math `$…${…}`, an image `![id]{…}`, a block-math closing fence `$${…}`, or
     bracketed text `[visible]{spoken}`. After plain text or `*italic*` the braces
     are printed on the card — a real bug, so never write `debt{det}`.
   - `[visible]{spoken}` is the general-purpose form and works inside emphasis:
     `*[F♯ major]{F sharp major}*`.
   - Add hints for what TTS gets wrong — `♯`/`♭`, formulas, acronyms, romanised
     syllables, degree lists — not to repeat text that already reads correctly.
8. Choose a display for glyph-only sides:
   - When a whole side **is** a character, symbol or single short word to be
     recognised — kana, kanji, an alphabet, a chemical symbol, an IPA sign, a note
     name — wrap it in a `::: hero` block so it renders large and centred instead
     of small in the corner of an empty card.
   - `::: center` is the same centring at body size.
   - Never for a sentence, a definition or anything with more than a few words.
9. Choose a visual only when the picture *is* the knowledge — a process, a state
   machine, a message exchange, a geometric figure, a schematic. Use a Mermaid
   diagram when one of the supported families fits and stays card-sized;
   otherwise draw an SVG and convert it to PNG. A side that holds a diagram or a
   generated image holds **nothing else**. See [Diagrams](#diagrams-mermaid) and
   [Generated images](#generated-images-svg--png).
10. Package the result:
   - JSON only: create or update a `.flashcards` file.
   - Media attached: create or update a `.flashcards.zip` with `content.json` plus root-level `images/`, `audio/`, and `pdfs/` folders.
11. Always emit top-level `format: "flashcard-content"`.
12. Default to `version: "1"` for the public content-creation format used by the current app spec and tests.
13. Do not generate UUID fields, timestamps, SRS/review-history payloads, or the full exchange / backup schema unless the user explicitly asks for the backup format. (The per-card `progress` field on progress trackers is fine — see below.)
14. **Progress trackers are a JustFlip Pro feature — never emit them by default.** Emit cards with `"kind": "progressTracker"` (where `q` is the tracker name, `a` an optional one-line description, `progress` the starting completion 0–100; omit for 0) only after explicit confirmation: if the user directly asks for progress/practice tracking, proceed; if the material merely suggests it (a setlist, exercise plan, technique checklist), ask first and mention that trackers require JustFlip Pro, offering plain flashcards as the alternative. When a delivered deck contains trackers, note in the summary that managing them in the app requires JustFlip Pro. Trackers never enter review sessions; keep them plain text (no media, TTS, LaTeX, or code). Mixing flashcards and trackers in one deck is fine. Details in [reference.md](reference.md).

## Card quality rules

- Keep one fact, concept, translation, or question per card.
- Make the question self-contained.
- Prefer direct recall over vague prompts.
- Skip low-value trivia, duplicates, and filler.
- Do not invent facts not supported by the source.
- Use simple Markdown only.
- Use inline code or fenced code blocks for technical snippets when it improves readability. Always tag fenced blocks with the language so the app can syntax-highlight them.
- Keep answers concise enough to read comfortably on mobile.
- Do not put more than one large image on a card side. If combining text with a large image, keep the text brief enough for both to fit comfortably together. If the text is substantial, put the image and explanation on separate sides or split the material into multiple cards.
- A side holding a Mermaid diagram or a generated (SVG → PNG) image holds nothing else — no heading, caption, question text or note. Put the question on the other side.
- For music terminology, use `♯` and `♭`, not `#` or `b`.

## Math content

The app renders math directly from LaTeX in card text.

- Inline math: `$<latex>$`
- Inline math with spoken text: `$<latex>${<spoken form>}`
- Block math: `$$<latex>$$` on its own lines
- Block math with spoken text: `{<spoken form>}` immediately after the closing `$$`

Do not generate math images.

## Code blocks & syntax highlighting

The app syntax-highlights fenced code blocks natively, driven by the fence language tag.

- Always put the language tag right after the opening fence (```` ```swift ````).
- Supported tags and aliases are listed in [reference.md](reference.md). Unknown or missing tags safely fall back to plain monospace — prefer the real language name over omitting the tag.
- Keep code lines under ~30 characters so blocks fit a phone screen without wrapping.
- Never embed pre-classified token spans (`language`/`spans` JSON) in `q`/`a` text. The `flashcard-content` schema carries plain Markdown only; the app tokenizes from the language tag.

## Diagrams (Mermaid)

A ```` ```mermaid ```` fence is drawn as a picture on the card. Use one only when
the *structure* is what the learner must recall — a flow, a state machine, a
message exchange, an inheritance. Facts that read fine as a sentence or a list stay
text.

**The diagram is the whole side.** No heading, no caption, no explanatory sentence
before or after it, no second diagram, no image. The other side carries the
question or the explanation:

```json
{
  "q": "What happens to a card after you grade it?",
  "a": "```mermaid\ngraph TD\n  A[Graded] --> B{Recalled?}\n  B -->|Yes| C[Interval grows]\n  B -->|No| D[Relearn]\n```"
}
```

**Only diagrams that fit a card.** A card face on a phone is about 330 × 250 pt and
labels must stay ≥ 10 pt without zooming. Measured limits:

| Family | Header | Stay within |
| --- | --- | --- |
| Flowchart | `graph TD` (preferred) or `graph LR` | ≤ 6 nodes, ≤ 3 levels deep, ≤ 3 side by side |
| Linear chain | `graph LR` | ≤ 4 steps |
| Sequence | `sequenceDiagram` | ≤ 3 participants, ≤ 4 messages |
| State | `stateDiagram-v2` | ≤ 4 states (plus `[*]`), ≤ 5 transitions |
| Class | `classDiagram` | ≤ 3 classes, ≤ 2 members each |
| ER | `erDiagram` | **Avoid** — always lays out too wide; use a flowchart |

- Labels: 1–3 words, ≤ ~16 characters. Put detail on the other side, not in a node.
- Too big? Split it into several cards (one per branch or stage), or simplify. Never
  rely on the zoom button to make a diagram readable.
- The app may lay a `TD` flowchart out left-to-right to fit the card; write the
  direction that reads naturally and let it.
- Do **not** use: `style`, `classDef`, `linkStyle`, colours, `%%{init}%%`, `<br>`,
  HTML, `click`, icons, `subgraph`. Colours break dark mode and themes; the rest is
  unsupported or wastes space.
- Unsupported families — `pie`, `gantt`, `mindmap`, `timeline`, `gitGraph`,
  `journey`, `xychart` — show as raw code. Use an SVG image instead.
- Speech reads the node labels, so write labels in the side's language.
- The Apple Watch shows only small diagrams; larger ones stay on the phone.

`scripts/build_flashcard_package.py` rejects a diagram side with other content,
unsupported headers and styling, and warns when a diagram looks too big.

## Generated images (SVG → PNG)

When a visual is needed that Mermaid cannot draw — a geometric figure, a circuit, a
number line, a function graph, a labelled schematic, a timeline — write an SVG,
convert it to PNG and attach it with `q_image` / `a_image` in a `.flashcards.zip`.
**The app does not display SVG files**; ship only the PNG.

Design it to be read on a small card **without zooming**:

- Canvas `viewBox="0 0 800 600"` (4:3 landscape — a card face is wider than tall).
- Text ≥ 36 px in that viewBox (≈ 15 pt on a phone); prefer 40–44. Strokes ≥ 4 px.
- At most ~6 labels and a handful of shapes. One idea per image.
- Keep ≥ 24 px margin; nothing important near the edges.
- **Opaque light background** — first element `<rect width="800" height="600" fill="#FFFFFF"/>`
  — with dark ink (`#1C1C1E`) and at most one accent colour. The app draws no plate
  behind images, so transparent art vanishes in dark mode.
- Generic fonts only: `font-family="Helvetica, Arial, sans-serif"`. Write maths as
  Unicode text (`a² + b² = c²`), not LaTeX.
- Draw it yourself from the source's facts — do not trace copyrighted figures.

**The image is the whole side.** Leave that side's text empty (`"q": ""` with
`q_image`, or `"a": ""` with `a_image`) so the picture fills the card; put the
question or explanation on the other side. Add `q_image_description` /
`a_image_description` — it is what VoiceOver reads.

```bash
scripts/svg_to_png.sh images/pythagoras.svg images/pythagoras.png
```

```json
{
  "q": "Which relation holds between the sides of this triangle?",
  "a": "",
  "a_image": "pythagoras.png",
  "a_image_description": "Right triangle with legs a and b and hypotenuse c; a² + b² = c²"
}
```

Keep the `.svg` sources out of the ZIP. Maths formulas themselves are still LaTeX
in card text, never images.

## Display blocks

A block fenced with `:::` is presented differently from body text. Content inside
parses normally, so hints, emphasis and math still work.

```markdown
::: hero
あ
:::
```

| Style | Use for |
| --- | --- |
| `hero` | The side **is** the thing being recognised: a kana, kanji, letter, chemical symbol, IPA sign, note name, single short word. Renders very large and centred. |
| `center` | Body size, centred. |

Rules:

- One subject per block. A hero block holding a sentence defeats the purpose.
- Put explanatory notes **outside** the block so they stay body text:

```markdown
::: hero
[shi]{shee}
:::

Not *si* — the whole s-row shifts here.
```

- An unknown style name renders as an ordinary paragraph, so a deck stays readable
  on older app versions.

## Spoken text for TTS

A `{...}` hint overrides how TTS reads the content it follows — but only after one
of four hosts. Anywhere else the braces are drawn on the card.

```markdown
$c^2${c squared}          ✅ inline math
![image]{a red apple}     ✅ image
[CRDT]{see-ar-dee-tee}    ✅ bracketed text — the general-purpose form
*[F♯]{F sharp}*           ✅ nests inside emphasis
colonel{kər-nəl}          ❌ no host — renders as "colonel{kər-nəl}"
```

For vocabulary cards, bracket the word: `[debt]{det}`.

## Output contract

For single-deck content:

```json
{
  "format": "flashcard-content",
  "version": "1",
  "interest": "Interest Name",
  "interest_icon": "brain.head.profile",
  "deck": "Deck Name",
  "deck_q_lang": "en",
  "deck_a_lang": "cs",
  "cards": [
    {
      "q": "Question",
      "a": "Answer"
    }
  ]
}
```

For ZIP bundles:

```text
output.flashcards.zip
├── content.json
├── images/
├── audio/
└── pdfs/
```

## Examples

### Vocabulary

```json
{
  "format": "flashcard-content",
  "version": "1",
  "interest": "English Vocabulary",
  "deck": "B2 Level Words",
  "deck_q_lang": "en",
  "deck_a_lang": "cs",
  "cards": [
    {
      "q": "image",
      "a": "obrázek, [image]{imidž} člověka"
    },
    {
      "q": "debt",
      "a": "dluh, [debt]{det}"
    }
  ]
}
```

### Technical cards

```json
{
  "format": "flashcard-content",
  "version": "1",
  "interest": "SwiftUI",
  "deck": "Property Wrappers",
  "deck_q_lang": "en",
  "deck_a_lang": "en",
  "cards": [
    {
      "q": "What is `@State` used for?",
      "a": "Stores local mutable view state."
    },
    {
      "q": "How do you declare a two-way binding to a `@State` property?",
      "a": "Prefix it with `$`:\n\n```swift\nToggle(\"On\", isOn: $isOn)\n```"
    }
  ]
}
```

### Progress trackers (practice tracking)

```json
{
  "format": "flashcard-content",
  "version": "1",
  "interest": "Bass",
  "deck": "Songs",
  "cards": [
    {
      "q": "Blackbird",
      "a": "Fingerpicking, verse tempo 90",
      "kind": "progressTracker",
      "progress": 60
    },
    {
      "q": "Come Together",
      "kind": "progressTracker"
    }
  ]
}
```

## Example user requests

```text
Create a set of flashcards with 50 most common Czech phrases and their translations into English.
```

```text
Create a set of flashcards from the series '100 days of SwiftUI' https://www.hackingwithswift.com/100/swiftui, focus on days 50-70.
```

```text
Create a set of flashcards from the CSV file `czech-verbs.csv`. Use the `question` column for the front, `answer` for the back, group rows by the `deck` column, and generate a JustFlip `.flashcards` file.
```

```text
Create a set of image/audio-based flashcards for beginner animals. Each card should have the animal name on the question side, an image on the answer side, and pronunciation audio. Package the result as `.flashcards.zip`.
```

```text
Create a bilingual English-German vocabulary deck for everyday travel phrases. Put English on the question side, German on the answer side, and include pronunciation hints where useful.
```

## Notes for AI agents

- If the user asks for a JustFlip-importable deck, use this format by default.
- If the user asks for media, produce `.flashcards.zip`.
- If the user asks for backup/export of an existing JustFlip database including learning progress, this skill is not the default path; that is a separate exchange format.
