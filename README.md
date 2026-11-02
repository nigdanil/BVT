# Blender Visual Toolkit

**Open-source Blender toolkit for reproducible synthetic Computer Vision datasets.**

Current release: **v0.1.0**

## What BVT v0.1 does

BVT v0.1 provides one complete public workflow:

```text
Retail scene
→ deterministic randomization
→ Artifact Engine
→ retail edge cases
→ rendering
→ YOLO annotations
→ validation
→ statistics / health
→ hashes
→ dataset ZIP
```

The first frozen public demo is:

```text
Beverage Fridge
```

## Current v0.1 features

- Blender add-on UI;
- project initialization;
- object/class registration;
- deterministic generation by seed;
- placement randomization;
- camera randomization;
- lighting randomization;
- Artifact Engine v1;
- eleven artifact providers;
- retail edge cases:
  - Wrong Angle;
  - Wrong Position;
  - Empty Slot;
  - Occlusion;
- YOLO bounding-box export;
- productized dataset structure;
- train/validation/test split;
- dataset statistics;
- health report;
- validation report;
- SHA-256 integrity manifest;
- deterministic ZIP packaging;
- CLI generation workflow;
- Blender UI generation workflow.

## Supported environment

Public v0.1 acceptance is performed with:

```text
Blender 5.2 LTS
Windows
```

Other Blender versions and operating systems are not part of the v0.1
acceptance matrix.

## Installation

Download:

```text
blender_visual_toolkit-0.1.0.zip
```

from the GitHub Release.

In Blender:

```text
Edit
→ Preferences
→ Extensions
→ Install from Disk
```

Choose the ZIP package and enable Blender Visual Toolkit.

## Retail Demo Quick Start

Open:

```text
examples/retail_demo/scenes/beverage-fridge-v0.1.blend
```

Then open the `BVT` panel in the 3D Viewport sidebar.

Set an output directory and click:

```text
Initialize Project
```

Then configure frame count / dataset split and click:

```text
Generate Dataset
```

Full guide:

```text
examples/retail_demo/QUICK_START.md
```

## Public presets

```text
clean
balanced
artifacts
stress
```

See:

```text
examples/retail_demo/configs/
```

## Showcase

Canonical v0.1 sample outputs:

```text
examples/retail_demo/SHOWCASE.md
```

## Sample dataset

GitHub Release asset:

```text
bvt-retail-demo-v0.1-sample.zip
```

## Demo video

GitHub Release asset:

```text
bvt-retail-demo-v0.1-demo.mp4
```

## Known limitations

See:

```text
examples/retail_demo/KNOWN_LIMITATIONS.md
```

v0.1 intentionally does not claim support for COCO export,
segmentation masks, cloud rendering, training pipelines or sim-to-real
benchmark results.

## Reproducibility

Generation records:

- seed;
- effective generation configuration;
- frame seeds;
- manifest;
- dataset splits;
- statistics;
- health;
- validation;
- SHA-256 hashes.

## Documentation

Core project documentation is stored under:

```text
docs/
```

Important release documents:

```text
docs/contracts/Dataset-v0.1.md
docs/contracts/Retail-Demo-v0.1.md
docs/releases/v0.1.0.md
examples/retail_demo/README.md
```

## Licensing

Add-on source code:

```text
GPL-3.0-or-later
```

Documentation:

```text
CC BY 4.0
```

Retail Demo v0.1 original assets and public sample dataset:

```text
CC BY 4.0
```

See:

```text
LICENSE.md
THIRD_PARTY.md
examples/retail_demo/LICENSES.md
examples/retail_demo/ATTRIBUTIONS.md
```

## Status

v0.1.0 is the first narrow public BVT release.

The next research milestone focuses on YOLO benchmarking and
sim-to-real evaluation.
