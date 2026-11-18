# Research report — cycle 2026-11-18

`candidates.json` (generated 2026-11-18T09:22Z) is heavily polluted this cycle.
Before the top 10, see **Excluded as coordinated spam** below — it matters
for novelty-b's prior-art pass, since several "huge" entries in the raw data
are fake.

Mix: 3 from `week`, 7 from `year`. The `week` list is almost entirely spam
clusters (details below); only 3 items in it had real, substantive code.

## Top 10

### 1. [mit-han-lab/pear](https://github.com/mit-han-lab/pear) — week
**What it does:** "Training Reasoning Models in Simulation to Natively Use
Real Robots." A framework from MIT Han Lab (real research group, known for
TinyML/efficient-AI work) for training VLA-style reasoning policies in sim
and deploying them on physical robots without a separate sim-to-real
fine-tuning stage. Repo has `pear/` core package, `examples/`, `tests/`,
`docs/`, `3rdparty/` submodules, pre-commit config — a real working codebase,
not a paper stub.
**Why it matters:** one of the only genuinely embodied-AI entries this cycle;
momentum is real (139 stars/day on a 5-day-old repo from a credible lab).
**License:** Apache-2.0. **Run locally:** needs a robot or sim backend
(likely MuJoCo/Isaac) — heavier to run than a pure-software repo, but the
*policy/training* half is inspectable and reusable without hardware.
**Build-on hint:** the simulation-to-real transfer recipe could be mined for
a lightweight "does this trained policy actually transfer" eval harness,
decoupled from needing a real robot.

### 2. [berkantay/gpucanvas](https://github.com/berkantay/gpucanvas) — week
**What it does:** Puts thousands of live DOM nodes on a WebGPU-rendered
infinite canvas — an editor can select/move/resize them, shaders and
transitions run on the GPU, and an AI agent can read the scene graph and
point at specific nodes. Real TypeScript codebase (`src/`, `demo/`, `docs/`,
tsup build, has `AGENTS.md`/`CLAUDE.md`).
**Why it matters:** a rare *agent-legible visual surface* — most agent UI
work is text-only; this gives an agent a structured way to perceive and act
on a spatial canvas (whiteboard/design-tool style).
**License:** MIT. **Run locally:** easy — `bun install`, browser demo, no
GPU-cluster or API key needed (just WebGPU-capable browser).
**Build-on hint:** an agent skill that reads gpucanvas's scene graph and
answers "what changed since last frame" or drives a multi-step layout task
could be a thin, demo-able wrapper.

### 3. [erkamyaman/rust-anything](https://github.com/erkamyaman/rust-anything) — week
**What it does:** Agent skill/CLI that rewrites a whole app into Rust
incrementally, piece by piece, checking each migrated unit against the
*recorded behavior* of the original (TS/Python/C/Go/Ruby/Java sources via
FFI). Has `.claude-plugin`, `skills/`, `npm/` wrapper, `Cargo.toml`, real
decision log (`DECISIONS.md`).
**Why it matters:** code migration-with-verification is a concrete, scoped
agent task (unlike open-ended "write an app" skills) — the behavior-recording
step is the interesting part.
**License:** MIT. **Run locally:** CLI + Cargo toolchain, straightforward.
**Build-on hint:** the "record behavior, check each rewritten unit against
it" harness is generalizable beyond Rust — could be stripped down into a
language-agnostic regression oracle for any agent-driven refactor.

### 4. [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) — year
**What it does:** DeepSeek's own agent harness/plugin runtime ("Everything is
a Plugin") — a large monorepo (apps/, packages/, native/, python/, benchmarks/,
website/, full i18n docs) that appears to be the substrate several *other*
candidates in this dataset plug into (the `dsh-plugin` topic shows up on
`Ebony-Vinyl/dsh-our-free-model`, `ccch1mneyyy/dsh-Go`, `tt-a1i/archify`).
**Why it matters:** if an ecosystem of plugins is genuinely forming around
it, it's a live integration target, not just a popular repo.
**License:** MIT, org-owned (`deepseek-ai`, verified via API — real org).
**Run locally:** heavier — full pnpm workspace, native bindings; expect a
non-trivial setup.
**Build-on hint:** writing a single well-scoped `dsh-plugin` is the lowest-
friction way to reach an already-assembled audience, rather than competing
with the harness itself.

### 5. [HKUDS/DeepTutor](https://github.com/HKUDS/DeepTutor) — year
**What it does:** "Lifelong Personalized Tutoring" — a multi-agent
RAG/deep-research tutoring system from HKUDS (Hong Kong University Data
Science Lab, a real, prolific research org — also behind LightRAG).
**Why it matters:** genuine multi-agent system with a clear end-user
(persistent personalized tutor), not a dev-tooling meta-skill.
**License:** Apache-2.0, org-owned (verified). **Run locally:** Python,
likely needs an LLM API key + vector store; moderate setup.
**Build-on hint:** the "lifelong" memory-of-the-learner piece is the novel
part — a narrower single-subject version of that memory model could be a
scoped weekend build.

### 6. [google/elephant-goldfish-model](https://github.com/google/elephant-goldfish-model) — year
**What it does:** An open-source plugin for designing and reviewing software
*with* agents — supports Claude Code, Codex, Gemini, Cursor, Windsurf plugin
surfaces simultaneously (`.claude-plugin`, `.codex-plugin`, `.cursor-plugin`,
`.gemini`, `.windsurf` dirs all present). Confirmed real `google` org via API.
**Why it matters:** cross-harness plugin design patterns are reusable
regardless of which agent CLI wins; worth studying the adapter layer.
**License:** Apache-2.0. **Run locally:** plugin install into an existing
agent CLI, light.
**Build-on hint:** its `adapters/` directory is a good reference for writing
one skill that works across Claude Code / Codex / Gemini CLI without
duplicating logic per-harness.

### 7. [vercel-labs/ui](https://github.com/vercel-labs/ui) — year
**What it does:** A library of accessible, headless *behaviors* (not
styled components) meant for agents to compose into generated UIs — ARIA-
correct primitives for React and Solid. Real Vercel Labs repo, `benchmarks/`,
changesets, full CI.
**Why it matters:** addresses a real failure mode of agent-generated UI
(inaccessible, inconsistent interaction patterns) at the behavior layer
instead of the visual layer.
**License:** Apache-2.0. **Run locally:** standard npm/bun package, trivial.
**Build-on hint:** an agent skill that audits generated UI against these
behavior contracts (did the agent wire up the right ARIA roles/keyboard
handling?) would directly extend this.

### 8. [microsoft/TokenEconomizer](https://github.com/microsoft/TokenEconomizer) — year
**What it does:** "Experience-Driven Black-Box Cost Control for Coding
Agents" — learns from past agent runs to cut token spend without touching
the agent's internals. Real Microsoft repo: `tokeneconomizer/` package,
`experiments/`, `plugin/`, tests, pyproject.
**Why it matters:** cost control is being treated as a first-class, black-box
problem (works without forking the agent) rather than a harness-specific hack.
**License:** MIT. **Run locally:** Python package + a target agent's logs;
moderate.
**Build-on hint:** the "black-box, experience-driven" framing (learn a
policy from traces, not from editing the agent) could be ported to a
different axis than cost — e.g. latency or risk — using the same trace format.

### 9. [headroomlabs-ai/headroom](https://github.com/headroomlabs-ai/headroom) — year
**What it does:** Compresses tool outputs, logs, files and RAG chunks before
they hit the LLM context — ships as a library, a proxy, and an MCP server.
Claims 60-95% token reduction on JSON with same answers. Large, mature repo
(act CI, gitleaks, release-please, devcontainer — production-grade hygiene).
**Why it matters:** context-compression-as-infrastructure is a recurring
theme this cycle (also see `rtk-ai/rtk`, `JuliusBrussee/caveman` in the raw
data) — worth noting as a crowded space, not a gap.
**License:** Apache-2.0. **Run locally:** pip/cargo install, light as a
library; proxy mode needs more setup.
**Build-on hint:** given how crowded this niche already is, building
*directly* on compression would mostly be prior-art collision — more
promising is compression applied to a specific, under-served payload type
(e.g. multi-modal tool output, not just text/JSON).

### 10. [tangency-labs/solidcraft](https://github.com/tangency-labs/solidcraft) — year
**What it does:** Open-source parametric 3D CAD application in pure Rust —
desktop, web (wasm/egui), and automatable via a built-in MCP server. Serious
engineering repo: `solidcore/` BREP kernel, `crates/`, `xtask`, full license
attribution trail, `ROADMAP.md`.
**Why it matters:** CAD is a domain agents have barely touched because the
geometry kernels are hard; this gives an MCP surface to drive real parametric
modeling, which is a genuinely new capability unlock, not a wrapper.
**License:** MIT/Apache-2.0 dual (plus a separate brand license — check
`LICENSE-BRAND` before reusing marks). **Run locally:** Rust toolchain via
`flake.nix`/`rust-toolchain.toml`; moderate build time, no GPU needed for the
core kernel.
**Build-on hint:** an agent skill that takes a plain-language part
description and drives solidcraft's MCP server to produce a parametric model
— then renders and self-checks dimensions — is a concrete, demoable slice
of "agents doing real CAD."

## Honorable mentions (verified real, didn't make the top 10)

- [Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach) —
  CLI giving an agent read/search access to Twitter, Reddit, YouTube,
  GitHub, Bilibili, XiaoHongShu with zero API fees. Real Python package,
  MIT. Worth a look if novelty wants an "agent perceives the social web" angle.
- [stablyai/orca](https://github.com/stablyai/orca) — runs a fleet of coding
  agents (Claude Code, Codex) across desktop/mobile/remote under one
  subscription. Real repo, MIT, heavy (full cloud/ dir).

## Excluded as coordinated spam

The raw `candidates.json` is dominated by what looks like deliberate star-
farming. Flagging explicitly since novelty-b's job is prior-art/cost
skepticism, and these inflate the apparent size of several "themes":

- **`Gemini-Config-Checker-`, ~20 near-duplicate repos** (owners:
  `YellowLaborerMarket`, `WingDataVacuum`, `weightcashiercupola`,
  `WinnerSpecialist`, `WharfBoulderColander`, `WireProvostPucker`,
  `WindGatorRise37`, etc. — generated-looking adjective+noun usernames).
  Identical description, identical topic list, nearly identical star counts
  (473-475) and `stars_per_day` (~175.7-176.6) across all clones, all created
  within the same ~90-second window on 2026-11-15. Confirmed one has real Go
  code (`main.go`, `android/`, `desktop/`) — so it's not an empty clone, but
  the duplication pattern is a star-fraud signature, and the product itself
  (finding proxy configs to bypass geo-blocks into Google AI Studio/Gemini)
  is an access-circumvention tool, not something to build on.
- **`ai--manus2.0`, ~8 near-duplicate repos** (owners: `topapothecarycanal`,
  `toppatronweave`, `topconstableinlet67`, `violetkomodolimit`,
  `trackersnailgrip`, `Ultimateakiln`, `taboospecialistblade`,
  `Tonephorepair`, `TrapBladesmith`). Checked one's contents directly:
  **`LICENSE`, `README.md`, `license.md` only — no code at all.** Pure
  star-farm clones of a real upstream project's README.
- **`blender-ai-copilot-*` / `Blender-AI-MCP-Studio`, 4 near-duplicate repos**
  (owners: `credoksopho1984`, `racdeufindurch198812`, `tiobeharxi1987`,
  `Doug-218`) — same template description repeated with keyword-stuffed
  variations ("blender ai copilot", "blender ai mcp studio", ...), same
  topic list, star counts clustered 510-516. Same signature as above.
- **`morluto/rea`** — claims 467,123 stars / 2,139 stars/day, which would
  make it one of the largest repositories on GitHub ever, under an owner
  account with no public profile data returned by the API. Content looks
  real (proper plugin dirs, lint configs) but the star count itself is not
  credible; treat engagement numbers from this entry as fabricated.
- **`Ebony-Vinyl/dsh-our-free-model`** — "no login, no API key, unlimited
  free frontier models" plugin for deepseek-harness. Classic too-good-to-be-
  true free-inference-proxy pattern; license is `NOASSERTION` (no license at
  all). Not excluded for fake stars, but flagged as a hidden-cost trap if
  anyone considers building on top of it — "unlimited free" inference
  proxies are either rate-limited bait, ToS-violating relays, or both.
- **`StormBrawlerSack/legwork-osint-ai-investigator`** — `pushed_at` is 88
  seconds after `created_at` (single dump, no subsequent activity), bot-
  pattern owner name. Same signature as the clusters above even though it's
  not duplicated; excluded rather than carried as "plausible."

## Themes

1. **Agent harness plugin ecosystems are consolidating** — `deepseek-harness`
   (DSH), its plugin topic (`dsh-plugin`) appearing on unrelated repos, and
   `google/elephant-goldfish-model`'s multi-harness adapter layer all point
   the same way: cross-harness portability (one skill, many CLIs) is where
   the real engineering problems are, not inside any single harness.
2. **Context/cost economics for agents is crowded** — `headroom`,
   `TokenEconomizer`, and (in the excluded/raw data) `rtk-ai/rtk` and
   `JuliusBrussee/caveman` are all attacking token/cost reduction from
   slightly different angles. A new entry here needs a genuinely different
   axis (not "yet another compressor") to avoid pure prior-art collision.
3. **Agents given a new perceptual surface** — `gpucanvas` (spatial canvas),
   `Agent-Reach` (social web), `vercel-labs/ui` (accessible UI behaviors) all
   extend what an agent can *perceive or safely act on*, beyond text I/O.
4. **Real embodied/physical-world work is thin and genuinely hard to verify**
   — `mit-han-lab/pear` (robotics) and `tangency-labs/solidcraft` (CAD/BREP)
   are the only two items this cycle touching the physical world, and both
   require real domain expertise (robotics sim stacks, geometry kernels) to
   build on credibly rather than superficially.
5. **Star-farming is actively distorting "momentum" as a signal this cycle**
   — roughly 32 of the ~50 entries in the raw `week` list were duplicate-
   clone spam. Treat `stars_per_day` from unfamiliar/bot-pattern-named owners
   as untrustworthy without a content check.
