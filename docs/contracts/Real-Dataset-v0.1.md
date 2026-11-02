# BVT Real Dataset Contract v0.1

Version: 0.1

Status: Foundation Frozen — Data Not Yet Collected

## Purpose

Real Dataset v0.1 is the held-out real-world dataset used by the BVT
Benchmark v0.1 sim-to-real experiment.

It exists to measure the domain gap between BVT-generated synthetic
training data and real camera imagery.

## Frozen taxonomy

The real dataset uses exactly the same eight SKU identities as the BVT
Retail Demo synthetic dataset.

Source:

```text
examples/retail_demo/sku/sku-pack-v0.1.json
```

Canonical class file:

```text
benchmarks/real/classes-v0.1.txt
```

## Physical SKU policy

Preferred real-world counterparts are physical packages carrying the
BVT synthetic artwork.

This gives the experiment:

- real optics;
- real camera noise;
- real illumination;
- real reflections;
- real refrigerator glass;
- real background variation;

while preserving the same class semantics as the synthetic dataset.

## Capture target

```text
10 independent sessions
50 images per session
500 planned images
```

Minimum acceptable dataset before freeze:

```text
400 images
```

The publication target remains 500.

## Session split

```text
R01–R07 → real_train       350 images
R08     → real_validation   50 images
R09–R10 → real_test        100 images
```

The split unit is the capture session, never the individual frame.

## Independence rule

A new capture session requires a deliberate reset of capture
conditions.

At minimum:

- new session manifest;
- physical scene/product rearrangement or reset;
- camera handling/position reset;
- lighting condition explicitly recorded.

## Leakage protection

Forbidden:

- one session in multiple splits;
- exact duplicate images;
- near-duplicate images crossing splits;
- `real_test` frames used for training;
- `real_test` used for hyperparameter tuning;
- `real_test` used for checkpoint selection.

Near-duplicate detection:

```text
algorithm: dHash-64
cross-split failure threshold: Hamming distance <= 4
```

## Real test

The real test split contains:

```text
R09
R10
```

Target size:

```text
100 images
```

The test split becomes immutable after freeze.

## Annotation

Format:

```text
YOLO detection
```

Policy:

```text
benchmarks/real/ANNOTATION_POLICY-v0.1.md
```

Real annotation semantics must match the frozen BVT YOLO exporter.

## Minimum class coverage

Required labeled instances:

```text
real_train       >= 100 instances per class
real_validation  >=  10 instances per class
real_test        >=  20 instances per class
```

## Privacy

The reference benchmark does not require people or private
information.

Forbidden in the retained dataset:

- faces;
- license plates;
- private documents;
- GPS EXIF metadata.

## Storage

Actual real images and labels are intentionally not committed to the
BVT source repository.

Ignored local path:

```text
benchmarks/real/data-v0.1/
```

The Git repository stores:

- capture protocol;
- session metadata schema;
- validator;
- hashes/evidence after freeze;
- benchmark results.

## Evidence

Once collection is complete, the validator produces a machine-readable
evidence record containing:

- session IDs;
- split membership;
- image counts;
- label counts;
- class coverage;
- image SHA-256;
- label SHA-256;
- exact-duplicate result;
- cross-split dHash result;
- split hashes;
- real-test hash.

Until that evidence exists, the EP7 backlog item:

```text
Separate real test set.
```

must remain open.
