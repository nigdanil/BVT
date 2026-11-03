# BVT R01 Physical Print Pack v0.1

Status: Print Candidate

## Purpose

Provide physical 1:1 labels for the eight BVT R01 SKU identities.

The printed labels use the same proxy textures that are rendered on the
accepted synthetic SKU models.

This creates a direct visual bridge:

```text
BVT SKU taxonomy
        ↓
proxy texture
        ↓
synthetic 3D label
        ↓
physical printed label
        ↓
R01 real photograph
```

## Printing rule

Print all labels at:

```text
scale = 100%
```

Disable:

```text
Fit to page
Shrink oversized pages
Scale to printable area
```

Each A4 sheet contains a:

```text
50 × 50 mm
```

calibration square.

Measure this square with a physical ruler before using the labels.

If it is not 50 × 50 mm, the printer or PDF/SVG viewer changed the
scale.

## Target package dimensions

### Cans

```text
package: 66 × 66 × 115 mm
label:   54.12 × 81.18 mm
```

### Bottles

```text
package: 68 × 68 × 225 mm
label:   55.76 × 83.64 mm
```

### Cartons

```text
package: 75 × 75 × 235 mm
label:   61.50 × 92.25 mm
```

### Boxes

```text
package: 90 × 55 × 145 mm
label:   73.80 × 110.70 mm
```

## Package tolerance

The physical container does not have to be an exact manufactured copy
of the Blender proxy.

Recommended acquisition tolerance:

```text
width/depth: ±5 mm
height:      ±10 mm
```

The printed BVT label dimensions themselves should remain 1:1.

## Output

Individual print labels:

```text
examples/retail_demo/print/r01-v0.1/labels/
```

A4 family sheets:

```text
examples/retail_demo/print/r01-v0.1/sheets/
```

Machine-readable manifest:

```text
examples/retail_demo/print/r01-v0.1/print-pack-v0.1.json
```

## Label source

The print pack uses:

```text
examples/retail_demo/textures/sku_proxy_v0.1/
```

This is intentional.

The physical label therefore matches the visual texture actually used
by the polished synthetic proxy models.

## Physical attachment

For R01:

- cans and bottles: attach the printed label to the front curved
  surface;
- cartons and boxes: attach the printed label to the front planar
  surface;
- center the label approximately as shown by the synthetic proxy
  scene;
- do not cover or replace the BVT class marker.

Matte adhesive paper is preferred because glossy paper can introduce an
uncontrolled reflection condition.

R01 is the neutral baseline; strong reflective material should be
reserved for later domain-shift sessions.

## Acceptance

The pack is accepted when:

1. exactly 8 print labels exist;
2. exactly 4 A4 family sheets exist;
3. label dimensions match the proxy manifest;
4. package dimensions match the frozen SKU taxonomy;
5. raster print assets are generated at 300 DPI;
6. SVG labels are self-contained;
7. each A4 sheet contains a 50 mm calibration square;
8. frozen v0.1 assets remain unchanged;
9. repository regression remains green.
