# protoH-emergent-life
Artificial-life experiment where protohumans start without concepts, learn through experience, and are analyzed by a detector that tracks emerging ideas such as refuge, danger, death and auto-life. The goal is to explore whether one of them can develop a functional proto-belief of being alive.
Created by **YJNWI**.  
Licensed under the **Apache License 2.0**.

--

## Recommended GitHub tagline

> **Artificial-life experiment where protohumans start without concepts and a detector tracks learned ideas like refuge, danger, death and auto-life, aiming to explore whether one can develop a functional proto-belief of being alive.**

---

## License

This project is distributed under the **Apache License 2.0**.

Copyright 2026 **YJNWI**.

The Apache License 2.0 allows people to:

- use the project;
- study it;
- modify it;
- fork it;
- redistribute it;
- include it in other projects;
- use it commercially;
- sell modified or unmodified copies;

as long as they comply with the terms of the license.

In practice, this means that derived or redistributed versions must keep the license and attribution notices. If the project includes a `NOTICE` file, the relevant attribution notices from that file must also be preserved in distributions or derivative works as required by the Apache License 2.0.

In plain English:

> You can modify, sell and share this project, but you cannot erase the original credit to **YJNWI**.

This project also includes a `NOTICE` file stating that `protoH` was originally created by **YJNWI**.

See the `LICENSE` file for the full legal text.

---

## Responsible claim

This repository **does not claim**:

- that the agents are truly conscious;
- that they feel real pain;
- that they have human-like subjective experience;
- that they are alive in the biological sense;
- that a detector percentage proves real awareness.

This repository **does claim** that it is possible to build a small, auditable experimental environment where:

- agents are born with no explicit abstract concepts;
- they experience hunger, thirst, sleep, pain, energy loss, predators, resources and death;
- they can form associations between events;
- those associations can be inspected with commands such as `brain NUMBER`;
- an external MetaObserver can propose hypotheses such as “possible refuge”, “possible danger”, “possible death/no-movement”, “possible bait/trap” or “possible auto-life”;
- those hypotheses can be exported, audited, challenged and compared against control agents.

The project is therefore about **emergent functional cognition**, not about proving consciousness.

---

## Table of contents

1. [What protoH is](#what-protoh-is)
2. [The core idea](#the-core-idea)
3. [Why this experiment exists](#why-this-experiment-exists)
4. [The “born without concepts” rule](#the-born-without-concepts-rule)
5. [What would count as cheating](#what-would-count-as-cheating)
6. [Architecture overview](#architecture-overview)
7. [Requirements](#requirements)
8. [Installation](#installation)
9. [Quick start](#quick-start)
10. [What you see when it runs](#what-you-see-when-it-runs)
11. [World, map and symbols](#world-map-and-symbols)
12. [Time system](#time-system)
13. [Humans](#humans)
14. [Genes and inheritance](#genes-and-inheritance)
15. [Associative neural memory](#associative-neural-memory)
16. [MetaObserver](#metaobserver)
17. [Longitudinal investigations](#longitudinal-investigations)
18. [Animals, predators and ecology](#animals-predators-and-ecology)
19. [Caves and refuge](#caves-and-refuge)
20. [Objects, inventory and simple physics](#objects-inventory-and-simple-physics)
21. [Command reference](#command-reference)
22. [Exports](#exports)
23. [Laboratory mode](#laboratory-mode)
24. [Concept clips](#concept-clips)
25. [How to test the auto-life hypothesis](#how-to-test-the-auto-life-hypothesis)
26. [Example simulation stories](#example-simulation-stories)
27. [The “gifted human #27” scenario](#the-gifted-human-27-scenario)
28. [Recommended workflows](#recommended-workflows)
29. [How to publish evidence](#how-to-publish-evidence)
30. [Known limitations](#known-limitations)
31. [Suggested roadmap](#suggested-roadmap)
32. [Suggested repository setup](#suggested-repository-setup)
33. [GitHub upload guide](#github-upload-guide)

---

## What protoH is

`protoH.py` is a 2D terminal simulation of primitive artificial agents called protohumans. The world is drawn with ASCII/ANSI characters. The agents move, eat, drink, sleep, attack, reproduce, carry objects, observe events and die. The important part is not the graphics. The important part is that the agents begin without modern human concepts.

They do not start with a symbolic rule such as:

```text
cave = safe place
T-Rex = danger
water = drink
death = permanent non-movement
I = alive
```

Instead, the simulation tries to let those meanings appear, if they appear at all, through repeated bodily experience.

The world includes:

- protohumans;
- chickens;
- cows;
- T-Rex predators;
- water;
- seeds;
- sticks;
- stones;
- meat;
- caves;
- hunger;
- thirst;
- sleepiness;
- energy;
- damage;
- reproduction;
- death;
- genes;
- associative memory;
- events;
- logs;
- conceptual detectors;
- laboratory controls;
- export tools.

---

## The core idea

The central idea is simple:

> A protohuman should not be given concepts. It should be given a body, needs, actions, memory and a world. If concepts appear, they should emerge from experience.

For example:

- If an agent becomes thirsty and later drinks water, the internal association `water ↔ thirst_reduction` may be reinforced.
- If an agent approaches a T-Rex and receives damage, `trex_shape ↔ pain` may be reinforced.
- If an agent sleeps in a cave and survives repeated attacks outside, `cave_interior ↔ rest` or `cave_interior ↔ less_damage` may become stronger.
- If an agent drops seeds near chickens and chickens approach, the external observer may investigate a possible `bait/trap` proto-concept.
- If an agent repeatedly sees other humans stop moving after damage, the observer may investigate `death/no_movement`.
- If an agent begins to include itself in a class of vulnerable beings, the observer may investigate a weak form of `auto-life`.

None of this proves human-like understanding. The project only asks whether stable, inspectable and behavior-changing associations can arise.

---

## Why this experiment exists

Most modern AI systems are trained on huge amounts of human text. If a chatbot says “I am alive”, it is extremely hard to know whether anything meaningful is happening or whether the model is simply generating language patterns.

`protoH.py` tries a very different path.

Instead of starting with language, it starts with:

- a small body;
- hunger;
- thirst;
- pain;
- sleep;
- energy;
- movement;
- other beings;
- danger;
- death;
- memory;
- heredity;
- a 2D environment.

This makes the experiment closer to artificial life than to a chatbot. The goal is not to build a useful assistant. The goal is to create a tiny world where primitive knowledge may appear from interaction.

---

## The “born without concepts” rule

The most important rule in the project:

> Protohumans are born without abstract knowledge.

They may be born with:

- a position;
- hit points;
- hunger;
- thirst;
- sleepiness;
- energy;
- genes;
- an empty or nearly empty associative memory;
- a body that can move and act;
- primitive ability to eat, drink, sleep, pick up objects, attack and reproduce.

They are not born with:

- knowledge of caves;
- knowledge of refuge;
- knowledge of death;
- knowledge of fear;
- knowledge of tools;
- knowledge of traps;
- knowledge of religion;
- knowledge of language;
- knowledge of “I am alive”.

The closest biological analogy is that a real animal is not born knowing how to build a house, but it can be born with hunger, pain, reflexes, curiosity and a nervous system. `protoH.py` follows that general idea at a toy-simulation level.

---

## What would count as cheating

Because the project is about emergence, it is important to define what would invalidate the experiment.

### Not cheating

These are allowed:

- agents have hunger and seek relief;
- agents have thirst and can drink;
- agents feel damage as negative state;
- agents can prefer lower suffering states;
- agents can form associations through repeated experience;
- agents can inherit genes;
- genes can influence memory, curiosity, exploration and survival;
- an external observer can translate internal patterns into human labels.

### Cheating

These would be cheating in a clean emergence run:

- directly inserting `refuge = cave` into the agent;
- making every agent flee T-Rex because the code says “T-Rex is dangerous” as a concept;
- allowing children to inherit memories;
- giving agents a full symbolic language at birth;
- using `spawnmax`, `immortal`, `faker`, `kill` or `boost` and then pretending the run was natural;
- declaring consciousness from one weak detector signal.

The project therefore distinguishes normal simulation from laboratory intervention.

---

## Architecture overview

At a high level, the code creates a `World` object. That world contains:

- the map grid;
- cave cells;
- water cells;
- items;
- creatures;
- humans;
- event history;
- concept logs;
- unexpected logs;
- complete logs;
- a MetaObserver;
- a gene bank;
- investigations;
- laboratory notes;
- command processing;
- export utilities.

A typical tick does something like this:

1. Advance simulated time.
2. Regrow or update seeds.
3. Update animals.
4. Update predators.
5. Update humans.
6. Register events.
7. Reinforce or decay memory.
8. Run detectors every few ticks.
9. Render the world or advance silently.
10. Process user commands.

The simulation is interactive. You can let it run automatically, pause it, inspect a specific agent, export the evidence, and resume.

---

## Requirements

Recommended:

- Python 3.10 or newer;
- macOS or Linux terminal;
- ANSI-compatible terminal.

The code uses only Python standard library modules such as:

- `math`
- `os`
- `random`
- `re`
- `statistics`
- `time`
- `sys`
- `select`
- `pathlib`
- `termios`
- `tty`
- `subprocess`
- `tempfile`
- `shutil`
- `html`
- `dataclasses`
- `typing`

No external package is required for the basic simulation.

### Windows note

The script uses Unix-oriented terminal modules such as `termios` and `tty`. On Windows, use WSL or adapt the input handling to `msvcrt`.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USER/protoH-emergent-life.git
cd protoH-emergent-life
```

Optional virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Run:

```bash
python3 protoH.py
```

Or:

```bash
chmod +x protoH.py
./protoH.py
```

---

## Quick start

Run the program:

```bash
python3 protoH.py
```

When asked how many initial humans to create, choose a small number for a clean experiment:

```text
2
```

Then use:

```text
auto
```

Let the simulation run. Later pause it:

```text
pause
```

Inspect interesting logs:

```text
logs
valiosos
investigaciones
best_genes
```

Inspect a specific human:

```text
brain 27
tree 27
lineage_watch 27
```

Export useful evidence:

```text
export useful ./exports/run_001_useful.txt
export all ./exports/run_001_full.txt
```

Exit:

```text
q
```

---

## What you see when it runs

The program draws a 2D ASCII map in the terminal. Depending on the mode and terminal, you may see colors for important elements.

A prompt appears:

```text
Command >
```

or:

```text
Comando >
```

Pressing Enter with no command advances the simulation manually. Using `auto` makes it run continuously.

---

## World, map and symbols

Typical symbols:

| Symbol | Meaning |
|---|---|
| `.` | empty ground |
| `~` | water |
| `s` | seed |
| `/` | stick |
| `o` | stone |
| `m` | meat |
| `C` | cave wall |
| `E` | logical cave entrance |
| `I` | logical cave interior |
| `H` | normal human |
| `L` | laboratory human |
| `P` | chicken |
| `V` | cow |
| `T` | T-Rex |

Important detail: cave entrances and interiors may be logically marked as `E` and `I`, but visually rendered like normal ground. This prevents agents from visually receiving an obvious symbolic label saying “this is a special place”.

---

## Time system

The simulation uses ticks.

Important defaults:

```python
TICKS_PER_DAY = 24
MAX_TICKS = 100_000
DETECTOR_EVERY_TICKS = 12
RENDER_EVERY_TICKS = 1
```

This means 24 ticks correspond to one simulated day. The detector runs periodically, not on every single step.

---

## Humans

A human has:

- entity ID;
- birth number;
- name;
- position;
- hit points;
- hunger;
- thirst;
- sleepiness;
- energy;
- age;
- parents;
- genes;
- inventory;
- memory events;
- associative neural memory;
- sleep history;
- last action;
- detected concept reports;
- possible experimental flags such as immortality.

Humans can:

- move;
- drink;
- eat seeds;
- eat meat;
- sleep;
- attack;
- bite;
- pick up items;
- drop items;
- carry a limited inventory;
- use simple weapons;
- reproduce;
- explore;
- interact with caves;
- encounter animals;
- encounter predators;
- receive damage;
- die.

None of these actions automatically means the agent has a concept. Actions create events, and events may reinforce memory.

---

## Genes and inheritance

Each human has a `Genes` object.

Main traits:

| Gene | Approximate meaning |
|---|---|
| `speed` | movement capability |
| `strength` | physical strength, carrying capacity, damage |
| `memory` | memory capacity |
| `curiosity` | tendency to explore and test |
| `sociability` | tendency to remain near humans |
| `aggression` | tendency to attack |
| `association` | tendency to reinforce connections |
| `fertility` | reproduction tendency |
| `sleep_need` | need for sleep |
| `energy_efficiency` | energy economy |
| `weirdness` | unusual actions / experimentation |
| `exploration_spirit` | drive to explore far away |

Children inherit genes with mutation. They do **not** inherit concepts or memories.

This is one of the most important rules in the project:

```text
genes can be inherited
concepts cannot be inherited
memories cannot be inherited
```

A child may be born with high curiosity, high memory and high association. That makes the child more likely to discover things, but it still begins without the discoveries themselves.

---

## Associative neural memory

Each human has a simplified `NeuralMemory`.

It is not a biological brain and not a deep neural network. It is a small associative memory made of:

- node activations;
- weighted connections;
- reinforcement;
- decay.

Examples of possible nodes:

```text
water
thirst_low
trex_shape
pain
cave_interior
rest
sleep_low
weak_hit
seed
chicken_near
human
no_movement
```

Examples of possible connections:

```text
water ↔ thirst_low = +0.42
trex_shape ↔ pain = +0.67
cave_interior ↔ rest = +0.31
sleep_low ↔ weak_hit = +0.28
seed ↔ chicken_near = +0.22
human ↔ no_movement = +0.18
```

The command:

```text
brain NUMBER
```

shows:

- active nodes;
- known nodes;
- reinforced connections;
- important raw events;
- concept reports related to the agent;
- why the external observer suspects a concept.

When the report says “neurons”, it means conceptual/sensory nodes in this toy associative system, not real biological neurons.

---

## MetaObserver

The MetaObserver is an external analysis system. It is not the agent’s mind. It observes events and memory patterns and proposes hypotheses.

It can investigate:

- water/thirst;
- food/hunger;
- sleep/strength;
- cave/safety;
- big creature avoidance;
- fear/pain/danger;
- death/no-movement;
- bait/trap;
- storage/provisions;
- cultural patterns;
- proto-language;
- auto-life;
- unclassified clusters.

A detector report does not mean the concept is certainly real. It means the external observer found evidence worth inspecting.

Good reports include:

- confidence percentage;
- importance;
- subject;
- evidence;
- related events;
- possible interpretation.

---

## Longitudinal investigations

If a signal is interesting, the MetaObserver may open an investigation. This is important because a single event can be accidental.

An investigation tracks:

- investigation ID;
- origin human;
- subject human;
- category;
- hypothesis;
- start tick/day;
- expiration tick;
- evidence for;
- evidence against;
- confidence;
- state;
- whether it became valuable;
- possible lineage watch.

Examples:

```text
INV17 H34 fear_death 71.0% STRONG OBSERVATION
INV22 H27 refuge 64.0% UNDER REVIEW
INV31 H52 bait_trap 48.0% WEAK BUT INTERESTING
```

Use:

```text
investigaciones
investigaciones_valiosas
investigar NUMBER
lineage_watch NUMBER
```

---

## Animals, predators and ecology

### Chickens

Chickens are small animals. They may move, eat, cluster around food and become prey. Their behavior can become relevant for bait/trap detection.

### Cows

Cows occupy more space and may damage humans. They can reproduce and influence ecology.

### T-Rex

T-Rex are large predators. They occupy several cells. They only pursue/attack if a human is close enough. They reproduce periodically but are capped by a maximum population.

Important settings include:

```python
INITIAL_TREX = 2
MAX_TREX = 7
TREX_REPRODUCE_EVERY_DAYS = 10
TREX_AGGRO_RADIUS = 3.0
```

Predator behavior matters because danger and refuge concepts need real survival pressure.

### Ecology

The world includes seed regeneration and animal dispersal controls to avoid everything accumulating in one corner. This makes food and movement more meaningful.

Use:

```text
seed_stats
export seed_stats ./exports/seed_stats.txt
```

---

## Caves and refuge

Caves are one of the most important experimental features.

They contain:

- walls;
- entrances;
- interiors.

But entrances/interiors are not simply shown as obvious “safe place” icons. A human may enter a cave by accident, curiosity, fleeing, or random movement.

A possible refuge concept becomes more interesting if the human:

- enters after danger;
- sleeps inside;
- receives less damage inside;
- survives repeated predator pressure;
- returns later;
- forms connections such as `cave_interior ↔ rest` or `cave_interior ↔ less_damage`;
- changes behavior in a stable way.

A weak cave event is not enough. A repeated pattern is needed.

---

## Objects, inventory and simple physics

Objects:

| Object | Symbol | Possible role |
|---|---|---|
| seed | `s` | food, possible bait |
| stick | `/` | portable object, weak weapon |
| stone | `o` | portable object, stronger weapon |
| meat | `m` | food |
| cave wall | `C` | physical obstacle |

The inventory is limited:

```python
MAX_INVENTORY_ITEMS = 5
ALLOWED_INVENTORY_KINDS = {"seed", "stick", "stone", "meat"}
```

Humans cannot carry unlimited objects and cannot pick up cave walls. This keeps the world from becoming magical.

---

# Command reference

Commands are typed at the prompt.

---

## Help commands

### `help`

Show general help.

Aliases:

```text
help
ayuda
comandos
?
```

### `help sim`

Show simulation commands.

```text
help sim
ayuda sim
```

### `help export`

Show export commands.

```text
help export
ayuda export
```

### `help humans`

Show human/population commands.

```text
help humans
help human
help población
help poblacion
```

### `help lab`

Show laboratory commands.

```text
help lab
ayuda lab
lab help
```

### `help detector`

Show detector and concept commands.

```text
help detector
help conceptos
```

### `help debug`

Show debug commands.

```text
help debug
help fallos
```

### `help kill`

Show kill command help.

```text
help kill
kill_help
```

---

## Basic simulation commands

### Empty Enter

Advance manually.

```text
Command >
```

### `auto`

Start automatic mode.

Aliases:

```text
auto
run
play
```

### `pause`

Pause or resume.

Aliases:

```text
pause
pausar
```

### `stop`

Return to manual mode.

Aliases:

```text
stop
manual
```

### `delay X`

Set delay between cycles.

Examples:

```text
delay 0.1
delay 0.05
delay 0
```

### `speed X`

Set ticks per cycle.

Examples:

```text
speed 1
speed 10
speed 100
speed 1000
```

### `fast`

Toggle adaptive turbo mode.

```text
fast
fast off
turbo
turbo off
```

### `q`

Quit.

Aliases:

```text
q
quit
salir
exit
```

---

## Population commands

### `spawn X`

Create X humans without parents.

```text
spawn 5
```

They do not inherit concepts.

### `spawn X PARENT1,PARENT2`

Create children from two specific birth numbers.

```text
spawn 5 9,24
```

Children inherit genes only, with mutation.

### `spawn X best`

Create humans from the best available genes.

```text
spawn 20 best
```

### `spawn X bank`

Create humans from the gene bank.

Aliases:

```text
spawn 20 bank
spawn 20 elite
spawn 20 preserved
```

### `spawn X max`

Create humans with extremely high useful genes.

```text
spawn 10 max
```

They still do not inherit concepts or memories.

### `spawnmax X`

Alias family for max-gene humans:

```text
spawnmax 10
spawn_max 10
spawn100 10
spawn_100 10
maxhumans 10
```

### `spawn_nolearn X`

Create real humans that cannot learn concepts.

```text
spawn_nolearn 10
spawn_nolearn 10 max
```

Useful for false-positive testing.

### `auto_spawn_1`

Toggle emergency auto-spawn when population collapses.

```text
auto_spawn_1
```

### `auto_spawn_1 N`

Set amount:

```text
auto_spawn_1 50
```

### `auto_spawn_1 off`

Disable it:

```text
auto_spawn_1 off
```

---

## Genetic preservation and boosting

### `boost NUMBER vida AMOUNT`

Increase max/current HP.

```text
boost 27 vida 20
```

### `boost NUMBER sed VALUE`

Increase thirst resistance.

```text
boost 27 sed 1.5
```

### `boost NUMBER hambre VALUE`

Increase hunger resistance.

```text
boost 27 hambre 1.5
```

### `boost NUMBER vejez VALUE`

Increase old-age resistance.

```text
boost 27 vejez 1.5
```

### `boost NUMBER all`

Apply full boost and preserve the human.

```text
boost 27 all
```

### `preserve NUMBER`

Add a human to the gene bank.

```text
preserve 27
```

Aliases:

```text
guardar_genes 27
proteger 27
```

### `gene_bank`

Show preserved genes.

Aliases:

```text
gene_bank
banco_genes
bank
elite
```

### `best_genes`

Show best genes.

Aliases:

```text
best_genes
genes
topgenes
best
```

### `tops`

Show rankings.

```text
tops
top
rankings
listas
```

Examples:

```text
top curiosidad
top memoria
top exploracion
```

---

## Concept and log commands

### `logs`

Show concept/useful logs.

Aliases:

```text
logs
conceptos
important
importantes
```

### `fallos`

Show unexpected actions/failures.

Aliases:

```text
fallos
errores
no_previstos
noprevistos
```

### `todos_logs`

Show complete session history.

Aliases:

```text
todos_logs
todo
all_logs
alllogs
```

### `valiosos`

Show valuable reports only.

Aliases:

```text
valiosos
valuable
valuable_logs
logs_valiosos
importantes_valiosos
```

### `investigaciones`

Show investigations.

Aliases:

```text
investigaciones
investigations
investigation
invests
```

### `investigaciones_valiosas`

Show valuable investigations only.

Aliases:

```text
investigaciones_valiosas
investigaciones utiles
investigaciones_útiles
valuable_investigations
```

### `investigar NUMBER`

Detailed investigation report for a human.

```text
investigar 27
```

Alias:

```text
investigate 27
```

### `lineage_watch NUMBER`

Lineage watch report.

```text
lineage_watch 27
```

Aliases:

```text
lineage watch 27
linaje_watch 27
linaje 27
```

---

## Brain and genealogy commands

### `brain NUMBER`

Show full neural/memory report.

```text
brain 27
```

Aliases:

```text
neuronal 27
mente 27
```

Includes:

- status;
- genes;
- needs;
- inventory;
- detected concepts;
- activations;
- reinforced connections;
- important raw events;
- reasoning behind external concept hypotheses.

### `tree NUMBER`

Show genealogy.

```text
tree 27
```

Includes:

- target human;
- ancestors;
- siblings;
- reproductive partners;
- children;
- grandchildren;
- descendants;
- main direct line;
- important badges.

---

## Immortality commands

### `immortal NUMBER`

Make a human immortal.

```text
immortal 27
```

Alias:

```text
inmortal 27
```

This is experimental and should be disclosed in evidence.

### `mortal NUMBER`

Remove immortality.

```text
mortal 27
```

Aliases:

```text
noimmortal 27
no_inmortal 27
```

Immortal humans are useful for controls but should not be used to claim natural emergence.

---

## Auto-life / life candidates

### `auto_vida`

Show possible external-life or auto-life candidates.

Aliases:

```text
auto_vida
autovida
vida
life
life_candidates
candidatos_vida
```

This report is about functional evidence, not proof of consciousness.

---

## Detector metrics

### `detector_metrics`

Show detector metrics.

Aliases:

```text
detector_metrics
metricas_detector
métricas_detector
detector v2
detector_v22
```

Useful for checking false positives and signal quality.

---

## Proto-language

### `lenguaje`

Show proto-language / signal report.

Aliases:

```text
lenguaje
proto_lenguaje
language
proto_language
señales
senales
```

This does not mean human language. It means possible repeated social signals or patterns.

---

## Seed statistics

### `seed_stats`

Show seed distribution statistics.

Aliases:

```text
seed_stats
semillas
seedmap
seed_stats_v231
```

---

## Kill command

### `kill SPECIES AMOUNT`

External intervention to remove entities.

Examples:

```text
kill t-rex 5
kill trex all
kill cow 20
kill chicken 10
kill human 3
kill lab all
kill all all
```

This is not a natural event. Always disclose it when sharing evidence.

---

## Error commands

### `error`

Show recorded errors.

Aliases:

```text
error
errors
errores
errores_brutos
```

### `error last`

Show last error.

```text
error last
```

### `error ID`

Show a specific traceback.

```text
error 3
```

---

# Exports

Exports are essential for making the experiment auditable.

## Logs

```text
export_logs ./exports/logs.txt
exportar_logs ./exports/logs.txt
export logs ./exports/logs.txt
```

## Concepts

```text
export conceptos ./exports/concepts.txt
```

## Failures

```text
export fallos ./exports/failures.txt
```

## Useful pack

```text
export useful ./exports/protoH_useful.txt
export util ./exports/protoH_useful.txt
export_valiosos ./exports/protoH_useful.txt
export important ./exports/protoH_useful.txt
```

Recommended for sharing concise evidence.

## Full export

```text
export all ./exports/protoH_FULL.txt
export_todo ./exports/protoH_FULL.txt
export absoluto ./exports/protoH_FULL.txt
export everything ./exports/protoH_FULL.txt
```

Use before closing a long run.

## Investigations

```text
export investigations ./exports/investigations.txt
export investigaciones ./exports/investigations.txt
```

## Lineage

```text
export lineage 27 ./exports/lineage_27.txt
export linaje 27 ./exports/lineage_27.txt
```

## Brain

```text
export brain 27 ./exports/brain_27.txt
export_brain 27 ./exports/brain_27.txt
```

## All brains

```text
export brains all ./exports/brains/
```

## Tree

```text
export tree 27 ./exports/tree_27.svg
export tree all ./exports/tree_all.svg
export trees all ./exports/trees/
```

## Laboratory

```text
export lab ./exports/lab.txt
export lab all ./exports/lab_pack/
```

## Auto-life

```text
export auto_life ./exports/auto_life.txt
export autovida ./exports/auto_life.txt
export vida ./exports/auto_life.txt
```

## Detector metrics

```text
export detector_metrics ./exports/detector_metrics.txt
export metricas_detector ./exports/detector_metrics.txt
export métricas_detector ./exports/detector_metrics.txt
```

## Proto-language

```text
export lenguaje ./exports/language.txt
export proto_lenguaje ./exports/language.txt
export language ./exports/language.txt
```

## Seed stats

```text
export seed_stats ./exports/seed_stats.txt
export semillas ./exports/seeds.txt
```

## Concept clips

```text
export clip 3 ./exports/clip_3.html
export clip 3 ./exports/clip_3.txt
export clips all ./exports/clips/
```

---

# Laboratory mode

Laboratory mode creates special test humans. These are not necessarily natural agents.

LAB humans usually appear as `L`.

Laboratory principles:

- LAB agents may be isolated from normal reproduction.
- LAB agents can be used to test detectors.
- LAB agents do not automatically prove natural emergence.
- LAB agents can be immortal or controlled.
- LAB results should be separated from clean simulation runs.

## Basic LAB commands

### `lab`

Show lab help.

```text
lab
lab help
help lab
```

### `lab spawn X`

Create lab humans.

```text
lab spawn 5
```

### `lab spawn X max`

Create high-gene lab humans.

```text
lab spawn 5 max
```

### `lab spawn X concept CONCEPT`

Create lab humans focused on a concept route.

```text
lab spawn 5 concept refugio
lab spawn 5 concept muerte
lab spawn 5 concept trampa
lab spawn 5 concept distancia
```

This does not mean they are born knowing the concept. It means they are useful for investigating that concept path.

Possible concept focuses:

```text
vida
muerte
miedo
refugio
agua
comida
trampa
almacenamiento
distancia
dimension
social
herramienta
sueño_fuerza
```

### `lab list`

List lab subjects.

```text
lab list
```

### `lab watch NUMBER`

Inspect a lab subject.

```text
lab watch 27
```

### `lab watch concept CONCEPT`

Inspect subjects related to a concept.

```text
lab watch concept refugio
```

### `lab report`

Show lab report.

```text
lab report
```

### `lab clear`

Mark living LAB subjects as dead.

```text
lab clear
```

### `lab isolate on/off`

Control reproductive isolation.

```text
lab isolate on
lab isolate off
```

## Advanced LAB

### `lab detector X CONCEPT`

Create detector-test subjects.

```text
lab detector 5 distancia
lab detector 5 refugio
```

### `lab bugs X`

Create bug hunters.

```text
lab bugs 5
```

Possible physical/logical tests:

- combine objects;
- move cave;
- hit air;
- pick heavy object;
- route edge;
- stack stones;
- drop/pick repeatedly.

### `lab faker X all`

Create fake-discovery subjects.

```text
lab faker 3 all
```

### `lab faker X vida,refugio`

```text
lab faker 2 vida,refugio
```

### `lab fake_report`

Show false discovery audit.

Aliases:

```text
lab fakereport
lab audit
lab auditoria
lab auditoría
```

---

# Concept clips

Concept clips are small evidence packages. They can capture context around an important concept report.

Commands:

```text
clips
concept_clips
clip list
clips list
clips on
clip on
clips off
clip off
play clip 3
clip play 3
clip 3
clip settings
export clip 3 ./clip_3.html
export clips all ./clips/
```

Recommended use:

1. Run a long simulation.
2. When a gold/purple report appears, run `clips`.
3. Open the relevant clip with `play clip N`.
4. Export it.
5. Share it with `brain`, `tree` and logs.

---

# How to test the auto-life hypothesis

The strongest public question is:

> Can an artificial agent born without concepts develop a functional proto-belief of being alive?

In this project, that would not mean true consciousness. It would mean something like:

```text
self-like entity ↔ human
human ↔ pain
human ↔ hunger/thirst/sleep
human ↔ movement
human ↔ no_movement/death
self-like entity ↔ vulnerable
vulnerable ↔ avoid_damage
refuge ↔ less_damage/rest
group ↔ safety/wellbeing
```

And those associations should affect behavior.

## Minimum evidence

A plausible case should include:

1. The human was not a faker.
2. The human was not `spawn_nolearn`.
3. The human was not given inserted concepts.
4. The human experienced relevant events.
5. `brain NUMBER` shows coherent connections.
6. Behavior changed after experience.
7. The evidence is not a single isolated accident.
8. Logs can be exported and audited.
9. The run discloses external interventions.
10. Controls are run when possible.

## Strong evidence

A stronger case includes:

- before/after behavior;
- concept clips;
- comparison with similar humans;
- lab faker controls;
- no-learn controls;
- multiple runs;
- lineage analysis.

## Extraordinary evidence

An extraordinary case would show a stable network involving:

```text
self
human
pain
no_movement
death
avoidance
refuge
group
```

and long-term behavior consistent with self-preservation.

Still, that would be called **functional proto-auto-life**, not proven consciousness.

---

# Example simulation stories

## Example 1 — Water/thirst

1. Human becomes thirsty.
2. It moves.
3. It reaches water.
4. It drinks.
5. Thirst drops.
6. `water ↔ thirst_low` strengthens.
7. Detector reports possible water/thirst association.

Possible report:

```text
Human #12 shows water/thirst association, confidence 62%.
```

## Example 2 — T-Rex danger

1. Human explores.
2. T-Rex enters aggression radius.
3. T-Rex attacks.
4. Human receives damage.
5. Human survives.
6. Later it avoids similar shapes/areas.
7. `trex_shape ↔ pain` strengthens.
8. Detector investigates danger/fear.

## Example 3 — Cave refuge

1. Human receives damage outside.
2. It enters a cave by chance or exploration.
3. It rests inside.
4. Predator cannot reach it.
5. It repeats the pattern.
6. `cave_interior ↔ rest` strengthens.
7. Detector reports possible refuge.

## Example 4 — Seed bait

1. Human carries seeds.
2. It drops seeds near chickens.
3. Chickens approach.
4. Human attacks or approaches them.
5. Pattern repeats.
6. `seed ↔ chicken_near` strengthens.
7. Detector investigates bait/trap.

## Example 5 — Storage

1. Human picks up food.
2. It does not eat immediately.
3. It carries food.
4. It drops food near a repeated location.
5. It later returns and eats.
6. Detector investigates storage/provisions.

## Example 6 — Sleep and strength

1. Human sleeps too little.
2. It attacks weakly.
3. Later it sleeps enough.
4. It attacks more effectively.
5. `sleep_low ↔ weak_hit` and `rested ↔ strong_hit` strengthen.

## Example 7 — Proto-language

1. Several humans cluster.
2. A repeated social signal appears.
3. Other humans react.
4. The signal repeats.
5. Language report marks possible proto-signal.

This is not human language. It is a primitive repeated social pattern.

---

# The gifted human #27 scenario

A human such as `#27` may become interesting if it is born with unusually good genes:

- high curiosity;
- high memory;
- high association;
- high exploration;
- good energy efficiency;
- enough strength;
- useful weirdness.

Such a human may:

- explore more;
- survive more;
- test unusual interactions;
- form more associations;
- generate more concept investigations;
- become a key ancestor.

To analyze it:

```text
brain 27
tree 27
lineage_watch 27
```

If valuable:

```text
preserve 27
spawn 20 27,OTHER
spawn 20 best
spawn 20 bank
```

Important: even if #27 is exceptional, children do not inherit #27’s memories or concepts. They inherit only genetic potential.

---

# Recommended workflows

## Clean natural run

```text
python3 protoH.py
```

Choose:

```text
2
```

Use mainly:

```text
auto
pause
logs
valiosos
investigaciones
best_genes
brain NUMBER
tree NUMBER
lineage_watch NUMBER
export useful ./runs/run_001_useful.txt
export all ./runs/run_001_full.txt
```

Avoid for clean runs:

```text
spawnmax
spawn X max
spawn X immortal
spawn_nolearn
lab faker
lab detector
lab bugs
boost
kill
preserve
```

Those are useful for lab/debug, not for pure emergence evidence.

## Search for exceptional humans

```text
auto
speed 100
fast
best_genes
tops
gene_bank
valiosos
```

If population collapses:

```text
auto_spawn_1 50
```

## Study refuge

```text
lab spawn 10 concept refugio
auto
lab watch concept refugio
investigaciones_valiosas
export lab ./exports/lab_refuge.txt
```

## False-positive test

```text
spawn_nolearn 20 max
detector_metrics
auto
detector_metrics
valiosos
fallos
```

If no-learn subjects produce strong “concepts”, the detector may be too generous.

## Debug physical/logical failures

```text
lab bugs 10
lab fake_report
fallos
error
export fallos ./exports/failures.txt
export detector_metrics ./exports/detector_metrics.txt
```

## Save everything

```text
export useful ./exports/protoH_useful.txt
export all ./exports/protoH_FULL.txt
export clips all ./exports/clips/
```

---

# How to publish evidence

When reporting an interesting case, include:

```text
brain NUMBER
export brain NUMBER ./evidence/brain_NUMBER.txt

tree NUMBER
export tree NUMBER ./evidence/tree_NUMBER.svg

lineage_watch NUMBER
export lineage NUMBER ./evidence/lineage_NUMBER.txt

conceptos
valiosos
investigaciones
clips

export useful ./evidence/useful.txt
export all ./evidence/full.txt
export clips all ./evidence/clips/
```

Write:

- human number;
- day/tick;
- suspected concept;
- confidence;
- why it matters;
- evidence for;
- evidence against;
- possible false positives;
- whether lab mode was used;
- whether `spawnmax`, `immortal`, `boost`, `kill` or `preserve` were used;
- whether controls were run.

---

# Known limitations

## Not consciousness

The simulation does not prove real consciousness.

## External interpretation

The MetaObserver uses human labels. Labels are interpretations, not direct access to subjective experience.

## False positives

Detectors can overinterpret behavior. Use lab controls.

## Monolithic code

The project is currently a large single Python file. That made rapid experimentation easy, but modularization would improve maintainability.

## Command layering

Command processing evolved through successive wrappers. A dispatcher-based architecture would be cleaner.

## Parameter sensitivity

Small changes to hunger, thirst, seeds, predator radius, reproduction or gene mutation may strongly affect results.

## Terminal performance

ASCII rendering can be slow. Use `speed`, `delay` and `fast`.

## No real language yet

Proto-language detection is only a first step. It does not prove symbolic communication.

## No real culture yet

Genes are inherited, but cultural knowledge is not yet robustly transmitted unless later versions add imitation/teaching.

---

# Suggested roadmap

## 1. Modularize

Suggested structure:

```text
protoh/
├── main.py
├── world.py
├── human.py
├── animals.py
├── genes.py
├── memory.py
├── metaobserver.py
├── commands.py
├── export.py
├── lab.py
└── render.py
```

## 2. Save/load simulations

Add:

```text
save ./saves/run1.json
load ./saves/run1.json
```

## 3. Improve social learning

Add:

- imitation;
- warning calls;
- food calls;
- refuge calls;
- teaching;
- group memory;
- cultural transmission.

## 4. Progressive construction

Let agents eventually learn to:

- move stones;
- stack sticks;
- build barriers;
- build huts;
- mark paths;
- store food;
- create primitive shelters.

## 5. Weather and disasters

Add:

- rain;
- storms;
- wind;
- cold;
- heat;
- drought;
- floods;
- earthquakes;
- fires;
- seasons.

## 6. Generational civilization

Add:

- proto-language;
- roles;
- parenting;
- elder knowledge;
- agriculture;
- domestication;
- burial-like behavior;
- rituals;
- territory;
- migration.

## 7. Visualizer

Build a web or pygame viewer for:

- world map;
- agent trails;
- neural connections;
- family trees;
- concept clips;
- population graphs.

## 8. Research mode

Add reproducible runs:

```text
--seed 1234
--days 1000
--export ./runs/seed_1234/
```

---

# Suggested repository setup

Recommended repository name:

```text
protoH-emergent-life
```

Alternative names:

```text
protoH
protoH-artificial-life
protoH-emergent-consciousness
protohumans-emergent-mind
protoH-zero-knowledge-life-simulation
```

Recommended description:

```text
Artificial-life experiment where protohumans start without concepts and a detector tracks learned ideas like refuge, danger, death and auto-life, aiming to explore whether one can develop a functional proto-belief of being alive.
```

Recommended topics:

```text
artificial-life
emergent-behavior
ai-consciousness
agent-based-simulation
python
simulation
proto-language
cognitive-architecture
digital-organisms
survival-simulation
```

Recommended files:

```text
protoH-emergent-life/
├── protoH.py
├── README.md
├── README_ES.md
├── LICENSE
├── NOTICE
└── .gitignore
```

---

# GitHub upload guide

## Option A — GitHub web

1. Go to GitHub.
2. Click **New repository**.
3. Repository name:

```text
protoH-emergent-life
```

4. Description:

```text
Artificial-life experiment where protohumans start without concepts and a detector tracks learned ideas like refuge, danger, death and auto-life, aiming to explore whether one can develop a functional proto-belief of being alive.
```

5. Choose **Public**.
6. Do not generate a README if you already have this one.
7. Create repository.
8. Click:

```text
Add file → Upload files
```

9. Upload:

```text
protoH.py
README.md
README_ES.md
LICENSE
NOTICE
.gitignore
```

10. Commit message:

```text
Initial release of protoH emergent life experiment
```

11. Click **Commit changes**.

## Option B — Terminal

```bash
cd /path/to/protoH-emergent-life

git init
git add protoH.py README.md README_ES.md LICENSE NOTICE .gitignore
git commit -m "Initial release of protoH emergent life experiment"
git branch -M main
git remote add origin https://github.com/YOUR_USER/protoH-emergent-life.git
git push -u origin main
```

Replace `YOUR_USER` with your GitHub username.

---

# Short public post

Use this to announce the project:

```text
I built protoH: a Python artificial-life experiment where agents are born without concepts and may develop primitive functional ideas of refuge, danger, death and possibly “being alive” through hunger, thirst, pain, memory and survival pressure.

It does not claim consciousness. It tries to make the question testable.
```

Spanish version:

```text
He creado protoH: un experimento de vida artificial en Python donde pequeñas IAs nacen sin conceptos y podrían llegar a desarrollar ideas primitivas de refugio, peligro, muerte y quizá de estar vivas mediante hambre, sed, dolor, memoria y presión de supervivencia.

No afirma haber creado conciencia. Intenta hacer la pregunta comprobable.
```

---

# Final summary

`protoH.py` is an artificial-life simulation centered on a radical but careful question:

> If an artificial creature is born without concepts, can experience alone create functional proto-concepts of danger, refuge, death and self-preservation?

The answer is not assumed. The project is designed so people can run it, inspect it, export evidence, challenge the detectors, create controls and improve the simulation.

The strongest possible future result would not be “proof of consciousness”. It would be something still fascinating:

> A simple artificial agent developing a stable, auditable, behavior-changing functional model of being a vulnerable entity in a world where damage, refuge, other beings and non-movement matter.

That is what `protoH` tries to explore.
