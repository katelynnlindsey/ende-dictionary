import re

# Storage for word counts
wordcounts = { }
revwordcounts = { }

glossmap = {
    'Raíz:': r'\textit{Raíz:}',
    'PL:': r'\textit{Plural:}',
    'Forma poseída:': r'\textit{Forma poseída:}',
    'Variante:': r'\textit{Variante:}',
    'No hay forma plural': r'\textit{No hay forma plural}',
    'Variantes:': r'\textit{Variantes:}'
}

posmap_en = {
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
    'Anaphoric pronoun' : 'anaph.pro.',
    'Complementizer' : 'comp.',
    'Conjunction' : 'conj.',               
    'Demonstrative' : 'dem.',
    'Manner demonstrative' : 'man.dem.',
    'Determiner' : 'det.',                         
    'Ditransitive verb' : 'd.v.',                                                                 
    'Interrogative word' : 'interrog.',   
    'Locative demonstrative' : 'loc.dem.', 
    'Locative postposition' : 'loc.postp.',                                         
    'Numeral' : 'num.',
    'Particle' : 'prtcl.',                                                     
    'Pronoun' : 'pro.',
    'Pro-clause' : 'procl.',
    'Relative pronoun' : 'rel.pro.',
    'Proper noun' : 'prop.n.',
    'Pronominal enclitic' : 'pro.enc.',
    'Modifier' : 'mod.',
    'Verb' : 'v.',
    'Subordinating connective' : 'sub.con.',
    'Clitic':'clt.',
    'Nominal enclitic':'nom.clt.',
    'Copular verb':'cop.',
    'Interrogative pronoun':'int.pro.',
    'Manner adverb':'man.adv.',
    'Discourse particle':'disc.prtcl.',
    'Auxiliary verb':'aux.',
    'Quantifier':'quant.',
    'Intransitive coverb':'cov.',
    'Transitive coverb':'cov.',
    'Personal pronoun':'pro.',
    'Color term':'col.',
    'Adverbial demonstrative':'adv.dem.',
    'Nominal demonstrative':'nom.dem.',
    'Transitive/Intransitive coverb':'cov.',
    'Transitive compound verb':'comp.v.',
    'Intransitive compound verb':'comp.v.',
}

verb_pos = [
    'verb',
    'ambitransitive verb',
    'copular verb',
    'ditransitive verb',
    'existential verb',
    'infinitive verb',
    'intransitive verb',
    'transitive verb'
]

order_varlab_ende = [
    'Spellingvariant',
    'FastSpeechvariant',
    'Inflectedform',
    'Unspecifiedvariant',
    'Dialectalvariant',
    'Derivedvariant',
    'Infinitivalreduplicant',
    'Pluralreduplicant',
    'BabyTalkvariant',
    'Derivationalreduplicant',
    'Freevariant'
]

# Ordered list of characters and digraphs in the alphabet
alphabet = ['a', 'ä', 'b', 'd', 'dd', 'e', 'f', 'g', 'i', 'ɨ', 'k', 'l', 'll', 'm', 'n', 'ng', 'ny', 'o', 'p', 'r', 's', 't', 'tt', 'u', 'w', 'y', 'z', 'c', 'h', 'j', 'q', 'v', 'x']

# Map characters and digraphs to their position in the alphabet
amap = {c: i for i, c in enumerate(alphabet)}

def str2alpha(s):
    '''Convert characters in s to a list of alphabetic characters and digraphs.
    Diacritics are preserved for ä, and digraphs are treated as single units.
    All other characters are lower case.
    '''
    # Canonicalize to lower case
    s = s.strip().lower()
    
    # Remove tex commands
    s = re.sub(r'\\\w+{([^}]+)}', r'\1', s)

    # Remove punctuation
    s = s.replace('"', '') \
         .replace('“', '').replace('”', '') \
         .replace('¿', '').replace('?', '')

    # Morpheme markers do not affect sorting
    s = s.replace('=', '').replace('-', '').replace('#', '')

    # Clean up bad character data
    s = cleanstr(s)

    # Process digraphs and return as list
    result = []
    i = 0
    while i < len(s):
        # Check for digraphs first
        if i + 1 < len(s) and s[i:i+2] in ['dd', 'll', 'ng', 'ny', 'tt']:
            result.append(s[i:i+2])
            i += 2
        else:
            result.append(s[i])
            i += 1
    return result

def str2sort(s):
    '''Convert characters in s to a sequence of ordered codepoints and return as a string.'''
    # Convert to list of characters/digraphs
    chars = str2alpha(s)
    # Map to alphabet indices, ignoring unmapped characters
    sortnum = [amap[c] for c in chars if c in amap]
    # Return as a string of ASCII bytes
    return ''.join(chr(n) for n in sortnum)

def firstletter(s):
    '''Return first alphabetic letter or digraph of s for chapter grouping.'''
    try:
        chars = str2alpha(s)
        if not chars:
            return ''
        first = chars[0]
        # Map to display form (e.g., for chapter headings)
        return first
    except IndexError:
        return ''

def cleanstr(s):
    '''Clean up bad character data in a string and return cleaned string.'''
    # Remove extraneous combining acute accent after precomposed characters
    for c in 'áéíóú':
        s = s.replace(c + '́', c).replace(c.upper() + '́', c.upper())
        s = s.replace(c + '\u0081', c).replace(c.upper() + '\u0081', c.upper())
    # Remove irrelevant diacritics and numeric characters
    s = s.replace('~', '').replace('ẽ', 'e') \
         .replace('0', '').replace('1', '').replace('2', '').replace('3', '') \
         .replace('4', '').replace('5', '').replace('6', '').replace('7', '') \
         .replace('8', '').replace('9', '')
    return s

def cleantex(s):
    '''Clean up a string value for use in latex.'''
    s = cleanstr(s)
    return s
        
def nodetext(node):
    '''Return all text found in node as a string.'''
    return cleantex(''.join(list(node.itertext())))

def get_headword(entry):
    '''Return an entry's headword. Throw an error if entry's headword fields are missing
    or empty.'''
    try:
        hdwd = nodetext(entry.find('citation/form[@lang="kit"]/text')).strip()
        assert(hdwd is not None)
    except:
        hdwd = nodetext(entry.find('lexical-unit/form[@lang="kit"]/text')).strip()
        assert(hdwd is not None)
    return hdwd

def add_wc(s, letter, rev=False):
    '''Add wordcount in `s` to chapter total in `wordcounts` global variable.'''
    #if letter is None:
    #    print(f'{s} has no letter')
    s = re.sub(r'{\\(sp|iqt) [^}]*}', '', s)  # Remove \sp|\iqt text
    words = [w for w in s.split() if re.search(r'\w', w) is not None]
    wc = len(words)
    if rev is False:
        try:
            wordcounts[letter] += wc
        except KeyError:
            wordcounts[letter] = wc
    else:
        try:
            revwordcounts[letter] += wc
        except KeyError:
            revwordcounts[letter] = wc

def reset_wordcounts():
    '''Reset the global `wordcounts` variable.'''
    wordcounts = {}

def reset_revwordcounts():
    '''Reset the global `revwordcounts` variable.'''
    revwordcounts = {}

def is_excluded(entry):
    '''Return True if entry is annotated for exclusion.'''
    is_exc = False
    try:
        ehist = ''.join(
            entry.find('field[@type="Entry History"]/form[@lang="es"]/text').itertext()
        )
        if ehist.find('EXCLUDE') >= 0:
            is_exc = True
    except AttributeError:  # No "Entry History" node.
        pass
    return is_exc

def is_suffix(entry):
    '''Return True if entry type is suffix.'''
    return entry.find('trait[@name="morph-type"][@value="suffix"]') is not None

def lexeme2tex(entry, do_superscriptLH=False):
    '''Return the formatted Lexeme Form if the Lexeme Form is not also the
    headword (i.e. if the Citation Form exists and is used as the headword.'''
    tex = ''
    if entry.find('citation/form[@lang="kit"]/text') is not None:
        try:
            tex = simplefield2tex(
                entry, 'lexeme', 'lexical-unit/form[@lang="kit"]/text', level=1,
                do_superscriptLH=do_superscriptLH
            )

        except:
            pass
    return tex

# This function added later for sense-specific POS for verbs.
def get_first_pos(e):
    '''Get the part of speech of the first sense in an entry.'''
    try:
        return e.find('sense/grammatical-info').attrib['value'].strip()
    except AttributeError:
        # print('WARNING: Could not find part-of-speech (sense/grammatical-info) ' \
        #       'for entry guid {:}'.format(e.attrib['guid'])
        # )
        #print('1')
        return ''

# This function added later for sense-specific POS for verbs.
def sense_pos2tex(s, lang="en"):
    tex = ''
    try:
        ginfo = s.find('grammatical-info').attrib['value'].strip()
    except AttributeError:
        ginfo = ''
    # Check for Verb-infl-class trait
    verb_class = ''
    for trait in s.findall('grammatical-info/trait'):
        if trait.get('name') == 'Verb-infl-class':
            verb_class = trait.get('value', '')
    # Special handling for Intransitive or Transitive verb with Verb-infl-class
    if ginfo in ['Intransitive verb', 'Transitive verb'] and verb_class:
        tex += r'  \pos{v. ' + verb_class + '}'
    else:
        if lang == "es":
            try:
                ginfo = posmap_es[ginfo]
            except (KeyError, AttributeError):
                pass
        elif lang == "en":
            try:
                ginfo = posmap_en[ginfo]
            except (KeyError, AttributeError):
                pass
        tex += '\n' + r'  \pos{' + ginfo + '}'
    return tex

def pos2tex(e, lang="en"):
    tex = ''
    try:
        ginfo = e.find('sense/grammatical-info').attrib['value'].strip()
    except AttributeError:
        ginfo = ''
    # Check for Verb-infl-class trait
    verb_class = ''
    for trait in e.findall('sense/grammatical-info/trait'):
        if trait.get('name') == 'Verb-infl-class':
            verb_class = trait.get('value', '')
    # Special handling for Intransitive or Transitive verb with Verb-infl-class
    if ginfo in ['Intransitive verb', 'Transitive verb'] and verb_class:
        tex += r'  \pos{v. ' + verb_class + '}'
    else:
        if lang == "es":
            try:
                ginfo = posmap_es[ginfo]
            except (KeyError, AttributeError):
                pass
        elif lang == "en":
            try:
                ginfo = posmap_en[ginfo]
            except (KeyError, AttributeError):
                pass
        tex += '\n' + r'  \pos{' + ginfo + '}'
    return tex

def get_irreg_pl(glosses):
    irreg_pl = []
    for gloss in glosses:
        try:
            irreg_pl += [g.strip() for g in nodetext(gloss).split('PL:')[1].split(',')]
        except IndexError:
            pass
    return irreg_pl
    
def glosses2tex(glosses):
#     tex = 'n  \\begin{itemize}[leftmargin=3.5em]'
#     for idx, gloss in enumerate(glosses):
#         gloss = nodetext(gloss)
#         for orig, repl in glossmap.items():
#             gloss = gloss.replace(orig, repl)
#         # TODO: doesn't seem to be necessary to check length anymore
#         if len(glosses) > 1:
# #            tex += r'  \item{\gloss{' + str(idx+1) + '. ' + nodetext(gloss) + '}}\n'
#             tex += '\n' + r'    \item{\gloss{' + gloss + '}}'
#         else:
#             tex += '\n' + r'    \item{\gloss{' + gloss + '}}'
#     return (tex + '\n' + r' \end{itemize}')
      return ''

def senses2tex(entry, sense_pos, letter):
    tex = ''
    senses = entry.findall('sense')
    for idx, s in enumerate(senses):
        tex += '  \\sense{'
        if len(senses) > 1:
            tex += r'\textbf{' + '{:d}'.format(idx + 1) + '.} '
        tex += '\n'
        if sense_pos is True:
            tex += sense_pos2tex(s)
        try:
            definitions = s.findall('definition/form[@lang="en"]/text')
            for definition in definitions:                
                defn =  ''.join(definition.itertext()).strip()
                tex += '    \\definition{' + defn + '}'
                add_wc(defn, letter)
        except (AttributeError, TypeError):
            pass
        tex += simplefield2tex(
            s,
            'scientificname',
            'field[@type="scientific-name"]/form[@lang="en"]/text',
            level=2
        )
        tex += simplefield2tex(
            s,
            'anthronote',
            'note[@type="anthropology"]/form[@lang="en"]/text',
            level=2, letter=letter
        )
        tex += simplefield2tex(
            s,
            'semnote',
            'note[@type="semantics"]/form[@lang="en"]/text',
            level=2, letter=letter
        )
        tex += simplefield2tex(
            s,
            'grammarnote',
            'note[@type="grammar"]/form[@lang="en"]/text',
            level=2, letter=letter
        )
        tex += simplefield2tex(
            s,
            'socionote',
            'note[@type="sociolinguistics"]/form[@lang="en"]/text',
            level=2, letter=letter
        )
        tex += simplefield2tex(
            s,
            'discoursenote',
            'note[@type="discourse"]/form[@lang="en"]/text',
            level=2, letter=letter
        )
        tex += examples2tex(s)
        tex += '}'
    #print(tex)
    return tex

def senses2tex_es(entry, sense_pos, letter):
    '''Return Spanish language senses in latex format.'''
    tex = ''
    senses = entry.findall('sense')
    for idx, s in enumerate(senses):
        tex += '  \\sense{'
        if len(senses) > 1:
            tex += r'\textbf{' + '{:d}'.format(idx + 1) + '.} '
        tex += '\n'
        if sense_pos is True:
            tex += sense_pos2tex(s, lang="es")
        try:
            definitions = s.findall('definition/form[@lang="kit"]/text')
            for definition in definitions:
                defn =  ''.join(definition.itertext()).strip()
                tex += '    \\definition{' + defn + '}'
                add_wc(defn, letter)  # Add wordcounts
        except (AttributeError, TypeError):
            pass
        tex += simplefield2tex(
            s,
            'scientificname',
            'field[@type="scientific-name"]/form[@lang="en"]/text',
            level=2
        )
        #The note entry is now added after the literal meaning.
        note = simplefield2tex(
           entry,
           'note',
           'note/form[@lang="en"]/text',
           level=2
        )
        # if note != '' and idx >= 2:
        #    print(
        #        'WARNING: entry for {:}) has multiple <senses> and a single <note>'.format(
        #            get_headword(entry)
        #        )
        #    )
        tex += note
        tex += simplefield2tex(
            s,
            'anthronote',
            'note[@type="anthropology"]/form[@lang="eu"]/text',
            level=2, letter=letter
        )
        tex += simplefield2tex(
            s,
            'semnote',
            'note[@type="semantics"]/form[@lang="eu"]/text',
            level=2, letter=letter
        )
        tex += simplefield2tex(
            s,
            'grammarnote',
            'note[@type="grammar"]/form[@lang="eu"]/text',
            level=2, letter=letter
        )
        tex += simplefield2tex(
            s,
            'posspref',
            f'field[@type="Poss Pref"]/form[@lang="eu"]/text',
            level=2, letter=letter
        )
        tex += simplefield2tex(
            s,
            'socionote',
            'note[@type="sociolinguistics"]/form[@lang="eu"]/text',
            level=2, letter=letter
        )
        tex += simplefield2tex(
            s,
            'discoursenote',
            'note[@type="discourse"]/form[@lang="eu"]/text',
            level=2, letter=letter
        )
        tex += examples2tex(s, lang="es")
        tex += '}'
    return tex

def relforms2tex(entry, letter, lang="en"):
    '''Returns related forms in latex format.'''
    tex = ''
    for suffix in ['', '2', '3', '4', '5']:
        xpath = 'field[@type="RelatedForms{:}"]'.format(suffix)
        relforms = entry.findall(xpath)
        for idx, rf in enumerate(relforms):
            forms = {}
            for l in ('kit', lang):
                try:
                    forms[l] = ''.join(rf.find('form[@lang="' + l + '"]/text').itertext())
                except AttributeError:
                    forms[l] = '' #MISSING
            tex += '  \\relforms{'
            if len(relforms) > 1:
                tex += '{:d}. '.format(idx + 1)
#            tex += '\n'
            tex += '\n' + r'\\relformiqu{' + forms['kit'] + '}'
            tex += '\n' + r'\\relformen{' + forms[lang] + '}'
            tex += '}'
            add_wc(forms[lang], letter)
    return tex

def relforms2tex_es(entry, letter):
    '''Returns related forms in latex format for Academic Spanish dictionary.'''
    tex = ''
    for suffix in ['', '2', '3', '4', '5']:
        n = '1' if suffix == '' else suffix
        xpath = f'field[@type="RelatedForms{suffix}"]'
        relforms = entry.findall(xpath)
        # Note that each RelatedFormsN field only contains one related form (I think),
        # but we loop just in case.
        for idx, rf in enumerate(relforms):
            forms = {}
            for l in ('kit', 'eu'):
                try:
                    forms[l] = ''.join(rf.find(f'form[@lang="{l}"]/text').itertext())
                except AttributeError:
                    forms[l] = '' #MISSING
            # Note that this loop is not correctly placed here if there is actually
            # more than one related form inside a singled RelatedFormsN field.
            for tfield, ident, lg in [('kit', 'root', 'kit'), ('pos', 'POS', 'en')]:
                rfxpath = f'field[@type="RelForm {n} {ident}"]/form[@lang="{lg}"]/text'
                try:
                    forms[ident] = ''.join(entry.find(rfxpath).itertext())
                except AttributeError:
                    forms[ident] = ''
            tex += '  \\relforms{'
            if len(relforms) > 1:
                tex += '{:d}. '.format(idx + 1)
            tex += '\n' + r'\\relformiqu{' + forms['kit'] + '}'
            tex += '\n' + r'\\relformpos{' + forms['POS'] + '}'
            tex += '\n' + r'\\relformeu{' + forms['eu'] + '}'
            if forms['root'] != '':
                tex += '\n' + r'\\relformiqurt{' + superscriptLH(forms['root']) + '}'
            tex += '}'
            add_wc(forms['eu'], letter)
    return tex

def examples2tex(sense, lang="en"):
    '''Returns examples in latex format, skipping empty examples or translations.'''
    tex = ''
    examples = sense.findall('example')
    for ex in examples:
        try:
            iquex = simplefield2tex(
                ex, 'exsen', 'form[@lang="kit"]/text',
                level=3, missing_ok=False, empty_ok=False
            )
            enex = simplefield2tex(
                ex,
                'extran',
                f'translation[@type="Free translation"]/form[@lang="{lang}"]/text',
                level=3, missing_ok=False, empty_ok=False
            )
            # Only include example if both iquex and enex are non-empty
            if iquex.strip() and enex.strip():
                tex += '    \\example{'
                tex += '\n'
                tex += iquex
                tex += enex
                tex += '}'
        except (AttributeError, AssertionError):
            # Skip examples with missing or empty fields
            pass
    return tex


def simplefield2tex(node, texfld, xpath, level=1, missing_ok=True, empty_ok=True, letter=None, do_superscriptLH=False, activemiddle_es=False):
    '''Return a simple field from a node as a latex command.'''
    tex = ''
    val = None
    try:
        val = nodetext(node.find(xpath))
        assert(val is not None)
        if do_superscriptLH:
            val = superscriptLH(val)
        if activemiddle_es:
            val = activemiddle_replace_es(val)
        tex += '  ' * level + '\\' + texfld + '{' + val.strip() + '}'
        if texfld in ('litmean', 'anthronote', 'grammarnote', 'semnote', 'socionote', 'discoursenote'):
            add_wc(val.strip(), letter)
    except AttributeError as e:
        if missing_ok is True:
            pass
        else:
            raise e
    except AssertionError as e:
        if empty_ok is True:
            pass
        else:
            raise e
    return tex

def entry2pglex(e):
    ginfo = e.find('sense/grammatical-info').attrib['value'].strip()
    try:
        ginfo = posmap[ginfo]
    except (KeyError, AttributeError):
        pass
    d = {
        'id': e.attrib['guid'],
        'lex': get_headword(e),
        'pos': ginfo,
        'defn': [nodetext(g) for g in e.findall('sense/gloss[@lang="ga"]/text')],
    }
    try:
        d['variants'] = variantmap[e.attrib['id']]
    except KeyError:
        pass
    return json.dumps(d)

def sanitize_latex(s):
    '''
    Sanitize a string for use in LaTeX commands like hyperlink and hypertarget.
    Escapes special LaTeX characters and ensures proper encoding.
    '''
    if not s:
        return s
    # Escape LaTeX special characters
    s = (s.replace('\\', r'\textbackslash{}')
          .replace('{', r'\{')
          .replace('}', r'\}')
          .replace('#', r'\#')
          .replace('$', r'\$')
          .replace('%', r'\%')
          .replace('&', r'\&')
          .replace('_', r'\_')
          .replace('~', r'\textasciitilde{}')
          .replace('^', r'\textasciicircum{}'))
    return s

def entry2dict_acad(entry, variantmap, mainwdmap, irreg_pl_map, impf_rt_map, valid_headwords):
    '''
    Return contents of <entry> node as a dict with useful values for academic dictionary.
    Adds hypertarget for headword and hyperlinks for variants that match headwords.
    valid_headwords: set of headwords from LIFT file, used to check valid hyperlinks.
    '''
    headword = get_headword(entry)
    letter = firstletter(headword).upper()
    sanitized_headword = sanitize_latex(headword)
    tex = '\n' + r'\entry{' + sanitized_headword + r'}{'
    tex += r'\hypertarget{' + sanitized_headword + r'}{}'
    tex += r'\headword{' + sanitized_headword + r'}'
    tex += lexeme2tex(entry)
    try:
        tex += '\n' + r'\impfrt{\impfrtlab ' + sanitize_latex(impf_rt_map[entry.attrib['id']]) + r'}'
    except KeyError:
        pass
    glosses = entry.findall('sense/gloss[@lang="ga"]/text')
    try:
        pass
    finally:
        isvariant = False
        try:
            tex += mainwdmap[entry.attrib['id']]
            isvariant = True
        except KeyError:
            pass
        finally:
            tex += simplefield2tex(
                entry, 'irregpl', 'field[@type="Irreg Pl"]/form/text', level=1
            )
            tex += simplefield2tex(
                entry, 'irregposs', 'field[@type="Irreg Poss"]/form/text', level=1
            )
            for irform in ['irregthirdposs', 'irregfirstposs']:
                try:
                    variants = ', '.join(
                        [sanitize_latex(v.strip()) for v in variantmap[entry.attrib['id']][irform]]
                    )
                    tex += '\n' + r'\\' + irform + r'{' + variants + r'}'
                except KeyError:
                    pass
            tex += simplefield2tex(
                entry, 'derivroot', 'field[@type="Deriv Root"]/form/text', level=1
            )
            tex += simplefield2tex(
                entry, 'litmean', 'field[@type="literal-meaning"]/form[@lang="en"]/text', level=1, letter=letter
            )
            tex += simplefield2tex(
                entry, 'pronnote', 'pronunciation/form/text', level=1
            )
            if isvariant is False:
                if get_first_pos(entry) in verb_pos:
                    tex += senses2tex(entry, sense_pos=True, letter=letter)
                else:
                    tex += pos2tex(entry)
                    tex += senses2tex(entry, sense_pos=False, letter=letter)
            else:
                s = entry.find('sense')
                if s is not None:
                    tex += simplefield2tex(
                        s,
                        'scientificname',
                        'field[@type="scientific-name"]/form[@lang="en"]/text',
                        level=2
                    )
                    tex += simplefield2tex(
                        s,
                        'anthronote',
                        'note[@type="anthropology"]/form[@lang="en"]/text',
                        level=2, letter=letter
                    )
                    tex += simplefield2tex(
                        s,
                        'semnote',
                        'note[@type="semantics"]/form[@lang="en"]/text',
                        level=2, letter=letter
                    )
                    tex += simplefield2tex(
                        s,
                        'grammarnote',
                        'note[@type="grammar"]/form[@lang="en"]/text',
                        level=2, letter=letter
                    )
                    tex += simplefield2tex(
                        s,
                        'socionote',
                        'note[@type="sociolinguistics"]/form[@lang="en"]/text',
                        level=2, letter=letter
                    )
                    tex += simplefield2tex(
                        s,
                        'discoursenote',
                        'note[@type="discourse"]/form[@lang="en"]/text',
                        level=2, letter=letter
                    )
            tex += simplefield2tex(
                entry,
                'activemiddle',
                'field[@type="activemiddle"]/form/text',
                level=1
            )
            tex += relforms2tex(entry, letter)
            try:
                for vartype in variantmap[entry.attrib['id']]:
                    if vartype in ['irregthirdposs', 'irregfirstposs', 'irregpllab']:
                        continue
                    variants = [v.strip() for v in variantmap[entry.attrib['id']][vartype]]
                    if len(variants) > 0:
                        if len(variants) > 1 and vartype in ['freevarlab', 'dialectvarlab']:
                            vartype += 's'
                        linked_variants = [
                            r'\hyperlink{' + sanitize_latex(v) + r'}{' + sanitize_latex(v) + r'}' if v in valid_headwords else sanitize_latex(v)
                            for v in variants
                        ]
                        tex += '\n' + r'\variants{' + '\\' + vartype + r' \vartext{' + ', '.join(linked_variants) + r'}}'
            except KeyError:
                pass
    tex += r'}'
    try:
        return ({
            'firstletter': letter,
            'headword': headword,
            'sortword': str2sort(headword),
            'tex': tex
        }, None)
    except Exception as e:
        return ({'firstletter': '', 'headword': '', 'sortword': '', 'tex': ''}, e)

def reventry2dict_acad(rev, e, entry_lookup):
    '''
    Return contents of reversal entry as a dict with useful values for academic dictionary.
    rev: reversal string (e.g., 'badly').
    e: dictionary of {pos: [entry_ids]} for the reversal.
    entry_lookup: dictionary mapping entry IDs to entry nodes for efficient lookup.
    '''
    tex = '\n' + r'\entry{' + sanitize_latex(rev) + r'}{'
    tex += r'\headword{' + sanitize_latex(rev) + r'}'
    rev_clean = rev.strip().replace(r'\sci ', '').replace(r'\sp ', '')
    letter = firstletter(rev_clean).upper()
    for pos in sorted(e.keys()):
        pos_clean = pos
        if pos in verb_pos:
            if pos == 'v':
                pos_clean = 'v. (V)'
            elif pos == 'v.t':
                pos_clean = 'v.t (V)'
            elif pos == 'v.i':
                pos_clean = 'v.i (V)'
        tex += '\n' + r'\pos{' + pos_clean + r'}'
        tex += '\n' + r'\sense{'
        headwords = []
        for entry_id in e[pos]:
            try:
                # Use entry_lookup to find the entry and verify headword
                entry = entry_lookup.get(entry_id, None)
                if entry is None:
                    print(f"Warning: No entry found for entry ID '{entry_id}' in reversal '{rev}'")
                    continue
                headword = get_headword(entry)
                sanitized_headword = sanitize_latex(headword)
                headwords.append(r'\gloss{\hyperlink{' + sanitized_headword + r'}{' + sanitized_headword + r'}}')
            except Exception as e:
                print(f"Error processing entry ID '{entry_id}' for reversal '{rev}': {e}")
                continue
        if not headwords:
            print(f"Error: No valid headwords for reversal '{rev}' (pos: {pos})")
            return None
        tex += ', '.join(headwords)
        tex += r'}'
    tex += r'}'
    try:
        return ({
            'firstletter': letter,
            'headword': rev,
            'sortword': str2sort(rev_clean),
            'tex': tex
        }, None)
    except Exception as e:
        return ({'firstletter': '', 'headword': '', 'sortword': '', 'tex': ''}, e)