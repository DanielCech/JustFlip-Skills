#!/usr/bin/env python3

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional

FIELD_ALIASES = {
    "q": ["q", "question", "front", "prompt"],
    "a": ["a", "answer", "back", "definition"],
    "note": ["note", "notes", "comment", "comments"],
    "q_image": ["q_image", "question_image", "front_image"],
    "q_audio": ["q_audio", "question_audio", "front_audio"],
    "q_pdf": ["q_pdf", "question_pdf", "front_pdf"],
    "a_image": ["a_image", "answer_image", "back_image"],
    "a_audio": ["a_audio", "answer_audio", "back_audio"],
    "a_pdf": ["a_pdf", "answer_pdf", "back_pdf"],
    "deck": ["deck", "deck_name", "category", "section", "group"],
}

DELIMITER_MAP = {
    "auto": None,
    "pipe": "|",
    "comma": ",",
    "tab": "\t",
    "semicolon": ";",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert structured delimited data into JustFlip flashcard-content JSON."
    )
    parser.add_argument("input", help="Source CSV/TSV/delimited file")
    parser.add_argument("output", help="Output JSON or .flashcards path")
    parser.add_argument("--interest", required=True, help="Interest name")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--deck", help="Single deck name")
    group.add_argument("--deck-col", help="Column used to group rows into decks")
    parser.add_argument(
        "--delimiter",
        choices=DELIMITER_MAP.keys(),
        default="auto",
        help="Delimiter to use. Defaults to auto detection.",
    )
    parser.add_argument("--question-col", help="Question column name")
    parser.add_argument("--answer-col", help="Answer column name")
    parser.add_argument("--note-col", help="Note column name")
    parser.add_argument("--q-image-col", help="Question image filename column name")
    parser.add_argument("--q-audio-col", help="Question audio filename column name")
    parser.add_argument("--q-pdf-col", help="Question PDF filename column name")
    parser.add_argument("--a-image-col", help="Answer image filename column name")
    parser.add_argument("--a-audio-col", help="Answer audio filename column name")
    parser.add_argument("--a-pdf-col", help="Answer PDF filename column name")
    parser.add_argument("--deck-q-lang", help="Default question language tag")
    parser.add_argument("--deck-a-lang", help="Default answer language tag")
    return parser.parse_args()


def detect_delimiter(path: Path) -> str:
    sample = path.read_text(encoding="utf-8-sig")
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters="|,\t;")
        return dialect.delimiter
    except csv.Error:
        counts = {delimiter: sample.count(delimiter) for delimiter in ["|", "\t", ",", ";"]}
        return max(counts, key=counts.get)


def normalize(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def resolve_column(field_name: str, headers: List[str], override: Optional[str]) -> Optional[str]:
    if override:
        if override in headers:
            return override

        normalized_headers = {normalize(header): header for header in headers}
        normalized_override = normalize(override)
        if normalized_override in normalized_headers:
            return normalized_headers[normalized_override]

        raise SystemExit(f"Column '{override}' not found for field '{field_name}'.")

    normalized_headers = {normalize(header): header for header in headers}
    for alias in FIELD_ALIASES[field_name]:
        if alias in normalized_headers:
            return normalized_headers[alias]
    return None


def clean(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def row_to_card(
    row: Dict[str, str],
    field_map: Dict[str, Optional[str]],
) -> Dict[str, str]:
    card = {}
    for field_name in [
        "q",
        "a",
        "note",
        "q_image",
        "q_audio",
        "q_pdf",
        "a_image",
        "a_audio",
        "a_pdf",
    ]:
        column = field_map[field_name]
        if column is None:
            continue
        value = clean(row.get(column))
        if value is not None:
            card[field_name] = value

    return card


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    delimiter = DELIMITER_MAP[args.delimiter] or detect_delimiter(input_path)
    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        headers = reader.fieldnames or []
        if not headers:
            raise SystemExit("Input file has no header row.")

        field_map = {
            "q": resolve_column("q", headers, args.question_col),
            "a": resolve_column("a", headers, args.answer_col),
            "note": resolve_column("note", headers, args.note_col),
            "q_image": resolve_column("q_image", headers, args.q_image_col),
            "q_audio": resolve_column("q_audio", headers, args.q_audio_col),
            "q_pdf": resolve_column("q_pdf", headers, args.q_pdf_col),
            "a_image": resolve_column("a_image", headers, args.a_image_col),
            "a_audio": resolve_column("a_audio", headers, args.a_audio_col),
            "a_pdf": resolve_column("a_pdf", headers, args.a_pdf_col),
        }

        if field_map["q"] is None and field_map["a"] is None:
            raise SystemExit("Could not infer question or answer columns.")

        deck_column = resolve_column("deck", headers, args.deck_col) if args.deck_col else None

        cards_by_deck: Dict[str, List[Dict[str, str]]] = {}
        for row in reader:
            if deck_column:
                deck_name = clean(row.get(deck_column)) or "Imported"
            else:
                deck_name = args.deck

            card = row_to_card(row, field_map)
            if not card:
                continue
            if "q" not in card and "a" not in card:
                continue

            cards_by_deck.setdefault(deck_name, []).append(card)

    if not cards_by_deck:
        raise SystemExit("No cards were created from the input.")

    if deck_column:
        payload = {
            "format": "flashcard-content",
            "version": "1",
            "interest": args.interest,
            "decks": [
                {
                    "deck": deck_name,
                    **({"deck_q_lang": args.deck_q_lang} if args.deck_q_lang else {}),
                    **({"deck_a_lang": args.deck_a_lang} if args.deck_a_lang else {}),
                    "cards": cards,
                }
                for deck_name, cards in cards_by_deck.items()
            ],
        }
    else:
        deck_name = args.deck or next(iter(cards_by_deck))
        payload = {
            "format": "flashcard-content",
            "version": "1",
            "interest": args.interest,
            "deck": deck_name,
            **({"deck_q_lang": args.deck_q_lang} if args.deck_q_lang else {}),
            **({"deck_a_lang": args.deck_a_lang} if args.deck_a_lang else {}),
            "cards": cards_by_deck[deck_name],
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
