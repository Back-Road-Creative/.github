# .github

Organization profile README, and the shared CI this org's public repositories call.

## leak-scan

`scripts/leak_scan.py` checks that a public repository publishes its own work and
nothing else: no sibling project's name, no client's name, no layout convention
from the private monorepo several of these repos were extracted from, and no
absolute path from an authoring machine.

It lives here once and is called by every repo, rather than vendored into each.
Twelve copies would drift, and the repo whose copy drifted would be the repo that
quietly stopped being checked.

### Calling it

Add this and nothing else. There is no pattern list to copy and no setting that
names the calling repo:

```yaml
name: leak-scan
on: [pull_request, push]
jobs:
  leak-scan:
    uses: Back-Road-Creative/.github/.github/workflows/leak-scan.yml@main
```

Pass `with: {history: true}` for an audit run that also reads every blob in
history. The pull-request gate deliberately does not: only a force-push removes a
published blob, so a history finding would be permanently red on something no pull
request can fix, and a permanently red gate gets switched off.

### Two things it will never do

**Flag a repo for naming itself.** The name comes from `${{ github.repository }}`,
never from configuration, so there is no per-repo setting to get wrong and no repo
left holding a stale one. The lookahead ends the name rather than using `\b`: a
word boundary sits between `driftless` and the `-` of `driftless-archive`, so an
earlier version of this rule could not see the one private sibling it existed to
catch. A trailing `.git` passes, because a clone URL carries it and still names the
repo itself.

**Flag a public sibling.** Naming a repository anyone can already open discloses
nothing. The public set is read from the org API at scan time rather than listed in
the script, because a hand-kept list goes stale the day a repo is published and
then fails every scan that mentions it. If that lookup fails the scan stops rather
than guess — mistaking a private repo for a public one is the error that matters.

### What it looks for

| Rule | Catches |
| --- | --- |
| `foreign-repo` | A repo in this org that is neither this one nor public. |
| `client-name` | A third-party client engagement. |
| `machine-path` | `/home/joe`, `/home/dev` — the two authoring accounts. |
| `private-project` | A project that exists only in private repos. |
| `workspace-convention` | `_active/`, `.data/<path>`, `baton`. |

Every pattern was validated against fresh clones of all thirteen public repos
before it was kept. Candidates that fired on legitimate content were dropped
rather than tightened: `GMS` (a test fixture name, and the industry term
"grant-management-software"), `gomoveshift` (a public brand), `workspaces`
(ordinary English), `openclaw` (a third-party product these tools support), and a
general `/home/<user>/` (documentation examples). An over-eager scanner gets
switched off, and a switched-off scanner protects nothing.

### The allowlist

A repo with a genuine exception adds `.github/leak-scan-allowlist.json`:

```json
{
  "allow": [
    {
      "rule": "workspace-convention",
      "path": "CHANGELOG.md",
      "match": ".data/plans",
      "reason": "Records that this build plan stayed in the monorepo at extraction; names no file that ships here.",
      "scope": "both"
    }
  ]
}
```

`rule`, `path`, `match` and `reason` are all required, and a `reason` under 20
characters is rejected. This is enforced, not advised: the scan exits non-zero on a
malformed allowlist, so an unexplained exemption cannot be merged. An entry
suppresses a finding only where all three of rule, path glob and matched substring
line up, so it cannot silently widen. `scope` is `worktree`, `history` or `both`
(default).

An exemption whose reason has been falsified by later code is the failure mode
here, and nothing rechecks a reason automatically. Re-derive each entry when you
touch the file it covers.
