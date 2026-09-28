# Dictionaria table validation

## Row counts

| Table | Rows |
|---|---|
| `entries.csv` | 5472 |
| `senses.csv` | 5555 |
| `examples.csv` | 2612 |
| `entries_variants.csv` | 875 |
| `entries_complex_forms.csv` | 836 |
| `senses_relations.csv` | 3693 |

## Referential integrity

All checked clean (0 dangling references, 0 duplicate IDs):

- Every `Senses.Entry_ID` resolves to a row in `entries.csv`
- Every `Examples.Sense_ID` resolves to a row in `senses.csv`
- Every `Entries_Variants.Entry_ID` / `Base_Entry_ID` resolves to `entries.csv`
- Every `Entries_ComplexForms.Base_Entry_ID` resolves to `entries.csv`
- Every `Senses_Relations.Sense_ID` resolves to `senses.csv`
- No duplicate IDs in `entries.csv`, `senses.csv`, or `examples.csv`

## Examples: filtering to match Dictionaria's translation requirement

Of 6,707 raw `<example>` nodes in the LIFT export:

- **4,079** are entirely empty placeholder slots (FLEx pre-creates a fixed number of example slots per sense; most were never filled in) -- excluded.
- **16** have an Ende sentence but no English translation yet -- excluded (Dictionaria requires an obligatory free translation on every example; the current LaTeX dictionary already excludes these too).
- **2,612** are complete (Ende text + English translation) and are written to `examples.csv`.

**One open question for you:** 2,612 vs. the 2,578 `\example{}` blocks in the current LaTeX output -- a 34-example gap. The reason: the LaTeX generator suppresses examples entirely for *variant-of* entries (an entry marked as a spelling/dialectal/etc. variant of another headword only shows a reduced set of fields -- no examples -- in the academic dictionary). Those 34 examples are real, complete, translated examples that happen to belong to a sense on a variant entry. I've kept them in `examples.csv` since Dictionaria's data model has no equivalent restriction and there's no reason to withhold real translated data from that submission -- but flagging so you can confirm or override.

## Sample entries (end to end)

### `ada` (ID `ada_00da4f01-5c11-4130-9b5c-09b5e60fce98`)

- Base of 8 complex form(s): `adade`, `adawalle`, `adingoll`, `adawae`, `adawatta`, `adame`, `adawede`, `adako`
- Sense `7c661e5c-e04e-440e-a1f4-23369a2196df`: POS=`man.dem.`, Description="like this, thus, so"
  - Synonym: any
  - Example: *Ada daeya.* -- 'So it was.'
  - Example: *Obo mälläng ik a ada ulleulle dageya.* -- 'His nostrils were this big.'
- Sense `8f7f57d1-3ccd-472b-95cc-763873c0b02b`: POS=`prtcl.`, Description="quotative particle (for quoted/direct speech)"
  - Example: *Ngänawa "Ngämlle gulag e" ada däga.* -- 'I said, "Come with me."'
  - Example: *Bogo ada, "Ngämo pätt a ttattllong agan."* -- 'He said, "My body has already gotten sore."'
- Sense `888e1f72-c2c8-416d-8778-a631d21636c5`: POS=`comp.`, Description="that"
  - Example: *Ngämo umllang dan ada bongo Grace bo nag dan.* -- 'I know that you are Grace's friend.'

### `dämen` (ID `dämen_14dbd951-2d3e-4628-af16-d01c9aed2d09`)

- Base of 1 complex form(s): `dämenangg`
- Sense `116e731e-71d4-4ecc-9ae9-a9de58e9f90f`: POS=`i.v.`, Description="to sit"
  - Example: *Ngäna dämenang dan.* -- 'I am sitting.'
  - Example: *Adämeneyo!* -- '(You two) sit down!'
  - Example: *Ttongo lla da dämenma toko me adämenan.* -- 'A person sat on top of the chair.'

### `mab` (ID `mab_08ec91e3-4baf-4db4-bd45-461d79171ad7`)

- Sense `26c75228-8e21-409b-942a-ceb6a9ffdeab`: POS=`n.`, Description="pandanus"
  - Specific: mare, miriwa, poma, sakar, sisi, täpäll, wizarab, bebe, maiwa, domäll, gällall, nängga, yuru, kud, därängbun
  - Example: *Bogo tätäm mab de däddänän.* -- 'Yesterday, he picked pandanus.'

### `molemoleg` (ID `molemoleg_000af5d2-0d6b-4cc5-84be-0d27aff39974`)

- Sense `1e3bd083-d885-4d3d-aed2-a6ae0406b752`: POS=`n.`, Description="type of grub"
  - Generic: budar

### `towall` (ID `towall_c1ce3968-a857-423f-affc-2783148ee009`)

- Base of 1 complex form(s): `towallang`
- Sense `fe1286ca-76be-4c3f-978e-967ae67f0aac`: POS=`n.`, Description="grass"
  - Specific: tätärpeyam, yaedidib, tältäl, apapun, ita, wandana, kukiny, darkukiny, esam, kuku, yäbäyäbäd, kabag
  - Example: *Ttall a towall wätätang dan.* -- 'Wallabies are grass eaters.' (source: Joshua Ben Danipa)

