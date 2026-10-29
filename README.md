# env-snapshot

**Record exactly which computational environment produced your results (OS, CPU, Python,
every installed package version, git commit and uncommitted changes, input file hashes) and see
what changed when results stop reproducing.**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

"It worked on my laptop last year" is the most common reproducibility failure. Package upgrades
silently change defaults and numerical results; analyses are run from uncommitted code. Journals
and funders increasingly require a description of the software environment. A snapshot saved next to
each result answers "what exactly did I run?" and `diff` answers "what is different now?".

## Features

- OS, machine, CPU count, Python implementation/version/executable
- All installed distributions with versions (`importlib.metadata`), as `name==version`
- Git commit, branch, remote and dirty state of the project
- SHA-256 fingerprints of chosen input files
- Allowlisted environment variables only (thread counts, CUDA devices, SLURM job): secrets are never recorded
- Markdown summary for a methods appendix; `diff` lists package, Python, OS, commit and file changes

## Usage

```bash
pip install .
env-snapshot capture -o results/environment.json --markdown results/ENVIRONMENT.md --hash data/raw.csv
env-snapshot diff old_run/environment.json results/environment.json
```

Call `env_snapshot.snapshot()` from your analysis script to save it alongside every output.

## Testing

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA
