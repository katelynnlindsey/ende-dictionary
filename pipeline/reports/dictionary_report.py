"""
Dictionary completeness & publication-readiness report.

Operates on the shared ParsedLift representation from lift_parser.py, so
it is not tied to Ende specifically -- point it at any LIFT export whose
`lift_parser.parse_lift()` has been adapted to that language's vernacular
writing-system tag (currently hardcoded to "kit" for Ende; see the
LANG_NOTE below) and it computes the same statistics.

Two things are produced:
  1. Completeness statistics -- the kind of per-entry/per-sense counts an
     editor or referee would want before reading 5,000 entries by hand:
     definition-length distribution, example/translation coverage,
     polysemy rate, verb-class coverage, abbreviation/verb-class
     inventories (for cross-checking a front-matter table), and known
     placeholder-entry contamination (RED/loanword pseudo-entries).
  2. A rubric score against the pasted evaluation criteria (entry
     quality, lexical depth, naturalistic-data balance) -- each tier
     assignment states exactly which computed number produced it, so
     it's auditable rather than a black-box verdict. Two rubric
     dimensions (community collaboration, existing resources) cannot be
     computed from LIFT data alone and are left for manual assessment.

LANG_NOTE: every threshold and grouping here operates on lift_parser's
already-parsed Entry/Sense/Example objects, which are language-agnostic.
The one language-specific dependency is upstream, in lift_parser.py's
hardcoded "kit"/"en" writing-system tags -- change those to run this
report against a different dictionary's LIFT export.

Usage:
    from lift_parser import parse_lift
    from dictionary_report import compute_stats, score_rubric, render_report
    parsed = parse_lift("ende.lift")
    stats = compute_stats(parsed)
    rubric = score_rubric(stats)
    render_report(stats, rubric, "report.md", "report.png")
"""

import sys
import os
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from lift_parser import POSMAP_EN  # noqa: E402

# Definition length buckets, in words. Stated explicitly so the thresholds are auditable/adjustable.
SHORT_MAX_WORDS = 3     # <=3 words: "type of tree", "eat meat"
MEDIUM_MAX_WORDS = 10   # 4-10 words: one clause of description
# >10 words counts as "long"

VERB_POS_RAW = {
    'Transitive verb', 'Intransitive verb', 'Ambitransitive verb', 'Ditransitive verb',
    'Copular verb', 'Auxiliary verb',
}

KNOWN_PLACEHOLDER_PATTERNS = ('loanword',)  # headwords like "English loanword" -- see field_coverage_audit.md


def _definition_bucket(definition):
    if not definition:
        return None
    n = len(definition.split())
    if n <= SHORT_MAX_WORDS:
        return 'short'
    elif n <= MEDIUM_MAX_WORDS:
        return 'medium'
    return 'long'


def compute_stats(parsed):
    '''Return a dict of completeness statistics computed from a ParsedLift.'''
    entries = parsed.entries
    n_entries = len(entries)
    all_senses = [(e, s) for e in entries for s in e.senses]
    n_senses = len(all_senses)

    # --- definitions ---
    def_buckets = Counter()
    senses_with_def = 0
    for e, s in all_senses:
        b = _definition_bucket(s.definition)
        if b:
            senses_with_def += 1
            def_buckets[b] += 1
        else:
            def_buckets['missing'] += 1

    # --- examples ---
    def is_real_example(ex):
        return bool(ex.primary_text and ex.primary_text.strip() and ex.translated_text and ex.translated_text.strip())

    entries_with_example = sum(1 for e in entries if any(is_real_example(ex) for s in e.senses for ex in s.examples))
    senses_with_example = sum(1 for e, s in all_senses if any(is_real_example(ex) for ex in s.examples))
    all_examples = [ex for e in entries for s in e.senses for ex in s.examples]
    real_examples = [ex for ex in all_examples if is_real_example(ex)]
    empty_examples = [ex for ex in all_examples
                       if not (ex.primary_text and ex.primary_text.strip()) and not (ex.translated_text and ex.translated_text.strip())]
    partial_examples = [ex for ex in all_examples if ex not in real_examples and ex not in empty_examples]

    # --- polysemy ---
    entries_multi_sense = sum(1 for e in entries if len(e.senses) > 1)

    # --- verbs & classes ---
    verb_senses = [(e, s) for e, s in all_senses if s.pos_raw in VERB_POS_RAW]
    verb_senses_missing_class = [(e, s) for e, s in verb_senses if not s.verb_class]

    # --- multi-POS entries (candidates for N/V-style splitting) ---
    multi_pos_entries = []
    for e in entries:
        pos_set = {s.pos_raw for s in e.senses if s.pos_raw}
        if len(pos_set) > 1:
            multi_pos_entries.append((e.headword, sorted(pos_set)))

    # --- headword-only entries (no usable content) ---
    def has_no_content(e):
        return not any(s.definition for s in e.senses) and not any(s.pos_raw for s in e.senses)
    headword_only_entries = [e.headword for e in entries if has_no_content(e)]

    # --- abbreviation / verb-class inventories actually used (for front-matter cross-check) ---
    pos_raw_used = Counter(s.pos_raw for e, s in all_senses if s.pos_raw)
    abbreviations_used = Counter()
    unmapped_pos = set()
    for pos_raw, count in pos_raw_used.items():
        abbr = POSMAP_EN.get(pos_raw)
        if abbr:
            abbreviations_used[abbr] += count
        else:
            unmapped_pos.add(pos_raw)
    verb_classes_used = Counter(s.verb_class for e, s in all_senses if s.verb_class)

    # --- known placeholder-entry contamination (RED / "<Lang> loanword") ---
    red_entries = [e.headword for e in entries if e.headword.strip().upper() == 'RED']
    red_variants = [e.headword for e in entries if e.variant_of and e.variant_of.headword
                    and e.variant_of.headword.strip().upper() == 'RED']
    loanword_placeholder_entries = [e.headword for e in entries
                                     if any(p in e.headword.lower() for p in KNOWN_PLACEHOLDER_PATTERNS)]
    loanword_variants = [e.headword for e in entries if e.variant_of and e.variant_of.headword
                          and any(p in e.variant_of.headword.lower() for p in KNOWN_PLACEHOLDER_PATTERNS)]

    # --- naturalistic-data proxy: examples with a source/reference trail vs not ---
    examples_with_source = sum(1 for ex in real_examples if ex.source_ref)
    senses_with_source_note = sum(1 for e, s in all_senses if s.source_note or s.reference_note)

    return {
        'n_entries': n_entries,
        'n_senses': n_senses,
        'senses_with_definition': senses_with_def,
        'definition_buckets': dict(def_buckets),
        'entries_with_example_pct': 100 * entries_with_example / n_entries if n_entries else 0,
        'senses_with_example_pct': 100 * senses_with_example / n_senses if n_senses else 0,
        'n_examples_total_raw': len(all_examples),
        'n_examples_translated': len(real_examples),
        'n_examples_empty_placeholder': len(empty_examples),
        'n_examples_partial_untranslated': len(partial_examples),
        'entries_multi_sense_pct': 100 * entries_multi_sense / n_entries if n_entries else 0,
        'n_verb_senses': len(verb_senses),
        'n_verb_senses_missing_class': len(verb_senses_missing_class),
        'verb_senses_missing_class_pct': 100 * len(verb_senses_missing_class) / len(verb_senses) if verb_senses else 0,
        'multi_pos_entries': multi_pos_entries,
        'n_multi_pos_entries': len(multi_pos_entries),
        'headword_only_entries': headword_only_entries,
        'n_headword_only_entries': len(headword_only_entries),
        'abbreviations_used': dict(abbreviations_used.most_common()),
        'unmapped_pos_values': sorted(unmapped_pos),
        'verb_classes_used': dict(verb_classes_used.most_common()),
        'red_placeholder_entries': red_entries,
        'red_placeholder_variants_count': len(red_variants),
        'loanword_placeholder_entries': loanword_placeholder_entries,
        'loanword_placeholder_variants_count': len(loanword_variants),
        'examples_with_source_pct': 100 * examples_with_source / len(real_examples) if real_examples else 0,
        'senses_with_source_note_pct': 100 * senses_with_source_note / n_senses if n_senses else 0,
    }


def score_rubric(stats):
    '''Score against the pasted evaluation rubric. Each verdict states the number(s) behind it.'''
    n = stats['n_entries']

    # Lexical depth
    if n >= 5000:
        depth = ('Comprehensive', f'{n} headwords (>=5,000)')
    elif n >= 2500:
        depth = ('Substantial', f'{n} headwords (2,500-4,999)')
    elif n >= 1000:
        depth = ('Foundational', f'{n} headwords (1,000-2,499)')
    else:
        depth = ('Below threshold', f'{n} headwords (<1,000)')

    # Entry quality: Basic (defn+POS) -> Standard (+example) -> Rich (+notes/domain/cross-ref)
    # Approximated at the entry level: an entry qualifies for a tier if it has the required
    # ingredients on at least one sense (documented here so the scoring is auditable).
    basic_pct = 100 * stats['senses_with_definition'] / stats['n_senses'] if stats['n_senses'] else 0
    standard_pct = stats['entries_with_example_pct']
    entry_quality = (
        f"Basic ingredients (definition present): {basic_pct:.1f}% of senses. "
        f"Standard (+ example sentence): {standard_pct:.1f}% of entries have at least one translated example. "
        f"See field_coverage_audit.md for what would lift many entries into 'Rich' (etymology, topic labels) "
        f"that already exist in FLEx but aren't surfaced yet."
    )

    # Naturalistic data proxy
    src_pct = stats['examples_with_source_pct']
    if src_pct >= 60:
        naturalistic = ('Corpus-grounded (proxy)', f'{src_pct:.1f}% of translated examples carry a source/reference code')
    elif src_pct >= 20:
        naturalistic = ('Mixed (proxy)', f'{src_pct:.1f}% of translated examples carry a source/reference code')
    else:
        naturalistic = ('Primarily elicited (proxy)', f'{src_pct:.1f}% of translated examples carry a source/reference code -- '
                         'NB this is a proxy only: an example can be corpus-derived without a recorded source code, so this likely understates naturalistic coverage')

    return {
        'lexical_depth': depth,
        'entry_quality_note': entry_quality,
        'naturalistic_data_proxy': naturalistic,
        'community_collaboration': ('Not computable from LIFT data', 'requires acknowledgements/authorship text, not entry data'),
        'existing_resources': ('Not computable from LIFT data', 'requires external knowledge of the language\'s resource landscape'),
    }


def render_report(stats, rubric, out_md, out_png=None):
    '''Write the markdown report; optionally render a summary bar chart to out_png.'''
    lines = []
    lines.append("# Dictionary completeness & publication-readiness report\n\n")
    lines.append(f"**{stats['n_entries']:,} entries, {stats['n_senses']:,} senses.**\n\n")

    lines.append("## Rubric scoring (against the pasted evaluation criteria)\n\n")
    lines.append(f"- **Lexical depth:** {rubric['lexical_depth'][0]} -- {rubric['lexical_depth'][1]}\n")
    lines.append(f"- **Entry quality:** {rubric['entry_quality_note']}\n")
    lines.append(f"- **Naturalistic data (proxy):** {rubric['naturalistic_data_proxy'][0]} -- {rubric['naturalistic_data_proxy'][1]}\n")
    lines.append(f"- **Community collaboration:** {rubric['community_collaboration'][0]} ({rubric['community_collaboration'][1]})\n")
    lines.append(f"- **Existing resources:** {rubric['existing_resources'][0]} ({rubric['existing_resources'][1]})\n\n")

    lines.append("## Completeness statistics\n\n")
    db = stats['definition_buckets']
    total_def = sum(db.values())
    lines.append(f"**Definitions** (bucketed by word count: short <={SHORT_MAX_WORDS}, medium <={MEDIUM_MAX_WORDS}, long above):\n\n")
    for bucket in ('short', 'medium', 'long', 'missing'):
        c = db.get(bucket, 0)
        pct = 100 * c / total_def if total_def else 0
        lines.append(f"- {bucket}: {c} senses ({pct:.1f}%)\n")
    lines.append(f"\n**Examples:** {stats['entries_with_example_pct']:.1f}% of entries have >=1 translated example "
                 f"({stats['senses_with_example_pct']:.1f}% of senses). Of {stats['n_examples_total_raw']:,} raw "
                 f"`<example>` slots in the LIFT export: {stats['n_examples_translated']:,} are complete "
                 f"(Ende text + translation), {stats['n_examples_empty_placeholder']:,} are empty FLEx template "
                 f"slots, {stats['n_examples_partial_untranslated']:,} have Ende text but no translation yet.\n\n")
    lines.append(f"**Polysemy:** {stats['entries_multi_sense_pct']:.1f}% of entries have more than one sense.\n\n")
    lines.append(f"**Verb classes:** {stats['n_verb_senses']:,} verb senses; {stats['n_verb_senses_missing_class']:,} "
                 f"({stats['verb_senses_missing_class_pct']:.1f}%) have no inflection class recorded. Classes in use: "
                 f"{stats['verb_classes_used']}.\n\n")
    lines.append(f"**Multi-POS entries** (senses on the same entry spanning >1 distinct part of speech -- candidates "
                 f"for the referee's suggested N/V split): {stats['n_multi_pos_entries']:,} entries.\n\n")
    lines.append(f"**Headword-only entries** (no definition and no part-of-speech on any sense): "
                 f"{stats['n_headword_only_entries']:,}.\n\n")
    lines.append(f"**Placeholder-entry contamination:** {len(stats['red_placeholder_entries'])} 'RED' entries "
                 f"({stats['red_placeholder_variants_count']} variants point to one), "
                 f"{len(stats['loanword_placeholder_entries'])} '<Language> loanword' entries "
                 f"({stats['loanword_placeholder_variants_count']} variants point to one) -- see "
                 f"reviewer_response_triage.md.\n\n")
    lines.append(f"**Abbreviations actually used in the output** (cross-check against the front-matter abbreviations "
                 f"table): {stats['abbreviations_used']}\n\n")
    if stats['unmapped_pos_values']:
        lines.append(f"**POS values with no abbreviation mapping** (would print as their raw FLEx value): "
                     f"{stats['unmapped_pos_values']}\n\n")

    with open(out_md, 'w', encoding='utf-8') as f:
        f.write(''.join(lines))

    if out_png:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 5))
        labels = [
            '≥1 example\n(entries)',
            'Multi-sense\n(entries)',
            'Verb class\npresent',
            'Definition\npresent',
            'Example has\nsource code',
        ]
        values = [
            stats['entries_with_example_pct'],
            stats['entries_multi_sense_pct'],
            100 - stats['verb_senses_missing_class_pct'],
            100 * stats['senses_with_definition'] / stats['n_senses'] if stats['n_senses'] else 0,
            stats['examples_with_source_pct'],
        ]
        bars = ax.bar(labels, values, color='#4C72B0')
        ax.set_ylabel('% of entries / senses')
        ax.set_ylim(0, 100)
        ax.set_title(f"Ende dictionary completeness ({stats['n_entries']:,} entries)")
        for bar, v in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, v + 1.5, f'{v:.0f}%', ha='center', fontsize=9)
        fig.tight_layout()
        fig.savefig(out_png, dpi=150)
        plt.close(fig)

    return out_md, out_png


if __name__ == '__main__':
    from lift_parser import parse_lift

    infile = sys.argv[1] if len(sys.argv) > 1 else 'ende.lift'
    parsed = parse_lift(infile)
    stats = compute_stats(parsed)
    rubric = score_rubric(stats)
    render_report(stats, rubric, 'dictionary_report.md', 'dictionary_report.png')
    print("wrote dictionary_report.md / dictionary_report.png")
