# BVT Retail Demo v0.1 Contract

Version: 0.1
Status: Released

## Purpose

Retail Demo v0.1 is the first narrow public reference workflow for
Blender Visual Toolkit.

The release scenario is:

```text
Beverage Fridge
→ synthetic SKU pack
→ deterministic / randomized generation
→ Artifact Engine
→ YOLO annotations
→ validation
→ statistics / health
→ hashes
→ dataset ZIP
```

## Scope

The release freezes one reference scene:

```text
examples/retail_demo/scenes/beverage-fridge-v0.1.blend
```

One synthetic SKU pack:

```text
examples/retail_demo/sku/sku-pack-v0.1.json
```

One geometry template pack:

```text
examples/retail_demo/assets/geometry-templates-v0.1.blend
examples/retail_demo/assets/geometry-templates-v0.1.json
```

One retail scene manifest:

```text
examples/retail_demo/manifests/beverage-fridge-v0.1.json
```

and eight synthetic SKU textures.

## Frozen SKU set

The public v0.1 SKU set contains exactly eight classes:

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

Changing class IDs, SKU IDs or package identity requires a new
versioned demo contract.

## Public presets

Retail Demo v0.1 exposes four canonical presets.

### clean

Purpose:

- deterministic clean reference;
- no Artifact Engine;
- no retail edge cases;
- no camera/light/placement randomization.

File:

```text
examples/retail_demo/configs/clean.json
```

### balanced

Purpose:

- typical synthetic training variation;
- mild placement/camera/lighting randomization;
- probabilistic low-to-medium Artifact Engine effects;
- no structural retail edge cases.

File:

```text
examples/retail_demo/configs/balanced.json
```

### artifacts

Purpose:

- Artifact Engine visibility / robustness scenario;
- all Artifact Engine v1 providers enabled;
- artifacts applied aggressively;
- no structural retail edge cases.

File:

```text
examples/retail_demo/configs/artifacts.json
```

### stress

Purpose:

- maximum public demo stress scenario;
- Artifact Engine v1 enabled;
- Wrong Angle;
- Wrong Position;
- Empty Slot;
- Occlusion.

File:

```text
examples/retail_demo/configs/stress.json
```

## Freeze mechanism

Frozen release inputs are recorded in:

```text
examples/retail_demo/release-v0.1.json
```

The release manifest stores SHA-256 hashes for all canonical scene,
SKU, geometry, texture and preset files.

A changed hash means the release input changed and requires an explicit
freeze update.

## Asset provenance

The v0.1 reference pack contains synthetic identities and synthetic
reference artwork.

Asset provenance is documented in:

```text
examples/retail_demo/ATTRIBUTIONS.md
```

No third-party asset may silently enter the frozen release set.

## Dataset contract

Generated datasets use the implemented Dataset v0.1 contract:

- manifest v2;
- generation config;
- YOLO labels;
- train/validation/test splits;
- statistics;
- health;
- validation;
- SHA-256 hashes;
- deterministic ZIP export.

## Out of scope

Retail Demo v0.1 does not add:

- COCO export;
- masks;
- new Artifact Engine providers;
- new retail scenes;
- benchmark training;
- real commercial brands;
- SaaS;
- cloud rendering.

Those items remain outside Endpoint 6.

## Public sample dataset

The canonical public sample is generated from:

```text
preset: balanced
seed: 20261102
frames: 12
```

The generated GitHub Release asset is:

```text
bvt-retail-demo-v0.1-sample.zip
```

The binary archive is not committed to the repository.

Its generation and validation are part of the EP6 release process.

## No-Python Quick Start

The public user workflow is documented in:

```text
examples/retail_demo/QUICK_START.md
```

The workflow uses Blender UI controls and the `Generate Dataset`
operator.

Writing or running Python code is not required by the end user.

## Known limitations

The v0.1 release boundary is documented in:

```text
examples/retail_demo/KNOWN_LIMITATIONS.md
```

## Public showcase outputs

Retail Demo v0.1 freezes four presentation outputs:

```text
clean
balanced
artifacts
stress
```

Each output contains:

- one canonical PNG image;
- the matching YOLO label file;
- SHA-256 metadata;
- object count;
- source frame metadata.

The showcase contract is stored in:

```text
examples/retail_demo/showcase/showcase-v0.1.json
```

Human-readable presentation is stored in:

```text
examples/retail_demo/SHOWCASE.md
```

The canonical source frame is `000001`.

## Demo video

The public v0.1 release includes:

```text
bvt-retail-demo-v0.1-demo.mp4
```

The video is generated from the four frozen showcase outputs.

The release video specification is stored in:

```text
examples/retail_demo/DEMO_VIDEO.md
```

The binary MP4 is a GitHub Release asset and is not committed to the
repository.

## Remaining EP6 release gates

After the release inputs are frozen:

1. generate public sample dataset;
2. write Quick Start without Python;
3. add screenshots / sample outputs;
4. document known limitations;
5. prepare demo video;
6. execute Release Checklist;
7. publish GitHub Release/tag.

## Exit criterion

A new user can install BVT, open the frozen Beverage Fridge scene and
generate a valid small dataset by following the public instructions
without developer assistance.
