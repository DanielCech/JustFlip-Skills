# JustFlip Flashcard Content Reference

Use this reference when producing files for the JustFlip app's **content creation** import flow.

## Supported output types

- `.flashcards`: JSON only
- `.flashcards.zip`: ZIP bundle with `content.json` plus optional media

The app also accepts `.flashcard` / `.flashcard.zip` naming for content import, but this public skill defaults to `.flashcards` / `.flashcards.zip` because the current JustFlip codebase and tests use those names for generated examples while still falling back to the content schema during import.

## Required top-level JSON

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

### Interest icon

`interest_icon` is an optional top-level SF Symbol name for the interest. It is
the same value selected in the app’s Create Interest / Edit Interest picker.
Choose it from [interest_icons.md](interest_icons.md), using the exact symbol
name. The app applies it only when the imported interest has no icon yet, so a
user’s existing choice is preserved on re-import.

## Multi-deck JSON

```json
{
  "format": "flashcard-content",
  "version": "1",
  "interest": "Interest Name",
  "decks": [
    {
      "deck": "Deck A",
      "deck_q_lang": "en",
      "deck_a_lang": "cs",
      "cards": [
        {
          "q": "Question",
          "a": "Answer"
        }
      ]
    }
  ]
}
```

## Deck fields

- `deck`: required deck name
- `deck_icon`: optional SF Symbol name
- `deck_q_lang`: default BCP 47 language tag for questions
- `deck_a_lang`: default BCP 47 language tag for answers

## Card fields

- `q`: question text
- `a`: answer text
- `q_lang`, `a_lang`: per-card language overrides
- `note`: optional author / AI comment, ignored by import
- `q_image`, `q_audio`, `q_pdf`: question-side media filename
- `a_image`, `a_audio`, `a_pdf`: answer-side media filename
- `q_image_description`, `a_image_description`: text VoiceOver reads for that side's image
- `q_image_license`, `a_image_license`: licence / attribution shown from the card's info button
- `kind`: optional card kind — `"standard"` (default) or `"progressTracker"` (alias key: `type`)
- `progress`: optional, progress trackers only — starting completion, 0–100 (a value ≤ 1 is read as a 0…1 fraction); omitted means 0

At least one of `q` or `a` should be present.

## Progress trackers

A progress tracker is a non-review card: the app shows a name and a 0–100 % bar
the user adjusts themselves. Trackers never enter review sessions or SRS — they
track practiced skills (songs in a repertoire, techniques, exercises, long-term
goals) rather than recall.

```json
{ "q": "Blackbird", "a": "Fingerpicking, verse tempo 90",
  "kind": "progressTracker", "progress": 60 }
```

- `q` is the tracker **name** (required); `a` is an optional one-line description.
- Media fields, language tags, TTS spoken forms, LaTeX and code rules do not
  apply to trackers — keep them plain text.
- **Trackers are a JustFlip Pro feature and strictly opt-in**: emit them only
  after the user explicitly confirmed they want tracking (ask first when the
  material merely suggests it, mentioning the Pro requirement). Mixing
  flashcards and trackers in one deck is fine.
- On re-import, an existing tracker's stored progress is preserved — the file's
  `progress` value only seeds newly created trackers.

## Language tags

Always set language tags when practical for better TTS and audio-learning behavior.

```json
{
  "format": "flashcard-content",
  "version": "1",
  "interest": "English-Czech Vocabulary",
  "deck_q_lang": "en",
  "deck_a_lang": "cs",
  "cards": [
    {
      "q": "image",
      "a": "obrázek, image{imidž} člověka"
    }
  ]
}
```

## Math content

The app renders LaTeX directly from card text.

- Inline math: `$<latex>$`
- Inline math with spoken text: `$<latex>${<spoken form>}`
- Block math: `$$<latex>$$` on dedicated lines
- Block math with spoken text: put `{<spoken form>}` immediately after the closing `$$`

Do **not** generate math images.

## Code blocks & syntax highlighting

Card text is Markdown. The app renders fenced code blocks with native syntax highlighting driven by the fence language tag:

    ```swift
    let greeting = "Hello"
    ```

Supported languages (aliases in parentheses):

| Tag | Aliases |
| --- | --- |
| `swift` | — |
| `python` | `py`, `python3` |
| `javascript` | `js`, `jsx`, `node` |
| `typescript` | `ts`, `tsx` |
| `java` | — |
| `kotlin` | `kt`, `kts` |
| `c` | `h` |
| `cpp` | `c++`, `cc`, `cxx`, `hpp` |
| `csharp` | `cs`, `c#` |
| `objectivec` | `objc`, `objective-c`, `m` |
| `go` | `golang` |
| `rust` | `rs` |
| `ruby` | `rb` |
| `php` | — |
| `sql` | — |
| `bash` | `sh`, `shell`, `zsh` |
| `smalltalk` | `st`, `pharo`, `squeak` |
| `json` | — |
| `yaml` | `yml` |

Rules:

- Always tag fenced blocks with the language when you know it. Tags are case-insensitive identifiers (letters, digits, `+#._-`).
- A missing or unknown tag is safe: the block falls back to plain monospaced rendering. Prefer the real language name over omitting the tag.
- Keep code lines under roughly 30 characters so blocks fit a phone screen without wrapping.
- Do **not** embed pre-classified token spans (`language`/`spans`/`kind` JSON) in card text. Span payloads belong to JustFlip's internal rich-document format and are not accepted by the `flashcard-content` schema — the app tokenizes automatically from the fence tag.

## Spoken text for TTS

A `{...}` group overrides speech output for the content it follows — but the parser
consumes it after **exactly four hosts**. Anywhere else the braces fall through and
are drawn on the card.

| Host | Example |
| --- | --- |
| inline math | `$c^2${c squared}` |
| image | `![image]{a red apple}` |
| block-math closing fence | `$${V equals S p times v}` |
| bracketed text | `[CRDT]{see-ar-dee-tee}` |

`[visible]{spoken}` is the general-purpose form: it takes any text, and nests inside
emphasis because emphasis is a style toggle rather than a wrapper —
`*[F♯ major]{F sharp major}*` renders italic and speaks correctly.

```text
[debt]{det}               ✅
*[shi]{shee}*             ✅
debt{det}                 ❌ renders as "debt{det}"
*B minor*{B minor}        ❌ renders as "B minor{B minor}"
```

Braces inside fenced or inline code are safe — code is never inline-parsed, so a
Kotlin `"${name.length}"` template needs no escaping.

Reserve hints for what TTS actually gets wrong: `♯` and `♭`, formulas, acronyms,
romanised syllables, and degree lists like `[1 – ♭3 – 5]{one, minor third, perfect
fifth}`. A hint that repeats already-correct text is noise.

## Display blocks

A `:::` fence sets how a block is presented. Content inside parses with the normal
inline rules.

```text
::: hero
あ
:::
```

| Style | Rendering | Use for |
| --- | --- | --- |
| `hero` | ~4× body size, centred | A side that **is** a glyph, symbol or single short word being recognised |
| `center` | body size, centred | Short answers, captions |

- The style name is case-insensitive; `centre` is accepted for `center`.
- Blank lines inside a block split it into several paragraphs, all keeping the style.
- Notes belong **outside** the block so they stay body text.
- An unrecognised style renders as an ordinary paragraph, and an unterminated block
  keeps its content — so neither loses the author's text.
- Presentation only: `plainText`, search, export and the speech projection are
  identical with or without a display block.

## Mermaid diagrams

A fenced block tagged `mermaid` renders as a diagram. It is stored as an ordinary
code block, so older app versions show the source.

- Rendered families: `graph`/`flowchart`, `sequenceDiagram`, `stateDiagram` /
  `stateDiagram-v2`, `classDiagram`, `erDiagram`. The header is the first
  non-comment line and is case-insensitive.
- Anything else, a missing header, more than 60 lines or more than 2 000
  characters renders as code.
- A side containing a diagram must contain only that one fenced block.
- Card-size limits and forbidden syntax: see SKILL.md → Diagrams.

## Generated images

- Images must be raster (PNG preferred, JPEG for photos). SVG is not displayed;
  convert it first (`scripts/svg_to_png.sh`, which uses `rsvg-convert` or
  ImageMagick and renders 1 200 px wide on a white plate).
- A side whose text is empty and which has an image is laid out as a whole-side
  picture that fills the card.

## ZIP layout

```text
deck-name.flashcards.zip
├── content.json
├── images/
├── audio/
└── pdfs/
```

Rules:

- Media field values must be filenames, not paths.
- Image files belong in `images/` (PNG or JPEG — never SVG).
- Audio files belong in `audio/`.
- PDF files belong in `pdfs/`.
- Every referenced file must exist in the ZIP.

## Important scope boundary

This skill targets **content creation** imports only.

It does **not** generate the full JustFlip exchange / backup schema with UUIDs, timestamps, and SRS progress unless the user explicitly asks for that different format.
