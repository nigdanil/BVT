# BVT R01 Neutral Refrigerator Scene v0.1

Status: Visual Accepted

## Purpose

Create a reproducible synthetic reference scene for the first real
capture session `R01`.

The scene uses the polished EP7 SKU Proxy Model Pack v0.1 and provides
a physical arrangement that can later be reproduced with real
containers covered by the corresponding BVT artwork.

## Source assets

Proxy asset pack:

```text
examples/retail_demo/assets/sku-proxy-pack-v0.1.blend
```

Proxy manifest:

```text
examples/retail_demo/assets/sku-proxy-pack-v0.1.json
```

The frozen Retail Demo v0.1 scene is not modified.

## R01 visual role

R01 is intentionally neutral.

Conditions:

```text
environment: refrigerator
view: frontal
lighting: neutral
camera: stable-front
glass: disabled
```

Glass is deliberately excluded from R01.

Reflection-heavy refrigerator glass belongs to a later domain-shift
capture condition rather than the neutral baseline.

## Cabinet

Target cabinet dimensions:

```text
width  = 0.92 m
height = 1.08 m
depth  = 0.36 m
```

The scene contains three product shelves.

Shelf top heights:

```text
0.12 m
0.46 m
0.80 m
```

## Canonical arrangement

Top shelf:

```text
bev_can_red_330
bev_can_blue_330
```

Middle shelf:

```text
bev_bottle_green_500
bev_bottle_amber_500
```

Bottom shelf:

```text
bev_carton_orange_1000
bev_carton_white_1000
bev_box_purple_250
bev_box_yellow_250
```

All package fronts face the camera using the existing BVT convention:

```text
front_direction = -Y
```

## Camera

The camera is centered and frontal.

The preview is portrait-oriented because a refrigerator is naturally
vertical and the intended physical capture may be reproduced with a
phone camera without requiring a wide horizontal composition.

## Sim-to-real rule

The synthetic scene is a reference arrangement, not a requirement that
real photographs be pixel-identical.

The real R01 session should preserve:

- the same eight semantic SKU identities;
- approximately the same shelf hierarchy;
- frontal neutral capture;
- no synthetic image post-processing.

Small physical placement and camera differences are desirable because
R01 is real data rather than a rendered replica.

## Accepted lighting baseline

The neutral R01 visual baseline is frozen with:

```text
render_engine = BLENDER_EEVEE
exposure      = -0.7

key_energy    = 360 W
fill_energy   = 240 W
top_energy    = 170 W
```

The darker neutral interior is intentional.

It keeps light-colored packages, especially
`bev_carton_white_1000`, visually separable while preserving a
front-neutral refrigerator condition.

The lighting configuration is not intended to simulate R06
reflection-heavy conditions.

## Acceptance

The scene is accepted when:

1. all 8 proxy SKU objects exist;
2. all labels remain parented to their SKU objects;
3. all texture paths remain portable/relative;
4. exactly 3 product shelves exist;
5. all products use the canonical R01 placements;
6. camera and lighting are present;
7. glass is disabled;
8. a preview renders successfully;
9. the frozen Retail Demo release remains unchanged.
