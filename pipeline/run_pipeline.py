#!/usr/bin/env python3
"""
Ende dictionary pipeline driver.

Runs the full FLEx -> LaTeX + Dictionaria pipeline from one .lift export:

    python run_pipeline.py path/to/ende.lift [--head path/to/head.txt] [--outdir pipeline/output]

Steps:
  1. Parse the .lift export once (pipeline/lib/lift_parser.py).
  2. Generate dictionary_ende.tex (pipeline/latex/build_latex.py).
  3. Generate the Dictionaria submission tables (pipeline/dictionaria/build_dictionaria.py).
  4. Write a timestamped provenance log to pipeline/logs/, recording the
     input file, entry/sense/example counts, warnings raised during
     parsing, and every output file path -- so any dictionary number can
     be traced back to the run that produced it (matches the convention
     used in your other repos).

To point the pipeline at a new FLEx export, just pass its path as the
first argument -- nothing else needs to change.
"""

import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'latex'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dictionaria'))

from lift_parser import parse_lift
from build_latex import build_latex_document
from build_dictionaria import build_dictionaria_tables, write_dictionaria_csvs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('lift_file', help='Path to the FLEx .lift export')
    ap.add_argument('--head', default=None,
                     help='Path to the LaTeX preamble/macros file (default: head.txt next to this script\'s repo root, '
                          'or configured-dictionary/20250803/head.txt if not given)')
    ap.add_argument('--outdir', default=None, help='Output directory (default: pipeline/output next to this script)')
    args = ap.parse_args()

    pipeline_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(pipeline_dir)
    outdir = args.outdir or os.path.join(pipeline_dir, 'output')
    latex_outdir = os.path.join(outdir, 'latex')
    dictionaria_outdir = os.path.join(outdir, 'dictionaria')
    logs_dir = os.path.join(pipeline_dir, 'logs')
    os.makedirs(latex_outdir, exist_ok=True)
    os.makedirs(dictionaria_outdir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)

    head_path = args.head or os.path.join(repo_root, 'configured-dictionary', '20250803', 'head.txt')

    start = datetime.datetime.now()
    timestamp = start.strftime('%Y%m%d_%H%M%S')

    print(f"Parsing {args.lift_file} ...")
    parsed = parse_lift(args.lift_file)
    print(f"  {parsed.stats}")

    print(f"Building LaTeX document (header: {head_path}) ...")
    header_text = open(head_path, 'r', encoding='utf-8').read()
    tex_doc = build_latex_document(parsed, header_text)
    tex_path = os.path.join(latex_outdir, 'dictionary_ende.tex')
    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write(tex_doc)
    print(f"  wrote {tex_path} ({len(tex_doc):,} chars)")

    print("Building Dictionaria tables ...")
    tables = build_dictionaria_tables(parsed)
    written = write_dictionaria_csvs(tables, dictionaria_outdir)
    for name, (path, n) in written.items():
        print(f"  {name}: {n} rows -> {path}")

    end = datetime.datetime.now()
    log = {
        'run_timestamp': timestamp,
        'started': start.isoformat(),
        'finished': end.isoformat(),
        'duration_seconds': (end - start).total_seconds(),
        'input_lift_file': os.path.abspath(args.lift_file),
        'header_file': os.path.abspath(head_path),
        'parse_stats': parsed.stats,
        'warnings': parsed.warnings,
        'outputs': {
            'latex': tex_path,
            **{name: path for name, (path, _n) in written.items()},
        },
        'dictionaria_row_counts': {name: n for name, (_p, n) in written.items()},
    }
    log_path = os.path.join(logs_dir, f'run_{timestamp}.json')
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2)
    print(f"\nProvenance log written to {log_path}")
    if parsed.warnings:
        print(f"({len(parsed.warnings)} parsing warnings -- see the log for details)")


if __name__ == '__main__':
    main()
