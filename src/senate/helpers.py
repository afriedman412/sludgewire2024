from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os


def parse_ptr(v, sale_):
    v_out = ptr_code[v]
    if sale_ is True:
        v_out = [-i for i in v_out[::-1]]
    return v_out


def use_dotenv():
    for k in [
        'DYNO',
        'AWS_EXECUTION_ENV',
        'GOOGLE_CLOUD_PROJECT'
    ]:
        if os.getenv(k):
            return False
    return True


def load_dotenv_with_env(env):
    if use_dotenv():
        load_dotenv(f".env.{env}")


def disabled_check(source):
    """
    Ham-fisted check if "Next" button on senate search page is disabled.

    returns True if it IS DISABLED.
    """
    soup = BeautifulSoup(source, 'lxml')
    try:
        if 'disabled' in soup.find(
            'a', attrs={'id': 'filedReports_next'}
        )['class']:
            return True
        else:
            return False
    except IndexError:
        return False


def scrape_senate_row(row):
    """
    Takes a row from senate search data (as a BeautifulSoup object!)

    Returns row data.
    """
    row_text = [r.text for r in row.find_all('td')]

    if len(row_text) > 1:
        row_dict = dict(
            zip([
                'Name (First)', 'Name (Last)',
                'Status', 'Filing Type', 'Filing Date'],
                row_text))
        # row_dict['Filing Date'] = row_dict['Filing Date'].replace('/', '_')
        row_dict['URL'] = row.find_all('td')[3].a['href']
        filing_code = file_typer(row_dict['Filing Type'].lower())

        if 'paper' in row_dict['URL']:
            filing_code += 'H'  # for 'Handwritten'
        else:
            filing_code += 'W'  # for 'web'

        row_dict['Filing Code'] = filing_code
        row_dict['State'] = 'UN'  # how do i find state?
        row_dict['File Name'] = '_'.join(
            [
                row_dict[k]
                for k in ['Name (Last)', 'State', 'Filing Code', 'Filing Date']
            ]
        ) + '.html'

        return row_dict


def file_typer(file_):
    code = ''
    code = ''.join([v for k, v in f_types.items() if k in file_])

    if '(amendment' in file_:
        code += 'X'
    else:
        code += '_'

    if 'due date extension' in file_:
        code += 'E'
    else:
        code += '_'

    return code


f_types = {
    'annual report': 'A',
    'periodic transaction report': 'P',
    'new filer report': 'N',
    'candidate report': 'C',
    'termination report': 'T'
}

ptr_code = {
    '$1,001 - $15,000': [1001, 15000],
    '$15,001 - $50,000': [15001, 50000],
    '$1,000,001 - $5,000,000': [1000001, 5000000],
    '$100,001 - $250,000': [100001, 250000],
    '$250,001 - $500,000': [250001, 500000],
    '$500,001 - $1,000,000': [500001, 1000000],
    '$50,001 - $100,000': [50001, 100000],
    '$5,000,001 - $25,000,000': [5000001, 25000000]
}
