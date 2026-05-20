---
name: justflip-create-flashcards
description: Create or modify importable JustFlip decks from CSV, TSV, pipe-delimited text, markdown notes, webpages, existing `.flashcards` JSON, or `.flashcards.zip` bundles. Use when asked to turn source material into app-importable flashcard decks for the JustFlip iOS app using the `flashcard-content` schema.
---

Create flashcard sets for the **JustFlip** app import format.

Read [reference.md](reference.md) before generating the final file so the JSON keys, version, and ZIP layout match the app contract.

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
5. Set language tags:
   - Always include `q_lang` and `a_lang` on every card when the languages vary card-by-card.
   - Otherwise include `deck_q_lang` and `deck_a_lang` at deck level.
   - Use BCP 47 codes such as `en`, `cs`, `es`, `de`.
6. Add spoken variants:
   - Use `{spoken form}` after unusual pronunciation, formulas, acronyms, and images.
   - Be generous because JustFlip supports audio learning and TTS.
7. Package the result:
   - JSON only: create or update a `.flashcards` file.
   - Media attached: create or update a `.flashcards.zip` with `content.json` plus root-level `images/`, `audio/`, and `pdfs/` folders.
8. Always emit top-level `format: "flashcard-content"`.
9. Default to `version: "1"` for the public content-creation format used by the current app spec and tests.
10. Do not generate UUID fields, timestamps, progress payloads, or the full exchange / backup schema unless the user explicitly asks for the backup format.

## Card quality rules

- Keep one fact, concept, translation, or question per card.
- Make the question self-contained.
- Prefer direct recall over vague prompts.
- Skip low-value trivia, duplicates, and filler.
- Do not invent facts not supported by the source.
- Use simple Markdown only.
- Use inline code or fenced code blocks for technical snippets when it improves readability.
- Keep answers concise enough to read comfortably on mobile.
- For music terminology, use `♯` and `♭`, not `#` or `b`.

## Math content

The app renders math directly from LaTeX in card text.

- Inline math: `$<latex>$`
- Inline math with spoken text: `$<latex>${<spoken form>}`
- Block math: `$$<latex>$$` on its own lines
- Block math with spoken text: `{<spoken form>}` immediately after the closing `$$`

Do not generate math images.

## Spoken text for TTS

Use `{...}` after eligible inline content to override how TTS reads it.

```markdown
$c^2${c squared}
[CRDT]{see-ar-dee-tee}
![image]{a red apple}
```

For vocabulary cards, add `{spoken form}` for non-obvious pronunciation when useful.

## Output contract

For single-deck content:

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
      "a": "obrázek, image{imidž} člověka"
    },
    {
      "q": "debt",
      "a": "dluh, debt{det}"
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
