"""
PROPOSED (not merged into build_latex.py's default output) fixes for three
reviewer complaints. Each is implemented as a self-contained variant of the
relevant build_latex.py function, so the validated baseline generator is
untouched -- these are opt-in, reviewable independently, and easy to either
fold into build_latex.py permanently or discard.

1. Suppress the 7 "RED" and 5 "<Language> loanword" placeholder entries from
   being published as their own dictionary headwords (they're FLEx's internal
   convention for tagging reduplication / loanword-origin, not real lexemes),
   while preserving the information their 84+92 dependent entries carry --
   rendered without a dangling link to a fake headword.
2. Join multiple complex-forms of the same base entry onto one line instead
   of one bulleted \\complexforms{} block per form.
3. Add \\includegraphics support for the 118 entries whose FLEx illustration
   file already exists in the repo.

None of this is wired into run_pipeline.py's default output. See
reviewer_response_triage.md for the review complaints these address and
field_coverage_audit.md for the underlying data counts.
"""

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from lift_parser import POSMAP_EN  # noqa: E402
import build_latex as bl  # reuse its sanitize_latex, field_tex, pos_tex, etc.


LOANWORD_RE = re.compile(r'^(.+?)\s+loanword$', re.IGNORECASE)


def classify_placeholder(headword):
    '''Return ('red', None) | ('loanword', donor_language) | (None, None).'''
    if headword.strip().upper() == 'RED':
        return ('red', None)
    m = LOANWORD_RE.match(headword.strip())
    if m:
        return ('loanword', m.group(1))
    return (None, None)


def find_placeholder_headwords(parsed):
    '''Return the set of headwords that are placeholder entries (to exclude from publication).'''
    return {e.headword for e in parsed.entries if classify_placeholder(e.headword)[0] is not None}


def variantof_tex_proposed(entry, valid_headwords, placeholder_headwords):
    '''Replacement for the \\variantof{} clause in entry_to_tex, aware of placeholder bases.'''
    vr = entry.variant_of
    if vr is None:
        return ''
    kind, donor = classify_placeholder(vr.headword or '')
    if kind == 'red':
        # No real word to point at -- just state what kind of form this is.
        return '\n' + r'\variantof{' + '\\' + vr.vartype + '}'
    if kind == 'loanword':
        sanitized_donor = bl.sanitize_latex(donor)
        return '\n' + r'\variantof{$\blacktriangleright$~\textsc{Loanword} (' + sanitized_donor + ')}'
    # Unchanged (normal) rendering, ported from entry_to_tex:
    sanitized_mainwd = bl.sanitize_latex(vr.headword) if vr.headword else ''
    if vr.headword and vr.headword in valid_headwords:
        return ('\n' + r'\variantof{' + '\\' + vr.vartype + r' of \vartext{\hyperlink{'
                + sanitized_mainwd + r'}{' + sanitized_mainwd + r'}}}')
    return '\n' + r'\variantof{' + '\\' + vr.vartype + r' of \vartext{' + sanitized_mainwd + r'}}'


def complexforms_tex_joined(entry, valid_headwords):
    '''Replacement for complexforms_tex: one \\complexforms{} block listing every complex form
    of this entry, comma-separated, instead of one block per form.'''
    parts = []
    for ref in entry.complex_forms:
        if not ref.headword:
            continue
        sanitized = bl.sanitize_latex(ref.headword)
        pos = POSMAP_EN.get(ref.pos_raw, ref.pos_raw) if ref.pos_raw else ''
        head = f'\\hyperlink{{{sanitized}}}{{{sanitized}}}' if ref.headword in valid_headwords else sanitized
        piece = r'\complexformhead{' + head + r'}'
        piece += r'\complexformpos{' + pos + r'}'
        if ref.definition:
            piece += r'\complexformdefn{' + ref.definition + r'}'
        piece += r'\complexformtype{' + ref.complex_type + r'}'
        parts.append(piece)
    if not parts:
        return ''
    return '  \\complexforms{' + ', '.join(parts) + ' }'


# --- pictures ---------------------------------------------------------------

def resolve_illustrations(parsed, lift_path, pictures_dir):
    '''Re-scan the raw LIFT XML for non-empty <illustration href="..."> entries, keyed by
    entry id, filtered to files that actually exist in pictures_dir. lift_parser.py doesn't
    currently expose this field (see field_coverage_audit.md #2), so this re-parses directly.'''
    import xml.etree.ElementTree as ET
    tree = ET.parse(lift_path)
    root = tree.getroot()
    available = set(os.listdir(pictures_dir)) if os.path.isdir(pictures_dir) else set()
    result = {}
    for e in root.findall('entry'):
        eid = e.attrib.get('id')
        for ill in e.findall('.//illustration'):
            href = ill.attrib.get('href', '').strip()
            if href and href in available:
                result.setdefault(eid, []).append(href)
    return result


def entryimage_tex(filenames):
    '''\\entryimage{} macro call(s) for a list of resolved image filenames (needs a matching
    \\newcommand{\\entryimage}[1]{\\includegraphics[width=0.3\\linewidth]{#1}} added to head.txt).'''
    return ''.join('\n' + r'\entryimage{images/' + fn + '}' for fn in filenames)
