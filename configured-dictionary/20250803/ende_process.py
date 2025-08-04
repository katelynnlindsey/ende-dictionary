import xml.etree.ElementTree as ET
import json
import ende_dict as endedict
import time
import sys

infile = 'ende.lift'
outfile_acad = 'dictionary_ende.tex'
tex_header = 'head.txt'

start_time = time.time()

try:
    print(f"Starting to parse {infile}...")
    tree = ET.parse(infile)
    root = tree.getroot()
    print(f"Parsed {infile} successfully.")
except ET.ParseError as e:
    print(f"Error parsing {infile}: {e}")
    sys.exit(1)
except FileNotFoundError:
    print(f"Error: {infile} not found.")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error reading {infile}: {e}")
    sys.exit(1)

entries = root.findall('entry')
print(f"Found {len(entries)} entries in {infile}.")

# Pre-build entry lookup dictionary
entry_lookup = {e.attrib['id']: e for e in entries if 'id' in e.attrib}
print(f"Built entry lookup for {len(entry_lookup)} entries.")

# Pre-build sense lookup dictionary
sense_lookup = {}
for e in entries:
    entry_id = e.attrib.get('id', '')
    for s in e.findall('sense'):
        sense_id = s.attrib.get('id', '')
        if sense_id:
            sense_lookup[sense_id] = e
print(f"Built sense lookup for {len(sense_lookup)} senses.")

# Cache valid headwords
valid_headwords = {endedict.get_headword(e) for e in entries if endedict.get_headword(e)}
print(f"Cached {len(valid_headwords)} valid headwords.")

reventries_en = [
    e for e in
    root.findall('entry/sense/reversal[@type="en"]/../..')
]
reversalentries_en = {}
print("Building reversal entries...")
for e in root.findall('entry'):
    if endedict.is_excluded(e) or endedict.is_suffix(e):
        continue
    entry_id = e.attrib.get('id', None)
    if entry_id is None:
        print(f"Warning: Entry with guid {e.attrib.get('guid', 'unknown')} has no 'id' attribute")
        continue
    headword = endedict.get_headword(e)
    if not headword:
        print(f"Warning: Skipping entry with id '{entry_id}' due to empty or invalid headword")
        continue
    for sns in e.findall('sense'):
        try:
            if sns.find('grammatical-info') is not None:
                pos = sns.find('grammatical-info').attrib['value'].strip()
            else:
                print(f'Error in sense (id {sns.attrib["id"]}): No grammatical-info (POS)')
                continue
        except AttributeError:
            print(f'Error in sense (id {sns.attrib["id"]}): Could not find grammatical-info (POS)')
            continue
        for revnode in sns.findall('reversal[@type="en"]'):
            try:
                rev = endedict.nodetext(revnode.find('form/text')).strip()
                if not rev:
                    print(f'WARNING: empty reversal for entry ID {entry_id}: guid {e.attrib["guid"]}')
                    continue
            except AttributeError:
                print(f'WARNING: invalid reversal node for entry ID {entry_id}: guid {e.attrib["guid"]}')
                continue
            try:
                reversalentries_en[rev]
            except KeyError:
                reversalentries_en[rev] = {}
            try:
                reversalentries_en[rev][pos].append(entry_id)
            except KeyError:
                reversalentries_en[rev][pos] = [entry_id]
for rev in reversalentries_en.keys():
    for pos in reversalentries_en[rev]:
        try:
            reversalentries_en[rev][pos].sort(key=lambda s: endedict.str2sort(endedict.get_headword(entry_lookup.get(s, None)) or ''))
        except (KeyError, AttributeError) as e:
            print(f'Error sorting reversals for "{rev}" (pos: {pos}): {e}')
            print(f'Could not sort entries: {reversalentries_en[rev][pos]}')
print(f"Built {len(reversalentries_en)} reversal entries.")

varmap = {
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
    'Free Variant': 'Freevariant'
}

variantmap = {}
mainwdmap_en = {}
irreg_pl_map = {}
impf_rt_map = {}
complex_map = {}
missingvariants = {}
print("Building variant, main word, and complex form mappings...")
for entry in entries:
    headword = endedict.get_headword(entry)
    if not headword:
        print(f"Warning: Skipping entry with id '{entry.attrib.get('id', 'unknown')}' due to empty or invalid headword in mappings")
        continue
    relations = entry.findall('relation[@type="_component-lexeme"]')
    for rel in relations:
        refid = rel.attrib.get('ref', '')
        if refid == '':
            continue
        try:
            mainwd = endedict.get_headword(entry_lookup[refid])
            if not mainwd:
                print(f"Warning: Invalid headword for referenced entry ID '{refid}'")
                continue
        except KeyError:
            print(f'Could not find entry {refid}')
            continue
        vartype_node = rel.find('trait[@name="variant-type"]')
        complex_type_node = rel.find('trait[@name="complex-form-type"]')
        entry_id = entry.attrib.get('id', '')
        if complex_type_node is not None:
            complex_type = complex_type_node.attrib.get('value', 'Complex')
            try:
                complex_map[refid].append((entry_id, complex_type))
            except KeyError:
                complex_map[refid] = [(entry_id, complex_type)]
        if vartype_node is not None:
            try:
                vartype = vartype_node.attrib['value']
                parts = vartype.split()
                parts[0] = parts[0].capitalize()
                vartype = ' '.join(parts)
            except AttributeError:
                continue
            if vartype in varmap:
                vartype = varmap[vartype]
            if vartype not in endedict.order_varlab_ende:
                missingvariants[vartype] = ''
            sanitized_mainwd = endedict.sanitize_latex(mainwd)
            if mainwd in valid_headwords:
                mainwdmap_en[entry_id] = '\n' + r'\variantof{' + '\\' + vartype + r' of \vartext{\hyperlink{' + sanitized_mainwd + r'}{' + sanitized_mainwd + r'}}}'
            else:
                mainwdmap_en[entry_id] = '\n' + r'\variantof{' + '\\' + vartype + r' of \vartext{' + sanitized_mainwd + r'}}'
            if vartype == 'impfrtlab':
                impf_rt_map[refid] = endedict.get_headword(entry)
                continue
            try:
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
print(f"Finished building mappings. Complex forms mapped for {len(complex_map)} entries.")

try:
    with open(tex_header, 'r', encoding='utf-8') as header_file:
        header_content = header_file.read()
    print(f"Read {tex_header} successfully.")
except FileNotFoundError:
    print(f"Error: {tex_header} not found.")
    header_content = ""
except Exception as e:
    print(f"Error reading {tex_header}: {e}")
    header_content = ""

with open(outfile_acad, 'w', encoding='utf-8') as out:
    if header_content:
        out.write(header_content)
        out.write("\n")

    endedict.reset_wordcounts()
    texentries = []
    total_entries = len([e for e in entries if not (endedict.is_excluded(e) or endedict.is_suffix(e))])
    print(f"Processing regular dictionary entries ({total_entries} valid entries)...")
    start_regular = time.time()
    for i, e in enumerate(entries, 1):
        if endedict.is_excluded(e) or endedict.is_suffix(e):
            continue
        headword = endedict.get_headword(e)
        if not headword:
            print(f"Warning: Skipping entry with id '{e.attrib.get('id', 'unknown')}' due to empty or invalid headword")
            continue
        percent = (i / len(entries)) * 100
        elapsed = time.time() - start_regular
        eta = (elapsed / i) * (len(entries) - i) if i > 0 else 0
        print(f"Processing entry {i}/{len(entries)} ({percent:.1f}%): {headword}, ETA: {eta:.0f}s")
        d, err = endedict.entry2dict_acad(e, variantmap, mainwdmap_en, irreg_pl_map, impf_rt_map, complex_map, entry_lookup, sense_lookup, valid_headwords)
        if err is None and d['headword']:
            texentries.append(d)
        else:
            print(f"Error in entry {headword or 'unknown'}: {err}")
    texentries.sort(key=lambda entry: entry['sortword'])
    out.write(r'\section{Regular Dictionary}' + "\n\n")
    lastchapter = ''
    for d in texentries:
        if d['firstletter'] != lastchapter:
            out.write('\n' + r'\chapter{' + d['firstletter'] + '}\n\n')
            lastchapter = d['firstletter']
        out.write(d['tex'] + '\n')

    endedict.reset_revwordcounts()
    texentries = []
    print(f"Processing reversal dictionary entries ({len(reversalentries_en)} entries)...")
    start_reversal = time.time()
    for i, (rev, e) in enumerate(reversalentries_en.items(), 1):
        if not rev:
            print(f"Warning: Skipping reversal entry with empty headword")
            continue
        percent = (i / len(reversalentries_en)) * 100
        elapsed = time.time() - start_reversal
        eta = (elapsed / i) * (len(reversalentries_en) - i) if i > 0 else 0
        print(f"Processing reversal {i}/{len(reversalentries_en)} ({percent:.1f}%): {rev}, ETA: {eta:.0f}s")
        result = endedict.reventry2dict_acad(rev, e, entry_lookup)
        if result is None:
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
                .replace('}', '')
            print(f"Error: reventry2dict_acad returned None for reversal '{rev}' (sortword: '{sortword}', entry: {e})")
            continue
        d, err = result
        if err is None and d['headword']:
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

    out.write("\n" + r'\end{document}' + "\n")
    print(f"Finished writing {outfile_acad}. Total elapsed time: {time.time() - start_time:.2f} seconds.")