## Back Road Creative

Software systems and technology consulting, based in Franklin, North Carolina.

We build in three layers, and this org is where the bottom one lives.

- **Open tooling at the base.** The general-purpose pieces of our production systems get pulled
  out, cleaned up, and published here as standalone repositories — useful on their own, with no
  obligation to adopt anything else we make.
- **An agent-run engineering practice in the middle.** The work is done by AI agents operating
  under mechanical constraints: gates in the filesystem and in CI that an agent cannot talk its
  way past, and every change landing as a pull request a human reviews and merges.
- **Products on top.** Our own products are built on those two layers. They stay private, but the
  parts of them that are generally useful do not.

### Public right now

**[rigscore](https://github.com/Back-Road-Creative/rigscore)** — a configuration hygiene checker
for AI development environments. Point it at a project and it reads the files that decide what
your agents are allowed to do — governance docs, MCP server configs, container settings,
permissions, skill files — then returns a score out of 100 and a list of what to fix, ordered by
how badly it would hurt. It runs entirely on your machine and makes no network calls. MIT.

```bash
npx github:Back-Road-Creative/rigscore
```

Also shipped, filed under the areas below:

- **Video tooling** — [keycut](https://github.com/Back-Road-Creative/keycut): lossless
  multi-range video cutting that snaps to keyframes instead of lying about it.
  [redactcam](https://github.com/Back-Road-Creative/redactcam): face and licence-plate redaction
  for video, with a second pass that proves it landed.
- **GPS and telemetry** — [sun-track](https://github.com/Back-Road-Creative/sun-track): solar
  position, golden-hour windows, and where a GPS track was at a given instant.
- **Color and imaging** — [pycube-lut](https://github.com/Back-Road-Creative/pycube-lut): reads
  and applies Adobe .cube 3D LUTs, HALD CLUTs and 1D tone curves to NumPy images.
- **Agent tooling** — [claude-batch-runner](https://github.com/Back-Road-Creative/claude-batch-runner):
  declarative parallel agent campaigns with schema-verified results and a cost table.
  [agent-audit](https://github.com/Back-Road-Creative/agent-audit): audits the skills, instruction
  files and workflows your AI agents actually read.

### More coming

A couple more areas are still being carved out of our production systems. **Not published yet** —
so these are areas, not links. Each one moves up to the section above as it lands:

- **SEO scoring** — dependency-free keyword extraction, readability, and per-platform metadata
  rules.
- **Static-site security** — a hardened header and content-security-policy baseline, with a build
  step that fails when the policy did not make it into the output.

Nothing ships until it stands alone: its own tests, its own documentation, and no leftover
references to the system it came out of. A short honest list beats a long one full of dead links.

### How we work

Mechanical enforcement over behavioral rules. If the only thing stopping an agent from doing
something destructive is a prompt asking it not to, that is not governance — that is a suggestion.
Constraints belong somewhere the agent cannot edit them out of the way.

Write-ups of the practice, and each tool as it ships:
**[headlessmode.com](https://headlessmode.com)**.

---

📍 Franklin, NC · 🔗 [backroadcreative.com](https://backroadcreative.com) · 𝕏 [@HeadlessMode](https://x.com/HeadlessMode)
