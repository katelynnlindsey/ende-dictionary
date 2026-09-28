# Variant-entry example fix

**Change:** translated examples that live on a *variant-of* entry's sense (spelling/dialectal/fast-speech/etc. variants) are now surfaced under the base entry's first sense in the LaTeX output, tagged with which variant spelling the example sentence actually uses. Previously these examples were silently dropped from the LaTeX dictionary entirely (though they were already present in the Dictionaria `examples.csv`, which is what surfaced the discrepancy in the first place).

**Result:** `\example{}` count in the LaTeX output went from 2,578 to 2,612 -- now matching Dictionaria's `examples.csv` count exactly, since both outputs draw on the same complete set of translated examples.

## Affected entries (22 base entries received 34 examples)

| Base entry | From variant(s) |
|---|---|
| arle | aräre |
| dädär | dɨdɨr, dɨdɨr, dɨdɨr |
| dämoe | domoe |
| dibagaeyo | dibageyo |
| ddokop | ddäkop |
| erany | yärany |
| ikopse ma | ikopse ma ma |
| kakakän | kakänkakän |
| kängkäl | kälängkäl |
| känyär | känyer, känyer |
| maket | market, market, market |
| märäl | mälläll |
| miny | minyminy, minyminy |
| ngasekäma | käma |
| ngonongg | ngänongg |
| olle | wälle |
| papälläk | papllek |
| penongg | penangg |
| RED | ibi, ibi, ibi, ibi, ibi, ibi |
| täträk | tɨtɨrɨk, tɨtɨrɨk |
| ttattleang | ttattllong |
| ttäkoe | ttokoe |

## Design note

The moved examples are spelled per the **variant**, not the base headword (e.g. the example under `arle` reads *"Obo moko da aräre we dan"* using the variant spelling `aräre`, not `arle`). This is standard dictionary practice (showing an attested variant form in context under its canonical entry), and the entry's own `\variants{}` line already lists `aräre` as an unspec. variant, so a careful reader has the context. No visual tag was added to the example itself -- flag if you'd like one (e.g. a small parenthetical noting the variant spelling used).

One case worth flagging on its own: `ibi` (6 examples) is a Dialectal variant of the placeholder `RED` entry (see field_coverage_audit.md / reviewer_response_triage.md for the RED-entry issue) -- its examples are currently attached to `RED`'s first sense, which will need to move again once the RED-placeholder handling is resolved.
