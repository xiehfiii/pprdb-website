# PPRDB

An evidence-curated catalogue of **plant-derived peptide–receptor physical binding**. The strict 3 October 2026 release contains 105 records from 10 plant species. The website is published at [www.pprdb.com](https://www.pprdb.com/).

The downloadable [`plant_LR_final_verified.tsv`](plant_LR_final_verified.tsv) gives, for every record, the tested peptide and receptor or receptor complex, primary DOI, experiment and figure, audit depth, and an interpretation boundary. PPR IDs are persistent. Withdrawn IDs remain in the audit history and are not reassigned; gaps in the public sequence are intentional.

Inclusion requires a same-species original study reporting a physical wet-lab binding experiment. Gene expression, genetic interaction, pathway response, orthology, docking, or a screen without pair-level binding are not enough. We label binding to an isolated receptor separately from binding measured only for a receptor complex. In-vitro binding is not automatically evidence for signalling in planta.

In a strict re-audit of 22 records previously lacking independent pair-level figure inspection, nine were confirmed against original figures and 13 were withdrawn pending primary-panel or reagent-identity verification. The prior 96 retained records had original-article figure, caption, or methods audits in the preceding release; this pass did not independently repeat all 96. `PPR-113`–`PPR-116` name GmLLG ligand-binding co-receptor contacts, not a demonstrated GmLMM1 complex. This is a dated literature snapshot, **not** a guarantee that every eligible article has been discovered.

Plausible but unresolved or misassigned claims, including the 13 withdrawn records, are documented separately in [`held_or_excluded_candidates.tsv`](held_or_excluded_candidates.tsv); they are not searchable database records. The decisions for all 22 re-reviewed records are in [`review_22_decisions.tsv`](review_22_decisions.tsv). Manuscript-specific limitations are in the local release package.
