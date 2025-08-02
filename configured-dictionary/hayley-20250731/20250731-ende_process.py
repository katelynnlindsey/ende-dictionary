import xml.etree.ElementTree as ET
import json
import ende_dict as endedict

infile = 'ende.lift'
outfile_acad = 'dictionary_ende.tex' # Configured dictionary (English)
tex_header = 'head.txt'

tree = ET.parse(infile)
root = tree.getroot()

entries = root.findall('entry')
reventries_en = [
    e for e in
    root.findall('entry/sense/reversal[@type="en"]/../..')
]
reversalentries_en = {}
#for e in root.findall('entry/sense/reversal[@type="en"]/../..'):
for e in root.findall('entry'):
    if endedict.is_excluded(e) or endedict.is_suffix(e):
        continue
    endeword = endedict.get_headword(e)
#    pos = e.find('sense/grammatical-info').attrib['value'].strip()
#    is_verb = pos in endedict.verb_pos
#    for revsns in e.findall('sense/reversal[@type="en"]/..'):
    for sns in e.findall('sense'):
        try:
            if(sns.find('grammatical-info') is not None):
                pos = sns.find('grammatical-info').attrib['value'].strip()
            
        except AttributeError:
            
            print(f'Error in sense (id {sns.attrib["id"]}). Could not find grammatical-info (POS).\n')
#            ET.dump(sns)
#        if is_verb is True:
#            pos = revsns.find('grammatical-info').attrib['value'].strip()
        for revnode in sns.findall('reversal[@type="en"]'):
            try:
                rev = endedict.nodetext(revnode.find('form/text')).strip()
            except AttributeError:
                print(f'WARNING: empty reversal for entry {endeword}: {e.attrib["guid"]}')
                continue
            try:
                reversalentries_en[rev]
            except KeyError:
                reversalentries_en[rev] = {}
            try:
                reversalentries_en[rev][pos].append(endeword)
            except KeyError:
                reversalentries_en[rev][pos] = [endeword]
for rev in reversalentries_en.keys():
    for pos in reversalentries_en[rev]:
        try:
            #print(reversalentries_en[rev][pos])
            reversalentries_en[rev][pos].sort(key=lambda s: endedict.str2sort(s))
        except KeyError as e:
            print(f'Found illegal character {e}')
            msg = f'Could not create sort entries for reversals {reversalentries_en[rev][pos]}.\n'
            #print(msg)
pos = {}

varmap = {
    'Spelling Variant':'Spellingvariant',
    'Fast Speech Variant':'FastSpeechvariant',
    'Inflected Form': 'Inflectedform',
    'Unspecified Variant':'Unspecifiedvariant',
    'Dialectal Variant':'Dialectalvariant',
    'Derived Variant':'Derivedvariant',
    'Infinitival reduplicant':'Infinitivalreduplicant',
    'Plural reduplicant':'Pluralreduplicant',
    'Baby Talk Variant':'BabyTalkvariant',
    'Derivational reduplicant':'Derivationalreduplicant',
    'Free Variant':'Freevariant'
}
#    'Free variant(s)': 'freevarlabs',
#    'Dialectal variant(s)': 'dialectvarlabs',

variantmap = {}
mainwdmap_en = {}
irreg_pl_map = {}
impf_rt_map = {}
missingvariants = {}
for entry in entries:
    relations = entry.findall('relation[@type="_component-lexeme"]')
    for rel in relations:
        refid = rel.attrib['ref']
        if refid == '':
            continue
        try:
            mainwd = endedict.get_headword(root.find('entry[@id="{:}"]'.format(refid)))
        except AttributeError:
            print('Could not find entry {:}'.format(refid))
            continue
        # Check if variant-type trait exists before accessing it
        vartype_node = rel.find('trait[@name="variant-type"]')
        if vartype_node is None:
            continue  # Skip silently if no variant type is found
        try:
            vartype = vartype_node.attrib['value']
            parts = vartype.split()
            parts[0] = parts[0].capitalize()  # Capitalize first word only
            vartype = ' '.join(parts)
        except AttributeError:
            continue  # Skip silently if variant type cannot be retrieved
        if vartype in varmap:
            vartype = varmap[vartype]
        if vartype not in endedict.order_varlab_ende:
            missingvariants[vartype] = ''
        mainwdmap_en[entry.attrib['id']] = '\n  \\variantof{' + '\\' + vartype + ' of \\vartext{' + mainwd + '}}'
        if vartype == 'impfrtlab':
            impf_rt_map[refid] = endedict.get_headword(entry)
            continue  # Do not include in variantmap
        try:  # Citation form if it exists, else lexeme form
            variant = entry.find('citation/form[@lang="kit"]/text').text
        except:
            variant = entry.find('lexical-unit/form[@lang="kit"]/text').text
        try:
            variantmap[refid]
        except KeyError:
            variantmap[refid] = {}
        try:
            variantmap[refid][vartype].append(variant)
        except KeyError:
            variantmap[refid][vartype] = [variant]
    glosses = entry.findall('sense/gloss[@lang="ga"]/text')
    for ipl in endedict.get_irreg_pl(glosses):
        irreg_pl_map[ipl] = endedict.get_headword(entry)

# Read the contents of the header .txt file
try:
    with open(tex_header, 'r', encoding='utf-8') as header_file:
        header_content = header_file.read()
except FileNotFoundError:
    print(f"Error: The file {tex_header} was not found.")
    header_content = ""
except Exception as e:
    print(f"Error reading {tex_header}: {e}")
    header_content = ""

# Write both dictionaries to the .tex file
with open(outfile_acad, 'w', encoding='utf-8') as out:
    # Write the header content first
    if header_content:
        out.write(header_content)
        out.write("\n")

    # Regular dictionary
    endedict.reset_wordcounts()  # Reset word counter
    texentries = []
    for e in entries:
        if endedict.is_excluded(e) or endedict.is_suffix(e):
            continue
        d, err = endedict.entry2dict_acad(e, variantmap, mainwdmap_en, irreg_pl_map, impf_rt_map)
        if err is None:
            texentries.append(d)
        else:
            print(f"Error in entry: {err}")
    texentries.sort(key=lambda entry: entry['sortword'])
    out.write(r'\section{Regular Dictionary}' + "\n\n")
    lastchapter = ''
    for d in texentries:
        if d['firstletter'] != lastchapter:
            out.write('\n' + r'\chapter{' + d['firstletter'] + '}\n\n')
            lastchapter = d['firstletter']
        out.write(d['tex'] + '\n')

    # Reversal dictionary
    endedict.reset_revwordcounts()  # Reset word counter
    texentries = []
    for rev, e in reversalentries_en.items():
        result = endedict.reventry2dict_acad(rev, e)
        if result is None:
            # Enhanced debugging to inspect sortword
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
            print(f"Error: reventry2dict_acad returned None for reversal '{rev}' (sortword: '{sortword}', entry: {e})")
            continue
        d, err = result
        if err is None:
            texentries.append(d)
        elif err == 'SCI':
            pass
        else:
            print(f"Error in reversal entry for '{rev}': {err}")
    texentries.sort(key=lambda entry: entry['sortword'])
    out.write('\n' + r'\section{Reversal Dictionary}' + "\n\n")
    lastchapter = ''
    for d in texentries:
        if d['firstletter'] != lastchapter:
            out.write('\n' + r'\chapter{' + d['firstletter'] + '}\n\n')
            lastchapter = d['firstletter']
        out.write(d['tex'] + '\n')

    # Write \end{document} at the end
    out.write("\n" + r'\end{document}' + "\n")