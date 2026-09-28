"""
LaTeX generator for the Ende-English academic dictionary.

Consumes the shared representation from `lift_parser.parse_lift()` and
reproduces `dictionary_ende.tex` exactly as the current
configured-dictionary/20250803/ende_dict.py + ende_process.py pipeline
does. Ported field-by-field, byte-for-byte, from that code -- including
two dead-code paths (the `irregthirdposs`/`irregfirstposs` possessed-form
macro and the `RelatedForms` macro) that contain a pre-existing
double-backslash typo in the original source. Both paths are inert on
the current data (0 entries trigger them) and are reproduced as-is
rather than silently fixed -- see pipeline/docs/field_mapping.md.

Usage:
    from lift_parser import parse_lift
    from build_latex import build_latex_document
    parsed = parse_lift("ende.lift")
    tex = build_latex_document(parsed, header_path="head.txt")
    open("dictionary_ende.tex", "w", encoding="utf-8").write(tex)
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from lift_parser import POSMAP_EN, VERB_POS  # noqa: E402  (path setup must precede this import)


RELATION_MACRO = {
    'Synonym': 'synonym',
    'Antonym': 'antonym',
    'Generic': 'generic',
    'Coordinate term': 'coordinateterm',
    'Specific': 'specific',
    'Colloquial term': 'colloquialterm',
    'Example': 'exampleterm',
    'Doublet': 'doublet',
    'Full phrase': 'fullphrase',
    'Near synonym': 'nearsynonym',
    'Whole': 'whole',
    'Part': 'partterm',
    'Not to be confused': 'nottobeconfused',
    'Nonsingular': 'nonsingular',
    'Singular': 'singular',
    'Ideophonic pair (voiced)': 'ideovoiced',
    'Ideophonic pair (voiceless)': 'ideovoiceless',
}


def sanitize_latex(s):
    '''Sanitize a string for use in LaTeX commands like \\hyperlink and \\hypertarget.'''
    if not s:
        return s
    return (s.replace('\\', r'\textbackslash{}')
             .replace('{', r'\{')
             .replace('}', r'\}')
             .replace('#', r'\#')
             .replace('$', r'\$')
             .replace('%', r'\%')
             .replace('&', r'\&')
             .replace('_', r'\_')
             .replace('~', r'\textasciitilde{}')
             .replace('^', r'\textasciicircum{}'))


def field_tex(val, texfld, level=1):
    '''Port of simplefield2tex, given an already-extracted value (no XPath lookup needed).'''
    if not val:
        return ''
    return '  ' * level + '\\' + texfld + '{' + val.strip() + '}'


def pos_tex(pos_raw, verb_class):
    '''Port of pos2tex / sense_pos2tex (identical logic, shared here).'''
    if pos_raw in ('Intransitive verb', 'Transitive verb') and verb_class:
        return r'  \pos{v. ' + verb_class + '}'
    ginfo = POSMAP_EN.get(pos_raw, pos_raw) if pos_raw else ''
    return '\n' + r'  \pos{' + ginfo + '}'


def entry_pos_and_verbclass(entry):
    '''Entry-level POS: first sense's pos_raw, but verb_class from the LAST sense that has one
    (ported from pos2tex, which used find() for ginfo but findall() for the trait scan).'''
    pos_raw = entry.senses[0].pos_raw if entry.senses else None
    verb_class = None
    for s in entry.senses:
        if s.verb_class:
            verb_class = s.verb_class
    return pos_raw, verb_class


def examples_tex(sense):
    '''Port of examples2tex.'''
    tex = ''
    for ex in sense.examples:
        if ex.primary_text and ex.primary_text.strip() and ex.translated_text and ex.translated_text.strip():
            tex += '    \\example{'
            tex += '\n'
            tex += field_tex(ex.primary_text, 'exsen', level=3)
            tex += field_tex(ex.translated_text, 'extran', level=3)
            tex += '}'
    return tex


def inherited_examples_tex(examples):
    '''Render examples inherited from variant entries (Entry.inherited_examples) -- same LaTeX
    shape as examples_tex, since these are already known translated (checked at parse time).'''
    tex = ''
    for ex in examples:
        tex += '    \\example{'
        tex += '\n'
        tex += field_tex(ex.primary_text, 'exsen', level=3)
        tex += field_tex(ex.translated_text, 'extran', level=3)
        tex += '}'
    return tex


def relations_tex(sense, valid_headwords):
    '''Port of relations2tex.'''
    tex = ''
    relations_by_type = {}
    for rel_type, refs in sense.relations.items():
        if rel_type not in RELATION_MACRO:
            continue
        for ref in refs:
            if not ref.headword:
                continue
            sanitized = sanitize_latex(ref.headword)
            formatted = f'\\hyperlink{{{sanitized}}}{{{sanitized}}}' if ref.headword in valid_headwords else sanitized
            relations_by_type.setdefault(rel_type, []).append(formatted)
    for rel_type, formatted_list in relations_by_type.items():
        tex += f'  \\{RELATION_MACRO[rel_type]}{{'
        tex += ', '.join(formatted_list)
        tex += '}'
    return tex


def relforms_tex(entry):
    '''Port of relforms2tex. Inert on current data (no RelatedForms fields exist) -- reproduced
    with the original's double-backslash typo (r'\\\\relformiqu{' etc.) for byte fidelity.'''
    tex = ''
    for idx, rf in enumerate(entry.related_forms):
        tex += '  \\relforms{'
        if len(entry.related_forms) > 1:
            tex += r'\textbf{' + f'{idx + 1}.}} '
        tex += '\n' + r'\\relformiqu{' + rf.get('kit', '') + '}'
        tex += '\n' + r'\\relformen{' + rf.get('en', '') + '}'
        tex += '}'
    return tex


def complexforms_tex(entry, valid_headwords):
    '''Port of complexforms2tex (this entry is the base of these complex forms).'''
    tex = ''
    for ref in entry.complex_forms:
        if not ref.headword:
            continue
        sanitized = sanitize_latex(ref.headword)
        pos = POSMAP_EN.get(ref.pos_raw, ref.pos_raw) if ref.pos_raw else ''
        head = f'\\hyperlink{{{sanitized}}}{{{sanitized}}}' if ref.headword in valid_headwords else sanitized
        tex += '  \\complexforms{'
        tex += r'\complexformhead{' + head + r'}'
        tex += r'\complexformpos{' + pos + r'}'
        if ref.definition:
            tex += r'\complexformdefn{' + ref.definition + r'}'
        tex += r'\complexformtype{' + ref.complex_type + r'} '
        tex += '}'
    return tex


def complexformof_tex(entry, valid_headwords):
    '''Port of complexformof2tex (this entry IS a complex form; show its one base entry).'''
    ref = entry.complex_form_of
    if ref is None or not ref.headword:
        return ''
    sanitized = sanitize_latex(ref.headword)
    pos = POSMAP_EN.get(ref.pos_raw, ref.pos_raw) if ref.pos_raw else ''
    head = f'\\hyperlink{{{sanitized}}}{{{sanitized}}}' if ref.headword in valid_headwords else sanitized
    tex = '  \\complexformof{'
    tex += r'\complexformhead{' + head + r'}'
    tex += r'\complexformpos{' + pos + r'}'
    if ref.definition:
        tex += r'\complexformdefn{' + ref.definition + r'}'
    tex += '}'
    return tex


def senses_tex(entry, sense_pos, valid_headwords):
    '''Port of senses2tex.'''
    tex = ''
    senses = entry.senses
    for idx, s in enumerate(senses):
        tex += '  \\sense{'
        if len(senses) > 1:
            tex += r'\textbf{' + f'{idx + 1}.}} '
        tex += '\n'
        if sense_pos:
            tex += pos_tex(s.pos_raw, s.verb_class)
        if s.definition:
            tex += '    \\definition{' + s.definition.strip() + '}'
        tex += field_tex(s.scientific_name, 'scientificname', level=2)
        tex += field_tex(s.cultural_note, 'anthronote', level=2)
        tex += field_tex(s.semantic_note, 'semnote', level=2)
        tex += field_tex(s.grammar_note, 'grammarnote', level=2)
        tex += field_tex(s.sociolinguistic_note, 'socionote', level=2)
        tex += field_tex(s.discourse_note, 'discoursenote', level=2)
        tex += examples_tex(s)
        if idx == 0 and entry.inherited_examples:
            tex += inherited_examples_tex(entry.inherited_examples)
        tex += relations_tex(s, valid_headwords)
        tex += '}'
    return tex


def entry_to_tex(entry, valid_headwords):
    '''Port of entry2dict_acad -- returns the LaTeX for one \\entry{...}{...} block.'''
    sanitized_headword = sanitize_latex(entry.headword)
    tex = '\n' + r'\entry{' + sanitized_headword + r'}{'
    tex += r'\hypertarget{' + sanitized_headword + r'}{}'
    tex += r'\headword{' + sanitized_headword + r'}'

    if entry.lexeme_form:
        tex += field_tex(entry.lexeme_form, 'lexeme', level=1)

    if entry.impf_rt:
        tex += '\n' + r'\impfrt{\impfrtlab ' + sanitize_latex(entry.impf_rt) + r'}'

    isvariant = entry.variant_of is not None
    if isvariant:
        vr = entry.variant_of
        sanitized_mainwd = sanitize_latex(vr.headword) if vr.headword else ''
        if vr.headword and vr.headword in valid_headwords:
            tex += ('\n' + r'\variantof{' + '\\' + vr.vartype + r' of \vartext{\hyperlink{'
                    + sanitized_mainwd + r'}{' + sanitized_mainwd + r'}}}')
        else:
            tex += '\n' + r'\variantof{' + '\\' + vr.vartype + r' of \vartext{' + sanitized_mainwd + r'}}'

    tex += field_tex(entry.irregular_plural, 'irregpl', level=1)
    tex += field_tex(entry.irregular_possessed, 'irregposs', level=1)
    for irform in ('irregthirdposs', 'irregfirstposs'):
        variants = entry.irregular_possessed_forms.get(irform)
        if variants:
            joined = ', '.join(sanitize_latex(v.strip()) for v in variants)
            # NB: reproduces the original's double-backslash typo -- see module docstring.
            tex += '\n' + r'\\' + irform + r'{' + joined + r'}'

    tex += field_tex(entry.derivational_root, 'derivroot', level=1)
    tex += field_tex(entry.literal_meaning, 'litmean', level=1)
    tex += field_tex(entry.pronunciation, 'pronnote', level=1)

    if not isvariant:
        pos_raw, verb_class = entry_pos_and_verbclass(entry)
        # NB: this comparison is always False on real data -- pos_raw is capitalized
        # ("Intransitive verb") while VERB_POS is lowercase. Reproduced as-is; see
        # pipeline/docs/field_mapping.md for why this is a pre-existing dead branch.
        if pos_raw in VERB_POS:
            tex += senses_tex(entry, sense_pos=True, valid_headwords=valid_headwords)
        else:
            tex += pos_tex(pos_raw, verb_class)
            tex += senses_tex(entry, sense_pos=False, valid_headwords=valid_headwords)
    else:
        if entry.senses:
            s = entry.senses[0]
            tex += field_tex(s.scientific_name, 'scientificname', level=2)
            tex += field_tex(s.cultural_note, 'anthronote', level=2)
            tex += field_tex(s.semantic_note, 'semnote', level=2)
            tex += field_tex(s.grammar_note, 'grammarnote', level=2)
            tex += field_tex(s.sociolinguistic_note, 'socionote', level=2)
            tex += field_tex(s.discourse_note, 'discoursenote', level=2)

    tex += field_tex(entry.active_middle_form, 'activemiddle', level=1)
    tex += relforms_tex(entry)
    tex += complexformof_tex(entry, valid_headwords)

    for vartype, forms in entry.variants.items():
        if vartype in ('irregthirdposs', 'irregfirstposs', 'irregpllab'):
            continue
        variants = [v.strip() for v in forms]
        if variants:
            vt = vartype
            if len(variants) > 1 and vt in ('freevarlab', 'dialectvarlab'):
                vt += 's'
            linked = [
                r'\hyperlink{' + sanitize_latex(v) + r'}{' + sanitize_latex(v) + r'}'
                if v in valid_headwords else sanitize_latex(v)
                for v in variants
            ]
            tex += '\n' + r'\variants{' + '\\' + vt + r' \vartext{' + ', '.join(linked) + r'}}'

    tex += complexforms_tex(entry, valid_headwords)
    tex += r'}'
    return tex


def reversal_entry_to_tex(gloss, pos_map, entry_lookup):
    '''Port of reventry2dict_acad. Returns (tex, sortword, firstletter) or None.'''
    if not gloss:
        return None
    tex = '\n' + r'\entry{' + sanitize_latex(gloss) + r'}{'
    tex += r'\headword{' + sanitize_latex(gloss) + r'}'
    gloss_clean = gloss.strip().replace(r'\sci ', '').replace(r'\sp ', '')

    from lift_parser import firstletter, str2sort
    letter = firstletter(gloss_clean).upper()

    for pos in sorted(pos_map.keys()):
        tex += '\n' + r'\pos{' + pos + r'}'
        tex += '\n' + r'\sense{'
        headwords_tex = []
        for entry_id in pos_map[pos]:
            entry = entry_lookup.get(entry_id)
            if entry is None or not entry.headword:
                continue
            sanitized = sanitize_latex(entry.headword)
            headwords_tex.append(r'\gloss{\hyperlink{' + sanitized + r'}{' + sanitized + r'}}')
        if not headwords_tex:
            return None
        tex += ', '.join(headwords_tex)
        tex += r'}'
    tex += r'}'
    return (tex, str2sort(gloss_clean), letter)


def build_latex_document(parsed, header_text):
    '''Assemble the full dictionary_ende.tex document from a ParsedLift and the head.txt preamble.'''
    parts = [header_text, '\n']

    # ---- Regular dictionary ----
    parts.append(r'\section{Regular Dictionary}' + '\n\n')
    lastchapter = ''
    for entry in parsed.entries:  # already sorted by sortword
        if entry.firstletter != lastchapter:
            parts.append('\n' + r'\chapter{' + entry.firstletter + '}\n\n')
            lastchapter = entry.firstletter
        parts.append(entry_to_tex(entry, parsed.valid_headwords) + '\n')

    # ---- Reversal dictionary ----
    rev_entries = []
    for gloss, pos_map in parsed.reversal_en.items():
        result = reversal_entry_to_tex(gloss, pos_map, parsed.entry_lookup)
        if result is not None:
            rev_entries.append(result)
    rev_entries.sort(key=lambda r: r[1])

    parts.append('\n' + r'\section{Reversal Dictionary}' + '\n\n')
    lastchapter = ''
    for tex, _sortword, letter in rev_entries:
        if letter != lastchapter:
            parts.append('\n' + r'\chapter{' + letter + '}\n\n')
            lastchapter = letter
        parts.append(tex + '\n')

    parts.append('\n' + r'\end{document}' + '\n')
    return ''.join(parts)


if __name__ == '__main__':
    import sys as _sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
    from lift_parser import parse_lift

    infile = _sys.argv[1] if len(_sys.argv) > 1 else 'ende.lift'
    header_path = _sys.argv[2] if len(_sys.argv) > 2 else 'head.txt'
    outfile = _sys.argv[3] if len(_sys.argv) > 3 else 'dictionary_ende.tex'

    parsed = parse_lift(infile)
    header_text = open(header_path, 'r', encoding='utf-8').read()
    doc = build_latex_document(parsed, header_text)
    with open(outfile, 'w', encoding='utf-8') as f:
        f.write(doc)
    print(f"Wrote {outfile} ({len(doc)} chars) from {len(parsed.entries)} entries.")
