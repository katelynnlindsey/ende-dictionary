# Field mapping: FLEx LIFT → shared representation → LaTeX / Dictionaria

Status: **draft for review — no code built from this yet.**

This inventories every field the current pipeline
(`configured-dictionary/20250803/ende_dict.py` + `ende_process.py`) extracts
from the FLEx `.lift` export, how it is currently rendered in
`dictionary_ende.tex`, and how it would map onto Dictionaria's submission
format. The goal of the new pipeline is a single parsed representation that
both the LaTeX generator and the Dictionaria generator read from, so the two
outputs can never drift apart.

## What Dictionaria expects

Per Dictionaria's submission guidelines (https://dictionaria.clld.org/submit)
and the CLDF `Dictionary` module it publishes on:

- A submission is **relational tables**: `entries`, `senses`, `examples`,
  and optionally `references`, joined by IDs.
- **Senses, not entries, hold the definition.** An entry can have multiple
  senses; a sense belongs to exactly one entry.
- **Examples attach to senses** (many-to-many: one example can illustrate
  several senses; a sense can have several examples), each example has an
  obligatory free translation and an optional gloss.
- They explicitly expect most submissions to arrive as **FLEx/Toolbox
  exports** — i.e. exactly what we already have.
- Extra columns beyond the required core ones are normal and expected
  (cross-references, notes, variant info, etc.) — there's no need to force
  every FLEx field into a fixed schema; we add custom columns as needed.

## Entries table

| LIFT source (XPath) | Current LaTeX macro | Shared field name | Dictionaria column |
|---|---|---|---|
| `citation/form[@lang="kit"]/text` (fallback `lexical-unit/form[@lang="kit"]/text`) | `\headword` | `headword` | `Entries.Headword` |
| `lexical-unit/form[@lang="kit"]/text` (only shown when it differs from the headword) | `\lexeme` | `lexeme_form` | `Entries.Comment` or custom `Entries.Lexeme_Form` — **needs your call** on whether Dictionaria should see this distinction at all |
| entry id / guid | — | `entry_id` | `Entries.ID` |
| `sense/grammatical-info@value` of first sense (+ `Verb-infl-class` trait) | `\pos` (on entry, for non-verbs) | `part_of_speech` | `Entries.Part_Of_Speech` (also duplicated per sense, see below) |
| `field[@type="Irreg Pl"]/form/text` | `\irregpl` | `irregular_plural` | custom `Entries.Irregular_Plural` |
| `field[@type="Irreg Poss"]/form/text` | `\irregposs` | `irregular_possessed` | custom `Entries.Irregular_Possessed` |
| variant relation, type `irregthirdposs`/`irregfirstposs` | `\irregthirdposs`/`\irregfirstposs` | `irregular_possessed_forms` | custom `Entries.Irregular_Possessed_Forms` |
| `field[@type="Deriv Root"]/form/text` | `\derivroot` | `derivational_root` | custom `Entries.Derivational_Root` |
| `field[@type="literal-meaning"]/form[@lang="en"]/text` | `\litmean` | `literal_meaning` | custom `Entries.Literal_Meaning` |
| `pronunciation/form/text` | `\pronnote` | `pronunciation` | custom `Entries.Pronunciation` |
| `field[@type="activemiddle"]/form/text` | `\activemiddle` | `active_middle_form` | custom `Entries.Active_Middle_Form` |
| `field[@type="RelatedForms"]` (+2–5 suffixes) | `\relforms` | `related_forms` (list of kit/en pairs) | custom `Entries.Related_Forms` |
| variant-type relation (Spelling/Dialectal/Free/etc. variant) | `\variants` | `variant_forms` (typed list) | custom `Entries.Variant_Forms` — needs a flattened text or repeated-row representation; **needs your call** |
| this entry *is* a variant of another entry (`mainwdmap`) | `\variantof` | `variant_of_entry_id` | custom `Entries.Variant_Of` (Entry_ID reference) |
| `_component-lexeme` relation with `complex-form-type` trait (this entry *is* the complex form) | `\complexformof` | `complex_form_of_entry_id` + `complex_form_type` | custom `Entries.Complex_Form_Of`, `Entries.Complex_Form_Type` |
| `_component-lexeme` relation with `complex-form-type` trait (this entry is the *base* of others) | `\complexforms` | derived (reverse lookup, not stored) | not a separate column — Dictionaria/CLDF consumers can derive this from `Complex_Form_Of` on the other rows |
| `entry/field[@type="Entry History"]/form[@lang="es"]/text` contains `EXCLUDE` | — (entry dropped entirely) | `excluded` (filter, not published) | entry omitted from all tables |
| `trait[@name="morph-type"][@value="suffix"]` | — (entry dropped entirely) | `is_suffix` (filter, not published) | entry omitted from all tables |

## Senses table

| LIFT source (XPath) | Current LaTeX macro | Shared field name | Dictionaria column |
|---|---|---|---|
| sense id | — | `sense_id` | `Senses.ID` |
| parent entry id | — | `entry_id` | `Senses.Entry_ID` |
| `grammatical-info@value` (+ `Verb-infl-class` trait) | `\pos` (per-sense, for verbs) | `part_of_speech` | `Senses.Part_Of_Speech` |
| `definition/form[@lang="en"]/text` | `\definition` | `definition` | `Senses.Description` |
| `gloss[@lang="ga"]/text` | *(not currently rendered — only mined for `PL:` irregular-plural notation)* | `gloss_ga` | custom `Senses.Gloss` — **needs your call**: what does writing-system `ga` represent in this project (Tok Pisin? a working gloss language?), and should it be published at all |
| `field[@type="scientific-name"]/form[@lang="en"]/text` | `\scientificname` | `scientific_name` | custom `Senses.Scientific_Name` |
| `note[@type="anthropology"]/form[@lang="en"]/text` | `\anthronote` | `cultural_note` | custom `Senses.Cultural_Note` |
| `note[@type="semantics"]/form[@lang="en"]/text` | `\semnote` | `semantic_note` | custom `Senses.Semantic_Note` |
| `note[@type="grammar"]/form[@lang="en"]/text` | `\grammarnote` | `grammar_note` | custom `Senses.Grammar_Note` |
| `note[@type="sociolinguistics"]/form[@lang="en"]/text` | `\socionote` | `sociolinguistic_note` | custom `Senses.Sociolinguistic_Note` |
| `note[@type="discourse"]/form[@lang="en"]/text` | `\discoursenote` | `discourse_note` | custom `Senses.Discourse_Note` |
| `relation[@type=...]` (Synonym, Antonym, Generic, Coordinate term, Specific, Colloquial term, Example, Doublet, Full phrase, Near synonym, Whole, Part, Not to be confused, Nonsingular, Singular, Ideophonic pair voiced/voiceless) | `\synonym`, `\antonym`, etc. (16 relation types) | `relations` (typed list of sense_id refs) | custom `Senses.<RelationType>` columns, each holding a list of referenced Sense_IDs — CLDF explicitly allows "associated senses" fields on the sense table |
| `sense/reversal[@type="en"]/form/text` | drives the separate `\section{Reversal Dictionary}` in the LaTeX (English headword → Ende entries, grouped by POS) | `reversal_en` | not a separate submitted table — Dictionaria's own site builds the English↔Ende reversal index automatically from `Senses.Description`/gloss; **needs your call** on whether we still owe them this field explicitly or can drop it |

## Examples table

| LIFT source (XPath) | Current LaTeX macro | Shared field name | Dictionaria column |
|---|---|---|---|
| example id | — | `example_id` | `Examples.ID` |
| `example/form[@lang="kit"]/text` | `\exsen` (inside `\example`) | `primary_text` | `Examples.Primary_Text` |
| `example/translation[@type="Free translation"]/form[@lang="en"]/text` | `\extran` (inside `\example`) | `translated_text` | `Examples.Translated_Text` |
| (implicit: which sense the example belongs to) | (nesting in the .tex) | `sense_ids` | `Examples.Sense_IDs` (list — supports the many-to-many rule) |

## Not carried into either output today

- `field[@type="Entry History"]` — used only for the `EXCLUDE` filter flag; the rest of any history note is not currently published anywhere. Flag if you want it captured.
- The `qaa-x-Ende`, `qaa`, `kit-fonipa`, `en`, `kit` writing-system definitions in `WritingSystems/*.ldml` (from the older 20250710 export folder) are FLEx project metadata, not entry content — not relevant to either output.

## Open questions for you before I build against this

1. **`gloss[@lang="ga"]`** — what is writing system `ga` in this FLEx project, and should it appear in either output?
2. **Lexeme form vs. headword** — when the underlying lexeme differs from the citation headword, should Dictionaria see both, or just the headword (as English readers of the site would see)?
3. **Reversal (English→Ende) index** — keep generating it explicitly for Dictionaria, or rely on their site to build it from `Senses.Description`?
4. **References table** — I did not find any bibliographic citation fields (e.g. cited sources for scientific names or cultural notes) in the current LIFT export/LaTeX macros. Confirm there's nothing to carry into a `references.csv`, or point me to where such citations live if they exist.
5. **Variant/complex-form representation** — comma-flattened text in one cell, or one row per variant/complex-form relationship in a side table? Either works; I lean toward one-row-per-relationship for referential integrity, but it's your dictionary's structure to decide.
