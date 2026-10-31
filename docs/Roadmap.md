# Blender Visual Toolkit

## Product Roadmap

Version: Draft 0.2

---

# Цель документа

Roadmap определяет стратегическое развитие Blender Visual Toolkit.

Это **не список задач**.

Это план развития проекта на несколько лет.

Roadmap отвечает на вопросы:

- куда развивается проект;
- какие функции появятся;
- какие приоритеты;
- что НЕ планируется;
- каким мы хотим видеть Toolkit через несколько лет.

---

# Главная стратегия

Проект развивается постепенно.

Не строится "идеальный продукт".

Каждая версия должна быть:

- стабильнее;
- проще;
- полезнее;
- расширяемее предыдущей.

Главный принцип:

> Release Early. Release Often.

---

# Roadmap Overview

```text
v0.1
↓

v0.2

↓

v0.3

↓

v0.4

↓

v0.5

↓

v1.0

↓

v1.5

↓

v2.0
```

---

# Current Execution Track — Retail MVP

Status: Active

Baseline: `develop` after BVT-019 Water Drops

Planning horizon: first public Retail Demo and benchmark

Этот раздел является **операционным roadmap текущего этапа**.

Он определяет последовательность ближайших работ до первого законченного retail-релиза. Старые разделы `Version 0.x / 1.x / 2.x` ниже сохраняются как долгосрочная карта возможностей, но не задают текущий порядок реализации.

Главное ограничение текущего этапа:

> Не расширять scope, пока не получен законченный путь Retail scene → controlled artifacts → annotated dataset → validation → export → benchmark.

## Endpoint 1 — BVT-020 Scratches / Artifact Engine v1 Complete

### Цель

Закрыть базовый Glass Artifact Pack и завершить набор артефактов, необходимый для первого retail demo.

### Мини-план

- зафиксировать контракт `scratches` до написания кода;
- реализовать deterministic procedural scratches без внешних текстур;
- таргетировать материалы роли `GLASS`;
- встроить Scratches в существующую композицию Artifact Engine;
- сохранить воспроизводимость через project/frame/artifact/material seed;
- сохранить пользовательские shader links, которые BVT не умеет безопасно оборачивать;
- не менять geometry, bbox и annotation;
- добавить UI только для согласованных публичных параметров v1;
- добавить manifest metadata и compatibility rules;
- добавить lifecycle smoke;
- добавить real RGB smoke;
- добавить CLI E2E config;
- прогнать полный regression и package.

### Критерий выхода

- одинаковый seed даёт одинаковый результат;
- другой seed меняет scratches;
- Glass chain корректно восстанавливается после reset;
- RGB действительно изменяется;
- bbox/labels не изменяются;
- полный regression зелёный;
- headless E2E зелёный;
- package валиден;
- feature-ветка слита в `develop`.

---

## Endpoint 2 — Artifact Engine v1 Freeze

### Цель

Зафиксировать Artifact Engine как стабильную подсистему MVP и прекратить добавление новых эффектов до завершения retail demo.

### Мини-план

- зафиксировать список Artifact Engine v1;
- зафиксировать execution order и stage каждого provider;
- зафиксировать общий provider contract;
- описать правила seed/subseed;
- описать baseline/apply/reset lifecycle;
- описать правила безопасной композиции shader nodes;
- зафиксировать manifest schema для artifacts;
- создать compatibility matrix артефактов;
- создать один canonical headless acceptance config;
- обновить `Artifact_Engine.md`, `Features.md`, `README.md` и backlog statuses;
- проверить установку собранного ZIP в чистом Blender-профиле;
- не добавлять новые artifact types до завершения Endpoint 6, кроме bugfix.

### Критерий выхода

Artifact Engine можно использовать как стабильную зависимость следующих этапов без изменения его базового API.

---

## Endpoint 3 — Retail Scene & Synthetic SKU Foundation

### Цель

Перестать тестировать BVT только на Cube и получить первый настоящий воспроизводимый retail workflow.

Первый обязательный сценарий: **Beverage Fridge**.

### Мини-план

- определить минимальную структуру `examples/retail_demo/`;
- подготовить холодильник/полки/разделители;
- выбрать 3–4 базовые геометрии упаковки;
- подготовить первые синтетические SKU и текстуры;
- определить `sku_id`, `class_id`, `class_name`, `instance_id`;
- создать asset/SKU manifest;
- реализовать или довести регистрацию ассетов;
- реализовать shelf placement для реальной выкладки;
- использовать существующие camera/light/placement randomizers;
- добавить Glass material role для дверцы холодильника;
- подготовить clean и artifact presets;
- генерировать минимум 100 кадров одной командой;
- валидировать изображения, labels и manifest.

### Критерий выхода

Одна Beverage Fridge сцена генерирует воспроизводимый YOLO dataset с несколькими SKU, корректными bbox и manifest без ручного редактирования каждого кадра.

---

## Endpoint 4 — Product & Scene Edge Cases

### Цель

Добавить нарушения, которые непосредственно нужны для retail CV, а не декоративные эффекты.

### Обязательный scope

- Wrong Angle;
- Wrong Position;
- Empty Slot;
- Occlusion.

### Мини-план

- определить границу между Placement Engine и Artifact Engine для scene/product mutations;
- реализовать deterministic selection объектов;
- Wrong Angle: контролируемый поворот товара;
- Wrong Position: смещение товара в допустимых пределах полки;
- Empty Slot: детерминированное отсутствие выбранного товара;
- Occlusion: частичное перекрытие объектов с корректной annotation policy;
- записывать исходное и изменённое состояние в manifest;
- обеспечить reset между кадрами;
- проверить bbox/clipping/visibility;
- добавить lifecycle и scene smoke tests;
- добавить stress presets для edge cases.

### Критерий выхода

BVT воспроизводимо генерирует clean и нарушенные выкладки, а labels/manifest остаются согласованными с фактическим кадром.

---

## Endpoint 5 — Dataset Productization

### Цель

Превратить текущий generator pipeline в законченный пользовательский dataset workflow.

### Мини-план

- зафиксировать структуру output dataset;
- versioned manifest schema;
- images/labels/classes/config/validation/statistics;
- train/validation/test split;
- dataset statistics;
- dataset health report;
- проверка class balance и empty labels;
- проверка bbox и файлов;
- сохранение generation config рядом с dataset;
- hashes для воспроизводимости;
- ZIP export;
- понятные ошибки CLI;
- UI entry point для типового Generate workflow;
- batch smoke на 100+ кадров;
- reproducibility smoke повторного запуска.

### Критерий выхода

Пользователь получает самодостаточный валидный dataset directory/archive, который можно сразу передать в обучение без ручной сборки файлов.

---

## Endpoint 6 — Retail Demo v0.1 / First Public Release

### Цель

Опубликовать первый узкий, законченный и повторяемый сценарий BVT.

### Мини-план

- заморозить Beverage Fridge demo scene;
- подготовить набор synthetic SKU с лицензиями;
- подготовить presets `clean`, `balanced`, `artifacts`, `stress`;
- сгенерировать демонстрационный dataset;
- проверить установку add-on из ZIP;
- подготовить Quick Start без Python;
- добавить screenshots и sample outputs;
- описать known limitations;
- обновить README и Retail Demo guide;
- подготовить короткое demo video;
- выполнить Release Checklist;
- создать GitHub Release/tag для первого demo milestone.

### Критерий выхода

Новый пользователь может установить BVT, открыть готовую retail-сцену и получить валидный небольшой dataset по инструкции без участия разработчика.

---

## Endpoint 7 — YOLO Benchmark, Sim-to-Real & Research Report

### Цель

Экспериментально проверить основную гипотезу BVT: контролируемая синтетика и Artifact Engine могут уменьшать domain gap для retail CV.

### Экспериментальные группы

1. Synthetic Clean.
2. Synthetic Balanced.
3. Synthetic + Artifacts.
4. Real-only baseline.
5. Real + Synthetic.
6. Ablation без Artifact Engine.
7. Ablation с Artifact Engine.

### Мини-план

- зафиксировать dataset configs и seeds;
- зафиксировать версию Blender/BVT;
- выбрать и зафиксировать версию YOLO baseline;
- подготовить отдельный real test set;
- не смешивать real test с synthetic train;
- обучить все экспериментальные группы по одному protocol;
- измерить Precision, Recall, mAP50, mAP50-95 и per-class AP;
- измерить performance по artifact type/severity;
- провести ablation Artifact Engine;
- сохранить model configs, logs и hashes;
- сформировать benchmark report;
- честно зафиксировать отрицательные результаты и ограничения;
- подготовить материал для научной статьи/публикации.

### Критерий выхода

Есть воспроизводимый публично описанный benchmark, который измеряет эффект synthetic/artifact data на real test set и даёт достаточную доказательную базу для статьи.

---

# Execution Dependency Chain

```text
BVT-020 Scratches
        ↓
Artifact Engine v1 Freeze
        ↓
Retail Scene + Synthetic SKU
        ↓
Product / Scene Edge Cases
        ↓
Dataset Productization
        ↓
Retail Demo v0.1
        ↓
YOLO Benchmark / Sim-to-Real / Article
```

# Scope Gate

До завершения `Retail Demo v0.1` новые крупные направления (Warehouse, OCR, Robotics, SaaS, Plugin Marketplace, новые категории Artifact Engine) не входят в active development и остаются в Backlog/Future.

---

# Version 0.1

## Первая публикация проекта

Цель

Показать миру идею.

### Основные функции

- Blender Add-on
- UI
- Asset Manager
- Scene Manager
- Camera Engine
- Lighting Engine
- Placement Engine
- YOLO Export
- Bounding Boxes
- Manifest

---

### Демо

Retail

- Shelf
- Fridge
- Showcase

---

### Документация

Полный комплект документации.

---

# Version 0.2

## Первый полноценный Dataset Generator

Добавляется:

- COCO Export
- Polygon Export
- Instance Masks
- Semantic Masks
- Dataset Statistics
- Dataset Preview

---

### Улучшения

Новые настройки камеры.

Больше вариантов света.

Улучшенный Export.

---

# Version 0.3

## Artifact Engine

Самый важный релиз.

Добавляется полноценная система артефактов.

---

## Camera

- Motion Blur
- Lens Noise
- JPEG
- Chromatic Aberration
- Defocus

---

## Glass

- Fingerprints
- Dust
- Scratches
- Condensation
- Water
- Frost

---

## Lighting

- Reflections
- Random Shadows
- Hot Spots
- Color Shift

---

## Product

- Wrong Rotation
- Wrong Position
- Damaged Package
- Missing Product
- Wet Surface

---

## Scene

- Occlusion
- Foreign Objects
- Shelf Gaps

---

# Version 0.4

## Placement Engine 2.0

Добавляется:

- Physics Placement
- Stack Placement
- Collision Detection
- Shelf Rules
- Facing Rules

---

### Новые генераторы

- Conveyor
- Pallet
- Warehouse

---

# Version 0.5

## Validation

Появляется полноценный Dataset Validator.

Проверяется:

- Bounding Boxes
- Masks
- COCO
- YOLO
- Manifest
- Statistics

---

Также:

Dataset Report

Dataset Health

Dataset Quality Score

---

# Version 1.0

## Stable Release

Первый официальный релиз.

### Возможности

✔ Scene Builder

✔ Asset Manager

✔ Placement

✔ Cameras

✔ Lighting

✔ Artifact Engine

✔ Annotation

✔ Export

✔ Validation

---

### Документация

Полностью завершена.

---

### Поддерживаемые форматы

YOLO

COCO

Masks

Depth

Normals

Manifest

---

# Version 1.1

## Performance

Работа над скоростью.

Например:

- Batch Render
- Parallel Generation
- Faster Export
- Faster Validation

---

# Version 1.2

## Asset Browser

Собственная библиотека ассетов.

Категории.

Поиск.

Теги.

Предпросмотр.

---

# Version 1.3

## Material Library

Готовые материалы.

Glass

Plastic

Metal

Paper

Cardboard

Food

---

# Version 1.5

## Industry Packs

Появляются отраслевые наборы.

Retail

Warehouse

Manufacturing

Electronics

Food

Agriculture

Robotics

Medical

---

Каждый пакет использует одно ядро.

---

# Version 2.0

## Blender Visual Toolkit Platform

Toolkit становится полноценной платформой.

---

Новые возможности

Plugin SDK

Module API

Dataset Templates

Scene Templates

Advanced Validation

Benchmark

Statistics

Artifact Profiles

---

# Long-Term Vision

Через несколько лет Toolkit должен стать стандартом генерации synthetic datasets в Blender.

---

# Возможные будущие направления

## OCR

Документы

Паспорта

Этикетки

Счета

Чеки

---

## Robotics

Depth

Pose

Manipulation

Grasp Planning

---

## Autonomous Driving

Дороги

Машины

Разметка

Пешеходы

---

## Warehouse

Коробки

Паллеты

Стеллажи

---

## Manufacturing

Детали

Конвейеры

Комплектность

Контроль качества

---

## Agriculture

Растения

Плоды

Болезни

Почва

---

## Medical

Инструменты

Лаборатории

Оборудование

---

# Plugin SDK

В будущем любой разработчик сможет написать собственный модуль.

Например:

```text
My Placement Engine

↓

Install

↓

Toolkit

↓

Новый Placement Algorithm
```

---

То же касается:

Artifacts

Export

Validation

Render

Dataset Templates

---

# Community Goals

Через 2–3 года хотелось бы получить:

- активный GitHub;
- внешний вклад в код;
- Issues;
- Pull Requests;
- новые отраслевые пакеты;
- статьи;
- примеры использования.

---

# Коммерческое развитие

Open Source остаётся основой проекта.

Возможные коммерческие направления:

- кастомные отраслевые пакеты;
- консалтинг;
- интеграция;
- обучение;
- создание сцен;
- создание ассетов;
- сопровождение.

---

# Что НЕ входит в Roadmap

На текущем этапе не планируется:

- собственный игровой движок;
- замена Blender;
- облачный SaaS как основной продукт;
- обучение нейросетей внутри Toolkit;
- собственная CAD-система.

Эти задачи находятся вне области проекта.

---

# Критерии успешного развития

Каждая новая версия должна:

- уменьшать количество ручной работы;
- улучшать качество датасетов;
- повышать воспроизводимость;
- упрощать использование;
- расширять возможности генерации.

---

# Release Philosophy

Перед добавлением новых функций необходимо:

1. Завершить документацию.
2. Реализовать функцию.
3. Написать тесты.
4. Обновить примеры.
5. Выпустить релиз.

---

# Связанные документы

Предыдущий:

03_MVP.md

Следующий:

05_Features.md

---

**End of document**