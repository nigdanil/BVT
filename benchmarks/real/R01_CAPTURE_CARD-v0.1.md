# BVT Real Dataset — R01 Capture Card

Session:

```text
R01
```

Split:

```text
train
```

Target:

```text
50 photographs
```

Environment:

```text
refrigerator
front-neutral-light
stable-front
```

## Before shooting

Use the same eight semantic SKU identities defined in:

```text
benchmarks/real/classes-v0.1.txt
```

Preferred physical setup:

```text
BVT artwork
→ physical cans / bottles / cartons / boxes
→ refrigerator or refrigerator-like shelf
```

Disable location tagging in the camera application if possible.

The retained images must contain no:

- faces;
- license plates;
- private documents;
- GPS EXIF metadata.

## Shot sequence

### R01-A — frames 0001–0010

Full frontal shelf.

All eight classes clearly visible.

### R01-B — frames 0011–0020

Change distance slightly between photographs.

Remain broadly frontal.

### R01-C — frames 0021–0030

Small horizontal and vertical camera shifts.

Do not turn R01 into the oblique-angle session.

### R01-D — frames 0031–0040

Reset the physical arrangement.

Move several products slightly.

Take ten new photographs.

### R01-E — frames 0041–0050

Introduce mild natural occlusion and arrangement variation.

All eight classes must remain represented.

## Important

Do not take fifty frames without changing anything.

The purpose is controlled within-session diversity, not burst
photography.

Do not manually rename phone photographs before import.

The importer creates canonical names:

```text
R01_0001.jpg
R01_0002.jpg
...
R01_0050.jpg
```

## Recommended temporary source folder

Example:

```text
D:\BVT\.tmp\r01-phone
```

Copy the fifty original phone images into that folder.

Do not put them directly into the benchmark dataset directory.

## Import command

From Git Bash:

```text
/d/BVT/.tmp/ep7-real-tools-env/Scripts/python.exe \
  benchmarks/scripts/import_real_session.py \
  --session R01 \
  --source /d/BVT/.tmp/r01-phone
```

The importer rejects:

- wrong image count;
- unreadable images;
- GPS EXIF;
- an already populated destination;
- an unknown session ID.

It copies image bytes without recompressing the photograph.

After successful import R01 becomes:

```text
captured-unannotated
```

Annotation is a separate step.
