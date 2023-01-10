"""
Tries to parse supplied file(s) as an Inspera test and convert to a cloze note HTML file
(named inputfilename-clozed.html), paste the HTML file contents into a note plain text
field (i.e. the HTML field, `Ctrl+Shift+X`)
- Requires Poppler `pdftotext` to be installed to rip PDF - http://poppler.freedesktop.org
- Requires BeautifulSoup 4 to be installed to rip from HTML -
  https://www.crummy.com/software/BeautifulSoup/ (`pip install beautifulsoup4`)
"""
import sys, os, tempfile, re, subprocess
from bs4 import BeautifulSoup
VER = "1.0.0"

if len(sys.argv) < 2:
    print("usage: python rip_inspera <filename(s)[html|pdf|txt]>")
    exit(-1)
elif sys.argv[1] == '-h' or sys.argv[1] == '--help':
    print("usage: python rip_inspera <filename(s)[html|pdf|txt]>\n",
        "\n",
        "Tries to parse supplied file(s) as an Inspera test and convert to a cloze note HTML\n",
        "file (named inputfilename-clozed.html). Paste the HTML file contents into a note plain\n",
        "text field (i.e. the HTML field, `Ctrl+Shift+X`).\n",
        "\n",
        "Notes on extensions:\n",
        "PDF:  Only works for text PDF's (Microsofts 'Print to PDF' sometimes produces images\n",
        "      rather than text), if you get 'Failed to split' that may be the case, try OCR the\n",
        "      PDF, select all text and copy/paste the into a `.txt`-file.\n",
        "HTML: Takes the text content of the HTML file and tries to parse.\n",
        "TXT:  Takes the file content and tries to parse.\n",
        "\n",
        "Requires the following to be installed in path:\n",
        "- Poppler `pdftotext` - http://poppler.freedesktop.org\n",
        "- BeautifulSoup 4 - https://www.crummy.com/software/BeautifulSoup/\n"
        "  (`pip install beautifulsoup4`)"
    )
    exit(-1)
elif sys.argv[1] == '-v' or sys.argv[1] == '--version':
    print(f"rip_inspera version {VER}")
    exit(-1)

tmp_dir = tempfile.TemporaryDirectory()

#Initial trim of intro, extro and cleaning
def trim_text(txt):
    txt = re.sub(r'”', r'"', txt)
    txt = re.sub(r'', r'↓', txt)
    txt = re.sub(r'', r'↑', txt)

    out = txt
    try:
        # Strip intro
        # match = re.search(r'^\f.*?$\n*(^[ \t]*1[\t ]+(.|\n)+)', txt, flags=re.M)
        if intro := re.search(r'Jag[\n\t ]*har[\n\t ]*kontrollerat[\n\t ]*att[\n\t ]*'
        r'jag[\n\t ]*inte[\n\t ]*har[\n\t ]*följande[\n\t ]*med[\n\t ]*mig[\n\t ]*'
        r'vid[\n\t ]*skrivplatsen:[\n\t ]*.[\n\t ]*Mobiltelefon[\n\t ]*och[\n\t ]*'
        r'annan[\n\t ]*otillåten[\n\t ]*elektronisk[\n\t ]*utrustning[\n\t ]*.[\n\t ]*'
        r'Armbandsur[\n\t ]*och[\n\t ]*övriga[\n\t ]*klockor', txt, flags=re.M):
            out = txt[intro.span()[1]:]
        # Strip outro
        out = out[:out.rfind('Totalpoäng: ')]
        # Clean text
        out = re.sub(r'^[\t ]+\d+/\d+[\t ]*$', '', out, flags=re.M) # Strip page numbers
        out = re.sub(r'^\f.*?$', '', out, flags=re.M) # Strip pgbrk rows
        #out = re.sub(r'\n+', r'\n', out, flags=re.M) # Strip empty lines
        # Strip typical header/footer lines
        out = re.sub(r'^.*https://ki-digex.inspera.com/.*$', '', out, flags=re.M)
        out = re.sub(r'^.*[0-3]?[1-9]/[0-3]?[1-9]/(19|20)[89012][0-9],'
                     r'[\t ]*[0-2]?[0-9]:[0-5]?[0-9].*$','', out, flags=re.M)
    except: # pylint: disable=bare-except
        print("Trim error, returning ountouched content...")
        return txt
    return out

# Return clean array of items
def split_items(txt):
    itms = re.split(r'[\n\t ]+Totalpoäng:[\t ]+[0-9,\.]+[\t ]*$', txt, flags=re.M)
    if len(itms) > 1:
        for i, itm in enumerate(itms):
            itms[i] = itm.strip()
        return itms
    print("Split error, aborting...")
    exit(-1)


# Return item split in parts
def parse_item(itm, _index):
    out = {}
    if nmatch := re.match(r'^[\n\t ]*((\d+)[ \t\n]+)', itm, flags=re.M):
        out['num'] = int(nmatch.group(2))
        body = itm[len(nmatch.group(1)):]
    else:
        out['num'] = ''
        body = itm

    if pmatch := re.match((
        r'(.*?)\n+[\t ]*((Välj [\w ]+ alternativ:)|'
        r'(Skriv in ditt svar här)|'
        r'(Välj alternativ[\t ]+))(.*)'
    ), body, flags=re.M|re.S):
        out['question'] = re.sub(r'[ \t]*\n[ \t]*', ' ', pmatch.group(1).strip())
        out['prompt'] = pmatch.group(2).strip()
        raw_opts_str = pmatch.group(6).strip()
        if pmatch.group(3):
            opts = []
            raw_opts = (raw_opts_str.split('\n\n')
                        if raw_opts_str.find('\n\n') > 1
                        else raw_opts_str.splitlines())
            for opt in raw_opts:
                opt = re.sub(r'[ \t]*\n[ \t]*', ' ', opt.strip()) # Join lines
                opts.append(opt)
            out['options'] = opts
            out['answer'] = out['options']
        elif pmatch.group(4):
            out['options'] = ""
            out['answer'] = re.sub(r'\s*Teckenf..*?\uf0b2\s+(.*?)Ord: 0.*',
                r'\1', raw_opts_str, flags=re.M|re.S).strip()
        else:
            opts = []
            for opt in raw_opts_str.split(', '):
                opt = re.sub(r'[ \t]*\n[ \t]*', ' ', opt.strip()) # Join lines
                opts.append(opt)
            out['options'] = opts
            out['answer'] = out['options']
    else:
        out['question'] = itm
        out['prompt'] = out['options'] = out['answer'] = None
    return out

for file in sys.argv[1:]:
    ext = file[file.rfind('.') + 1:].lower()
    if ext == 'html' or ext == 'htm':
        with open(file, encoding='utf-8') as fh:
            html = fh.read()
        tmp_dir.cleanup()
        RAW = BeautifulSoup(html, features='html.parser').get_text()
    elif ext == 'pdf':
        tmp_file = os.path.join(tmp_dir.name, "pdftotext-out.txt")
        proc_info = subprocess.run(["pdftotext.exe", "-layout", file, tmp_file],
            stdout=subprocess.PIPE, universal_newlines=True, check=True)
        with open(tmp_file, encoding='utf-8') as fh:
            RAW = fh.read()
        tmp_dir.cleanup()
    elif ext == 'txt':
        with open(file, encoding='utf-8') as fh:
            RAW = fh.read()
    else:
        print(f"{file}: Invalid file format, skipping...")
        continue

    txt = trim_text(RAW)
    itms = split_items(txt)
    for i, itm in enumerate(itms):
        if parts := parse_item(itm, i):
            if isinstance(parts['options'], list):
                options = f'<ol><li>{"</li><li>".join(parts["options"])}</li></ol>'
            else:
                options = parts['options'] if parts['options'] else "<br><br>"

            if isinstance(parts['answer'], list):
                answer = f'<ol><li>{"</li><li>".join(parts["options"])}</li></ol>'
            else:
                answer = parts['answer'] if parts['answer'] else "<br>"

            itm = (fr'{parts["num"]}. {parts["question"]}<br><br><u>{parts["prompt"]}</u>'
                fr'{options}{{{{c{i + 1}::{answer}}}}}')

        else:
            itm = fr'{i + 1}. {itm.strip()}<br>{{{{c{i + 1}::<br>}}}}'

        itm = re.sub(r'\n', '<br>', itm, flags=re.M)
        itm = re.sub(r'\s*<br>\s*', '<br>', itm)
        itms[i] = itm

    OUT = '<hr>' + "<hr>".join(itms)

    with open(f'{file}-clozed.html', 'w', encoding='utf-8') as fh:
        fh.write(OUT)
