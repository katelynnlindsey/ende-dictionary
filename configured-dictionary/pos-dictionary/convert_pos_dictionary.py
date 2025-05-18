from bs4 import BeautifulSoup
import uuid
import logging

# Set up logging to help diagnose issues
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Function to extract entries from the input file
def parse_entries(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except FileNotFoundError:
        logging.error(f"Input file {file_path} not found.")
        return {}
    except UnicodeDecodeError:
        logging.error(f"Input file {file_path} is not UTF-8 encoded.")
        return {}

    soup = BeautifulSoup(content, 'html.parser')
    entries = soup.find_all('div', class_='entry')
    pos_dict = {}  # Dictionary to store entries by part of speech

    for idx, entry in enumerate(entries, 1):
        # Extract headword
        headword_span = entry.find('span', class_='mainheadword')
        headword = ''
        if headword_span:
            inner_span = headword_span.find('span')
            headword = inner_span.get_text(strip=True) if inner_span else ''
        if not headword:
            logging.warning(f"Entry {idx}: Missing or empty headword. Skipping entry.")
            continue

        # Extract entry-level POS (from sharedgrammaticalinfo)
        entry_pos = 'unknown'
        shared_gram = entry.find('span', class_='sharedgrammaticalinfo')
        if shared_gram:
            pos_span = shared_gram.find('span', class_='partofspeech')
            if pos_span:
                lang_span = pos_span.find('span', lang='en')
                entry_pos = lang_span.get_text(strip=True) if lang_span else 'unknown'
        if entry_pos == 'unknown':
            logging.warning(f"Entry {idx} (headword: {headword}): Missing entry-level partofspeech.")

        # Extract senses
        senses = entry.find_all('span', class_='sense')
        if not senses:
            logging.warning(f"Entry {idx} (headword: {headword}): No senses found. Skipping entry.")
            continue

        for sense_idx, sense in enumerate(senses, 1):
            # Extract sense-level POS (if present)
            pos = entry_pos  # Default to entry-level POS
            pos_span = sense.find('span', class_='partofspeech')
            if pos_span:
                lang_span = pos_span.find('span', lang='en')
                pos = lang_span.get_text(strip=True) if lang_span else entry_pos
            if pos == 'unknown':
                logging.warning(f"Entry {idx}, sense {sense_idx} (headword: {headword}): No sense-level POS, using entry-level POS '{entry_pos}'.")

            # Extract definition for this sense
            definition = ''
            def_span = sense.find('span', class_='definitionorgloss')
            if def_span:
                def_text = def_span.find('span', lang='en')
                definition = def_text.get_text(strip=True) if def_text else ''
            if not definition:
                logging.warning(f"Entry {idx}, sense {sense_idx} (headword: {headword}): No definition found. Skipping sense.")
                continue

            # Store in dictionary by part of speech
            if pos != 'unknown':  # Only include non-unknown POS
                if pos not in pos_dict:
                    pos_dict[pos] = []
                pos_dict[pos].append({'headword': headword, 'definitions': [definition]})

    return pos_dict

# Function to generate LaTeX content for a part of speech
def generate_latex_section(pos, entries):
    latex = f"\\section{{{pos}}}\n"
    latex += "\\begin{enumerate}\n"

    for entry in entries:
        headword = entry['headword'].replace('&', '\\&').replace('%', '\\%').replace('#', '\\#')
        definitions = entry['definitions']
        
        # Start the entry with the headword
        entry_text = f"\\entry{{{pos}}}{{\\headword{{{headword}}}"
        
        # Add numbered definitions
        for i, definition in enumerate(definitions, 1):
            def_text = definition.replace('&', '\\&').replace('%', '\\%').replace('#', '\\#')
            entry_text += f" \\definition{{{i}. {def_text}}}"
        
        entry_text += "}"
        latex += f"\\item {entry_text}\n"

    latex += "\\end{description}\n\n"
    return latex

# Function to generate the complete LaTeX document
def generate_latex_file(pos_dict, output_file):
    preamble = r"""
"""
    document_end = r""

    latex_content = preamble
    for pos, entries in sorted(pos_dict.items()):
        latex_content += generate_latex_section(pos, entries)

    latex_content += document_end

    try:
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(latex_content)
        logging.info(f"LaTeX file generated: {output_file}")
    except Exception as e:
        logging.error(f"Failed to write LaTeX file {output_file}: {e}")

# Main execution
input_file = 'dictionary-configured-20250509.txt'  # Updated path
output_file = 'word_lists.tex'  # Output LaTeX file

pos_dict = parse_entries(input_file)
if pos_dict:
    generate_latex_file(pos_dict, output_file)
else:
    logging.error("No entries parsed. LaTeX file not generated.")