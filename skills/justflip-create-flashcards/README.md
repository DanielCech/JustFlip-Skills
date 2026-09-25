# justflip-create-flashcards

AI skill for creating **JustFlip** import files.

## What it does

- Generates new decks in JustFlip's `flashcard-content` JSON schema.
- Produces JSON-only `.flashcards` files.
- Produces `.flashcards.zip` bundles when cards reference images, audio, or PDFs.
- Can transform CSV / TSV / pipe-delimited sources into the import format.
- Can update existing `.flashcards` or `.flashcards.zip` files.
- Draws card-sized Mermaid diagrams, and SVG figures converted to PNG, each as the whole card side.

## Install

```bash
npx skills add DanielCech/JustFlip-Skills
```

## Default output

Use this skill for **content creation** files that users can import into JustFlip:

- `.flashcards` — JSON only
- `.flashcards.zip` — `content.json` plus `images/`, `audio/`, `pdfs/`

The app also has a separate exchange / backup format that preserves UUIDs and study progress. This skill does **not** generate that format unless explicitly requested.

## Example prompts

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

```text
Create flashcards explaining the TCP handshake and HTTP caching. Use small diagrams where the flow is the point.
```

## References

- `SKILL.md` — agent instructions
- `reference.md` — format details
- `interest_icons.md` — curated SF Symbols available for interest icons
- `scripts/csv_to_flashcard.py` — delimited text → content JSON
- `scripts/build_flashcard_package.py` — validate/package JSON into `.flashcards` or `.flashcards.zip` (also checks diagram sides and rejects SVG media)
- `scripts/svg_to_png.sh` — render an SVG figure to a 1200 px PNG on a white plate
