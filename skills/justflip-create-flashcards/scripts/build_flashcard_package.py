#!/usr/bin/env python3

import argparse
import json
import re
import sys
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
    if filename.lower().endswith(".svg"):
        raise SystemExit(
            f"The app cannot display SVG ({filename}). Convert it: scripts/svg_to_png.sh {filename} "
            f"{filename[:-4]}.png"
        )


def unhosted_spoken_hints(text: str) -> List[str]:
    """Brace groups that will be drawn on the card instead of steering TTS.

    The app consumes a `{spoken}` hint only after inline math `$…$`, an image
    `![id]`, a block-math closing fence `$$`, or bracketed text `[visible]`. So
    strip everything it legitimately consumes — including code, which is never
    inline-parsed, and math spans, whose LaTeX has braces of its own — and any
    group still standing is a bug the reader will see.
    """
    stripped = re.sub(r"```.*?```", " ", text, flags=re.S)
    stripped = re.sub(r"`[^`\n]*`", " ", stripped)
    stripped = re.sub(r"\$\$.*?\$\$(\{[^}\n]*\})?", " ", stripped, flags=re.S)
    stripped = re.sub(r"\$[^$\n]+\$(\{[^}\n]*\})?", " ", stripped)
    stripped = re.sub(r"!\[[^\]\n]*\](\{[^}\n]*\})?", " ", stripped)
    stripped = re.sub(r"\[[^\]\n]*\]\{[^}\n]*\}", " ", stripped)
    return re.findall(r"\{[^}\n]*\}", stripped)


MERMAID_FENCE = re.compile(r"```mermaid[ \t]*\n(.*?)\n[ \t]*```", re.S)
MERMAID_HEADERS = ("graph ", "graph;", "flowchart ", "sequencediagram", "statediagram", "classdiagram", "erdiagram")
MERMAID_FORBIDDEN = {
    "style ": "colours break dark mode and themes",
    "classdef ": "colours break dark mode and themes",
    "linkstyle ": "colours break dark mode and themes",
    "%%{": "init directives are ignored",
    "click ": "interactions are unsupported",
    "subgraph": "subgraphs waste card space",
}
MERMAID_MAX_LINES = 60
MERMAID_MAX_CHARS = 2000
# Card-size budgets from SKILL.md → Diagrams (≈ 330 × 250 pt face, ≥ 10 pt labels).
MERMAID_MAX_FLOW_NODES = 6
MERMAID_MAX_PARTICIPANTS = 3
MERMAID_MAX_MESSAGES = 4
MERMAID_MAX_STATES = 4
MERMAID_MAX_CLASSES = 3
MERMAID_MAX_LABEL_CHARS = 16


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def mermaid_size_warnings(source: str) -> List[str]:
    """Heuristic card-size check. Warnings only: the counting is approximate."""
    lines = [line.strip() for line in source.split("\n") if line.strip() and not line.strip().startswith("%%")]
    header = lines[0].lower()
    body = lines[1:]
    notes = []

    labels = re.findall(r"[\[\(\{>]+([^\[\]\(\)\{\}|]+)[\]\)\}]+|\|([^|]+)\|", "\n".join(body))
    long_labels = [text for pair in labels for text in pair if len(text.strip()) > MERMAID_MAX_LABEL_CHARS]
    if long_labels:
        notes.append(f"labels longer than {MERMAID_MAX_LABEL_CHARS} characters: {long_labels[:3]}")

    if header.startswith(("graph", "flowchart")):
        nodes = set()
        for line in body:
            # Drop edge labels and node text, then read the id in front of every arrow.
            bare = re.sub(r"\|[^|]*\|", " ", line)
            bare = re.sub(r"[\[\(\{>][^\]\)\}]*[\]\)\}]+", " ", bare)
            for part in re.split(r"-{2,}>|-{3,}|-\.+->|={2,}>|--[xo]|&", bare):
                match = re.match(r"\s*([A-Za-z0-9_]+)", part)
                if match:
                    nodes.add(match.group(1))
        if len(nodes) > MERMAID_MAX_FLOW_NODES:
            notes.append(f"{len(nodes)} flowchart nodes (card limit {MERMAID_MAX_FLOW_NODES})")
    elif header.startswith("sequencediagram"):
        participants = set()
        messages = 0
        for line in body:
            match = re.match(r"([A-Za-z0-9_ ]+?)\s*-{1,2}>{1,2}[+-]?\s*([A-Za-z0-9_ ]+?)\s*:", line)
            if match:
                messages += 1
                participants.update(part.strip() for part in match.groups())
        if len(participants) > MERMAID_MAX_PARTICIPANTS:
            notes.append(f"{len(participants)} participants (card limit {MERMAID_MAX_PARTICIPANTS})")
        if messages > MERMAID_MAX_MESSAGES:
            notes.append(f"{messages} messages (card limit {MERMAID_MAX_MESSAGES})")
    elif header.startswith("statediagram"):
        states = {name for line in body for name in re.findall(r"([A-Za-z0-9_]+)", line.split(":")[0]) if name}
        if len(states) > MERMAID_MAX_STATES:
            notes.append(f"{len(states)} states (card limit {MERMAID_MAX_STATES})")
    elif header.startswith("classdiagram"):
        classes = {name for line in body for name in re.findall(r"\b([A-Z][A-Za-z0-9_]*)\b", line.split(":")[0])}
        if len(classes) > MERMAID_MAX_CLASSES:
            notes.append(f"{len(classes)} classes (card limit {MERMAID_MAX_CLASSES})")
    elif header.startswith("erdiagram"):
        notes.append("ER diagrams lay out too wide for a card — prefer a flowchart")
    return notes


def validate_mermaid(text: str, card: Dict, side: str, where: str) -> None:
    diagrams = MERMAID_FENCE.findall(text)
    if not diagrams and "```mermaid" not in text:
        return
    if len(diagrams) != 1:
        raise SystemExit(f"{where}: a side may hold exactly one closed ```mermaid block.")
    if MERMAID_FENCE.sub("", text).strip():
        raise SystemExit(
            f"{where}: a diagram side must contain only the diagram — move the other text to the other side."
        )
    if card.get(f"{side}_image"):
        raise SystemExit(f"{where}: a diagram side must not also carry an image.")

    source = diagrams[0]
    content_lines = [line.strip() for line in source.split("\n") if line.strip() and not line.strip().startswith("%%")]
    if not content_lines or not content_lines[0].lower().startswith(MERMAID_HEADERS):
        header = content_lines[0] if content_lines else "(empty)"
        raise SystemExit(
            f"{where}: unsupported Mermaid header '{header}' — it would render as code. "
            "Use graph/flowchart, sequenceDiagram, stateDiagram-v2 or classDiagram, or draw an SVG image."
        )
    if len(content_lines) > MERMAID_MAX_LINES or len(source) > MERMAID_MAX_CHARS:
        raise SystemExit(f"{where}: diagram exceeds {MERMAID_MAX_LINES} lines / {MERMAID_MAX_CHARS} characters.")
    lowered = source.lower()
    for token, reason in MERMAID_FORBIDDEN.items():
        if any(line.strip().lower().startswith(token) for line in source.split("\n")) or (token == "%%{" and token in lowered):
            raise SystemExit(f"{where}: remove '{token.strip()}' from the diagram — {reason}.")
    if "<br" in lowered:
        raise SystemExit(f"{where}: remove <br> from the diagram — keep labels to a few words.")

    for note in mermaid_size_warnings(source):
        warn(f"{where}: diagram may not fit a card: {note}. Split or simplify it.")


def validate_markup(card: Dict, index: int, deck_name: str) -> None:
    for side in ("q", "a"):
        text = card.get(side)
        if not isinstance(text, str):
            continue

        validate_mermaid(text, card, side, f"Card {index} in deck '{deck_name}' ({side})")

        for group in unhosted_spoken_hints(text):
            raise SystemExit(
                f"Card {index} in deck '{deck_name}' ({side}): spoken hint {group} has no "
                f"host and would render literally. Use [visible]{{spoken}}, or drop it."
            )

        fences = [
            line for line in text.split("\n")
            if line.strip().startswith(":::")
        ]
        if len(fences) % 2:
            raise SystemExit(
                f"Card {index} in deck '{deck_name}' ({side}): unbalanced ::: display block."
            )


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

            validate_markup(card, index, deck["deck"])

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
