# 12_Backlog.md

# Blender Visual Toolkit

## Master Backlog

Version: Draft 0.2

---

# Цель документа

Данный документ является единым Backlog проекта.

В отличие от Roadmap, здесь содержится полный перечень задач.

Любая новая идея должна попадать именно сюда.

Backlog — это "единый источник истины" по текущему состоянию разработки.

---

# Статусы

Используются следующие статусы:

```
☐ Not Started

◐ In Progress

☑ Completed

⚠ Blocked

❄ Future

🧪 Research
```

---

# Приоритеты

```
P0 Critical

P1 High

P2 Medium

P3 Low

P4 Nice to Have
```

---

# Active Execution Milestones

Этот раздел синхронизирует Master Backlog с текущим операционным Roadmap.

## EP1 — BVT-020 Scratches / Artifact Engine v1 Complete

Priority: P0

Status: ☑ Completed

- [x] Зафиксировать contract `scratches`.
- [x] Определить execution order и compatibility rules.
- [x] Реализовать deterministic procedural scratches mask/provider.
- [x] Поддержать target role `GLASS`.
- [x] Реализовать safe baseline/apply/reset.
- [x] Интегрировать в Artifact Engine.
- [x] Добавить Project Properties и UI.
- [x] Добавить manifest metadata.
- [x] Добавить lifecycle smoke.
- [x] Добавить real RGB smoke.
- [x] Добавить CLI E2E config.
- [x] Прогнать regression — 27/27 PASS.
- [x] Прогнать package validation.
- [x] Merge в `develop`.

## EP2 — Artifact Engine v1 Freeze

Priority: P0

Status: ☑ Completed

- [x] Зафиксировать список providers v1.
- [x] Зафиксировать stage/execution order.
- [x] Зафиксировать provider API/lifecycle.
- [x] Зафиксировать seed/subseed rules.
- [x] Зафиксировать compatibility matrix.
- [x] Зафиксировать artifact manifest schema.
- [x] Создать canonical acceptance config.
- [x] Обновить Artifact Engine documentation.
- [x] Актуализировать статусы Artifact Engine в Backlog.
- [x] Проверить install/package в чистом Blender profile.
- [x] Freeze новых artifact types до Retail Demo v0.1.

## EP3 — Retail Scene & Synthetic SKU Foundation

Priority: P0

Status: ☐ Not Started

- [ ] Создать `examples/retail_demo/`.
- [ ] Подготовить Beverage Fridge scene.
- [ ] Подготовить 3–4 базовые упаковочные geometry templates.
- [ ] Подготовить первые synthetic SKU/textures.
- [ ] Зафиксировать SKU metadata contract.
- [ ] Создать asset/SKU manifest.
- [ ] Реализовать/довести asset registration.
- [ ] Реализовать deterministic shelf placement.
- [ ] Подготовить Glass door material role.
- [ ] Подготовить clean/artifact presets.
- [ ] Сгенерировать 100-frame acceptance dataset.
- [ ] Проверить bbox/YOLO/manifest/validation.

## EP4 — Product & Scene Edge Cases

Priority: P0

Status: ☐ Not Started

- [ ] Зафиксировать architecture boundary Placement vs Artifact Engine.
- [ ] Wrong Angle.
- [ ] Wrong Position.
- [ ] Empty Slot.
- [ ] Occlusion.
- [ ] Deterministic object selection.
- [ ] Per-frame reset.
- [ ] Manifest before/after state.
- [ ] Bbox/clipping/visibility policy.
- [ ] Lifecycle tests.
- [ ] Scene/RGB tests.
- [ ] Edge-case stress preset.

## EP5 — Dataset Productization

Priority: P0

Status: ☐ Not Started

- [ ] Зафиксировать output dataset structure.
- [ ] Version manifest schema.
- [ ] Сохранять generation config.
- [ ] Train/validation/test split.
- [ ] Dataset statistics.
- [ ] Dataset health report.
- [ ] Class/bbox/file validation.
- [ ] Dataset hashes.
- [ ] ZIP export.
- [ ] CLI error contract.
- [ ] UI Generate workflow.
- [ ] 100+ frame batch acceptance.
- [ ] Reproducibility acceptance.

## EP6 — Retail Demo v0.1 / First Public Release

Priority: P0

Status: ☐ Not Started

- [ ] Freeze Beverage Fridge scene.
- [ ] Freeze synthetic SKU pack.
- [ ] Проверить asset licenses/attribution.
- [ ] Preset `clean`.
- [ ] Preset `balanced`.
- [ ] Preset `artifacts`.
- [ ] Preset `stress`.
- [ ] Сгенерировать sample dataset.
- [ ] Quick Start без Python.
- [ ] Screenshots/sample outputs.
- [ ] Known limitations.
- [ ] Demo video.
- [ ] Release Checklist.
- [ ] GitHub Release/tag.

## EP7 — YOLO Benchmark / Sim-to-Real / Research

Priority: P1

Status: ☐ Not Started

- [ ] Freeze benchmark protocol.
- [ ] Freeze BVT/Blender/model versions.
- [ ] Synthetic Clean dataset.
- [ ] Synthetic Balanced dataset.
- [ ] Synthetic + Artifacts dataset.
- [ ] Real-only baseline.
- [ ] Real + Synthetic training.
- [ ] Separate real test set.
- [ ] Precision/Recall/mAP50/mAP50-95.
- [ ] Per-class AP.
- [ ] Artifact severity analysis.
- [ ] Artifact Engine ablation.
- [ ] Reproducible configs/logs/hashes.
- [ ] Benchmark report.
- [ ] Research/article draft.

---

# Milestone 0

## Репозиторий

P0

- ☐ Создать GitHub Repository
- ☐ Настроить License
- ☐ Добавить README
- ☐ Добавить CONTRIBUTING
- ☐ Добавить CODE_OF_CONDUCT
- ☐ Добавить CHANGELOG
- ☐ Настроить GitHub Issues
- ☐ Настроить GitHub Projects
- ☐ Настроить Labels
- ☐ Настроить Milestones

---

# Документация

P0

- ☑ Vision
- ☑ Architecture
- ☑ Project Structure
- ☑ MVP
- ☑ Roadmap
- ☑ Features
- ☑ Artifact Engine
- ☑ Domain Randomization
- ☑ Retail Demo
- ☑ Testing
- ☑ Monetization
- ☑ Competitors
- ☑ Backlog
- ☑ Contributing
- ☑ Release Checklist

---

# Архитектура

P0

- ☐ Создать Core
- ☐ Plugin Loader
- ☐ Event System
- ☐ Logger
- ☐ Config System
- ☐ Manifest Schema
- ☐ Seed Manager

---

# Blender Add-on

P0

- ☐ Регистрация Add-on
- ☐ Панель UI
- ☐ Preferences
- ☐ Property Groups
- ☐ Operators
- ☐ Icons
- ☐ Version Checker

---

# Project Manager

P0

- ☐ Создание проекта
- ☐ Сохранение проекта
- ☐ Загрузка проекта
- ☐ Автосохранение
- ☐ История изменений
- ☐ Версия проекта

---

# Asset Manager

P0

- ☐ Импорт Blend
- ☐ Импорт FBX
- ☐ Импорт GLB
- ☐ Импорт OBJ
- ☐ Asset Browser
- ☐ Категории
- ☐ Preview
- ☐ Metadata
- ☐ Search
- ☐ Tags

---

# Demo Assets

P0

- ☐ Холодильник
- ☐ Полка
- ☐ Банка 330
- ☐ Банка 500
- ☐ Бутылка
- ☐ Коробка
- ☐ Пачка снеков
- ☐ Ценник
- ☐ Разделитель

---

# UV Templates

P0

- ☐ Банка
- ☐ Бутылка
- ☐ Коробка
- ☐ Пачка

---

# Synthetic SKU

P1

- ☐ Первые 10 бутылок
- ☐ Первые 10 банок
- ☐ Первые 10 снеков
- ☐ Первые 10 коробок
- ☐ Preview Images
- ☐ sku.json

---

# Scene Manager

P0

- ☐ New Scene
- ☐ Clone Scene
- ☐ Save Template
- ☐ Load Template
- ☐ Scene Metadata

---

# Demo Scenes

P0

- ☐ Beverage Fridge
- ☐ Snack Shelf
- ☐ Mixed Shelf
- ☐ Showcase

---

# Placement Engine

P0

- ☐ Grid
- ☐ Shelf
- ☐ Random

P1

- ☐ Physics
- ☐ Stack
- ☐ Conveyor

P2

- ☐ Warehouse
- ☐ Pallets

---

# Camera Engine

P0

- ☐ Front
- ☐ Left
- ☐ Right
- ☐ Top
- ☐ Mobile

P1

- ☐ CCTV
- ☐ Robot
- ☐ Drone

---

# Lighting Engine

P0

- ☐ HDRI
- ☐ Area
- ☐ Spot
- ☐ Point
- ☐ Sun

P1

- ☐ Lighting Profiles

---

# Artifact Engine

## Lighting

P0

- ☑ Over Exposure

---

## Camera

P0

- ☑ Noise
- ☑ Motion Blur
- ☑ JPEG

P1

- ☐ Rolling Shutter
- ☐ Lens Distortion
- ☐ Chromatic Aberration
- ☐ Defocus

---

## Glass

P0

- ☑ Fingerprints
- ☑ Reflection
- ☑ Condensation

P1

- ☑ Frost
- ☑ Dust
- ☑ Water Drops
- ☑ Scratches

---

## Product

P0

- ☐ Wrong Angle
- ☐ Wrong Position
- ☐ Empty Slot

P1

- ☐ Damaged Package
- ☐ Missing Label
- ☐ Torn Label
- ☐ Wet Surface

---

## Scene

P0

- ☐ Occlusion

P1

- ☐ Human Reflection
- ☐ Foreign Object
- ☐ Shelf Gap

---

# Domain Randomization

P0

- ☑ Camera
- ☑ Lighting
- ☑ Placement

P1

- ☐ Materials
- ☐ Background
- ☐ Correlated Randomization

---

# Annotation

P0

- ☑ Bounding Box
- ☑ YOLO

P1

- ☐ COCO
- ☐ Object ID

P2

- ☐ Semantic Masks
- ☐ Instance Masks
- ☐ Pose
- ☐ Depth

---

# Manifest

P0

- ☐ Schema
- ☐ JSON Export
- ☐ Validation

---

# Export

P0

- ☑ Images
- ☑ Labels
- ☑ Manifest

P1

- ☐ Statistics
- ☐ ZIP Export

---

# Validation

P0

- ☐ Bounding Boxes
- ☐ Images
- ☐ Labels
- ☐ Manifest

P1

- ☐ Dataset Statistics
- ☐ Dataset Health

---

# Testing

P0

- ☐ Unit Tests
- ☐ Integration Tests
- ☐ Scene Tests
- ☐ Validation Tests

P1

- ☐ Performance Tests
- ☑ Regression Tests

---

# Benchmark

P1

- ☐ YOLO Training
- ☐ Synthetic Only
- ☐ Synthetic + Artifacts
- ☐ Real + Synthetic
- ☐ Report

---

# Documentation

P1

- ☐ API Documentation
- ☐ Tutorials
- ☐ FAQ
- ☐ Screenshots
- ☐ GIF
- ☐ Video

---

# Community

P2

- ☐ Discord
- ☐ Telegram
- ☐ GitHub Discussions

---

# Plugin SDK

P2

- ☐ IPlacementEngine
- ☐ IArtifactProvider
- ☐ IExporter
- ☐ IValidator
- ☐ ICameraProvider

---

# Industry Packs

P3

- ❄ Retail Pack
- ❄ Warehouse Pack
- ❄ Manufacturing Pack
- ❄ Agriculture Pack
- ❄ Electronics Pack
- ❄ OCR Pack
- ❄ Robotics Pack

---

# Research

🧪

- ☐ Domain Gap Analysis
- ☐ Artifact Severity
- ☐ Dataset Diversity Metrics
- ☐ Sim-to-Real Evaluation
- ☐ Benchmark Suite

---

# Nice to Have

P4

- ❄ Cloud Export
- ❄ Multi-GPU Rendering
- ❄ Blender Asset Store Integration
- ❄ Automatic LOD
- ❄ Material Generator
- ❄ Procedural Packaging Generator

---

# Known Risks

- ⚠ Нехватка ассетов
- ⚠ Ограниченное время разработки
- ⚠ Изменения Blender API
- ⚠ Производительность Cycles
- ⚠ Лицензии сторонних моделей
- ⚠ Рост сложности UI

---

# Definition of Done

Задача считается завершённой только если:

- ☑ Код реализован
- ☑ Документация обновлена
- ☑ Есть тесты
- ☑ Нет критических ошибок
- ☑ Проверена воспроизводимость
- ☑ Обновлён CHANGELOG
- ☑ Проведён Code Review (если есть участники)

---

# Правило Backlog

Ни одна идея не должна потеряться.

Если задача не попадает в текущий релиз — она переносится в Backlog со статусом:

```
❄ Future
```

Backlog регулярно пересматривается перед каждым новым milestone.

---

# Связанные документы

Предыдущий:

- 11_Competitors.md

Следующий:

- 13_Contributing.md

---

**End of document**