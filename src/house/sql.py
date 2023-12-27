import os
from datetime import datetime as dt
import pandas as pd
import requests
from bs4 import BeautifulSoup
from ..moving_data import DB
from assets import base_url, states, table_cols, trans_cols
from src.house.pdf_processing import extract_all_ptr_data


class HouseDB(DB):
    """

    """
    def __init__(self):
        super().__init__()
        self.date_ = dt.strftime(dt.now(), "%Y-%m-%d")

    def get_new_file_list(self):
        """
        Get new list of PTR files for year in self.date_.
        """
        files_out = []
        for k in states:
            r = requests.post(
                os.getenv("HOUSE_URL"),
                params={
                    'State': k,
                    'FilingYear': self.date_[:4]
                }
            )
            soup = BeautifulSoup(r.content, 'lxml')
            for row in soup.find_all('tr')[1:]:
                data = [td.text.strip() for td in row.find_all('td')]
                data += ([k, row.a['href']])
                if 'ptr' in data[3].lower():
                    files_out.append(data)

        self.new_files = pd.DataFrame(files_out,
                                      columns=['Who', 'District', 'Year',
                                               'Filing', 'State', 'Path']
                                      ).drop_duplicates()

        print('new files: ' + str(len(self.new_files)))

    def get_old_file_list(self):
        """
        Get existing list of PTR files.
        """
        self.old_files = self.from_db("select * from file_table;")
        print('old files: ' + str(len(self.old_files)))

    def compare_file_list(self):
        """
        Download current file list and compare files_df (from get_file_list)

        Return list of new urls.
        """
        self.unrun_files = self.new_files[
            ~self.new_files['Path'].isin(self.old_files['Path']
                                         )]['Path'].values

        print('unrun files: ' + str(len(self.unrun_files)))

    def parse_file(self, url):
        full_url = base_url + url
        print(full_url)
        if full_url.split('/')[-1][0] != '8':
            dicto_ = extract_all_ptr_data(full_url)
            df = pd.DataFrame(dicto_)

            df_ = df[trans_cols]
            df_.columns = table_cols
            for c in ['date', 'notification_date']:
                df_[c] = pd.to_datetime(df_[c])

            self.to_db(df_, 'transactions_table')
        else:
            print('bad url')
            pass

    def upload_new_data(self):
        for u in self.unrun_files:
            self.parseFile(u)

    def update_files(self):
        """
        - combine old files and new files,
        - drop duplicates
        - overwrite existing table data.
        """
        all_files = self.old_files.append(self.new_files, 1).drop_duplicates()
        self.to_db(all_files, 'file_table', if_exists='replace')

    # def test_text(self):
    #     client = Client(self.twilio_sid, self.twilio_auth)
    #     if isinstance(self.phone_numbers, str):
    #         self.phone_numbers = eval(self.phone_numbers)
    #     for n in self.phone_numbers:
    #         client.messages.create(
    #             body="This is a test message!",
    #             from_='+19179822265',
    #             to=n)

    # def sendText(self):
    #     """

    #     """
    #     unrun_files = self.new_files[~self.new_files['Path'].isin(
    #         self.old_files['Path'])]

    #     payload = ''
    #     try:
    #         for f in unrun_files.iterrows():
    #             payload += ' / '.join([f[1]['Who'], f[1]
    #                                   ['District'], f[1]['Filing']]) + '\n'

    #     except Exception as e:
    #         payload = 'New House Financial Data!\n(there was also an error:{})'.format(e.strerror)

    #     client = Client(self.twilio_sid, self.twilio_auth)
    #     if isinstance(self.phone_numbers, str):
    #         self.phone_numbers = eval(self.phone_numbers)
    #     for n in self.phone_numbers:
    #         client.messages.create(
    #             body=payload,
    #             from_='+19179822265',
    #             to=n)
