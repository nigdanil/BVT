# BVT Physical/Digital SKU Pack v0.1

Status: Foundation

## Purpose

This contract adds a physical/digital artwork layer for EP7
sim-to-real experiments.

It does not replace or modify the frozen Retail Demo v0.1 SKU
taxonomy.

## Frozen source taxonomy

Canonical source:

```text
examples/retail_demo/sku/sku-pack-v0.1.json
```

The eight frozen SKU identities are:

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

These identifiers are already used by:

- synthetic datasets;
- YOLO labels;
- EP7 benchmark protocol;
- Real Dataset v0.1 class taxonomy.

They must not be renamed by the physical asset workflow.

## Artwork layer

Machine-readable artwork mapping:

```text
examples/retail_demo/artwork/sku_pack_v0.1/artwork-manifest-v0.1.json
```

Each SKU receives one additional SVG artwork file intended for:

1. new proxy 3D package models;
2. printable physical wrappers/labels;
3. real capture R01.

The existing frozen synthetic PNG texture remains recorded separately.

## Package families

```text
bev_can_red_330          → can
bev_can_blue_330         → can

bev_bottle_green_500     → bottle
bev_bottle_amber_500     → bottle

bev_carton_orange_1000   → carton
bev_carton_white_1000    → carton

bev_box_purple_250       → box
bev_box_yellow_250       → box
```

## Proxy model target

The next asset checkpoint creates eight actual Blender objects:

```text
SKU_bev_can_red_330
SKU_bev_can_blue_330
SKU_bev_bottle_green_500
SKU_bev_bottle_amber_500
SKU_bev_carton_orange_1000
SKU_bev_carton_white_1000
SKU_bev_box_purple_250
SKU_bev_box_yellow_250
```

Target physical dimensions should approximately correspond to their
semantic packaging class.

## Sim-to-real rule

Synthetic and real imagery must use the same semantic SKU identity.

The physical object may be a neutral commercial container covered by
BVT artwork, but the class identity remains the corresponding frozen
`bev_*` SKU.

## Release boundary

The original Retail Demo v0.1 files remain frozen.

New EP7 assets are additive.

No EP7 physical/proxy asset may silently rewrite the released v0.1 SKU
taxonomy.

## Acceptance

This foundation is accepted when:

- frozen SKU manifest matches the repository HEAD and v0.1 release;
- all eight frozen classes have artwork mappings;
- all eight SVG files exist;
- class IDs remain exactly 0–7;
- package-family cardinality is 2/2/2/2;
- the full repository regression remains green.
