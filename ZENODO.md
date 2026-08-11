# ZENODO.md — Zenodo archival for this repository

This repository ships a completed `.zenodo.json` metadata file describing the
code + result-JSON snapshot that backs the manuscript
(`manuscripts/paper.tex` / `paper.pdf`). Depositing archives a citable,
DOI-reserved copy of HEAD for the paper's Data & Code Availability statement.

## Steps to reserve / publish the DOI (once a token exists)

1. Create a personal access token at
   <https://zenodo.org/account/settings/applications> with scopes
   `deposit:write` and `deposit:actions`, then `export ZENODO_TOKEN=<token>`
   (never commit it).

2. Rehearse without network first:

   ```bash
   python3 ${COMMONS_ROOT}/zenodo/zenodo_deposit.py \
       --repo ${REPO_ROOT} \
       --dry-run
   ```

3. Real run — creates a DRAFT deposition with a prereserved DOI and uploads a
   `git archive` tarball of HEAD; it does **not** publish. Publishing stays a
   deliberate manual step in the Zenodo web UI.

4. Record the reserved DOI in `CITATION.cff` (`doi:`), `README.md`, and the
   manuscript's Data & Code Availability statement, then commit.

## Deposit record

### 2026-07-02 — reserved DOI on draft deposition

- Deposition ID: `21130297`
- Reserved DOI: `10.5281/zenodo.21130297`
- Draft record URL: <https://zenodo.org/deposit/21130297>
- Status: **reserved on a DRAFT deposition** — not yet published/active. The
  DOI resolves only after the record is published in the Zenodo web UI.
- Archived commit: `b8a4abd` (repo HEAD *before* this DOI-propagation commit).
  The uploaded tarball was built by `git archive` at that HEAD.
- Propagated the DOI into `CITATION.cff`, `README.md`, and
  `manuscripts/paper.tex` (Data & Code Availability), all marked
  reserved/draft pending publication.

Note: the uploaded tarball predates this DOI-propagation commit, so it does not
contain the DOI strings themselves. Before pressing Publish, optionally replace
the file in the draft (via the web UI, or by rerunning `zenodo_deposit.py`
after deleting the old file) so the archive reflects the final repository state.
