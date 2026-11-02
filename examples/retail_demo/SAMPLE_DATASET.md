# BVT Retail Demo v0.1 — Sample Dataset

Status: Release Candidate

## Purpose

The public sample dataset demonstrates the complete BVT Retail Demo
output without requiring the user to generate a large dataset first.

The sample uses the canonical:

```text
balanced
```

preset.

## Source

Scene:

```text
examples/retail_demo/scenes/beverage-fridge-v0.1.blend
```

Preset:

```text
examples/retail_demo/configs/balanced.json
```

Seed:

```text
20261102
```

Frames:

```text
12
```

SKU classes:

```text
8
```

## Release asset

The generated release asset is:

```text
bvt-retail-demo-v0.1-sample.zip
```

The archive is generated during the EP6 release process.

It is intentionally not committed to the Git repository.

The final archive is attached to the GitHub Release.

## Dataset contents

```text
dataset/
├── images/
├── labels/
├── config/
│   └── generation.json
├── splits/
│   ├── train.txt
│   ├── validation.txt
│   └── test.txt
├── classes.txt
├── manifest.json
├── statistics.json
├── health.json
├── validation.json
└── hashes.json
```

## Acceptance

Before publication the sample must satisfy:

```text
frames       = 12
images       = 12
labels       = 12
validation   = PASS
health       = PASS
hashes       = PASS
```

Archive SHA-256 is calculated during release preparation and may be
published with the GitHub Release asset.

The ZIP container hash is not part of the source-code freeze contract.

## License

The public sample dataset is licensed under:

```text
CC BY 4.0
SPDX: CC-BY-4.0
```

See `SAMPLE_DATASET_LICENSE.md`.
