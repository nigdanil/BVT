# BVT Retail Demo v0.1

Retail Demo is the first public reference scenario for Blender Visual
Toolkit.

Canonical scene:

```text
Beverage Fridge
```

Pipeline:

```text
Synthetic SKU
→ Beverage Fridge
→ Placement / Camera / Lighting
→ Artifact Engine
→ Retail Edge Cases
→ Render
→ YOLO
→ Dataset Validation
→ Statistics / Health
→ Hashes
→ ZIP
```

## Frozen release inputs

The v0.1 release candidate is described by:

```text
release-v0.1.json
```

The file contains SHA-256 hashes for the frozen scene, SKU pack,
geometry templates, textures and public presets.

## Public presets

```text
configs/clean.json
configs/balanced.json
configs/artifacts.json
configs/stress.json
```

`clean` is the deterministic reference.

`balanced` adds normal training variability and mild probabilistic
artifacts.

`artifacts` demonstrates Artifact Engine v1 without structural retail
edge cases.

`stress` combines Artifact Engine v1 with Wrong Angle, Wrong Position,
Empty Slot and Occlusion.

## Synthetic SKU pack

The public v0.1 reference pack contains eight synthetic SKU classes.

No real commercial brand artwork is required by the reference demo.

See:

```text
sku/sku-pack-v0.1.json
ATTRIBUTIONS.md
```


## Getting started

User-facing release documentation:

```text
QUICK_START.md
SAMPLE_DATASET.md
KNOWN_LIMITATIONS.md
```

The Quick Start uses the Blender UI and does not require writing
Python code.

The public sample dataset is generated from the canonical `balanced`
preset and is attached to the GitHub Release.

## Showcase

Canonical public output examples:

```text
SHOWCASE.md
showcase/showcase-v0.1.json
showcase/images/clean.png
showcase/images/balanced.png
showcase/images/artifacts.png
showcase/images/stress.png
```

Each showcase image has its matching YOLO label file under:

```text
showcase/labels/
```

## Licensing and attribution

```text
LICENSES.md
ATTRIBUTIONS.md
SAMPLE_DATASET_LICENSE.md
```

Retail Demo v0.1 uses synthetic BVT reference assets and declares zero
third-party demo assets.

## Demo video

Release video specification and timeline:

```text
DEMO_VIDEO.md
```

The generated binary release asset is:

```text
bvt-retail-demo-v0.1-demo.mp4
```

## Current release status

Retail Demo v0.1 is under EP6 release preparation.

Quick Start, sample dataset, screenshots, known limitations and public
release artifacts are completed in the following EP6 checkpoints.
