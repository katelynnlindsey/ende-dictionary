import xml.etree.ElementTree as ET
from collections import defaultdict
import re

# Define verb classes
VERB_CLASSES = ['I', 'II', 'III', 'IV', 'Irregular']

def clean_text(text):
    """Clean text by removing extra whitespace and replacing underscores with spaces."""
    if text:
        text = re.sub(r'\s+', ' ', text.strip())
        return text.replace('_', ' ')
    return ''

def extract_headword(entry):
    """Extract the headword (analytic non-plural) from lexical-unit."""
    lexical_unit = entry.find('lexical-unit')
    if lexical_unit is not None:
        form = lexical_unit.find("./form[@lang='kit']/text")
        return clean_text(form.text) if form is not None and form.text else ''
    return ''

def extract_analytic_plural(entry):
    """Extract all analytic plural forms from variants, joined by commas."""
    variants = entry.findall('variant')
    plurals = []
    for variant in variants:
        env = variant.find("./trait[@name='environment'][@value='analytic plural']")
        if env is not None:
            form = variant.find("./form[@lang='kit']/text")
            if form is not None and form.text:
                plurals.append(clean_text(form.text))
    return ', '.join(plurals) if plurals else '[]'

def extract_definition(entry):
    """Extract definition or gloss, concatenated with commas."""
    senses = entry.findall('sense')
    definitions = []
    for sense in senses:
        # Try definition first
        def_form = sense.find("./definition/form[@lang='en']/text")
        if def_form is not None and def_form.text:
            definitions.append(clean_text(def_form.text))
        else:
            # Fallback to gloss
            gloss = sense.find("./gloss[@lang='en']/text")
            if gloss is not None and gloss.text:
                definitions.append(clean_text(gloss.text))
    return ', '.join(definitions) if definitions else ''

def extract_verb_class(entry):
    """Extract verb inflection class."""
    sense = entry.find('sense')
    if sense is not None:
        trait = sense.find("./grammatical-info/trait[@name='Verb-infl-class']")
        if trait is not None:
            return trait.get('value', 'Irregular')
    return 'Irregular'

def extract_examples(entry):
    """Extract example sentences and their translations."""
    examples = entry.findall('sense/example')
    example_list = []
    for ex in examples:
        sentence = ex.find("./form[@lang='kit']/text")
        translation = ex.find("./translation[@type='Free translation']/form[@lang='en']/text")
        sentence_text = clean_text(sentence.text) if sentence is not None and sentence.text else ''
        trans_text = clean_text(translation.text) if translation is not None and translation.text else ''
        if sentence_text and trans_text:  # Only include complete examples
            example_list.append({'sentence': sentence_text, 'translation': trans_text})
    return example_list

def parse_lift_file(file_path):
    """Parse LIFT file and group entries by verb class."""
    tree = ET.parse(file_path)
    root = tree.getroot()
    verb_groups = defaultdict(list)
    
    for entry in root.findall('entry'):
        verb_class = extract_verb_class(entry)
        if verb_class in VERB_CLASSES:
            headword = extract_headword(entry)
            analytic_plural = extract_analytic_plural(entry)
            definition = extract_definition(entry)
            examples = extract_examples(entry)
            if headword and definition:  # Only include entries with headword and definition
                verb_groups[verb_class].append({
                    'headword': headword,
                    'analytic_plural': analytic_plural,
                    'definition': definition,
                    'examples': examples
                })
    
    return verb_groups

def generate_latex(verb_groups, output_file):
    """Generate LaTeX document with verb class lists."""
    latex_content = r"""
\documentclass[12pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{enumitem}
\usepackage{xcolor}

% Custom commands for dictionary entries
\newcommand{\anpl}[1]{\textbf{#1}} % Analytic non-plural (headword)
\newcommand{\apl}[1]{\textit{#1}} % Analytic plural
\newcommand{\defi}[1]{#1} % Definition

"""
    
    for verb_class in VERB_CLASSES:
        entries = verb_groups.get(verb_class, [])
        if entries:
            latex_content += f"\\section*{{Class {verb_class} Verbs}}\n"
            latex_content += "\\begin{itemize}\n"
            for entry in sorted(entries, key=lambda x: x['headword']):
                latex_content += (
                    f"\\item \\anpl{{{entry['headword']}}} "
                    f"\\apl{{{entry['analytic_plural']}}} "
                    f"\\defi{{{entry['definition']}}}\n"
                )
                if entry['examples']:
                    latex_content += "\\begin{itemize}\n"
                    for example in entry['examples']:
                        latex_content += (
                            f"\\item \\exsen{{{example['sentence']}}} "
                            f"\\extran{{{example['translation']}}}\n"
                        )
                    latex_content += "\\end{itemize}\n"
            latex_content += "\\end{itemize}\n\n"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(latex_content)

def main():
    input_file = 'dictionary-verb-20250513.lift'  # Replace with your LIFT file path
    output_file = 'verb-dictionary.tex'  # Output LaTeX file
    verb_groups = parse_lift_file(input_file)
    generate_latex(verb_groups, output_file)
    print(f"LaTeX file generated: {output_file}")

if __name__ == "__main__":
    main()