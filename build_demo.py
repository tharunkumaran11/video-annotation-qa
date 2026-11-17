"""Generate deterministic annotations and an offline preview."""
import csv
import json
from pathlib import Path
from audit import COLUMNS, audit

ROOT = Path(__file__).resolve().parent


def write_rows(name, rows):
    with (ROOT / name).open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    clean = []
    for frame in range(1, 49):
        for track, label, x, y, width, height in (
            (1, "pedestrian", 48 + 8 * frame, 112, 36, 100),
            (2, "cart", 540 - 7 * frame, 225, 68, 48),
        ):
            overlap = max(0, min(x + width, 316) - max(x, 294))
            visibility = round(1 - overlap / width, 3) if track == 1 else 1
            clean.append(dict(frame=frame, track_id=track, label=label, x=x, y=y,
                              width=width, height=height, visibility=visibility))
    faulty = []
    for row in clean:
        row = row.copy()
        key = row["frame"], row["track_id"]
        if key == (14, 1):
            continue
        if key == (20, 1):
            row["visibility"] = 1.5
        if key == (26, 2):
            row["label"] = "pedestrian"
        if key == (33, 2):
            row["x"] += 115
        if key == (42, 1):
            row["x"] = 630
        faulty.append(row)
        if key == (8, 2):
            faulty.append(row.copy())
    write_rows("annotations_review.csv", faulty)
    write_rows("annotations_corrected.csv", clean)
    before = audit(ROOT / "annotations_review.csv")
    after = audit(ROOT / "annotations_corrected.csv")
    expected = {"duplicate": 1, "invalid_box": 1, "invalid_visibility": 1,
                "track_gap": 2, "label_change": 2, "center_jump": 2}
    assert before["counts"] == expected, before
    assert not after["issues"], after
    report = {"fixture": "synthetic", "review": before, "corrected": after}
    (ROOT / "qa_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    template = (ROOT / "preview.template.html").read_text(encoding="utf-8")
    data = json.dumps(dict(clean=clean, faulty=faulty, issues=before["issues"]))
    (ROOT / "preview.html").write_text(template.replace("__DATA__", data), encoding="utf-8")
    print(f"Verified {len(before['issues'])} findings in review data and zero after correction.")


if __name__ == "__main__":
    main()
