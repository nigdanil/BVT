# BVT Real Dataset v0.1 — Annotation Policy

Status: Foundation Frozen

## Format

Real Dataset v0.1 uses YOLO object-detection labels.

Each image has one matching `.txt` label file.

Every annotation row contains:

```text
<class_id> <center_x> <center_y> <width> <height>
```

All coordinates are normalized to `[0, 1]`.

Class IDs are frozen to:

```text
0 bev_can_red_330
1 bev_can_blue_330
2 bev_bottle_green_500
3 bev_bottle_amber_500
4 bev_carton_orange_1000
5 bev_carton_white_1000
6 bev_box_purple_250
7 bev_box_yellow_250
```

## Bounding-box semantics

Real annotations must follow the same bounding-box convention as the
frozen BVT YOLO exporter.

Before real annotation begins, the annotator must review at least 20
frozen synthetic examples with their BVT labels.

This calibration prevents a systematic annotation-policy difference
between synthetic and real datasets.

## Class identity

Use the same semantic SKU identity as the frozen BVT synthetic pack.

Preferred physical workflow:

```text
BVT synthetic artwork
→ printed label / sleeve
→ physical package
→ real refrigerator / shelf
→ photograph
→ manual YOLO annotation
```

Commercial product branding is not required.

## Manual QA

Training and validation:

```text
manual review >= 20%
```

Real test:

```text
manual review = 100%
```

Every reviewed annotation checks:

- correct class;
- one box per intended SKU instance;
- normalized coordinates;
- no negative width or height;
- no box outside image bounds;
- image/label filename match.

## Test-set rule

`real_test` is evaluation-only.

It must never be used for:

- model training;
- augmentation tuning;
- hyperparameter tuning;
- checkpoint selection;
- dataset-profile selection.

## Changes after freeze

After the real test set is frozen, annotation corrections require:

1. documented reason;
2. new evidence hash;
3. benchmark result invalidation and rerun.
