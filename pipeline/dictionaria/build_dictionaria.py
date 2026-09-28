"""
Dictionaria submission generator for the Ende dictionary.

Consumes the shared representation from `lift_parser.parse_lift()` and
produces a Dictionaria-style relational submission: entries, senses,
examples, plus small side tables for variant/complex-form/sense-relation
links (kept as one-row-per-relationship tables rather than flattened
text, per your preference -- see pipeline/docs/field_mapping.md).

Per Dictionaria's submission guidelines (https://dictionaria.clld.org/submit)
and the CLDF `Dictionary` module: a submission is entries + senses +
examples (+ optional references), related by IDs; senses (not entries)
hold the definition; examples attach to senses.

Language_ID: uses "kit", the ISO 639-3 code already used as the `kit`
writing-system tag throughout the FLEx export, corresponding to Glottolog
languoid "Agob-Ende-Kawam" (glottocode agob1244) -- confirmed via
Wikipedia's Agob-languages page and Grambank (which lists you as a
contributor for this exact languoid). Ende does not have its own
separate Glottocode; it is lumped with Agob/Kawam as one Glottolog
languoid. Flag if you'd rather use something else here.

Not produced (by design, per your decisions -- see field_mapping.md):
  - No separate English->Ende reversal file (Dictionaria builds this
    from Senses.Description on their end).
  - No references.csv (no bibliographic-citation fields exist in the
    current LIFT export; Examples.Source and Senses.Source/Reference
    carry the raw citation text that does exist, unprocessed, pending
    a separate design conversation about a people/topic index).

Usage:
    from lift_parser import parse_lift
    from build_dictionaria import build_dictionaria_tables
    parsed = parse_lift("ende.lift")
    tables = build_dictionaria_tables(parsed)
    write_dictionaria_csvs(tables, "output_dir/")
"""

import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from lift_parser import POSMAP_EN  # noqa: E402

LANGUAGE_ID = 'kit'  # see module docstring


def pos_label(pos_raw):
    '''Abbreviated POS label, matching what the LaTeX dictionary shows (e.g. "t.v.", "n.").'''
    if not pos_raw:
        return None
    return POSMAP_EN.get(pos_raw, pos_raw)


def build_dictionaria_tables(parsed):
    '''Return a dict of table_name -> list[dict rows], derived from a ParsedLift.'''
    entries_rows = []
    senses_rows = []
    examples_rows = []
    variants_rows = []
    complex_forms_rows = []
    relations_rows = []

    for entry in parsed.entries:
        entry_pos = pos_label(entry.senses[0].pos_raw) if entry.senses else None
        entries_rows.append({
            'ID': entry.id,
            'Language_ID': LANGUAGE_ID,
            'Headword': entry.headword,
            'Part_Of_Speech': entry_pos,
            'Irregular_Plural': entry.irregular_plural,
            'Irregular_Possessed': entry.irregular_possessed,
            'Derivational_Root': entry.derivational_root,
            'Literal_Meaning': entry.literal_meaning,
            'Pronunciation': entry.pronunciation,
            'Active_Middle_Form': entry.active_middle_form,
        })

        if entry.variant_of is not None:
            vr = entry.variant_of
            variants_rows.append({
                'Entry_ID': entry.id,
                'Base_Entry_ID': vr.entry_id,
                'Variant_Type': vr.vartype,
            })

        for ref in entry.complex_forms:
            complex_forms_rows.append({
                'Complex_Entry_ID': ref.entry_id,
                'Base_Entry_ID': entry.id,
                'Complex_Form_Type': ref.complex_type,
            })

        for s in entry.senses:
            senses_rows.append({
                'ID': s.id,
                'Entry_ID': entry.id,
                'Part_Of_Speech': pos_label(s.pos_raw),
                'Description': s.definition,
                'Scientific_Name': s.scientific_name,
                'Cultural_Note': s.cultural_note,
                'Semantic_Note': s.semantic_note,
                'Grammar_Note': s.grammar_note,
                'Sociolinguistic_Note': s.sociolinguistic_note,
                'Discourse_Note': s.discourse_note,
                'Source': s.source_note,
                'Reference': s.reference_note,
            })

            for ex in s.examples:
                # Many <example> nodes in the FLEx export are empty template slots (no form,
                # no translation at all -- ~4079 of 6707 on the current export) that FLEx
                # pre-creates per sense and were never filled in. Dictionaria's guidelines
                # require an obligatory free translation on every example, and the current
                # LaTeX dictionary already silently skips any example missing either side
                # (see examples2tex's missing_ok=False/empty_ok=False). Matching that here:
                # empty/untranslated examples are omitted from examples.csv, not published as
                # blank rows. See dictionaria_validation.md for exact counts.
                if not (ex.primary_text and ex.primary_text.strip() and ex.translated_text and ex.translated_text.strip()):
                    continue
                examples_rows.append({
                    'ID': ex.id,
                    'Sense_ID': s.id,
                    'Language_ID': LANGUAGE_ID,
                    'Primary_Text': ex.primary_text,
                    'Translated_Text': ex.translated_text,
                    'Source': ex.source_ref,
                    'Do_Not_Publish_In': '; '.join(ex.do_not_publish_in) if ex.do_not_publish_in else None,
                })

            for rel_type, refs in s.relations.items():
                for ref in refs:
                    if not ref.headword:
                        continue
                    relations_rows.append({
                        'Sense_ID': s.id,
                        'Related_Sense_ID': ref.sense_id,
                        'Related_Entry_Headword': ref.headword,
                        'Relation_Type': rel_type,
                    })

    return {
        'entries': entries_rows,
        'senses': senses_rows,
        'examples': examples_rows,
        'entries_variants': variants_rows,
        'entries_complex_forms': complex_forms_rows,
        'senses_relations': relations_rows,
    }


def write_dictionaria_csvs(tables, output_dir):
    '''Write each table to <output_dir>/<name>.csv, UTF-8, comma-delimited.'''
    os.makedirs(output_dir, exist_ok=True)
    written = {}
    for name, rows in tables.items():
        path = os.path.join(output_dir, f'{name}.csv')
        if rows:
            fieldnames = list(rows[0].keys())
        else:
            fieldnames = []
        with open(path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        written[name] = (path, len(rows))
    return written


if __name__ == '__main__':
    from lift_parser import parse_lift

    infile = sys.argv[1] if len(sys.argv) > 1 else 'ende.lift'
    outdir = sys.argv[2] if len(sys.argv) > 2 else 'dictionaria_output'

    parsed = parse_lift(infile)
    tables = build_dictionaria_tables(parsed)
    written = write_dictionaria_csvs(tables, outdir)
    for name, (path, n) in written.items():
        print(f'{name}: {n} rows -> {path}')
