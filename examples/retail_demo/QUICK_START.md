# BVT Retail Demo v0.1 — Quick Start

This workflow requires no Python programming.

## Requirements

- Blender 5.2 LTS;
- Blender Visual Toolkit v0.1 release package;
- BVT Retail Demo v0.1 files.

The v0.1 release acceptance is performed with Blender 5.2.x.

## 1. Install BVT

Open Blender.

Go to:

```text
Edit
→ Preferences
→ Extensions
→ Install from Disk
```

Select:

```text
blender_visual_toolkit-0.1.0.zip
```

Enable Blender Visual Toolkit if Blender does not enable it
automatically.

## 2. Open the Retail Demo

Open:

```text
examples/retail_demo/scenes/beverage-fridge-v0.1.blend
```

The scene contains the frozen Beverage Fridge reference scene and
synthetic SKU set.

## 3. Open BVT Tools

In the 3D Viewport press:

```text
N
```

Open the:

```text
BVT
```

tab.

The Generation section contains the dataset controls.

## 4. Choose an output directory

Set an output directory for the generated dataset.

Do not use the BVT source directory as the output directory.

## 5. Initialize the BVT project

In the `Project` section click:

```text
Initialize Project
```

BVT must initialize the current Blender scene before dataset
generation can start.

After initialization the panel shows:

```text
Project initialized
```

## 6. Configure generation

For the first test use a small dataset.

Recommended initial values:

```text
Frames:       5
Train:        0.8
Validation:   0.1
Test:         0.1
```

The three split ratios must sum to:

```text
1.0
```

## 7. Generate

Click:

```text
Generate Dataset
```

BVT runs the same canonical generation pipeline used by CLI
generation.

## 8. Check the output

A successful run creates:

```text
dataset/
dataset.zip
```

The dataset contains images, YOLO labels, manifest, saved generation
configuration, dataset splits, statistics, health report, validation
report and SHA-256 hashes.

The expected final validation state is:

```text
PASS
```

## Public presets

The repository also contains four canonical release presets:

```text
configs/clean.json
configs/balanced.json
configs/artifacts.json
configs/stress.json
```

They are reference configurations for reproducible CLI and release
testing.

For the no-Python Quick Start, use the Blender UI workflow above.

## Public sample

Users who want to inspect the result before generating anything can
download:

```text
bvt-retail-demo-v0.1-sample.zip
```

from the GitHub Release assets after v0.1 is published.
