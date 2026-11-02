# BVT Dataset Contract v0.1

Status: Implemented

Milestone: EP5 — Dataset Productization

## Purpose

This contract defines the user-facing BVT dataset package produced by
the generation pipeline.

EP5 turns the renderer/annotation pipeline into a self-contained,
versioned and reproducible dataset workflow.

## Dataset root

The canonical generated dataset directory is:

```text
<output_directory>/
└── dataset/
```

The dataset must not depend on temporary files outside this directory
for validation, inspection, splitting or reproducibility metadata.

## Canonical structure

```text
dataset/
├── images/
│   └── <frame_id>.png
├── labels/
│   └── <frame_id>.txt
├── splits/
│   ├── train.txt
│   ├── validation.txt
│   └── test.txt
├── config/
│   └── generation.json
├── classes.txt
├── manifest.json
├── statistics.json
├── health.json
├── validation.json
└── hashes.json
```

EP5 may implement these files incrementally, but their names and
responsibilities are fixed by this contract.

## Images

Directory:

```text
images/
```

Current public image format:

```text
PNG
```

Canonical frame name:

```text
000001.png
000002.png
...
```

## Labels

Directory:

```text
labels/
```

Current annotation format:

```text
YOLO bounding boxes
```

Canonical frame name:

```text
000001.txt
000002.txt
...
```

Each non-empty row contains:

```text
<class_id> <x_center> <y_center> <width> <height>
```

Coordinates are normalized to `[0, 1]`.

## Classes

File:

```text
classes.txt
```

One class name per line in ascending class ID order.

Class IDs are stable for the lifetime of one generated dataset.

## Manifest

File:

```text
manifest.json
```

Manifest schema introduced by EP5:

```text
bvt-dataset-manifest-2
```

The manifest is the canonical index of the dataset.

It records:

- toolkit version;
- Blender version;
- dataset/project identity;
- generation seed and frame count;
- generation config reference;
- render settings;
- annotation contract;
- per-frame image and label paths;
- per-frame randomization;
- retail edge cases;
- Artifact Engine metadata.

## Generation config

File:

```text
config/generation.json
```

Schema:

```text
bvt-generation-config-1
```

This file stores the effective BVT project settings used for the run.

It is a resolved runtime snapshot and is therefore also available for
generation started from Blender UI, not only from CLI scenario files.

It contains:

- project identity;
- project schema;
- seed;
- frame count;
- configured output directory;
- scene/camera identity;
- effective render settings;
- all generation-affecting public BVT project properties.

The manifest references this file through:

```text
generation.config_file
generation.config_schema_version
```

## Splits

Directory:

```text
splits/
```

Required EP5 split files:

```text
train.txt
validation.txt
test.txt
```

Each row contains one dataset-relative image path:

```text
images/000001.png
```

A frame may belong to exactly one split.

Split assignment must be deterministic for the same dataset seed and
configuration.

## Statistics

File:

```text
statistics.json
```

Dataset-level statistics include at minimum:

- frame count;
- image count;
- label count;
- object count;
- class count;
- per-class object counts;
- empty-label frame count;
- bbox size summary;
- split counts.

## Health report

File:

```text
health.json
```

Health analysis includes at minimum:

- class imbalance;
- empty labels;
- missing files;
- invalid labels;
- invalid or clipped bbox state;
- duplicate or suspicious files where detectable.

Health findings are distinct from hard validation errors.

## Validation

File:

```text
validation.json
```

Validation represents machine-checkable correctness.

Hard failures include:

- missing referenced files;
- unsupported schema;
- invalid class IDs;
- malformed YOLO rows;
- non-finite coordinates;
- invalid bbox sizes;
- bbox outside image bounds;
- manifest/config disagreement.

## Hashes

File:

```text
hashes.json
```

Hashes use SHA-256.

Hashes cover productized dataset files and are used to verify integrity
and reproducibility.

The hashes file must not recursively hash itself.

## ZIP export

EP5 ZIP export packages the canonical `dataset/` contents without
changing internal relative paths.

An extracted archive must be independently validatable.

## CLI error contract

Dataset CLI failures use:

```text
bvt-cli-error-1
```

Machine-readable failure markers:

```text
ERROR_SCHEMA=bvt-cli-error-1
ERROR_CODE=<stable_code>
ERROR_MESSAGE=<single_line_message>
BVT_DATASET=FAIL
```

Current public error codes include:

```text
INPUT_NOT_FOUND
INVALID_INPUT
GENERATION_FAILED
BLENDER_TRACEBACK
PROCESS_FAILED
SUCCESS_MARKER_MISSING
INTERNAL_ERROR
```

A successful dataset command emits:

```text
BVT_DATASET_CLI=OK
BVT_DATASET=OK
```

The human-readable message may evolve, while `ERROR_CODE` is the
stable automation-facing field.

## UI Generate workflow

The Blender `BVT` panel provides the standard generation workflow.

The user configures:

- output directory;
- project seed;
- frame count;
- train split;
- validation split;
- test split;
- existing randomization / Artifact Engine / retail edge-case settings.

`Generate Dataset` calls the same canonical `generate_dataset()`
pipeline used by programmatic generation.

Successful UI generation produces:

- `dataset/`;
- `dataset.zip`;
- manifest;
- generation config;
- splits;
- statistics;
- health report;
- validation report;
- hashes.

The UI does not implement a separate generation engine.

## Reproducibility

For identical:

```text
seed
+ generation config
+ source scene/assets
+ BVT version
+ Blender version
```

BVT must reproduce the same structural dataset state.

PNG container bytes are not assumed to be identical when Blender writes
semantically identical decoded pixels.

## Versioning

Changing the meaning of existing required manifest fields requires a
new manifest schema version.

Adding backward-compatible optional metadata does not necessarily
require a version bump.

Current versions:

```text
dataset layout:          bvt-dataset-layout-1
dataset manifest:        bvt-dataset-manifest-2
generation config:       bvt-generation-config-1
validation report:       bvt-validation-report-1
dataset hashes:          bvt-dataset-hashes-1
dataset hashes:          bvt-dataset-hashes-1
dataset hashes:          bvt-dataset-hashes-1
```

## EP5 acceptance gates

### Batch acceptance

The EP5 productization acceptance dataset contains at least 100 frames.

Canonical acceptance size:

```text
120 frames
```

For the 80/10/10 split this produces:

```text
train:       96
validation:  12
test:        12
```

Acceptance requires:

- all images and labels present;
- manifest frame count correct;
- class/object statistics correct;
- validation PASS;
- health PASS;
- hashes verification PASS;
- complete ZIP export.

### Reproducibility acceptance

Two runs using the same:

```text
source scene
+ BVT version
+ Blender version
+ seed
+ effective generation config
```

must produce identical:

- manifest;
- generation config;
- frame seeds;
- YOLO labels;
- split assignments;
- statistics;
- health report;
- validation report;
- decoded PNG pixel content.

PNG container byte identity is not required.

`hashes.json` is an integrity artifact for one generated dataset and
may therefore contain different image-file hashes when Blender writes
different PNG container bytes for identical decoded pixels.

## EP5 scope boundary

EP5 does not add:

- new Artifact Engine providers;
- new retail edge-case categories;
- COCO;
- segmentation;
- benchmark training;
- new demo scenes.

Those belong to later milestones.
