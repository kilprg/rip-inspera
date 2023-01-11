# Rip inspera

Tries to parse supplied file(s) as a Swedish Inspera test and convert to an [Anki](https://apps.ankiweb.net/) cloze note HTML file (named *inputfilename*-clozed.html), paste the HTML file contents into a note plain text field (i.e. the HTML field, `Ctrl+Shift+X`). The parsing is based on the tests being in Swedish. Note that in the case of MCQ's the script is unable to parse which answer is correct so it writes all options in the answer cloze:

- On first study of the note simply read the question in the Anki browser and answer the question (cloze is exposed but the correct answer isn't marked).
- Look up the correct answer in the original PDF
- Tripple click the correct answer row inside the answer cloze and bold (`Ctrl+B`) it.

## Use

Open a command prompt or powershell and run `python rip_inspera.py [input-file-name][pdf|html|txt]`. Depending on PDF generation the PDF might actually be scanned images, if use software with good OCR (for instance Adobe Acrobat Pro) to OCR the document and export to text and run the text file through the ripper.

## Requirements

Requires the following:

- Requires [python](https://python.org) to be installed (duh!).
- Requires [Poppler](https://poppler.freedesktop.org) `pdftotext` to be installed to rip PDFs.
- Requires [BeautifulSoup 4](https://www.crummy.com/software/BeautifulSoup/) to be installed to rip from HTML - (`pip install beautifulsoup4`).
