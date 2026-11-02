# Categories

Every machine I design for falls into one category, and the category is the first filter on which patterns are worth trying. A drum voice and a step sequencer have almost nothing in common on screen: one is an object you hit, the other is state over time. Sorting by category up front keeps me from proposing an orrery for a reverb.

The machine-readable version is `catalog.json`. The MCP server reads it (`opxy_patterns` filters by category, `design_pass_start` draws its five directions from it), so when I change a row here I change it there too.

## The categories

| Category | SDK `kind` | What it is | What its screen usually shows |
| --- | --- | --- | --- |
| **engine** | `synth` | A voice that makes the sound: oscillators, folders, filters, physical models | The mechanism or the signal path, reshaped by each control |
| **drum** | `synth` or `sample` | A percussion voice or kit | The instrument itself, because the player already knows its parts by sight |
| **sampler** | `sample` | Plays, slices or granulates recorded audio | The material (stack of slices, grain field) and where playback sits in it, drawn from the sample overview |
| **effect** | `effect` | Processes another track's audio | What happens to the signal on its way through: taps, a space, a transfer curve |
| **player** | none yet | Generates notes for another engine | The rule that picks notes, drawn as something with the same shape |
| **sequencer** | none yet | Step, pattern or multi-page sequencing | A sequence over time, with history visible without a list |
| **function** | none yet | Keys are functions acting on a target track | The target being acted on, not a panel of function cells |

What each one gets to draw with differs (`constraints.md`, Which machines draw a screen):

- **engine** and **drum** voices built as synths draw their engine page on any SDK. A **drum kit** also gets the selected key's model, its choices and the Shift state from SDK 1.8, so the screen can show which drum the encoders are editing.
- An **effect** draws its own send page from SDK 1.7, with an optional shift row of modes. There's no browser preview for effect pages yet, so I design from stills and check on a device.
- A **sampler** (a sample engine forking the stock sampler) draws over the sampler's page from SDK 1.8. It gets a 96-bin overview of the sample, the outer markers and whether a sample is loaded, so the sample itself is the obvious subject. It also gives up stock's trim controls on that page, so if trimming matters, two of its own controls have to be start and end, and the screen should show them on the overview.

`player`, `sequencer` and `function` have no SDK kind of their own today, and their pages need bound nodes the stock player page doesn't give them. I still design them, but the handoff says so up front, the same way P12–P14 do.

The SDK `kind` and the category aren't the same thing. `kind` is the contract with open-xy (it decides the control counts and resources `lint_definition.py` checks); the category is a design decision about what the screen is of. Theseus is `kind: synth`, category `drum`.

## Which patterns fit

My reading of where each pattern has worked or should work. `*` means it's a layout discipline that applies on top of any subject.

| Pattern | engine | drum | sampler | effect | player | sequencer | function |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P1 Section drawing | ● | ● | | ● | | | |
| P2 Diagram + trace | ● | | | ● | | | |
| P3 Trace as subject | ● | | | ● | | | |
| P4 Stack in depth | ● | | ● | ● | | | |
| P5 Field and figure | ● | | ● | | ● | | |
| P6 Figures (caution) | ● | ● | | | | | |
| P9 One-bit ink (caution) | ● | | | | | | |
| P10 Voice field | ● | | | ● | | | |
| P11 Instrument stack | | ● | | | | | |
| P12 Orrery | | | | | ● | ● | |
| P13 Capture | | | | | ● | | ● |
| P14 Loom | | | | | ● | ● | ● |
| P15 Cell field | ● | | ● | ● | | | |
| P7 Column affinity, P8 Headers | * | * | * | * | * | * | * |

A pattern outside its column isn't banned, it just has to earn it in the subject pass: the candidate says why this machine is the exception.

## Where the category is recorded

- `screens/<id>/brief.md`: the **Category** row in intake, next to the SDK kind.
- `library/README.md`: the Category column.
- `catalog.json`: `library.<entry>.category`, so the server can answer "show me every audited drum screen".

## Adding a category

Only when a machine doesn't fit any row above, and only through training mode (`training/README.md`): the proposal adds the row here, the entry in `catalog.json`, and says which patterns fit it. A new category with no fitting pattern is a sign the first machine in it needs a new pattern too.
