import xml.etree.ElementTree as ET
import re

def escape_latex(text):
    """Escape special LaTeX characters."""
    if not text:
        return ""
    latex_special_chars = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "\\": r"\textbackslash{}",
    }
    return "".join(latex_special_chars.get(c, c) for c in text)

def process_text_element(element, lang, tag="text"):
    """Extract text from an element based on language and tag."""
    if element is None:
        return ""
    text_elem = element.find(f".//{tag}[@lang='{lang}']")
    return escape_latex(text_elem.text) if text_elem is not None and text_elem.text else ""

def process_entry(entry, tex_file, entry_index):
    """Process a single LIFT entry."""
    tex_file.write(f"\\noindent\\textbf{{Entry {entry_index}}}\n\n")

    # Citation
    citation = process_text_element(entry.find("lexical-unit/form"), "kit")
    if citation:
        tex_file.write(f"\\EntryCitation{{{entry_index}}}{{{citation}}}\n")

    # Pronunciation
    pronunciation = entry.find("pronunciation/form[@lang='kit-fonipa']/text")
    if pronunciation is not None and pronunciation.text:
        tex_file.write(f"\\EntryPronunciation{{{entry_index}}}{{{escape_latex(pronunciation.text)}}}\n")

    # Variants
    for var_idx, variant in enumerate(entry.findall("variant"), start=1):
        form = process_text_element(variant.find("form"), "kit")
        if form:
            tex_file.write(f"\\EntryVariant{{{entry_index}}}{{{var_idx}}}{{{form}}}\n")
        for trait in variant.findall("trait"):
            name = escape_latex(trait.get("name", ""))
            value = escape_latex(trait.get("value", ""))
            if name and value:
                tex_file.write(f"\\EntryVariantTrait{{{entry_index}}}{{{var_idx}}}{{{name}}}{{{value}}}\n")

    # Senses
    for sense_idx, sense in enumerate(entry.findall("sense"), start=1):
        sense_id = escape_latex(sense.get("id", ""))
        order = escape_latex(sense.get("order", str(sense_idx)))
        tex_file.write(f"\\EntrySense{{{entry_index}}}{{{order}}}{{{sense_id}}}\n")

        # Grammatical Info
        gram_info = sense.find("grammatical-info")
        if gram_info is not None:
            value = escape_latex(gram_info.get("value", ""))
            if value:
                tex_file.write(f"\\EntrySenseGrammaticalinfo{{{entry_index}}}{{{order}}}{{{value}}}\n")
            for trait in gram_info.findall("trait"):
                name = escape_latex(trait.get("name", ""))
                value = escape_latex(trait.get("value", ""))
                if name and value:
                    tex_file.write(f"\\EntrySenseGrammaticalinfoTrait{{{entry_index}}}{{{order}}}{{{name}}}{{{value}}}\n")

        # Definition
        definition = process_text_element(sense.find("definition/form"), "en")
        if definition:
            tex_file.write(f"\\EntrySenseDefinition{{{entry_index}}}{{{order}}}{{{definition}}}\n")

        # Gloss
        gloss = process_text_element(sense.find("gloss"), "en")
        if gloss:
            tex_file.write(f"\\EntrySenseGloss{{{entry_index}}}{{{order}}}{{{gloss}}}\n")

        # Examples
        for ex_idx, example in enumerate(sense.findall("example"), start=1):
            form = process_text_element(example.find("form"), "kit")
            if form:
                tex_file.write(f"\\EntrySenseExample{{{entry_index}}}{{{order}}}{{{ex_idx}}}{{{form}}}\n")
            translation = process_text_element(example.find("translation/form"), "en")
            if translation:
                tex_file.write(f"\\EntrySenseExampleTranslation{{{entry_index}}}{{{order}}}{{{ex_idx}}}{{{translation}}}\n")
            note = process_text_element(example.find("note/form"), "en")
            if note:
                tex_file.write(f"\\EntrySenseExampleNote{{{entry_index}}}{{{order}}}{{{ex_idx}}}{{{note}}}\n")
            for trait in example.findall("trait"):
                name = escape_latex(trait.get("name", ""))
                value = escape_latex(trait.get("value", ""))
                if name and value:
                    tex_file.write(f"\\EntrySenseExampleTrait{{{entry_index}}}{{{order}}}{{{ex_idx}}}{{{name}}}{{{value}}}\n")

        # Illustrations
        for ill_idx, illustration in enumerate(sense.findall("illustration"), start=1):
            href = escape_latex(illustration.get("href", ""))
            if href:
                tex_file.write(f"\\EntrySenseIllustration{{{entry_index}}}{{{order}}}{{{ill_idx}}}{{{href}}}\n")
            label = process_text_element(illustration.find("label/form"), "en")
            if label:
                tex_file.write(f"\\EntrySenseIllustrationLabel{{{entry_index}}}{{{order}}}{{{ill_idx}}}{{{label}}}\n")

        # Notes
        note = process_text_element(sense.find("note/form"), "en")
        if note:
            tex_file.write(f"\\EntrySenseNote{{{entry_index}}}{{{order}}}{{{note}}}\n")

        # Relations
        for relation in sense.findall("relation"):
            rel_type = escape_latex(relation.get("type", ""))
            ref = escape_latex(relation.get("ref", ""))
            if rel_type and ref:
                tex_file.write(f"\\EntrySenseRelation{{{entry_index}}}{{{order}}}{{{rel_type}}}{{{ref}}}\n")

        # Reversals
        for reversal in sense.findall("reversal"):
            form = process_text_element(reversal.find("form"), "en")
            if form:
                tex_file.write(f"\\EntrySenseReversal{{{entry_index}}}{{{order}}}{{{form}}}\n")

        # Traits
        for trait in sense.findall("trait"):
            name = escape_latex(trait.get("name", ""))
            value = escape_latex(trait.get("value", ""))
            if name and value:
                tex_file.write(f"\\EntrySenseTrait{{{entry_index}}}{{{order}}}{{{name}}}{{{value}}}\n")

    # Etymology
    etymology = entry.find("etymology")
    if etymology is not None:
        source = escape_latex(etymology.get("source", ""))
        if source:
            tex_file.write(f"\\EntryEtymology{{{entry_index}}}{{{source}}}\n")
        gloss = process_text_element(etymology.find("gloss"), "en")
        if gloss:
            tex_file.write(f"\\EntryEtymologyGloss{{{entry_index}}}{{{gloss}}}\n")

    # Notes
    note = process_text_element(entry.find("note/form"), "en")
    if note:
        tex_file.write(f"\\EntryNote{{{entry_index}}}{{{note}}}\n")

    # Relations
    for relation in entry.findall("relation"):
        rel_type = escape_latex(relation.get("type", ""))
        ref = escape_latex(relation.get("ref", ""))
        if rel_type and ref:
            tex_file.write(f"\\EntryRelation{{{entry_index}}}{{{rel_type}}}{{{ref}}}\n")

    # Traits
    for trait in entry.findall("trait"):
        name = escape_latex(trait.get("name", ""))
        value = escape_latex(trait.get("value", ""))
        if name and value:
            tex_file.write(f"\\EntryTrait{{{entry_index}}}{{{name}}}{{{value}}}\n")

    tex_file.write("\n")

def main():
    # Parse LIFT file
    tree = ET.parse("input.lift")
    root = tree.getroot()

    # Open output LaTeX file
    with open("dictionary.tex", "w", encoding="utf-8") as tex_file:
        # Writing LaTeX preamble
        tex_file.write("\\documentclass{article}\n")
        tex_file.write("\\usepackage[utf8]{inputenc}\n")
        tex_file.write("\\usepackage[T1]{fontenc}\n")
        tex_file.write("\\usepackage{geometry}\n")
        tex_file.write("\\geometry{a4paper, margin=1in}\n")
        tex_file.write("\\usepackage{parskip}\n")
        tex_file.write("\\begin{document}\n\n")

        # Define simplified commands
        tex_file.write("% Simplified command definitions\n")
        tex_file.write("\\newcommand{\\EntryCitation}[2]{#2}\n")
        tex_file.write("\\newcommand{\\EntryPronunciation}[2]{[#2]}\n")
        tex_file.write("\\newcommand{\\EntryVariant}[3]{Variant #2: #3}\n")
        tex_file.write("\\newcommand{\\EntryVariantTrait}[4]{[#3: #4]}\n")
        tex_file.write("\\newcommand{\\EntrySense}[3]{Sense #2 (#3): }\n")
        tex_file.write("\\newcommand{\\EntrySenseGrammaticalinfo}[3]{#3}\n")
        tex_file.write("\\newcommand{\\EntrySenseGrammaticalinfoTrait}[4]{[#3: #4]}\n")
        tex_file.write("\\newcommand{\\EntrySenseDefinition}[3]{Definition: #3}\n")
        tex_file.write("\\newcommand{\\EntrySenseGloss}[3]{Gloss: #3}\n")
        tex_file.write("\\newcommand{\\EntrySenseExample}[4]{Example #3: #4}\n")
        tex_file.write("\\newcommand{\\EntrySenseExampleTranslation}[4]{Translation: #4}\n")
        tex_file.write("\\newcommand{\\EntrySenseExampleNote}[4]{Note: #4}\n")
        tex_file.write("\\newcommand{\\EntrySenseExampleTrait}[5]{[#4: #5]}\n")
        tex_file.write("\\newcommand{\\EntrySenseIllustration}[4]{Illustration #3: #4}\n")
        tex_file.write("\\newcommand{\\EntrySenseIllustrationLabel}[4]{Label: #4}\n")
        tex_file.write("\\newcommand{\\EntrySenseNote}[3]{Note: #3}\n")
        tex_file.write("\\newcommand{\\EntrySenseRelation}[4]{Relation (#3): #4}\n")
        tex_file.write("\\newcommand{\\EntrySenseReversal}[3]{Reversal: #3}\n")
        tex_file.write("\\newcommand{\\EntrySenseTrait}[4]{[#3: #4]}\n")
        tex_file.write("\\newcommand{\\EntryEtymology}[2]{Etymology: #2}\n")
        tex_file.write("\\newcommand{\\EntryEtymologyGloss}[2]{Gloss: #2}\n")
        tex_file.write("\\newcommand{\\EntryNote}[2]{Note: #2}\n")
        tex_file.write("\\newcommand{\\EntryRelation}[3]{Relation (#2): #3}\n")
        tex_file.write("\\newcommand{\\EntryTrait}[3]{[#2: #3]}\n")
        tex_file.write("\n")

        # Process each entry
        for entry_idx, entry in enumerate(root.findall(".//entry"), start=1):
            process_entry(entry, tex_file, entry_idx)

        # End LaTeX document
        tex_file.write("\\end{document}\n")

    print("LaTeX file 'dictionary.tex' generated successfully.")

if __name__ == "__main__":
    main()