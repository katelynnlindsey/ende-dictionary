# Proposed LaTeX fixes (not yet merged into the default pipeline)

Three concrete fixes from the reviewer triage, implemented in `pipeline/latex/proposed_fixes.py` as standalone functions that wrap/replace pieces of the validated `build_latex.py` -- **not currently called by `run_pipeline.py`**. Each is shown below on a real affected entry so you can see exactly what changes before deciding whether to fold it into the default build.

## 1. Suppress RED / loanword placeholder entries

6 placeholder headwords no longer publish their own `\entry{}` block: `RED`, `Agob loanword`, `English loanword`, `Idi loanword`, `Motu loanword`, `Taeme loanword`. Their 84 (RED) + 92 (loanword) dependent entries render without a dangling link to a fake headword.

**Before** (`ibi`, a dialectal-variant sense of the reduplication placeholder):
```latex

\entry{ibi}{\hypertarget{ibi}{}\headword{ibi}
\variantof{\Dialectalvariant of \vartext{\hyperlink{RED}{RED}}}  \pronnote{ibi}  \complexforms{\complexformhead{\hyperlink{ibiatt}{ibiatt}}\complexformpos{n.}\complexformdefn{footprint}\complexformtype{Derivative} }}
```
**After:**
```latex

\entry{ibi}{\hypertarget{ibi}{}\headword{ibi}
\variantof{\Dialectalvariant}  \pronnote{ibi}  \complexforms{\complexformhead{\hyperlink{ibiatt}{ibiatt}}\complexformpos{n.}\complexformdefn{footprint}\complexformtype{Derivative} }}
```

**Before** (`1940`, a dialectal-variant sense of the English-loanword placeholder):
```latex

\entry{1940}{\hypertarget{1940}{}\headword{1940}
\variantof{\Dialectalvariant of \vartext{\hyperlink{English loanword}{English loanword}}}}
```
**After** (donor language now stated directly and correctly, instead of a broken link):
```latex

\entry{1940}{\hypertarget{1940}{}\headword{1940}
\variantof{$\blacktriangleright$~\textsc{Loanword} (English)}}
```

## 2. Join multiple complex-forms onto one line

`yu` 'fire' has 8 complex forms; previously each got its own bulleted `\complexforms{}` block (the reviewer's exact complaint). Now joined into one:

**Before** (tail of the `yu` entry):
```latex
...ll fire}\complexformtype{Compound} }  \complexforms{\complexformhead{\hyperlink{yu bägäl}{yu bägäl}}\complexformpos{n.}\complexformdefn{gun, firearm}\complexformtype{Compound} }  \complexforms{\complexformhead{\hyperlink{yu kire}{yu kire}}\complexformpos{n.}\complexformdefn{firewood}\complexformtype{Compound} }  \complexforms{\complexformhead{\hyperlink{yu torkomoll}{yu torkomoll}}\complexformpos{n.}\complexformdefn{charcoal}\complexformtype{Compound} }  \complexforms{\complexformhead{\hyperlink{yu ttängäm}{yu ttängäm}}\complexformpos{n.}\complexformdefn{hell}\complexformtype{Compound} }  \complexforms{\complexformhead{\hyperlink{yu ttätta}{yu ttätta}}\complexformpos{n.}\complexformdefn{burning wood, burnt wood}\complexformtype{Compound} }}
```
**After:**
```latex
...type{Compound}, \complexformhead{\hyperlink{yu bägäl}{yu bägäl}}\complexformpos{n.}\complexformdefn{gun, firearm}\complexformtype{Compound}, \complexformhead{\hyperlink{yu kire}{yu kire}}\complexformpos{n.}\complexformdefn{firewood}\complexformtype{Compound}, \complexformhead{\hyperlink{yu torkomoll}{yu torkomoll}}\complexformpos{n.}\complexformdefn{charcoal}\complexformtype{Compound}, \complexformhead{\hyperlink{yu ttängäm}{yu ttängäm}}\complexformpos{n.}\complexformdefn{hell}\complexformtype{Compound}, \complexformhead{\hyperlink{yu ttätta}{yu ttätta}}\complexformpos{n.}\complexformdefn{burning wood, burnt wood}\complexformtype{Compound} }}
```

## 3. Embed pictures for the 118 entries whose illustration file already exists

97 kept entries resolve to an actual image file on disk (of 118 total matched filenames -- some entries reference more than one image, or the same file is shared). Requires one new macro in `head.txt`:

```latex
\newcommand{\entryimage}[1]{\includegraphics[width=0.3\linewidth]{#1}}
```

and copying the matched image files into `pipeline/output/latex/images/` alongside the generated `.tex` (handled by `resolve_illustrations()` + a copy step, not yet wired into `run_pipeline.py`).

**Before** (`mise` 'common cicadabird'):
```latex

\entry{mise}{\hypertarget{mise}{}\headword{mise}  \pronnote{mise}
  \pos{n.}  \sense{
    \definition{common cicadabird}    \scientificname{Edolisoma tenuirostre}}}
```
**After:**
```latex

\entry{mise}{\hypertarget{mise}{}\headword{mise}
\entryimage{images/mise.jpg}  \pronnote{mise}
  \pos{n.}  \sense{
    \definition{common cicadabird}    \scientificname{Edolisoma tenuirostre}}}
```

## Not implemented

No PDF render was produced (no LaTeX engine in this environment) -- these are source-level before/afters only. Compile locally to see the visual result before deciding.

## To adopt any of these

Say which ones you want, and I'll fold them into `build_latex.py`'s default path (behind the same validated diff-check discipline used for the rest of the pipeline), update `head.txt` for the picture macro, and re-run the full diff report so you can see the complete, entry-by-entry effect before it's final.
