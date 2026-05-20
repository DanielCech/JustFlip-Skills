# JustFlip Skills

Public AI skill repository for generating importable decks for the **JustFlip** iOS app.

## Install with skills.sh

```bash
npx skills add DanielCech/JustFlip-Skills
```

That installs the `justflip-create-flashcards` skill from this repository.

## Included skills

- `justflip-create-flashcards` — generates JustFlip content files in `.flashcards` or `.flashcards.zip` format using the app's `flashcard-content` schema.

## Repo structure

```text
skills/
  justflip-create-flashcards/
    SKILL.md
    README.md
    reference.md
    scripts/
```

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

## App

- Website: https://just-flip.app/
- App Store / product links can be added on the website alongside the install command above.
