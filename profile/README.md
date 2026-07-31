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

### More coming

A batch of libraries is being carved out of our production systems right now. **None of them are
published yet** — so this is a list of areas, not links. Each one moves up to the section above as
it lands:

- **Video tooling** — supervising long encodes so a stalled job fails loudly instead of hanging,
  and privacy redaction that re-checks the rendered output to prove the blur actually landed.
- **GPS and telemetry** — track parsing, cached geocoding, and pairing footage to the trip that
  produced it without silently attaching the wrong one.
- **Color and imaging** — LUT reading and application, measured color correction, and a
  deterministic develop pipeline from raw capture to finished still.
- **SEO scoring** — dependency-free keyword extraction, readability, and per-platform metadata
  rules.
- **Agent tooling** — the harness the practice above runs on: merge gating that refuses on red
  CI, run locks, and batch dispatch.
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
