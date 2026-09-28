"""
Shared FLEx LIFT parser for the Ende dictionary pipeline.

Reads a FLEx `.lift` export and returns one normalized, format-agnostic
representation of every entry/sense/example. This module does NOT know
about LaTeX or Dictionaria/CSV output -- it only parses and cleans the
LIFT XML. `pipeline/latex/build_latex.py` and
`pipeline/dictionaria/build_dictionaria.py` both consume its output so the
two publications can never drift apart.

Parsing logic (headword resolution, sort-key computation, exclusion
rules, variant/complex-form/relation resolution) is ported directly from
the proven configured-dictionary/20250803/ende_dict.py and
ende_process.py so behavior matches the existing pipeline exactly. See
pipeline/docs/field_mapping.md for the full field inventory this is
based on.

Usage:
    from lift_parser import parse_lift
    parsed = parse_lift("ende.lift")
    parsed.entries            # list[Entry], already filtered + sorted
    parsed.reversal_en        # dict[str, dict[str, list[str]]] -> gloss -> pos -> [entry_id]
    parsed.warnings           # list[str] collected during parsing
    parsed.stats              # dict of counts for the provenance log
"""

import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict
from typing import Optional


# ---------------------------------------------------------------------------
# Constants (ported verbatim from ende_dict.py / ende_process.py)
# ---------------------------------------------------------------------------

POSMAP_EN = {
    'Adjective': 'adj.',
    'Adverb': 'adv.',
    'Ambitransitive verb': 'a.v.',
    'Interjection': 'interj.',
    'Intransitive verb': 'i.v.',
    'Locational': 'loc.n.',
    'Locative postposition': 'loc.postp.',
    'Noun': 'n.',
    'Postposition': 'postp.',
    'Proper noun': 'prop.n.',
    'Transitive verb': 't.v.',
    'Anaphoric pronoun': 'anaph.pro.',
    'Complementizer': 'comp.',
    'Conjunction': 'conj.',
    'Demonstrative': 'dem.',
    'Manner demonstrative': 'man.dem.',
    'Determiner': 'det.',
    'Ditransitive verb': 'd.v.',
    'Interrogative word': 'interrog.',
    'Locative demonstrative': 'loc.dem.',
    'Numeral': 'num.',
    'Particle': 'prtcl.',
    'Pronoun': 'pro.',
    'Pro-clause': 'procl.',
    'Relative pronoun': 'rel.pro.',
    'Pronominal enclitic': 'pro.enc.',
    'Modifier': 'mod.',
    'Verb': 'v.',
    'Subordinating connective': 'sub.con.',
    'Clitic': 'clt.',
    'Nominal enclitic': 'nom.clt.',
    'Copular verb': 'cop.',
    'Interrogative pronoun': 'int.pro.',
    'Manner adverb': 'man.adv.',
    'Discourse particle': 'disc.prtcl.',
    'Auxiliary verb': 'aux.',
    'Quantifier': 'quant.',
    'Intransitive coverb': 'cov.',
    'Transitive coverb': 'cov.',
    'Personal pronoun': 'pro.',
    'Color term': 'col.',
    'Adverbial demonstrative': 'adv.dem.',
    'Nominal demonstrative': 'nom.dem.',
    'Transitive/Intransitive coverb': 'cov.',
    'Transitive compound verb': 'comp.v.',
    'Intransitive compound verb': 'comp.v.',
    'Property noun': 'prop.n.',
    'Coordinating connective': 'coord.conn.',
}

VERB_POS = [
    'verb', 'ambitransitive verb', 'copular verb', 'ditransitive verb',
    'existential verb', 'infinitive verb', 'intransitive verb', 'transitive verb'
]

ORDER_VARLAB_ENDE = [
    'Spellingvariant', 'FastSpeechvariant', 'Inflectedform', 'Unspecifiedvariant',
    'Dialectalvariant', 'Derivedvariant', 'Infinitivalreduplicant', 'Pluralreduplicant',
    'BabyTalkvariant', 'Derivationalreduplicant', 'Freevariant'
]

VARMAP = {
    'Spelling Variant': 'Spellingvariant',
    'Fast Speech Variant': 'FastSpeechvariant',
    'Inflected Form': 'Inflectedform',
    'Unspecified Variant': 'Unspecifiedvariant',
    'Dialectal Variant': 'Dialectalvariant',
    'Derived Variant': 'Derivedvariant',
    'Infinitival reduplicant': 'Infinitivalreduplicant',
    'Plural reduplicant': 'Pluralreduplicant',
    'Baby Talk Variant': 'BabyTalkvariant',
    'Derivational reduplicant': 'Derivationalreduplicant',
    'Free Variant': 'Freevariant',
}

RELATION_TYPES = [
    'Synonym', 'Antonym', 'Generic', 'Coordinate term', 'Specific',
    'Colloquial term', 'Example', 'Doublet', 'Full phrase', 'Near synonym',
    'Whole', 'Part', 'Not to be confused', 'Nonsingular', 'Singular',
    'Ideophonic pair (voiced)', 'Ideophonic pair (voiceless)',
]

ALPHABET = ['a', 'ä', 'b', 'd', 'dd', 'e', 'f', 'g', 'i', 'ɨ', 'k', 'l', 'll', 'm',
            'n', 'ng', 'ny', 'o', 'p', 'r', 's', 't', 'tt', 'u', 'w', 'y', 'z',
            'c', 'h', 'j', 'q', 'v', 'x']
AMAP = {c: i for i, c in enumerate(ALPHABET)}


# ---------------------------------------------------------------------------
# String / text helpers (ported verbatim)
# ---------------------------------------------------------------------------

def str2alpha(s):
    '''Convert characters in s to a list of alphabetic characters and digraphs.'''
    s = s.strip().lower()
    s = re.sub(r'\\\w+{([^}]+)}', r'\1', s)
    s = s.replace('"', '').replace('“', '').replace('”', '').replace('¿', '').replace('?', '')
    s = s.replace('=', '').replace('-', '').replace('#', '')
    s = cleanstr(s)
    result = []
    i = 0
    while i < len(s):
        if i + 1 < len(s) and s[i:i + 2] in ['dd', 'll', 'ng', 'ny', 'tt']:
            result.append(s[i:i + 2])
            i += 2
        else:
            result.append(s[i])
            i += 1
    return result


def str2sort(s):
    '''Convert characters in s to a sequence of ordered codepoints and return as a string.'''
    chars = str2alpha(s)
    sortnum = [AMAP[c] for c in chars if c in AMAP]
    return ''.join(chr(n) for n in sortnum)


def firstletter(s):
    '''Return first alphabetic letter or digraph of s for chapter grouping.'''
    try:
        chars = str2alpha(s)
        if not chars:
            return ''
        return chars[0]
    except IndexError:
        return ''


def cleanstr(s):
    '''Clean up bad character data in a string and return cleaned string.'''
    for c in 'áéíóú':
        s = s.replace(c + '\u0301', c).replace(c.upper() + '\u0301', c.upper())
        s = s.replace(c + '\u0081', c).replace(c.upper() + '\u0081', c.upper())
    s = s.replace('~', '').replace('ẽ', 'e')
    return s


def nodetext(node):
    '''Return all text found in node as a plain (non-LaTeX-escaped) string.'''
    return cleanstr(''.join(list(node.itertext())))


def get_headword(entry):
    '''Return an entry's headword, preferring the citation form, falling back to lexical-unit.'''
    try:
        hdwd = nodetext(entry.find('citation/form[@lang="kit"]/text')).strip()
        if not hdwd:
            return None
    except (AttributeError, TypeError):
        try:
            hdwd = nodetext(entry.find('lexical-unit/form[@lang="kit"]/text')).strip()
            if not hdwd:
                return None
        except (AttributeError, TypeError):
            return None
    return hdwd


def get_first_pos(e):
    '''Get the raw part-of-speech string of the first sense in an entry.'''
    try:
        return e.find('sense/grammatical-info').attrib['value'].strip()
    except AttributeError:
        return ''


def is_excluded(entry):
    '''Return True if entry is annotated EXCLUDE in its Entry History field.'''
    try:
        ehist = ''.join(entry.find('field[@type="Entry History"]/form[@lang="es"]/text').itertext())
        return ehist.find('EXCLUDE') >= 0
    except AttributeError:
        return False


def is_suffix(entry):
    '''Return True if entry type is a suffix (excluded from both publications).'''
    return entry.find('trait[@name="morph-type"][@value="suffix"]') is not None


def get_irreg_pl(glosses):
    '''Extract irregular plurals noted as "PL: form1, form2" inside a gloss text.'''
    irreg_pl = []
    for gloss in glosses:
        try:
            irreg_pl += [g.strip() for g in nodetext(gloss).split('PL:')[1].split(',')]
        except IndexError:
            pass
    return irreg_pl


def simplefield(node, xpath):
    '''Return plain text at xpath under node, or None if missing/empty.
    Applies cleanstr (matches simplefield2tex/nodetext in the original code).'''
    try:
        val = nodetext(node.find(xpath)).strip()
        return val if val else None
    except (AttributeError, TypeError):
        return None


def simplefield_raw(node, xpath, do_strip=True):
    '''Return RAW plain text at xpath under node (itertext only, no cleanstr), or None if
    missing/empty. The original code bypasses cleanstr in exactly two places: the sense
    definition in senses2tex (`defn = ''.join(definition.itertext()).strip()`) and the
    RelatedForms extraction in relforms2tex (same, without even a .strip()). Both are
    reproduced via this helper so e.g. literal "~" (a genuine dictionary character, not a
    LaTeX artifact) survives in definitions exactly as the original leaves it.'''
    try:
        node_found = node.find(xpath)
        if node_found is None:
            return None
        val = ''.join(node_found.itertext())
        if do_strip:
            val = val.strip()
        return val if val else None
    except (AttributeError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Example:
    id: str
    sense_id: str
    primary_text: Optional[str] = None
    translated_text: Optional[str] = None
    source_ref: Optional[str] = None          # example/@source attribute (corpus text + line code)
    do_not_publish_in: list = field(default_factory=list)  # raw trait values, e.g. "Verbal Dictionary"
    variant_headword: Optional[str] = None    # set only on Entry.inherited_examples: the variant
                                               # entry whose sense this example actually belongs to
                                               # (the example text is spelled per that variant, not
                                               # the base headword -- see Entry.inherited_examples)


@dataclass
class Relation:
    sense_id: str            # referenced sense id
    headword: Optional[str]  # referenced entry headword (resolved), may be None if unresolved


@dataclass
class Sense:
    id: str
    entry_id: str
    pos_raw: Optional[str] = None
    verb_class: Optional[str] = None
    definition: Optional[str] = None
    scientific_name: Optional[str] = None
    cultural_note: Optional[str] = None
    semantic_note: Optional[str] = None
    grammar_note: Optional[str] = None
    sociolinguistic_note: Optional[str] = None
    discourse_note: Optional[str] = None
    source_note: Optional[str] = None         # sense-level note[@type="source"], raw pass-through
    reference_note: Optional[str] = None      # sense-level note[@type="reference"], raw pass-through
    semantic_domains: list = field(default_factory=list)   # semantic-domain-ddp4 trait values, unused by either output today
    relations: dict = field(default_factory=dict)          # relation_type -> list[Relation]
    examples: list = field(default_factory=list)            # list[Example]
    reversal_en: list = field(default_factory=list)         # english reversal gloss strings attached to this sense


@dataclass
class VariantRef:
    entry_id: str
    headword: Optional[str]
    vartype: str


@dataclass
class ComplexFormRef:
    entry_id: str
    headword: Optional[str]
    complex_type: str
    pos_raw: Optional[str] = None       # raw grammatical-info of the referenced entry's first sense
    definition: Optional[str] = None    # first sense's English definition of the referenced entry


@dataclass
class Entry:
    id: str
    guid: Optional[str]
    headword: str
    sortword: str
    firstletter: str
    lexeme_form: Optional[str] = None         # only set when it differs from the headword
    irregular_plural: Optional[str] = None
    irregular_possessed: Optional[str] = None
    irregular_possessed_forms: dict = field(default_factory=dict)   # {'irregthirdposs':[...], 'irregfirstposs':[...]}
    derivational_root: Optional[str] = None
    literal_meaning: Optional[str] = None
    pronunciation: Optional[str] = None
    active_middle_form: Optional[str] = None
    related_forms: list = field(default_factory=list)        # [{'kit':..., 'en':...}]
    impf_rt: Optional[str] = None
    variant_of: Optional[VariantRef] = None
    variants: dict = field(default_factory=dict)             # vartype -> list[str] (this entry's own variant forms, as base)
    complex_form_of: Optional[ComplexFormRef] = None
    complex_forms: list = field(default_factory=list)        # list[ComplexFormRef] (this entry is the base of these)
    senses: list = field(default_factory=list)               # list[Sense]
    inherited_examples: list = field(default_factory=list)   # list[Example]: translated examples that live on a
                                                              # *variant* entry pointing at this one as base. The LaTeX
                                                              # generator surfaces these here (since variant entries
                                                              # otherwise show no examples at all); the Dictionaria
                                                              # generator ignores this field and keeps each example on
                                                              # its actual originating sense. See pipeline/README.md.


@dataclass
class ParsedLift:
    entries: list                 # list[Entry], already filtered (excluded/suffix dropped) and sorted by sortword
    entry_lookup: dict            # entry_id -> Entry (post-filter)
    valid_headwords: set          # set of headwords that exist as real entries (for hyperlinking)
    reversal_en: dict             # gloss -> pos -> list[entry_id], sorted
    warnings: list
    stats: dict

    def to_json_safe(self):
        '''Return a plain-dict version suitable for json.dump / pickling as a checkpoint.'''
        return {
            'entries': [asdict(e) for e in self.entries],
            'reversal_en': self.reversal_en,
            'valid_headwords': sorted(self.valid_headwords),
            'warnings': self.warnings,
            'stats': self.stats,
        }


# ---------------------------------------------------------------------------
# Main parse function
# ---------------------------------------------------------------------------

def parse_lift(path):
    '''Parse a FLEx .lift export at `path` and return a ParsedLift.'''
    warnings = []
    start_time = time.time()

    tree = ET.parse(path)
    root = tree.getroot()
    raw_entries = root.findall('entry')

    # ---- Pass 1: build raw lookups, decide inclusion, compute headwords ----
    entry_lookup_raw = {e.attrib['id']: e for e in raw_entries if 'id' in e.attrib}
    sense_lookup_raw = {}
    for e in raw_entries:
        for s in e.findall('sense'):
            sid = s.attrib.get('id', '')
            if sid:
                sense_lookup_raw[sid] = e

    valid_headwords = {get_headword(e) for e in raw_entries if get_headword(e)}

    kept_raw = []
    for e in raw_entries:
        if is_excluded(e) or is_suffix(e):
            continue
        hw = get_headword(e)
        if not hw:
            eid = e.attrib.get('id', 'unknown')
            warnings.append(f"Skipping entry id='{eid}': empty or invalid headword")
            continue
        kept_raw.append(e)

    # ---- Pass 2: variant / main-word / complex-form / irregular-plural maps ----
    # (ported from ende_process.py's mapping-building loop, operating over ALL
    #  raw entries since a variant may point at a kept entry from anywhere)
    mainwdmap_en = {}      # entry_id (variant) -> VariantRef pointing at its base entry
    variantmap = {}        # base_entry_id -> vartype -> [variant form strings]
    irreg_pl_map = {}
    impf_rt_map = {}       # base_entry_id -> headword of the "imperfect root" variant entry
    complex_map = {}       # base_entry_id -> [ComplexFormRef, ...]
    complex_of_map = {}    # complex_entry_id -> ComplexFormRef pointing at its base entry

    for entry in raw_entries:
        headword = get_headword(entry)
        if not headword:
            continue
        entry_id = entry.attrib.get('id', '')
        relations = entry.findall('relation[@type="_component-lexeme"]')
        for rel in relations:
            refid = rel.attrib.get('ref', '')
            if not refid:
                continue
            base_entry = entry_lookup_raw.get(refid)
            if base_entry is None:
                warnings.append(f"Entry '{headword}': could not find referenced entry {refid}")
                continue
            base_headword = get_headword(base_entry)

            complex_type_node = rel.find('trait[@name="complex-form-type"]')
            if complex_type_node is not None:
                complex_type = complex_type_node.attrib.get('value', 'Complex')
                # pos/definition of THIS (complex-form) entry, for the reverse listing on the base entry
                complex_map.setdefault(refid, []).append(
                    ComplexFormRef(
                        entry_id=entry_id, headword=headword, complex_type=complex_type,
                        pos_raw=get_first_pos(entry) or None,
                        definition=simplefield(entry, 'sense/definition/form[@lang="en"]/text'),
                    )
                )
                # pos/definition of the BASE entry, for complexformof2tex -- first match wins
                # (mirrors the original's `break` after the first matching relation)
                if entry_id not in complex_of_map:
                    complex_of_map[entry_id] = ComplexFormRef(
                        entry_id=refid, headword=base_headword, complex_type=complex_type,
                        pos_raw=get_first_pos(base_entry) or None,
                        definition=simplefield(base_entry, 'sense/definition/form[@lang="en"]/text'),
                    )

            vartype_node = rel.find('trait[@name="variant-type"]')
            if vartype_node is not None:
                try:
                    vartype = vartype_node.attrib['value']
                    parts = vartype.split()
                    parts[0] = parts[0].capitalize()
                    vartype = ' '.join(parts)
                except (AttributeError, KeyError, IndexError):
                    continue
                vartype = VARMAP.get(vartype, vartype)
                if vartype not in ORDER_VARLAB_ENDE:
                    warnings.append(f"Unrecognized variant type '{vartype}' on entry '{headword}'")
                mainwdmap_en[entry_id] = VariantRef(entry_id=refid, headword=base_headword, vartype=vartype)

                if vartype == 'impfrtlab':
                    impf_rt_map[refid] = headword
                    continue
                try:
                    variant_form = entry.find('citation/form[@lang="kit"]/text').text
                except AttributeError:
                    try:
                        variant_form = entry.find('lexical-unit/form[@lang="kit"]/text').text
                    except AttributeError:
                        variant_form = headword
                variantmap.setdefault(refid, {}).setdefault(vartype, []).append(variant_form)

        glosses = entry.findall('sense/gloss[@lang="ga"]/text')
        for ipl in get_irreg_pl(glosses):
            irreg_pl_map[ipl] = headword

    # ---- Pass 3: build english reversal index (before per-entry conversion, as in ende_process.py) ----
    reversal_en = {}
    for entry in raw_entries:
        if is_excluded(entry) or is_suffix(entry):
            continue
        entry_id = entry.attrib.get('id', None)
        if entry_id is None:
            continue
        headword = get_headword(entry)
        if not headword:
            continue
        for sns in entry.findall('sense'):
            ginfo_node = sns.find('grammatical-info')
            if ginfo_node is None:
                continue
            pos = ginfo_node.attrib['value'].strip()
            for revnode in sns.findall('reversal[@type="en"]'):
                try:
                    rev = nodetext(revnode.find('form/text')).strip()
                    if not rev:
                        continue
                except AttributeError:
                    continue
                reversal_en.setdefault(rev, {}).setdefault(pos, []).append(entry_id)
    for rev in reversal_en:
        for pos in reversal_en[rev]:
            reversal_en[rev][pos].sort(
                key=lambda eid: str2sort(get_headword(entry_lookup_raw.get(eid)) or '')
            )

    # ---- Pass 4: build the normalized Entry/Sense/Example objects ----
    entries = []
    for e in kept_raw:
        headword = get_headword(e)
        entry_id = e.attrib.get('id', '')
        letter = firstletter(headword).upper()

        lexeme_form = None
        lex_text = simplefield(e, 'lexical-unit/form[@lang="kit"]/text')
        if lex_text and e.find('citation/form[@lang="kit"]/text') is not None and lex_text != headword:
            lexeme_form = lex_text

        irregular_possessed_forms = {}
        for irform in ('irregthirdposs', 'irregfirstposs'):
            try:
                irregular_possessed_forms[irform] = [v.strip() for v in variantmap[entry_id][irform]]
            except KeyError:
                pass

        related_forms = []
        for suffix in ['', '2', '3', '4', '5']:
            for rf in e.findall(f'field[@type="RelatedForms{suffix}"]'):
                kit_form = simplefield_raw(rf, 'form[@lang="kit"]/text', do_strip=False) or ''
                en_form = simplefield_raw(rf, 'form[@lang="en"]/text', do_strip=False) or ''
                related_forms.append({'kit': kit_form, 'en': en_form})

        variants = {}
        for vartype, forms in variantmap.get(entry_id, {}).items():
            if vartype in ('irregthirdposs', 'irregfirstposs'):
                continue
            variants[vartype] = [v.strip() for v in forms]

        entry_obj = Entry(
            id=entry_id,
            guid=e.attrib.get('guid'),
            headword=headword,
            sortword=str2sort(headword),
            firstletter=letter,
            lexeme_form=lexeme_form,
            irregular_plural=simplefield(e, 'field[@type="Irreg Pl"]/form/text'),
            irregular_possessed=simplefield(e, 'field[@type="Irreg Poss"]/form/text'),
            irregular_possessed_forms=irregular_possessed_forms,
            derivational_root=simplefield(e, 'field[@type="Deriv Root"]/form/text'),
            literal_meaning=simplefield(e, 'field[@type="literal-meaning"]/form[@lang="en"]/text'),
            pronunciation=simplefield(e, 'pronunciation/form/text'),
            active_middle_form=simplefield(e, 'field[@type="activemiddle"]/form/text'),
            related_forms=related_forms,
            impf_rt=impf_rt_map.get(entry_id),
            variant_of=mainwdmap_en.get(entry_id),
            variants=variants,
            complex_form_of=complex_of_map.get(entry_id),
            complex_forms=complex_map.get(entry_id, []),
        )

        for s in e.findall('sense'):
            sense_id = s.attrib.get('id', '')
            ginfo_node = s.find('grammatical-info')
            pos_raw = ginfo_node.attrib['value'].strip() if ginfo_node is not None else None
            verb_class = None
            for trait in s.findall('grammatical-info/trait'):
                if trait.get('name') == 'Verb-infl-class':
                    verb_class = trait.get('value')

            relations = {}
            for rel in s.findall('relation'):
                rel_type = rel.get('type')
                if rel_type not in RELATION_TYPES:
                    continue
                ref_id = rel.get('ref', '')
                if not ref_id:
                    warnings.append(f"Sense '{sense_id}' (entry '{headword}'): empty ref for relation '{rel_type}'")
                    continue
                ref_entry = sense_lookup_raw.get(ref_id)
                ref_headword = get_headword(ref_entry) if ref_entry is not None else None
                if ref_headword is None:
                    warnings.append(f"Sense '{sense_id}' (entry '{headword}'): unresolved relation '{rel_type}' -> sense {ref_id}")
                relations.setdefault(rel_type, []).append(Relation(sense_id=ref_id, headword=ref_headword))

            examples = []
            for i, ex in enumerate(s.findall('example'), 1):
                primary = simplefield(ex, 'form[@lang="kit"]/text')
                translated = simplefield(ex, 'translation[@type="Free translation"]/form[@lang="en"]/text')
                dnp = [t.attrib.get('value') for t in ex.findall('trait[@name="do-not-publish-in"]')]
                examples.append(Example(
                    id=f'{sense_id}-ex{i}',
                    sense_id=sense_id,
                    primary_text=primary,
                    translated_text=translated,
                    source_ref=ex.attrib.get('source'),
                    do_not_publish_in=dnp,
                ))

            reversal_for_sense = []
            for revnode in s.findall('reversal[@type="en"]'):
                rv = simplefield(revnode, 'form/text')
                if rv:
                    reversal_for_sense.append(rv)

            sense_obj = Sense(
                id=sense_id,
                entry_id=entry_id,
                pos_raw=pos_raw,
                verb_class=verb_class,
                definition=simplefield_raw(s, 'definition/form[@lang="en"]/text'),
                scientific_name=simplefield(s, 'field[@type="scientific-name"]/form[@lang="en"]/text'),
                cultural_note=simplefield(s, 'note[@type="anthropology"]/form[@lang="en"]/text'),
                semantic_note=simplefield(s, 'note[@type="semantics"]/form[@lang="en"]/text'),
                grammar_note=simplefield(s, 'note[@type="grammar"]/form[@lang="en"]/text'),
                sociolinguistic_note=simplefield(s, 'note[@type="sociolinguistics"]/form[@lang="en"]/text'),
                discourse_note=simplefield(s, 'note[@type="discourse"]/form[@lang="en"]/text'),
                source_note=simplefield(s, 'note[@type="source"]/form/text'),
                reference_note=simplefield(s, 'note[@type="reference"]/form/text'),
                semantic_domains=[t.attrib.get('value') for t in s.findall('trait[@name="semantic-domain-ddp4"]')],
                relations=relations,
                examples=examples,
                reversal_en=reversal_for_sense,
            )
            entry_obj.senses.append(sense_obj)

        entries.append(entry_obj)

    entries.sort(key=lambda entry: entry.sortword)
    entry_lookup = {e.id: e for e in entries}

    # ---- Pass 5: surface translated examples from variant entries onto their base entry ----
    # A variant-of entry (e.g. a spelling/dialectal/fast-speech variant) shows no senses/examples
    # of its own in the LaTeX output -- so any example recorded only under the variant's sense was
    # previously invisible everywhere except examples.csv. Attach a copy to the base entry's first
    # sense here (tagged with the variant's headword, since the example text is spelled per the
    # variant, not the base) so the LaTeX generator can render it. The variant entry's own Sense
    # objects are left untouched -- Dictionaria's examples.csv keeps the original, precise linkage.
    inherited_count = 0
    for entry in entries:
        if entry.variant_of is None:
            continue
        base = entry_lookup.get(entry.variant_of.entry_id)
        if base is None or not base.senses:
            continue
        for s in entry.senses:
            for ex in s.examples:
                if ex.primary_text and ex.primary_text.strip() and ex.translated_text and ex.translated_text.strip():
                    import copy as _copy
                    moved = _copy.copy(ex)
                    moved.variant_headword = entry.headword
                    base.inherited_examples.append(moved)
                    inherited_count += 1

    stats = {
        'total_raw_entries': len(raw_entries),
        'kept_entries': len(entries),
        'excluded_or_suffix': len(raw_entries) - len(entries) - (len(raw_entries) - len(kept_raw) - (len(raw_entries) - len(kept_raw))),
        'total_senses': sum(len(e.senses) for e in entries),
        'total_examples': sum(len(s.examples) for e in entries for s in e.senses),
        'reversal_entries': len(reversal_en),
        'warning_count': len(warnings),
        'parse_seconds': round(time.time() - start_time, 2),
    }
    # Simpler, unambiguous exclusion count:
    stats['excluded_or_suffix'] = len(raw_entries) - len(kept_raw)
    stats['examples_inherited_from_variants'] = inherited_count

    return ParsedLift(
        entries=entries,
        entry_lookup=entry_lookup,
        valid_headwords=valid_headwords,
        reversal_en=reversal_en,
        warnings=warnings,
        stats=stats,
    )


if __name__ == '__main__':
    import sys
    import json
    infile = sys.argv[1] if len(sys.argv) > 1 else 'ende.lift'
    parsed = parse_lift(infile)
    print(json.dumps(parsed.stats, indent=2))
    if parsed.warnings:
        print(f"\n{len(parsed.warnings)} warnings (showing first 10):")
        for w in parsed.warnings[:10]:
            print(' -', w)
