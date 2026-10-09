# Behavioural A/B eval

Does the plugin change what the coding assistant actually ships? Each task is a small
project (`tasks/<task>/fixture/`), a one-line user request (`prompt.txt`) and a checklist a
senior agent engineer would apply (`rubric.json`, written before any run). The same request
goes to Claude Code with and without the plugin; the results are graded blind.

```bash
export CLAUDE_BIN=claude                        # if `claude` isn't on PATH
python3 evals/ab/run_ab.py --runs 3 --jobs 4    # both arms; skips runs that already exist
python3 evals/ab/grade_ab.py --jobs 4           # two blinded judges per run, third on splits
python3 evals/ab/report_ab.py                   # results/summary.md and summary.json
python3 evals/ab/run_ab.py --retest             # re-run every saved project's tests here
```

- Both arms disable every installed plugin through `--settings`; the plugin arm adds this
  checkout with `--plugin-dir`. A run aborts if its loaded-plugin list doesn't match its arm.
- Runs may edit files and run local Python, pytest and read-only git. Package installs are
  denied explicitly (`python3 *` would otherwise allow `python3 -m pip install`).
- The judge gets the diff and final message inline, with every tool disabled. A judge given
  read tools sometimes skipped reading and invented evidence.
- Results for the plugin v0.2.0 arm are kept as `with-v0.2-<n>`; `with-<n>` is the current
  version. Raw transcripts stay local (gitignored).

The write-up, with results and caveats, is in [docs/README.md](../../docs/README.md#does-it-work-the-ab-experiment).
