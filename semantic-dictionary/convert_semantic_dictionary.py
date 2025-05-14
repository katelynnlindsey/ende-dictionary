import xml.etree.ElementTree as ET
from collections import defaultdict
import re

def clean_text(text):
    """Clean text by removing extra whitespace and replacing underscores with spaces."""
    if text:
        text = re.sub(r'\s+', ' ', text.strip())
        return text.replace('_', ' ')
    return ''

def extract_headword(entry):
    """Extract the headword from lexical-unit."""
    lexical_unit = entry.find('lexical-unit')
    if lexical_unit is not None:
        form = lexical_unit.find("./form[@lang='kit']/text")
        return clean_text(form.text) if form is not None and form.text else ''
    return ''

def extract_senses(entry):
    """Extract senses with part of speech, definition, and semantic domains."""
    senses = entry.findall('sense')
    sense_data = []
    for i, sense in enumerate(senses, 1):
        # Part of speech
        pos = sense.find('grammatical-info')
        pos_text = clean_text(pos.get('value')) if pos is not None else ''
        
        # Definition or gloss
        def_form = sense.find("./definition/form[@lang='en']/text")
        definition = clean_text(def_form.text) if def_form is not None and def_form.text else ''
        if not definition:
            gloss = sense.find("./gloss[@lang='en']/text")
            definition = clean_text(gloss.text) if gloss is not None and gloss.text else ''
        
        # Semantic domains
        domains = [clean_text(trait.get('value')) for trait in sense.findall("./trait[@name='semantic-domain-ddp4']")]
        
        sense_data.append({
            'sense_number': i,
            'pos': pos_text,
            'definition': definition,
            'domains': domains
        })
    return sense_data

def parse_lift_file(file_path):
    """Parse LIFT file and group entries by semantic domain."""
    tree = ET.parse(file_path)
    root = tree.getroot()
    domain_groups = defaultdict(list)
    
    for entry in root.findall('entry'):
        headword = extract_headword(entry)
        if not headword:
            continue
        senses = extract_senses(entry)
        for sense in senses:
            for domain in sense['domains']:
                if domain:  # Only include entries with a valid domain
                    domain_groups[domain].append({
                        'headword': headword,
                        'pos': sense['pos'],
                        'sense_number': sense['sense_number'],
                        'definition': sense['definition']
                    })
    
    return domain_groups

def generate_latex(domain_groups, output_file):
    """Generate LaTeX document with entries grouped by semantic domain."""
    latex_content = r"""

"""
    
    def domain_sort_key(domain):
        """Split domain into numeric parts and description for sorting."""
        # Check if domain starts with a numeric code (e.g., '6.6.5.1')
        if re.match(r'^\d+\.\d+', domain):
            # Split on first space to separate code from description
            parts = domain.split(' ', 1)
            code = parts[0]
            desc = parts[1] if len(parts) > 1 else ''
            # Split code by dots and convert numeric parts to integers
            code_parts = [int(n) if n.isdigit() else n for n in code.split('.')]
            # Return tuple: (0 for numeric, code_parts, description)
            return (0, code_parts, desc)
        else:
            # Non-numeric domain: sort after numeric domains
            return (1, [domain])
    
    for domain in sorted(domain_groups.keys(), key=domain_sort_key):
        entries = domain_groups[domain]
        if entries:
            latex_content += f"\\section*{{{domain}}}\n"
            latex_content += "\\begin{entrylist}\n"
            for entry in sorted(entries, key=lambda x: x['headword']):
                latex_content += (
                    f"\\entry{{{entry['headword']}}}\\headword{{{entry['headword']}}}{{\\pos{{{entry['pos']}}}}} {{\\definition{{{entry['definition']}}}}}\n"
                )
            latex_content += "\\end{entrylist}\n\n"
        
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(latex_content)

def main():
    input_file = 'dictionary-20250513.lift'  # Replace with your LIFT file path
    output_file = 'dictionary_by_domain.tex'  # Output LaTeX file
    domain_groups = parse_lift_file(input_file)
    generate_latex(domain_groups, output_file)
    print(f"LaTeX file generated: {output_file}")

if __name__ == "__main__":
    main()