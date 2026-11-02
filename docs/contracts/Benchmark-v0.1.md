# BVT Benchmark Contract v0.1

Version: 0.1
Status: Frozen Foundation

## Purpose

This contract defines the reproducible EP7 benchmark used to evaluate
the synthetic-to-real behavior of BVT-generated object-detection
datasets.

The benchmark does not attempt to prove that synthetic data is always
better than real data.

The core question is:

> How does BVT synthetic-data composition affect YOLO object-detection
> performance on a fixed real-world test set?

## Frozen software baseline

```text id="qrsyjj"
BVT release:       v0.1.0
BVT commit:        d40fb3c72386c4c87c55bee2e2e4b0f4f0090bd7
Blender:           5.2.3 LTS
Ultralytics:       8.4.198
Model:             yolo11n.pt
Task:              detect
Training imgsz:    640
```

The YOLO model weights SHA-256 must be recorded before the first
training run.

## Why YOLO11n

YOLO11n is the frozen reference detector for EP7.

The purpose of the benchmark is comparability between dataset
conditions, not comparison between detector architectures.

A future benchmark version may introduce YOLO26, RT-DETR or another
detector as an additional model family.

It must not silently replace the v0.1 baseline.

## Frozen class taxonomy

The benchmark uses the eight classes from:

```text id="zxzh9j"
examples/retail_demo/sku/sku-pack-v0.1.json
```

Synthetic and real datasets must use the same class IDs and semantic
identities.

## Real-world counterpart rule

A real sim-to-real benchmark is only valid if the real dataset
contains the same semantic classes as the synthetic training set.

Preferred method:

```text id="o0tgdb"
BVT synthetic texture
→ print label / sleeve
→ apply to physical package
→ photograph in a real retail environment
```

This creates real optics, camera noise, glass, lighting and
backgrounds while keeping the same SKU identity and avoiding
commercial trademarks.

## Synthetic profiles

### Clean

Training allowed.

Purpose:

- clean-render baseline;
- no Artifact Engine;
- minimal domain variation.

### Balanced

Training allowed.

Purpose:

- normal domain randomization;
- mild probabilistic artifacts;
- primary general synthetic profile.

### Artifacts

Training allowed.

Purpose:

- isolate the effect of Artifact Engine;
- compare against Clean.

### Stress

Training is forbidden.

Purpose:

- robustness evaluation;
- hard artifacts;
- structural retail edge cases.

Stress therefore remains an independent evaluation domain.

## Dataset sizes

Pilot:

```text id="urhvyh"
100 images per synthetic training profile
```

Publication:

```text id="emc0dg"
1000 images per synthetic training profile
250 stress images
```

The same synthetic training count is used across Clean, Balanced and
Artifacts to avoid dataset-size confounding.

## Synthetic splits

```text id="w1kk6n"
train       80%
validation  10%
test        10%
```

## Real split

Real data is grouped by capture session.

Target proportions:

```text id="a61t98"
train       70%
validation  15%
test        15%
```

The grouping boundary is more important than an exact percentage.

No capture session may cross split boundaries.

## Leakage policy

The following are forbidden:

- the same capture session in train and test;
- near-duplicate real frames across splits;
- use of `real_test` for hyperparameter tuning;
- use of `real_test` for checkpoint selection;
- use of `real_test` to choose augmentations;
- training on the Stress evaluation set.

## Core experiment matrix

```text id="zjxljz"
E01  Synthetic Clean
E02  Synthetic Balanced
E03  Synthetic Artifacts
E04  Real Only
E05  Real + Synthetic Balanced
```

E05 uses a deterministic 1:1 image-count mix between `real_train` and
a deterministic sample of `synthetic_balanced_train`.

## Training baseline

```text id="ya6ouk"
epochs         100
patience       100
imgsz          640
batch          8
optimizer      AdamW
lr0            0.001
AMP            true
deterministic  true
workers        4
```

Pilot seed:

```text id="llwf9c"
20261102
```

Publication seeds:

```text id="0ua8a8"
20261102
20261103
20261104
```

The core experiment must not change hyperparameters between dataset
conditions.

## Primary endpoint

```text id="oxfvpc"
mAP50-95 on the frozen real_test dataset
```

This is the principal metric used for the sim-to-real comparison.

## Required metrics

Every core experiment must produce:

```text id="zkzlzp"
Precision
Recall
mAP50
mAP50-95
Per-class AP
```

Additional analysis includes:

- F1;
- confusion matrix;
- precision-recall curves.

## Statistical reporting

Publication results use three fixed seeds.

For each metric the report includes:

```text id="5zvp47"
mean
standard deviation
absolute score
delta versus Synthetic Clean
delta versus Real Only
```

A single-seed pilot result cannot support a publication claim.

## Artifact Engine ablation

The first ablation is:

```text id="j43ee5"
Synthetic Clean
vs
Synthetic Artifacts
```

All non-artifact training parameters remain unchanged.

## Artifact severity research

Severity analysis is evaluation-only.

Normalized target levels:

```text id="26lyp4"
0.00
0.25
0.50
0.75
1.00
```

Provider-specific mappings are implemented in a later EP7 checkpoint.

## Reproducibility record

Each dataset records:

- generation config;
- manifest;
- statistics;
- health;
- validation;
- dataset hashes.

Each training run records:

- BVT tag and commit;
- Blender version;
- Python version;
- Ultralytics version;
- PyTorch version;
- CUDA version;
- GPU model;
- pretrained weight SHA-256;
- dataset SHA-256;
- training seed;
- resolved training arguments;
- results CSV;
- best checkpoint hash;
- last checkpoint hash.

## Publication synthetic dataset evidence

The Benchmark v0.1 publication synthetic dataset freeze contains:

```text
Synthetic Clean       1000
Synthetic Balanced    1000
Synthetic Artifacts   1000
Synthetic Stress       250
```

Clean, Balanced and Artifacts are training conditions.

Stress is evaluation-only.

Every dataset passed:

- BVT validation;
- BVT health checks;
- YOLO label validation;
- class taxonomy validation;
- split isolation;
- exact duplicate image detection;
- hash-manifest verification.

The evidence record is:

```text
benchmarks/publication-datasets-v0.1.json
```

This freeze closes synthetic dataset generation only.

Real-world data collection, training and evaluation remain separate
research gates.

## Pilot execution evidence

Before publication-scale dataset generation, Benchmark v0.1 runs a
100-frame pilot for each synthetic profile.

The pilot validates:

- config resolution;
- generator compatibility;
- validation and health;
- split generation;
- dataset integrity hashes;
- deterministic ZIP production;
- benchmark environment capture;
- pretrained model hash capture.

Machine-readable pilot evidence:

```text id="ybklvo"
benchmarks/pilot-datasets-v0.1.json
```

The pilot result is engineering evidence only.

It cannot be used as a publication result.

## Claim policy

Allowed:

> Measured condition X produced metric Y under Benchmark v0.1.

Not allowed without supporting evidence:

- synthetic data is always better;
- artifacts always improve accuracy;
- BVT guarantees accuracy improvement;
- BVT outperforms all competing generators.

## Acceptance

Benchmark v0.1 results are valid only when:

1. the dataset is reproducible;
2. configuration is published;
3. evaluation code is available;
4. metrics are documented;
5. limitations are documented;
6. the real test set remained isolated;
7. software/model versions are recorded;
8. dataset/model hashes are recorded.

## Source of truth

Machine-readable protocol:

```text id="83ydrj"
benchmarks/protocol-v0.1.json
```
