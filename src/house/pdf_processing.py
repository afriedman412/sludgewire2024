import re
from itertools import dropwhile, pairwise
from .assets import notes, amount_key, df_keys, table_end_text
import pandas as pd
import pdfplumber
from pdfplumber import PDF
import urllib3
import io
from typing import List


def extract_all_ptr_data(path: str, local: bool = False):
    """
    Highest order function for data extraction.

    Runs `extract_ptr_entries`, then adds a couple things to the df.

    TODO: parse id_, make new tests for it
    """
    p = get_pdf(path, local)
    id_ = extract_id(p)

    df = extract_ptr_entries(p)
    df['URL'] = path
    df['Filer'] = id_
    return df


def extract_ptr_entries(p: PDF) -> pd.DataFrame:
    """
    Extracts and parses entries from a pdf.

    Input:
        p (PDF): pdfplumber object containing target pdf

    Output:
        df (pd.DataFrame): dataframe containing all pdf data
    """
    lines = [fix_hex_note_labels(line) for line in extract_pdf_text(p)]
    id_ = extract_id(p)

    entries = get_entries(lines)

    final_entries = []
    for e in entries:
        entry_dict = parse_entry(e)
        entry_dict['Filer'] = id_
        # entry_dict['URL'] = url
        for k in df_keys:
            if k not in entry_dict:
                entry_dict[k] = None
        final_entries.append(entry_dict)

    df = pd.DataFrame(final_entries)[df_keys]
    return df


def get_pdf(path: str, local: bool = False) -> PDF:
    """
    Loads pdfplumber from `path`.

    Inputs:
        path (str): path to or url of pdf
        local (bool): toggles looking locally (v looking on the web)

    Output:
        p (PDF): pdfplumber object containing the pdf
    """
    if local:
        p = pdfplumber.open(path)
    else:
        http = urllib3.PoolManager()
        temp = io.BytesIO()
        temp.write(http.request("GET", path).data)
        p = pdfplumber.open(temp)

    return p


def parse_entry(entry: List[str]) -> dict:
    """
    Input:
        entry (list): list of lines from one table entry (usually an asset)

    Output:
        entry_dict (dict): dict containing info for one entry
    """
    first_line = entry.pop(0)
    entry_dict = {}

    entry_dict['Cap Gains > $200?'] = re.search(r"gfedcb$", first_line)
    first_line = re.sub(r"gfedcb?$", "", first_line)

    amount = re.search(r"\$[\d,]+\s\-\s?", first_line)
    if amount:
        if amount[0].strip() in amount_key:
            min_, max_ = tuple(amount_key.get(amount[0].strip()))
            entry_dict['Min Amount'] = min_
            entry_dict['Max Amount'] = max_
            entry[0] = entry[0].replace(str(max_), "")
        else:
            entry_dict['Amount'] = amount[0]
        first_line = first_line[:amount.start()]

    for label, date in zip(
        ["Date", "Notification Date"],
        re.findall(r"\d{2}/\d{2}/\d{4}", first_line)
    ):
        entry_dict[label] = date
    first_line = first_line[
        :re.search(r"\d{2}/\d{2}/\d{4}", first_line).start()
        ]

    transaction_type = re.search(r"(\s[A-Z]\s$)|(S \(partial\))", first_line)
    if transaction_type:
        entry_dict['Transaction Type'] = transaction_type[0].strip()
        first_line = first_line[:transaction_type.start()]

    entry = [first_line] + entry

    entry_dict.update({k: "" for k in notes})
    k = 'Asset'
    for e in entry:
        for n in notes:
            if e.lower().startswith(f"{n.lower()}: "):
                k = n
                e = e[re.search(r"^[\w\s]+\:", e, flags=re.I).end():]
        entry_dict[k] = ' '.join([entry_dict[k], e]).strip()
    return entry_dict


def table_toggle(line: str) -> bool:
    """
    Evaluates whether a line is the beginning of a table.

    Used to ignore pre-table text in a pdf.
    """
    return not any([
        line.strip().lower().startswith(k.lower()) for k in
        [
            "ID Owner Asset Transaction Date",
            "transactions",
            'T\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            ]
    ])


def get_table_end_index(lines, s: str = table_end_text):
    """
    Finds the index of the first line that begins with `s`.

    Default is `table_end_text`, set in `assets.py`.

    Returns -1 if none is found.
    """
    for i, line in enumerate(lines):
        if line.lower().startswith(s.lower()):
            return i
    return -1


def start_entry(line: str) -> bool:
    """
    Evaluates whether a line is the beginning of an entry.
    """
    for regex in [
        r"gfedcb$",
        r"\$[\d,]{3,8}[\s\-]{2}$",
        r"[\s\-]{3}\$[\d,]{3,8}$",
    ]:
        if re.search(regex, line):
            return True
    return False


def detect_table_header(line: str) -> bool:
    """
    Evaluates if a line is table header text (and can be ignored).
    """
    return any([
        line.strip().lower().startswith(line_start.lower())
        for line_start in [
            "iD owner asset transaction",
            "type Date gains >",
            "$200?"
        ]])


def extract_pdf_text(p: PDF) -> List[str]:
    """
    Collects all lines of text across all pages of a pdf in one list.
    """
    lines = []
    for p in p.pages:
        lines += p.extract_text().split("\n")
    return lines


def get_entries(lines: List[str]) -> List[List[str]]:
    """
    Groups `lines` into entries using syntax.
    """
    lines_ = [
        line for line in dropwhile(table_toggle, lines)
        if not detect_table_header(line)
        ]

    starts = [i for i, line in enumerate(lines_) if start_entry(line)]

    end = get_table_end_index(lines_)

    entries = [
        [line for line in lines_[a:b]]
        for a, b in pairwise(starts)
    ] + [lines_[starts[-1]:end]]

    return entries


def extract_id(p) -> str:
    """
    Gets name, state and district.
    Probably doesn't need its own function.

    Input:
        p (PDF object): PDF object

    Output:
        id_ (str)
    """
    id_ = ' '.join([
        i['text']
        for i in p.pages[0].crop(
            [100, 200, 600, 250]
        ).extract_words()
    ])
    return id_


def fix_hex_note_labels(line: str) -> str:
    """
    `notes` text often has lowercase letters replaced by "\x00" and needs to be translated.

    ie:
    What should be "Filing Status" looks like "F\x00\x00\x00\x00\x00 S\x00\x00\x00\x00"
    """
    hexed_notes = [
        r"^A(\x00){4}: ",
        r"^D(\x00){10}: ",
        r"^F(\x00{5}) S(\x00{5}): ",
        r"^S(\x00{9}) O\x00: ",
        r"^L(\x00){7}: ",
        r"^C(\x00){7}: ",
    ]
    for hexed_note, note in zip(hexed_notes, notes):
        if re.search(hexed_note, line, flags=re.I):
            return re.sub(hexed_note, note + ": ", line, flags=re.I)
    return line
