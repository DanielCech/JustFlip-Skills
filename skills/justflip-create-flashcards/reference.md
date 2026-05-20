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

At least one of `q` or `a` should be present.

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

## Spoken text for TTS

Use `{...}` after eligible inline content to override speech output.

```text
$c^2${c squared}
[CRDT]{see-ar-dee-tee}
![image]{a red apple}
```

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
- Image files belong in `images/`.
- Audio files belong in `audio/`.
- PDF files belong in `pdfs/`.
- Every referenced file must exist in the ZIP.

## Important scope boundary

This skill targets **content creation** imports only.

It does **not** generate the full JustFlip exchange / backup schema with UUIDs, timestamps, and SRS progress unless the user explicitly asks for that different format.
