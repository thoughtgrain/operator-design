# <Machine name> · screen brief

> Copy to `screens/<machine-id>/brief.md`. Fill phase by phase; don't skip a gate. Protocol: `opxy/protocol.md`.

## 0 · Screen or stock page?

- Subject in one sentence: …
- Or: stock page, because …

## 1 · Intake

| | |
| --- | --- |
| Machine id | `…` |
| Kind | synth / effect / sample (the SDK contract) |
| Category | engine / drum / sampler / effect / player / sequencer / function (`opxy/categories.md`) |
| Sounds like | two sentences |
| Controls | N (≤ 4 stock header, 5–8 two pages) |
| Control source | existing XY definition / port of … / new |

### 1A · Port map (skip if an XY definition already exists)

| source control | source range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| | | | | | | | keep / split / merge / drop | |

Integer conversion (e.g. OP-1 0..32767 from the top 15 bits of Q31): …

### 1B · Definition review

`python3 opxy/tools/lint_definition.py <definition.json>` → … errors, … warnings. Warnings resolved or justified:

| warning | resolution |
| --- | --- |
| | |

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | | |
| Header values in real units, ≤ ~5 chars | | |
| Defaults plainest useful; presets sound good (by ear) | | |
| Engine page holds only the sound's own parameters | | |
| Page 1 holds what's played most | | |
| Port parity: nothing silently lost | | |
| Saved sounds compatible (if released) | | |
| `id` final | | |

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | | | | | | | |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: yes / pending device.

Page 1 (played most): … · Page 2: … · Repeated controls: …

## 2 · Listen and rank

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 | | |

## 3 · Subject

Five candidates, one per direction from `design_pass_start` (or by hand: five different pattern × drawing-language pairs that fit the category). Pass record: `passes/01-subject/pass.json`.

| candidate | pattern | drawing language | subject in one sentence | what each control moves | verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | | | | | |
| v2 | | | | | |
| v3 | | | | | |
| v4 | | | | | |
| v5 | | | | | |

Chosen: … because …

## 4 · Map and budget

| # | score | channel | part (node) | travel 0 → 100 | what the player sees |
| --- | --- | --- | --- | --- | --- |
| 1 | | | | | |

```json
"display": {"stateBytes": 0, "stateAlignment": 4,
            "paths": 0, "points": 0, "nodes": 0, "texts": 0, "palette": 0}
```

| case | changed nodes / frame |
| --- | --- |
| at rest | 0 |
| playing, defaults | |
| playing, heaviest setting (name it) | avg … · peak … |
