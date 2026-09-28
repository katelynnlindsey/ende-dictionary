# Ende dictionary pipeline

One FLEx `.lift` export in, two publications out: the academic LaTeX
dictionary and a Dictionaria submission. Both are generated from the
same parsed data so they can't drift apart.

```
                     ┌─────────────────┐
   ende.lift  ─────▶ │ lib/lift_parser │ ─────▶ ParsedLift (in memory)
                     └─────────────────┘              │
                                          ┌────────────┴────────────┐
                                          ▼                         ▼
                              latex/build_latex.py     dictionaria/build_dictionaria.py
                                          │                         │
                                          ▼                         ▼
                          output/latex/dictionary_ende.tex   output/dictionaria/*.csv
```

## Directory layout

```
pipeline/
├── run_pipeline.py              -- the one command to run everything
├── lib/
│   └── lift_parser.py           -- shared FLEx LIFT parser (no output-format logic)
├── latex/
│   └── build_latex.py           -- LaTeX generator (academic dictionary + reversal index)
├── dictionaria/
│   └── build_dictionaria.py     -- Dictionaria CSV table generator
├── output/
│   ├── latex/dictionary_ende.tex
│   └── dictionaria/{entries,senses,examples,entries_variants,entries_complex_forms,senses_relations}.csv
├── logs/
│   └── run_<timestamp>.json     -- provenance log for every run (not gitignored -- this is the audit trail)
├── reports/
│   └── dictionary_report.py     -- completeness stats + evaluation-rubric scoring, reusable on any LIFT export
└── docs/
    ├── field_mapping.md          -- full inventory: LIFT field -> shared field -> LaTeX macro -> Dictionaria column
    ├── diff_report.md            -- validation that the new LaTeX output matches the old pipeline's, byte-for-byte
    ├── dictionaria_validation.md -- referential-integrity checks + sample entries for the Dictionaria tables
    ├── variant_example_fix.md    -- 34 examples moved from variant entries onto their base entry (with rationale)
    ├── field_coverage_audit.md   -- FLEx fields NOT currently used by either output, with counts + recommendations
    ├── reviewer_response_triage.md -- every point from both PL reviews, tagged code-fixable / FLEx-side / policy
    └── proposed_fixes.md         -- before/after samples for 3 reviewer-driven fixes awaiting your go-ahead
```

## Completeness & rubric reporting

`pipeline/reports/dictionary_report.py` computes the kind of numbers an editor wants before reading 5,000 entries by
hand: definition-length distribution, % of entries with an example, % multi-sense, verb-class coverage,
multi-POS-entry count, and a scoring pass against the pasted Dictionaria-style evaluation rubric (lexical depth,
entry quality, naturalistic-data proxy). It operates on the shared `ParsedLift` representation, so it's reusable on
any dictionary's LIFT export -- not just Ende's -- once `lift_parser.py`'s hardcoded `"kit"` vernacular tag is
pointed at that language's writing-system code. Run it standalone:

```bash
python reports/dictionary_report.py path/to/export.lift
```

## Running it

```bash
cd pipeline
python run_pipeline.py path/to/your-fresh-export.lift
```

That's the only thing that needs to change when you have a new FLEx
export: point the command at the new `.lift` file. Everything else
(header, output paths) has a sensible default. Optional flags:

```bash
python run_pipeline.py your-export.lift --head path/to/head.txt --outdir path/to/output
```

Each run writes:
- `output/latex/dictionary_ende.tex` -- drop-in replacement for the file in `configured-dictionary/20250803/`
- `output/dictionaria/*.csv` -- the Dictionaria submission tables
- `logs/run_<timestamp>.json` -- what ran, when, on what input, how many entries/senses/examples came out, and every warning raised during parsing

## What's in each Dictionaria table

Per [Dictionaria's submission guidelines](https://dictionaria.clld.org/submit): entries and senses
are separate tables (a sense holds the definition, not the entry), and
examples attach to senses.

| File | One row per... | Key columns |
|---|---|---|
| `entries.csv` | headword | `ID`, `Language_ID`, `Headword`, `Part_Of_Speech`, plus irregular-form/root/pronunciation columns |
| `senses.csv` | sense | `ID`, `Entry_ID`, `Part_Of_Speech`, `Description` (the definition), scientific name, and the five note types (cultural/semantic/grammar/sociolinguistic/discourse) |
| `examples.csv` | example | `ID`, `Sense_ID`, `Primary_Text` (Ende), `Translated_Text` (English), `Source` |
| `entries_variants.csv` | variant relationship | `Entry_ID` (the variant), `Base_Entry_ID`, `Variant_Type` |
| `entries_complex_forms.csv` | complex-form relationship | `Complex_Entry_ID`, `Base_Entry_ID`, `Complex_Form_Type` |
| `senses_relations.csv` | cross-reference (synonym/antonym/etc.) | `Sense_ID`, `Related_Sense_ID`, `Related_Entry_Headword`, `Relation_Type` |

`Language_ID` is `kit` -- the ISO 639-3 code already used as the FLEx
writing-system tag throughout the export, corresponding to Glottolog
languoid *Agob-Ende-Kawam* (glottocode `agob1244`; Ende doesn't have its
own separate Glottocode).

`examples.csv` only includes examples with both an Ende sentence and an
English translation (matching Dictionaria's "obligatory free
translation" requirement, and matching what the current LaTeX
dictionary already does). Of 6,707 raw `<example>` nodes in the current
export, 4,079 are empty FLEx template slots and 16 have Ende text but no
translation yet -- both excluded. See `docs/dictionaria_validation.md`
for exact counts on any given run.

**Not produced**, by your choice (see `docs/field_mapping.md`):
- No separate English-to-Ende reversal file for Dictionaria (their site
  builds this from `Senses.Description`; the LaTeX output keeps its own
  reversal section).
- No `references.csv` -- no bibliographic-citation fields exist in the
  current LIFT data. `Senses.Source`/`Senses.Reference` and
  `Examples.Source` carry the raw citation text that *does* exist
  (consultant names, corpus text+line codes) as plain pass-through
  columns. Building an actual people/topic source index is a separate
  design task, not yet started.

## Design decisions already made (don't relitigate without asking)

- Dictionaria's `Headword` is the citation form only -- no separate
  `Lexeme_Form` column (this never differs from the headword in the
  current data anyway).
- Variant-of and complex-form relationships are one row per relationship
  in a side table, not flattened comma-separated text.
- The `gloss[@lang="ga"]` field in the LIFT export is a leftover from a
  different language project's template and is never surfaced anywhere.

## Known pre-existing quirks in the source data / original pipeline

Documented in detail in `docs/diff_report.md` and `docs/field_mapping.md`.
None of these are things this pipeline introduced or silently fixed:

1. A multi-sense verb entry whose senses have different parts of speech
   (e.g. one transitive, one intransitive) will only ever show the
   *first* sense's POS for the whole entry in the LaTeX output -- a
   pre-existing case-sensitivity bug in the original `ende_dict.py`
   (`get_first_pos(entry) in verb_pos` compares a capitalized value
   against an all-lowercase list, so it's always False).
2. `\lexeme{}`, `\relforms{}`, and the irregular-possessed-form macros
   are wired up but never fire on the current export (the underlying
   LIFT fields don't exist in this data) -- and two of them
   (`\relformiqu{}`/`\relformen{}`, `\irregthirdposs{}`/`\irregfirstposs{}`)
   contain a double-backslash typo that would misrender if they ever did.
3. 34 complete, translated examples belong to senses on *variant-of*
   entries. The LaTeX dictionary suppresses examples entirely for
   variant entries, so these never appear there -- but they're included
   in `examples.csv` since Dictionaria has no equivalent restriction.

## Re-running against a new FLEx export

1. Export fresh from FLEx as LIFT (`.lift` + its `.lift-ranges` file, though only the `.lift` is read here).
2. `python run_pipeline.py path/to/new-export.lift`
3. Check the printed `parse_stats` and any warnings against the previous run's log in `logs/`.
4. Diff `output/latex/dictionary_ende.tex` against the previous version if you want to see exactly what changed entry-by-entry.
5. Review `output/dictionaria/*.csv` before actually submitting anything to Dictionaria -- this pipeline does the mechanical conversion; the content review is yours.
