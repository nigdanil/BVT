# BVT Retail Demo

Retail Demo is the first public reference scenario for Blender Visual
Toolkit.

Initial scenario:

```text
Beverage Fridge
```

Pipeline:

```text
Synthetic SKU
→ Retail Scene
→ Deterministic Shelf Placement
→ Camera / Lighting
→ Artifact Engine v1
→ Render
→ YOLO
→ Manifest
→ Validation
```

## Directory structure

```text
examples/retail_demo/
├── assets/
├── configs/
├── manifests/
├── scenes/
├── scripts/
├── sku/
└── textures/
```

## Scope

EP3 establishes:

- Beverage Fridge scene foundation;
- synthetic SKU metadata;
- package geometry templates;
- deterministic retail instance IDs;
- asset/SKU manifests;
- shelf placement;
- GLASS door integration;
- clean/artifact presets;
- 100-frame acceptance dataset.

Real commercial brands, trademarks and proprietary product artwork are
not required for the public reference demo.

The initial SKU pack should use synthetic identities and synthetic
visual design.
