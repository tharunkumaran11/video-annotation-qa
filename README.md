# Video Annotation & QA

A reproducible portfolio demo for reviewing object tracks frame by frame. The included fixture is a **synthetic animation** of a pedestrian and a cart. It uses deliberately seeded labeling defects and corrected reference labels.

## Try it

1. Open `preview.html` directly in a browser. No server or installation is required.
2. Click **Play** or scrub to a frame. Select a finding to jump to its frame, then switch the label overlay to **Corrected** to compare.
3. Around frame 30, inspect the pedestrian behind the post. The full box marks the tracked object and the visibility value estimates the unobscured fraction of the box width in this fixture.

## Annotation rules

Each CSV row contains a frame number, track ID, label, pixel box, and visibility from zero to one. Coordinates start at the upper-left corner. Within the fixture, a track retains one ID and class, and its box remains in the frame. Visibility decreases during partial occlusion. Motion and internal track gaps are review signals. On real footage, fast motion or a fully occluded object can justify them.

## QA result

| Check | Review findings |
| --- | ---: |
| Duplicate frame and track | 1 |
| Invalid box | 1 |
| Visibility outside range | 1 |
| Internal track gap | 2 |
| Class change | 2 |
| Sudden center movement | 2 |
| **Total** | **9** |

Six seeded edits produce nine findings. A class swap creates two transitions, a shifted box creates two jumps, and excluding an invalid box leaves a gap in the valid track history. The corrected fixture has **zero findings** on these checks. The report is a consistency audit. It does not establish annotation accuracy on real video.

## Reproduce

Requires Python 3.10 or newer and uses the standard library.

```text
python build_demo.py
python audit.py annotations_review.csv
python audit.py annotations_corrected.csv
```

The builder regenerates the two CSV files, the browser preview, and `qa_report.json`. It checks that the six seeded edits produce the expected findings and that the corrected data passes. The preview plays generated frames on canvas. No source video, model output, or human annotation claims are included.

## Review decisions

The assistant compared flagged rows and their neighboring frames with the generated reference labels.

| Frame | Track | Evidence and correction |
| --- | --- | --- |
| 8 | Cart #2 | Two identical rows described one cart. Kept one row. |
| 14 | Pedestrian #1 | The pedestrian was visible between frames 13 and 15. Restored its missing box. |
| 20 | Pedestrian #1 | The box lies clear of the post. Replaced the invalid visibility of 1.5 with 1. |
| 26 | Cart #2 | Track #2 is a cart in both neighboring frames. Restored the cart class. This resolves the alerts at 26 and 27. |
| 33 | Cart #2 | The box was shifted 115 pixels to the right of the generated cart. Restored x = 309. This resolves both motion alerts. |
| 42 | Pedestrian #1 | The box at x = 630 extended beyond the 640-pixel frame. Restored x = 384, resolving the box alert and the subsequent track gap. |

Frame 30 is a useful control. The post covers 22 of the pedestrian box's 36 horizontal pixels, which yields a recorded visibility of 0.389. The track remains continuous. That partial occlusion is expected in the fixture.
