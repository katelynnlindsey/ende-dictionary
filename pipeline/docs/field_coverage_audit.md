# FLEx field coverage audit

Every field/note/trait type found in `ende.lift`, cross-checked against what `build_latex.py` and `build_dictionaria.py` currently read. Ordered roughly by how much this would improve the manuscript relative to effort. **No code changes made here** -- this is the menu; nothing below is implemented except where noted as already done.

## High-value, not currently used anywhere

### 1. Etymology / loanword source (524 entries, 461 "borrowed" + 63 "proto")

A complete, structured `<etymology>` field exists: `type="borrowed"` entries give the actual source-language word (e.g. `gita` -> "guitar") and, for **217** of them, a `languages` trait naming the donor language ("English" in every case seen). This directly answers the anonymous referee's complaint that loanwords like `gita` 'guitar', `rabis` 'rubbish', `sabana` 'savanna', `saen` 'sign', `traeb` 'tribe' "are not marked as such" -- **they already are, in FLEx, but the pipeline never reads this field.** (A few of the referee's other examples -- `raba`, `traib`, `vice-chairman`, `volleyball` -- genuinely have no etymology element yet, so those still need FLEx-side entry.) The other 307 etymology elements (mostly `type="proto"`, reconstructed/decomposed forms like `käm + =ang`) don't name a donor language but do give a morphological breakdown, which is exactly the kind of information the referee's report asked for under "more background information." **Recommendation: surface this as a new `\etymology{}` line in the LaTeX entry (something like "< Eng. guitar") and an `Etymology_Source`/`Etymology_Language` column pair in `entries.csv`.**

### 2. Illustrations (217 non-empty references, 118 resolvable to files already in the repo)

Every entry has an `<illustration href="...">` slot (FLEx pre-creates one per sense, mostly empty -- 4,786/5,508 entries have the empty placeholder). **217 have a real filename** (e.g. `tabe 1.jpg`, `Willy Wagtail.jpg`), of which **118 files already exist** in `configured-dictionary/older files/20250710-export/pictures/` (100% of what's in that folder is referenced -- none are orphaned). The other 93 referenced files aren't in the repo (likely still only on the FLEx machine's linked-files folder) and would need to be exported/located before they could be embedded. This directly answers the referee's complaint: "the proposal announces that entries are illustrated with pictures. But these are also lacking." **Recommendation: add `\includegraphics{}` support for the 118 resolvable images now; ask about locating the other 93 separately.**

### 3. Entry-level topic/category labels (1,293 entries, 104 distinct topics)

A `<note>` with no `type` attribute, attached directly to 1,293 entries (23% of the dictionary), holds a short topical tag -- e.g. 210 entries tagged "Trees", 84 "Places around Limol", 41 "Birds", 33 "Types of Taro", 32 "Water", 31 "Numbers", 28 "Clothing", 23 "Names of bananas", down to 104 distinct labels total. This is a ready-made topic index -- exactly what you described wanting to build for the Dictionaria source/topic index, except it already exists and just needs to be read. **Recommendation: a `Topic` column in `entries.csv`, and/or a thematically-organized index section in the LaTeX front or back matter** (distinct from the existing `semantic-domain-ddp4` codes below, which are a different, more granular classification).

### 4. Allomorphs / alternate forms (1,598 `<variant>` elements on 650 entries)

FLEx's native allomorph field (distinct from the variant-*entry* system already handled): alternate phonological/morphological shapes of the *same* lexeme, sometimes tagged with an `environment` trait describing when that shape is used (e.g. `ugug` has allomorphs `ug`, `ugnen` ["analytic plural"], `og`). Not currently surfaced anywhere. **Recommendation: lower priority than 1-3, but could feed a "also realized as ..." note on the ~12% of entries that have it.**

## Present but low-value or already effectively covered

- **`semantic-domain-ddp4`** trait (4,669 senses) -- a full semantic-domain classification (e.g. "2.5.2 Disease", "7.4.1 Give, hand to") already used by the separate `semantic-dictionary/` output; not part of this pipeline's scope (main dictionary only) but confirms the data exists if that output is folded in later.
- **`Verb-slot`** trait (83, e.g. "TAM+Agent") and **`inflection-feature`** (8, complex feature strings) -- verb morphology template/paradigm information for a small subset of verb entries. Specialist grammatical detail; would mainly matter for a grammar sketch, not the dictionary entries themselves.
- **`is-primary`** trait (828, on `relation` elements) -- marks which of several relations (e.g. which synonym) FLEx considers primary. Could be used to bold/order the primary one first in `\synonym{}` etc. Minor presentation refinement.
- **`anthro-code`** trait (2 instances, values "MC"/"290") -- looks like a legacy anthropological classification code, essentially unused (2 of 5555 senses). Not worth building for.
- **`languagenotes`** field (1 instance), **`exemplar`** field (1), **`import-residue`** field (1) -- single-instance fields, almost certainly incidental. Not worth building for.
- **`kit-fonipa` pronunciation**: already captured (3,737/5,472 kept entries, 68%) via the existing `\pronnote{}` macro -- no gap here.

## Already fixed this session

- Sense-level `note[@type="source"]`/`note[@type="reference"]` (consultant names / corpus text+line codes) and example-level `source` attribute -- pass-through columns already added to Dictionaria's `senses.csv`/`examples.csv` (see `dictionaria_validation.md`); not yet in the LaTeX output.
- Examples on variant-of entries -- now surfaced under the base entry (see `variant_example_fix.md`).
