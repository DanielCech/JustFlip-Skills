#!/usr/bin/env python3

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Set
from zipfile import ZIP_DEFLATED, ZipFile

MEDIA_FIELDS = {
    "q_image": "images",
    "a_image": "images",
    "q_audio": "audio",
    "a_audio": "audio",
    "q_pdf": "pdfs",
    "a_pdf": "pdfs",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate JustFlip flashcard-content JSON and package it as .flashcards or .flashcards.zip."
    )
    parser.add_argument("content", help="Path to flashcard-content JSON")
    parser.add_argument("output", help="Output .flashcards or .flashcards.zip path")
    parser.add_argument(
        "--media-root",
        help="Directory containing images, audio, and pdfs subfolders",
    )
    return parser.parse_args()


def load_payload(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def get_decks(payload: Dict) -> List[Dict]:
    if payload.get("format") != "flashcard-content":
        raise SystemExit("Top-level 'format' must be 'flashcard-content'.")
    version = str(payload.get("version"))
    if version != "1":
        raise SystemExit("Top-level 'version' must be '1'.")
    if not payload.get("interest"):
        raise SystemExit("Top-level 'interest' is required.")

    if "decks" in payload:
        decks = payload["decks"]
        if not isinstance(decks, list) or not decks:
            raise SystemExit("'decks' must be a non-empty array.")
        return decks

    if payload.get("deck") and isinstance(payload.get("cards"), list):
        return [{
            "deck": payload["deck"],
            "deck_icon": payload.get("deck_icon"),
            "deck_q_lang": payload.get("deck_q_lang"),
            "deck_a_lang": payload.get("deck_a_lang"),
            "cards": payload["cards"],
        }]

    raise SystemExit("Provide either 'deck' + 'cards' or a non-empty 'decks' array.")


def validate_media_name(filename: str) -> None:
    if "/" in filename or "\\" in filename:
        raise SystemExit(f"Media filename must not include directories: {filename}")


def collect_media(payload: Dict) -> Dict[str, Set[str]]:
    media_refs = {"images": set(), "audio": set(), "pdfs": set()}
    for deck in get_decks(payload):
        if not deck.get("deck"):
            raise SystemExit("Every deck must have a 'deck' name.")
        cards = deck.get("cards")
        if not isinstance(cards, list) or not cards:
            raise SystemExit(f"Deck '{deck.get('deck')}' must contain a non-empty 'cards' array.")

        for index, card in enumerate(cards, start=1):
            if not isinstance(card, dict):
                raise SystemExit(f"Card {index} in deck '{deck['deck']}' must be an object.")
            if not card.get("q") and not card.get("a"):
                raise SystemExit(
                    f"Card {index} in deck '{deck['deck']}' must include 'q' or 'a'."
                )

            for field_name, media_folder in MEDIA_FIELDS.items():
                value = card.get(field_name)
                if not value:
                    continue
                validate_media_name(value)
                media_refs[media_folder].add(value)

    return media_refs


def ensure_media_exists(media_root: Path, media_refs: Dict[str, Set[str]]) -> None:
    for folder, filenames in media_refs.items():
        for filename in filenames:
            path = media_root / folder / filename
            if not path.is_file():
                raise SystemExit(f"Missing media file: {path}")


def write_flashcard(output_path: Path, payload: Dict) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_zip(output_path: Path, payload: Dict, media_root: Optional[Path], media_refs: Dict[str, Set[str]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content_json = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("content.json", content_json)
        if media_root is None:
            return
        for folder, filenames in media_refs.items():
            for filename in sorted(filenames):
                archive.write(media_root / folder / filename, f"{folder}/{filename}")


def main() -> None:
    args = parse_args()
    content_path = Path(args.content)
    output_path = Path(args.output)
    media_root = Path(args.media_root) if args.media_root else None

    payload = load_payload(content_path)
    media_refs = collect_media(payload)
    has_media = any(media_refs.values())

    if has_media and media_root is None:
        raise SystemExit("Media references exist, but --media-root was not provided.")
    if media_root is not None:
        ensure_media_exists(media_root, media_refs)

    output_name = output_path.name
    if output_name.endswith(".flashcards"):
        if has_media:
            raise SystemExit("Use a .flashcards.zip output when media fields are present.")
        write_flashcard(output_path, payload)
        return

    if output_name.endswith(".flashcards.zip"):
        write_zip(output_path, payload, media_root, media_refs)
        return

    raise SystemExit("Output path must end with .flashcards or .flashcards.zip.")


if __name__ == "__main__":
    main()
