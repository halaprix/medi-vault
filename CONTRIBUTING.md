# Contributing to medi-vault

## Branch naming
- `feat/` — new features
- `fix/` — bug fixes
- `chore/` — maintenance, dependencies
- `infra/` — Docker, CI/CD, config
- `docs/` — documentation only

## Commit style
Keep commits atomic — one logical change per commit.
Prefix with scope: `feat:`, `fix:`, `chore:`, `infra:`, `docs:`, `test:`.

## Before submitting
- [ ] Tests pass (`make test`)
- [ ] Lint passes (`make lint`)
- [ ] No secrets in commits
- [ ] Flywheel bead updated if applicable

## Development
```bash
make up          # start all services
make down        # stop
make logs        # tail logs
make shell-backend  # shell into backend container
make seed        # seed biomarker data
make migrate     # run DB migrations
```
