<!-- Managed by ai-dev-process. Do not edit in a project: change it upstream, or record a deviation in CLAUDE.md. -->

# Repositories of a project

A project is one repository, or several. `.ai-dev-process.conf` says which:
the board (`board_owner`, `board_number`), the **home repository**
(`home_repo`) and the **member repositories** (`member_repos`). Every
repository of the project carries the same file with the same values, and a
change to it is made in all of them. Its role — `single`, `home` or `member` —
is in `.ai-dev-process.lock`.

## What lives where

- **The home repository** holds what belongs to the whole project: the
  vision, the ADRs, the iteration files and their retros, the epics, the
  project's `CLAUDE.md` with its hard rules and process parameters, and the
  issues for work that is not about one repository's contents. In a project
  of one repository, that repository is its own home.
- **A member repository** holds code or data, its own issues, and a
  `CLAUDE.md` that imports the home repository's and adds what holds for this
  repository only. It has no ADRs, no iteration files and no vision of its
  own. Its `docs/architecture.md` states what holds there in sentences that
  stand on their own, because a reader of the member may not be able to read
  the home repository.
- **The board** is one, shared by all repositories of the project. Size and
  iteration are the board's fields, whichever repository an issue is in.

## Working across repositories

- All repositories of a project are checked out beside each other, in one
  parent directory, under their repository names. A member's `CLAUDE.md`
  imports `../<home>/CLAUDE.md` from there. If the home repository is not
  checked out, the project's hard rules are missing from the session: stop
  and say so.
- Issue numbers count per repository. A branch carries the number of an issue
  in its own repository. Across repositories, refer to `owner/repo#n`.
- Work that changes several repositories is one issue per repository, each
  naming the others, under one epic in the home repository. Each repository
  gets its own pull request; they are merged in dependency order, and the
  order is stated in each pull request.
- A session works in the repository its task is about, and names that
  repository before its first edit. Handover commands say which repository
  they run in (`cd`, `--repo`).

## Nothing flows from private to public

Where a project has public and private repositories, content never moves from
a private one into a public one: not in files, commit messages, branch names,
issues, pull request bodies or review comments. A public issue may refer to a
private one by its number, and a public document to an ADR by its number.
What holds in the public repository is stated there in its own words — never
by quoting or summarising the private reasoning, data or plans behind it.
When unsure whether something is private, treat it as private and ask.
