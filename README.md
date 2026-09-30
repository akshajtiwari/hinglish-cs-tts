# SwitchMOS

A whole-clip naturalness predictor for synthetic speech that aims to beat UTMOS where it fails (modern, Indian-language, and code-switched speech), trained on a broad mix of existing human ratings, with a built-in branch that scores language switches.

**All documentation is in [`switchmos/`](switchmos/README.md).** Start with its README; for the full non-specialist overview read `switchmos/00_committee_proposal.md`; before implementing, read `switchmos/12_pre_implementation_checklist.md`.

| Folder | Contents |
|---|---|
| `switchmos/` | Research docs: problem, related work, datasets, architecture, training, evaluation, roadmap, checklist |
| `model/` | IndicF5 toolkit: data prep, checkpoint converter, fine-tune script; used for before/after switch pairs and as an optional test voice |

Earlier documents from previous project directions are recoverable at git tag `archive-pre-consolidation`.
