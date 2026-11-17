"""Audit MOT-style bounding boxes in a CSV file."""
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

COLUMNS = ("frame", "track_id", "label", "x", "y", "width", "height", "visibility")
LABELS = {"pedestrian", "cart"}


def audit(path, width=640, height=360, frames=48, max_step=45):
    issues = []
    tracks = defaultdict(list)
    seen = set()

    def flag(code, row, frame, track, detail):
        issues.append(dict(code=code, row=row, frame=frame, track_id=track, detail=detail))

    with Path(path).open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if tuple(reader.fieldnames or ()) != COLUMNS:
            raise ValueError("Expected CSV columns: " + ", ".join(COLUMNS))
        for line, record in enumerate(reader, 2):
            try:
                frame, track, x, y, w, h = (
                    int(record[key]) for key in ("frame", "track_id", "x", "y", "width", "height")
                )
                visibility = float(record["visibility"])
            except (ValueError, TypeError):
                flag("invalid_value", line, None, None, "Expected integer coordinates and numeric visibility.")
                continue
            if not 1 <= frame <= frames or track <= 0:
                flag("invalid_key", line, frame, track, "Frame or track ID outside allowed range.")
                continue
            if (frame, track) in seen:
                flag("duplicate", line, frame, track, "Track appears more than once in this frame.")
                continue
            seen.add((frame, track))
            label = record["label"]
            if label not in LABELS:
                flag("unknown_label", line, frame, track, "Label outside the project taxonomy.")
            if not 0 <= visibility <= 1:
                flag("invalid_visibility", line, frame, track, "Visibility must be between 0 and 1.")
            if w <= 0 or h <= 0 or x < 0 or y < 0 or x + w > width or y + h > height:
                flag("invalid_box", line, frame, track, "Box must have positive dimensions and fit inside the frame.")
                continue
            tracks[track].append((frame, line, label, x + w / 2, y + h / 2))

    for track, sequence in tracks.items():
        sequence.sort()
        for previous, current in zip(sequence, sequence[1:]):
            old_frame, _, old_label, old_x, old_y = previous
            frame, line, label, cx, cy = current
            elapsed = frame - old_frame
            if elapsed > 1:
                flag("track_gap", line, frame, track, f"Missing frames {old_frame + 1}–{frame - 1}.")
            if label != old_label:
                flag("label_change", line, frame, track, f"Track class changed from {old_label} to {label}.")
            distance = ((cx - old_x) ** 2 + (cy - old_y) ** 2) ** 0.5
            if distance / elapsed > max_step:
                flag("center_jump", line, frame, track, f"Center moved {distance / elapsed:.1f} pixels per frame.")
    return dict(issues=issues, counts=dict(sorted(Counter(i["code"] for i in issues).items())))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv")
    args = parser.parse_args()
    print(json.dumps(audit(args.csv), indent=2))
