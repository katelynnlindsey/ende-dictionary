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
    'adjective': 'adj.',
    'adverb': 'adv.',
    'ambitransitive verb': 'a.v.',
    'interjection': 'interj.',
    'intransitive verb': 'i.v.',
    'locative noun': 'loc.n.',
    'locative postposition': 'loc.postp.',
    'noun': 'n.',
    'postposition': 'postp.',
    'proper noun': 'prop.n.',
    'transitive verb': 't.v.',
    'anaphoric pronoun' : 'anaph.pro.',
    'complementizer' : 'comp.',
    'conjunction' : 'conj.',               
    'copular verb' : 'cop.',
    'demonstrative' : 'dem.',
    'determiner' : 'det.',                         
    'ditransitive verb' : 'd.v.',                                                                 
    'interrogative word' : 'interrog.',   
    'locative demonstrative' : 'loc.dem', 
    'locative postposition' : 'loc.postp.',                                         
    'numeral' : 'num.',
    'particle' : 'prtcl.',                                                     
    'pronoun' : 'pro.',
    'pro-clause' : 'procl.',
    'relative pronoun' : 'rel.pro.', 
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

# Ordered list of (single byte) characters in the alphabet.
# Ɨ is a single-byte placeholder for ɨ́, which is a sequence of two characters (vowel+diacritic).
#alphabet = ' øáabcdéefghíiƗɨjklmnóopqrstúuvwxyz'
# AEIOU = aa, ee, ii, oo, uu
alphabet = ' øaäbdDefgiɨklLmnGYoprstTuwyzchjqvx'

# Map characters to position in the alphabet.
amap = {c: alphabet.index(c) for c in alphabet}

def str2alpha(s):
    '''Convert characters in s to conventionalized set of alphabetic characters.
    Diacritics are stripped out and long vowels are replaced by upper case characters.
    All other characters are lower case.
    '''
    # Canonicalize to lower case.
    s = s.strip().lower()
    
    # Remove tex commands.
    s = re.sub(r'\\\w+{([^}]+)}', r'\1', s)

    # Remove punctuation.
    s = s.replace('"', '') \
         .replace('“', '').replace('”', '') \
         .replace('¿', '').replace('?', '')

    # Morpheme markers do not affect sorting. Remove them.
    s = s.replace('=', '').replace('-', '').replace('#', '')

    # Replace diacritic digraphs (i.e. vowel+diacritic combinations) with precomposed characters.
    s = s.replace('á', 'á').replace('é', 'é').replace('í', 'í') \
         .replace('ó', 'ó').replace('ú', 'ú') \
         .replace('à', 'à').replace('è', 'è').replace('ì', 'ì') \
         .replace('ò', 'ò').replace('ù', 'ù').replace('ä','a').replace('~','')\
         .replace('ẽ','e').replace('2','').replace('3','').replace('4','')\
         .replace('5','').replace('6','').replace('7','').replace('8','').replace('9','').replace('1','').replace('0','')

    # Replace digraph sequences with single upper case.
    s = s.replace('ll', 'L').replace('tt', 'T').replace('dd', 'D') \
         .replace('ny', 'Y').replace('ng', 'G')

    # Clean up bad character data.
    s = cleanstr(s)

    return s

def str2sort(s):
    '''Convert characters in s to set of ordered codepoints and return as an ascii string.'''
    
    # Map characters to ordered codepoints.
    s = str2alpha(s)
    sortnum = [amap[c] for c in s]

    # Return as an ascii string.
# TODO: can this be simplified?
    return (bytes(sortnum).decode('ascii')).encode('ascii')

def firstletter(s):
    '''Return first alphabetic letter of s.'''
    #print(str2alpha(s))
    try:
        first = str2alpha(s)[0]   
        if first is not None:
            first = first.replace('A', 'aa').replace('E', 'ee').replace('I', 'ii') \
                 .replace('Ɨ', 'ɨɨ').replace('O', 'oo').replace('U', 'uu')
            return first
        else:
            return''
    except IndexError:
        #print(str2alpha(s))
        return ''
    

def cleanstr(s):
    '''Clean up bad character data in a string and return cleaned string.'''
    # Remove extraneous combining acute accent that follows precomposed character with acute accent.
    for c in 'áéíóú':
        # Replaces b'\xcc\x81' (U+0301).
        s = s.replace(c + '́', c).replace(c.upper() + '́', c.upper())
        # Replaces b'\xc2\x81' (U+0081).
        s = s.replace(c + '\u0081', c).replace(c.upper() + '\u0081', c.upper())
    return s

def cleantex(s):
    '''Clean up a string value for use in latex.'''
    s = cleanstr(s)
    # Replace latex reserved characters.
# TODO: is this necessary?
#    s.replace()
    return s
        
def nodetext(node):
    '''Return all text found in node as a string.'''
    return cleantex(''.join(list(node.itertext())))

def superscriptLH(s):
    '''Replace L/H with tex superscript form.'''
    return s.replace('L', '\\textsuperscript{L}') \
            .replace('H', '\\textsuperscript{H}')

def activemiddle_replace_es(s):
    '''Translate activemiddle field to Spanish.'''
    return s.replace('active', 'activo').replace('middle', 'medio')

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
        # print('WARNING: Could not find part-of-speech (sense/grammatical-info) ' \
        #       'for sense guid {:}'.format(s.attrib['guid'])
        # )
       # print('2')
        ginfo = ''
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
    tex += r'  \pos{' + ginfo + '}'
    return tex

def pos2tex(e, lang="en"):
    tex = ''
    try:
        ginfo = e.find('sense/grammatical-info').attrib['value'].strip()
    except AttributeError:
        # print('WARNING: Could not find part-of-speech (sense/grammatical-info) ' \
        #       'for entry guid {:}'.format(e.attrib['guid'])
        # )
        #print('3')
        ginfo = ''
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
#     return (tex + r'\n  \end{itemize}')
      return ''
def senses2tex(entry, sense_pos, letter):
    
    '''Return senses in latex format.'''
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
    print(tex)
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
            definitions = s.findall('definition/form[@lang="eu"]/text')
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
            tex += '\n    \\relformiqu{' + forms['kit'] + '}'
            tex += '\n    \\relformen{' + forms[lang] + '}'
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
            tex += '\n    \\relformiqu{' + forms['kit'] + '}'
            tex += '\n    \\relformpos{' + forms['POS'] + '}'
            tex += '\n    \\relformeu{' + forms['eu'] + '}'
            if forms['root'] != '':
                tex += '\n    \\relformiqurt{' + superscriptLH(forms['root']) + '}'
            tex += '}'
            add_wc(forms['eu'], letter)
    return tex

def examples2tex(sense, lang="en"):
    '''Returns examples in latex format.'''
    tex = ''
    examples = sense.findall('example')
    for ex in examples:
        tex += '    \\example{'
        tex += '\n'
        try:
            iquex = simplefield2tex(
                ex, 'exsen', 'form[@lang="kit"]/text',
                level=3, missing_ok=False, empty_ok=False
            )
        except:
            iquex=''
           # iquex = '\n      \\exsen{MISSING}'
        tex += iquex
        try:
            enex = simplefield2tex(
                ex,
                'extran',
                f'translation[@type="Free translation"]/form[@lang="{lang}"]/text',
                level=3, missing_ok=False, empty_ok=False
            )
        except AttributeError:
            enex=''
           # enex = '\n      \\extran{MISSING}'
        tex += enex
        tex += '}'
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

def entry2dict_de(entry, variantmap, mainwdmap, irreg_pl_map):
    '''
    Return contents of <entry> node as a dict with useful values
    for diccionario escolar.replace
    '''
    headword = get_headword(entry)
    tex = r'\entry{' + headword + '}{'
    tex += r'\n\headword{' + headword + '}'
    tex += pos2tex(entry, lang='kit')
    glosses = entry.findall('sense/gloss[@lang="ga"]/text')
    irreg_pl = get_irreg_pl(glosses)
   # gltex = glosses2tex(glosses)
    try:
        tex += '\n' + r'  \variants{Plural irregular de: ' + irreg_pl_map[headword] + '}'
    except KeyError:
        pass
        try:
            tex += mainwdmap[entry.attrib['id']]
        except KeyError:
            # tex += glosses
            # xpath = 'lexical-unit/form[@lang="kit"]/text'
            # try:
            #    variants = [v.strip() for v in variantmap[entry.attrib['id']] if v.strip() not in irreg_pl]
            #    if len(variants) > 0:
            #        if len(variants) == 1:
            #            tex += r'  \variants{Variante: ' + variants[0] + '}\n'
            #        else:
            #            tex += r'  \variants{Variantes: ' + ', '.join([v for v in variants]) + '}\n'
            # except KeyError:
            #    pass
            try:
                variants = []
                for vartype in variantmap[entry.attrib['id']]:
                    variants += [
                        v.strip() \
                        for v in variantmap[entry.attrib['id']][vartype] \
                        if v.strip() not in irreg_pl
                    ]
                if len(variants) > 0:
                    variants.sort(key=lambda x: str2sort(x))
                    intro = 'Variante'
                    if len(variants) > 1:
                        intro += 's'
                    tex += '\n' + r'  \variants{' + intro + ': ' + ', '.join([v for v in variants]) + '}'
            except KeyError:
                pass
   
    tex += '}'
    try:
        return ({
            'firstletter': firstletter(headword).upper(),
            'headword': headword,
            'sortword': str2sort(headword),
            'tex': tex
        }, None)
    except Exception as e:
        return ({'firstletter': '', 'headword': '', 'sortword': '', 'tex': ''}, e)

def reventry2dict_de(rev, e):
    '''
    Return contents of <entry> node as a dict with useful values
    for diccionario escolar.
    '''
    return reventry2dict_acad(rev, e)

#    # TODO: check that there is only one reversal per <entry>
#    rev = nodetext(entry.find('sense/reversal[@type="es"]/form/text'))
#
#    if is_excluded(entry) or is_suffix(e):
#        return ({'firstletter': '', 'headword': '', 'sortword': '', 'tex': ''}, 'EXCLUDE')
#    
#    if '\sci' in rev:
#        return ({'firstletter': '', 'headword': '', 'sortword': '', 'tex': ''}, 'SCI')
#    tex = r'\reventry{' + rev + '}{'
#    tex += r'\headword{' + rev + '}\n'
#    tex += pos2tex(entry)
#    revheadwd = get_headword(entry)
#    tex += '  \gloss{' + revheadwd + '}\n'
#    tex += '}\n'
#    try:
#        sortword = rev.strip().replace(r'\sci ', '').replace(r'\sp ', '').upper()
#        sortword = sortword \
#            .replace('Á', 'A') \
#            .replace('É', 'E') \
#            .replace('Ó', 'O') \
#            .replace('Ñ', 'N') \
#            .replace('ñ', 'n') \
#            .replace('-', '') \
#            .replace('=', '') \
#            .replace('“', '') \
#            .replace('”', '') \
#            .replace('"', '') \
#            .replace('`', '') \
#            .replace('¡', '') \
#            .replace('{', '') \
#            .replace('}', '')
#        m = re.search('(?P<firstletter>[^\W\d_])', sortword, re.UNICODE)
#        return ({
#            'firstletter': m.groupdict()['firstletter'],
#            'headword': rev,
#            'sortword': sortword,
#            'tex': tex
#        }, None)
#    except Exception as e:
#        return ({'firstletter': '', 'headword': '', 'sortword': '', 'tex': ''}, e)

def entry2dict_acad(entry, variantmap, mainwdmap, irreg_pl_map, impf_rt_map):
    
    '''
    Return contents of <entry> node as a dict with useful values
    for academic dictionary.
    '''
    headword = get_headword(entry)
    letter = firstletter(headword).upper()
    tex = '\n' + r'\entry{' + headword + '}{'
    tex += r'\headword{' + headword + '}'
    tex += lexeme2tex(entry)
    try:
        tex += r'\n  \impfrt{\impfrtlab ' + impf_rt_map[entry.attrib['id']] + '}'
    except KeyError:
        pass
    glosses = entry.findall('sense/gloss[@lang="ga"]/text')
    #irreg_pl = get_irreg_pl(glosses)
    try:
        #tex += '\n' + r'  \variants{\irregpllab \vartext{' + irreg_pl_map[headword] + '}}'
        pass
    #except KeyError:
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
                entry,
                'irregposs',
                'field[@type="Irreg Poss"]/form/text',
                level=1
            )
            for irform in ['irregthirdposs', 'irregfirstposs']:
                try:
                    variants = ', '.join(
                        [
                            v.strip() \
                            for v in variantmap[entry.attrib['id']][irform]
                        ]
                    )
                    tex += ' \\' + irform + '{' + variants + '}'
                except KeyError:
                    pass
            tex += simplefield2tex(
                entry, 'derivroot', 'field[@type="Deriv Root"]/form/text', level=1
            )
            tex += simplefield2tex(
                entry, 'litmean', 'field[@type="literal-meaning"]/form[@lang="en"]/text', level=1, letter=letter
            )
            tex += simplefield2tex(
                entry, 'note', 'note/form[@lang="en"]/text', level=1
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
                print(tex)
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
                    #tex += examples2tex(s)
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
                    variants = [
                        v.strip() \
                        for v in variantmap[entry.attrib['id']][vartype] #\
                        #if v.strip() not in irreg_pl
                    ]
                    if len(variants) > 0:
                        if len(variants) > 1 and vartype in ['freevarlab', 'dialectvarlab']:
                            vartype += 's'
                        tex += '\n' + r'  \variants{' + '\\' + vartype + r' \vartext{' + ', '.join([v for v in variants]) + '}}'
            except KeyError:
                pass
    tex += '}'
    try:
        return ({
            'firstletter': letter,
            'headword': headword,
            'sortword': str2sort(headword),
            'tex': tex
        }, None)
    except Exception as e:
        return ({'firstletter': '', 'headword': '', 'sortword': '', 'tex': ''}, e)

def reventry2dict_acad(rev, e):
    '''
    Return reversals of rev for academic dictionary.
    '''
    tex = ''
    parts_of_speech = list(e.keys())
    parts_of_speech.sort()
    for mypos in parts_of_speech:
        tex += '\n' + r'\reventry{' + rev + '}{'
        tex += '\n' + r'\headword{' + rev + '}'
        try:
            tex += '\n' + r'  \pos{' + posmap_en[mypos] + '}'
        except KeyError:
            tex += '\n' + r'  \pos{' + mypos + '}'
        revheadwd = ', '.join(e[mypos])
        tex += r'\n  \gloss{' + revheadwd + '}'
        tex += '}\n\n'
    sortword = rev.strip().replace(r'\sci ', '').replace(r'\sp ', '').upper()
    sortword = sortword \
        .replace('Á', 'A') \
        .replace('É', 'E') \
        .replace('Í', 'I') \
        .replace('Ó', 'O') \
        .replace('Ú', 'U') \
        .replace('Ñ', 'N') \
        .replace('ñ', 'n') \
        .replace('-', '') \
        .replace('=', '') \
        .replace('“', '') \
        .replace('”', '') \
        .replace('"', '') \
        .replace('`', '') \
        .replace('¡', '') \
        .replace('{', '') \
        .replace('}', '')
    m = re.search(r'(?P<firstletter>[^\W\d_])', sortword, re.UNICODE)
    if m is not None:
        letter = m.groupdict()['firstletter']
    else:
        print(f"Warning: No valid first letter found for reversal '{rev}' (sortword: '{sortword}'). Using fallback '#'.") 
        letter = '#'  # Fallback for numeric or invalid sortwords
    add_wc(rev, letter, rev=True)
    return ({
        'firstletter': letter,
        'headword': rev,
        'sortword': sortword,
        'tex': tex
    }, None)

def entry2dict_acad_es(entry, variantmap, mainwdmap, irreg_pl_map, impf_rt_map):
    '''
    Return contents of <entry> node as a dict with useful values
    for Spanish-language academic dictionary.
    '''
    headword = get_headword(entry)
    letter = firstletter(headword).upper()
    headword = superscriptLH(headword)
    tex = '\n' + r'\entry{' + headword + '}{'
    tex += r'\headword{' + headword + '}'
#!# Commented out for new ordering
#    tex += lexeme2tex(entry)
#    try:
#        tex += '\n  \impfrt{\impfrtlab ' + impf_rt_map[entry.attrib['id']] + '}'
#    except KeyError:
#        pass
#!# End commented out for new ordering
    glosses = entry.findall('sense/gloss[@lang="ga"]/text')
    try:
        #tex += '\n' + r'  \variants{\irregpllab \vartext{' + irreg_pl_map[headword] + '}}'
        pass
    #except KeyError:
    finally:
        isvariant = False
        try:
            tex += mainwdmap[entry.attrib['id']]
            isvariant = True
        except KeyError:
            pass
        finally:
            if isvariant is False:
                first_pos = get_first_pos(entry)
                if get_first_pos(entry) == 'derivational verb root':
                    # Suppress these
                    return ({}, 'pass')
                elif first_pos in verb_pos:
                    tex += senses2tex_es(entry, sense_pos=True, letter=letter)
                else:
                    tex += pos2tex(entry, lang="es")
                    tex += senses2tex_es(entry, sense_pos=False, letter=letter)
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
                    tex += examples2tex(s)
            tex += ' ~$\\parallel$~ '
            #!# New additions
            #tex += simplefield2tex(
            #    entry, 'pronnote', 'pronunciation/form/text', level=1
            #)
            efields = [
                ('litmean', 'literal-meaning', 'eu'),
                ('note', 'note/form[@lang="eu"]/text', ''),
                ('anthnoteentry', 'Entry Anthro', 'eu'),
                ('semnoteentry', 'Entry Semantics', 'eu'),
                ('gramnoteentry', 'Entry Grammar', 'eu'),
                ('socionoteentry', 'Entry Socioling', 'eu'),
                ('lexeme', '', ''),
                ('derivroot', 'Deriv Root', ''),
                ('irregpl', 'Irreg Pl', ''),
                ('irregposs', 'Irreg Poss', ''),
                ('irregposspl', 'Irreg Poss Pl', 'kit'),
                ('irregfirstposs', '', ''),
                ('irregthirdposs', '', ''),
                ('altpronuncnote', 'Alternate Pronunciation', 'eu'),
                ('altpronunc', 'Alternate Pronunciation', 'kit'),
            ]
            for tfield, ident, lg in efields:
                if tfield == 'lexeme':
                    tex += lexeme2tex(entry, do_superscriptLH=True)
                    continue
                elif tfield in ('irregfirstposs', 'irregthirdposs'):
                    try:
                        irp = ', '.join(
                            [
                                v.strip() \
                                for v in variantmap[entry.attrib['id']][tfield]
                            ]
                        )
                        tex += ' \\' + tfield + '{' + irp + '}'
                    except KeyError:
                        pass
                else:
                    lgattr = '' if lg == '' else f'[@lang="{lg}"]'
                    xpath = ident if '/' in ident else f'field[@type="{ident}"]/form{lgattr}/text'
                    ssLH = True if tfield in ('derivroot', 'altpronunc') else False
                    tex += simplefield2tex(entry, tfield, xpath, level=1, do_superscriptLH=ssLH)
            #!# End new additions
            for vartype in order_varlab_acad_es:
                try:
                    vstr = [
                        v.strip() \
                        for v in variantmap[entry.attrib['id']][vartype]
                    ]
                    if len(vstr) > 0:
                        if len(vstr) > 1 and vartype in ['freevarlab', 'dialectvarlab']:
                            vartype += 's'
                        tex += '\n' + r'  \variants{' + '\\' + vartype + r' \vartext{' + ', '.join([v for v in vstr]) + '}}'
                except KeyError:
                    pass
            tex += simplefield2tex(
                entry,
                'activemiddle',
                'field[@type="activemiddle"]/form/text',
                level=1,
                activemiddle_es=True
            )
            tex += relforms2tex_es(entry, letter)
    tex += '}'
    try:
        return ({
            'firstletter': letter,
            'headword': headword,
            'sortword': str2sort(headword),
            'tex': tex
        }, None)
    except Exception as e:
        return ({'firstletter': '', 'headword': '', 'sortword': '', 'tex': ''}, e)

def reventry2dict_acad_es(rev, e):
    '''
    Return reversals of rev for Spanish-language academic dictionary.
    '''
    tex = ''
    parts_of_speech = list(e.keys())
    parts_of_speech.sort()
    for mypos in parts_of_speech:
        tex += '\n' + r'\reventry{' + rev + '}{'
        tex += '\n' + r'\headword{' + rev + '}'
        try:
            tex += '\n' + r'  \pos{' + posmap_es[mypos] + '}'
        except KeyError:
            tex += '\n' + r'  \pos{' + mypos + ' (TODO: FIELD NOT MAPPED)}'
        revheadwd = ', '.join(e[mypos])
        tex += r'\n  \gloss{' + revheadwd + '}'
        tex += '}\n\n'

    # Remove tex commands.
    sortword = re.sub(r'\\\w+{([^}]+)}', r'\1', rev.strip()).upper()

    sortword = sortword \
        .replace('Á', 'A') \
        .replace('É', 'E') \
        .replace('Í', 'I') \
        .replace('Ó', 'O') \
        .replace('Ú', 'U') \
        .replace('Ñ', 'N') \
        .replace('ñ', 'n') \
        .replace('-', '') \
        .replace('=', '') \
        .replace('¿', '') \
        .replace('?', '') \
        .replace('“', '') \
        .replace('”', '') \
        .replace('"', '') \
        .replace('`', '') \
        .replace('¡', '') \
        .replace('{', '') \
        .replace('}', '')
    m = re.search(r'(?P<firstletter>[^\W\d_])', sortword, re.UNICODE)
    letter = m.groupdict()['firstletter']
    add_wc(rev, letter, rev=True)
    return ({
        'firstletter': letter,
        'headword': rev,
        'sortword': sortword,
        'tex': tex
    }, None)

