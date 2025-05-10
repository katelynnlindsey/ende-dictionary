from bs4 import BeautifulSoup
import re

# Load HTML content from .txt file
with open('dictionary-configured-20250509.txt', 'r', encoding='utf-8') as f:
    html_content = f.read()

# Function to escape LaTeX special characters
def escape_latex(text):
    replacements = {
        '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_',
        '{': r'\{', '}': r'\}', '~': r'\textasciitilde', '^': r'\textasciicircum',
        '\\': r'\textbackslash'
    }
    for char, escape in replacements.items():
        text = text.replace(char, escape)
    return text

# Parse HTML
soup = BeautifulSoup(html_content, 'html.parser')

# Initialize LaTeX output
latex = [
]

current_letter = None
for div in soup.body.find_all('div', recursive=False):
    if div.get('class') == ['letHead']:
        letter = div.find('span', class_='letter')
        if letter:
            letter_text = letter.get_text().strip()
            latex.append(f'\\lettersection{{{escape_latex(letter_text)}}}')
            current_letter = letter_text
    elif div.get('class') == ['entry']:
        entry_parts = []
        headword_elem = div.find('span', class_='mainheadword')
        if headword_elem:
            headword_span = headword_elem.find('span', lang='kit')
            if headword_span:
                headword = headword_span.get_text().strip()
                entry_parts.append(f'\\headword{{{escape_latex(headword)}}}')

                pos = div.find('span', class_='partofspeech')
                if pos:
                    entry_parts.append(f'\\pos{{{escape_latex(pos.get_text().strip())}}}')

                etym = div.find('span', class_='etymology')            
                if etym:
                    etym_prec_elem = etym.find('span', class_='preccomment')
                    etym_name_elem = etym.find('span', class_='name')
                    etym_form_elem = etym.find('span', class_='form')
                    if etym_prec_elem and etym_name_elem and etym_form_elem:
                        etym_prec = etym_prec_elem.get_text().strip()
                        etym_name = etym_name_elem.get_text().strip()
                        etym_form = etym_form_elem.get_text().strip()
                        entry_parts.append(f'\\etymology{{{{escape_latex(etym_prec)}}{{escape_latex(etym_name)}}}}{{{escape_latex(etym_form)}}}')
                    elif etym_prec_elem and etym_form_elem:
                        etym_prec = etym_prec_elem.get_text().strip()
                        etym_form = etym_form_elem.get_text().strip()
                        entry_parts.append(f'\\etymology{{{escape_latex(etym_prec)}}}{{{escape_latex(etym_form)}}}')

                senses = div.find_all('span', class_='sense')
                for i, sense in enumerate(senses, 1):
                    sense_num = sense.find_previous('span', class_='sensenumber')
                    if sense_num:
                        entry_parts.append(f'\\sensenumber{{{sense_num.get_text().strip()}}}')
                    def_elem = sense.find('span', class_='definitionorgloss')
                    if def_elem:
                    # Extract text from each child span and join with a space
                        def_texts = [span.get_text().strip() for span in def_elem.find_all('span')]
                        def_text = ' '.join(def_texts)
                    else:
                        def_text = "no definition provided"
                    entry_parts.append(f'\\definition{{{escape_latex(def_text)}}}')

                    examples = sense.find_all('span', class_='example')
                    for ex in examples:
                        ex_text = ex.get_text().strip()
                        trans = ex.find_next('span', class_='translation')
                        if trans:
                            trans_text = trans.get_text().strip()
                            entry_parts.append(f'\\example{{{escape_latex(ex_text)}}}{{{escape_latex(trans_text)}}}')

                allomorphs = div.find_all('span', class_='allomorph')
                for allo in allomorphs:
                    allo_text_elem = allo.find('span', lang='kit')
                    if allo_text_elem:
                        allo_text = allo_text_elem.get_text().strip()
                        entry_parts.append(f'\\allomorph{{{escape_latex(allo_text)}}}')

                subentries = div.find_all('span', class_='subentry')
                for sub in subentries:
                    sub_head_elem = sub.find('span', class_='headword')
                    sub_def_elem = sub.find('span', class_='definitionorgloss')
                    if sub_head_elem and sub_def_elem:
                        sub_head = sub_head_elem.get_text().strip()
                        sub_def = sub_def_elem.get_text().strip() if sub_def_elem else "no definition provided"
                        sub_parts = [f'\\headword{{{escape_latex(sub_head)}}}']
                        sub_pos = sub.find('span', class_='partofspeech')
                        if sub_pos:
                            sub_parts.append(f'\\pos{{{escape_latex(sub_pos.get_text().strip())}}}')
                        sub_parts.append(f'\\definition{{{escape_latex(sub_def)}}}')   
                        
                        sub_examples = sub.find_all('span', class_='example')
                        for ex in sub_examples:
                            ex_text = ex.get_text().strip()
                            trans = ex.find_next('span', class_='translation')
                            if trans:
                                trans_text = trans.get_text().strip()
                                sub_parts.append(f'\\example{{{escape_latex(ex_text)}}}{{{escape_latex(trans_text)}}}')

                        entry_parts.append(f'\\subentry{{{''.join(sub_parts)}}}')
                    else:
                        print(f"Warning: Skipping subentry under '{headword}' due to missing headword or definition")

                latex.append(f'\\entry{{{escape_latex(headword)}}}{{{''.join(entry_parts)}}}')
    elif div.get('class') == ['minorentryvariant']:
        headword = div.find('span', class_='headword')
        if headword:
            headword_text = headword.get_text().strip()
            var_type_elem = div.find('span', class_='reverseabbr')
            ref_head_elem = div.find('span', class_='referencedentry')
            if var_type_elem and ref_head_elem:
                var_type = var_type_elem.get_text().strip()
                ref_head_span = ref_head_elem.find('span', lang='kit')
                if ref_head_span:
                    ref_head = ref_head_span.get_text().strip()
                    entry_parts = [
                        f'\\headword{{{escape_latex(headword_text)}}}',
                        f'\\variant{{{escape_latex(var_type)}}}{{{escape_latex(ref_head)}}}'
                    ]
                    latex.append(f'\\entry{{{escape_latex(headword_text)}}}{{{''.join(entry_parts)}}}')
                else:
                    print(f"Warning: Skipping minorentryvariant for headword '{headword_text}' due to missing referenced entry")
            else:
                print(f"Warning: Skipping minorentryvariant for headword '{headword_text}' due to missing reverseabbr or referencedentry")

latex.append(r'\end{document}')

with open('dictionary.tex', 'w', encoding='utf-8') as f:
    f.write('\n'.join(latex))

print("Conversion complete! Check dictionary.tex")
