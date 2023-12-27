import os
import time
from datetime import datetime as dt
from datetime import timedelta
from typing import List, Union

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .helpers import disabled_check, parse_ptr, scrape_senate_row


class SenateDownloader:
    def __init__(
            self,
            chrome: bool = False,
            headless: bool = True
    ):
        self.chrome = chrome
        self.headless = headless

    def get_start_date(self):
        start_date = dt.today() - timedelta(1)
        return start_date.strftime("%m/%d/%Y")

    def search(
            self,
            start_date: Union[str, None] = None,
            end_date: Union[str, None] = None
            ) -> Union[dict, None]:
        self.start_date = start_date if start_date else self.get_start_date()
        print(f"starting on {self.start_date}")
        if end_date:
            self.end_date = end_date
            print(f"ending on {self.end_date}")

        self.load_PTR_search(start_date)
        search_results = self.scrape_PTR_search()
        if not search_results:
            print("no search results!")
            return
        else:
            search_row_dicts = self.get_all_search_row_data(search_results)
            row_data = self.process_search_data(search_row_dicts)
            return row_data

    def load_senate_driver(self):
        """
        - opens a browser
        - loads the senate search page,
        - accepts the popup

        Returns driver and "wait" object.
        """
        if self.chrome:
            chrome_options = webdriver.ChromeOptions()
            if self.headless:
                chrome_options.add_argument("--headless")

            if os.getenv("DYNO"):
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--no-sandbox")

                chrome_options.binary_location = os.getenv("GOOGLE_CHROME_BIN")

                print("Running Chrome Webdriver to pull Senator data...")
                self.driver = webdriver.Chrome(
                    executable_path=os.getenv("CHROMEDRIVER_PATH"),
                    chrome_options=chrome_options
                )
            else:
                print("Running Chrome Webdriver to pull Senator data...")
                self.driver = webdriver.Chrome(chrome_options=chrome_options)

        else:
            options = Options()
            if self.headless:
                options.add_argument('-headless')

            print("Running Webdriver to pull Senator data...")
            self.driver = webdriver.Firefox(options=options)

        self.wait = WebDriverWait(self.driver, 5)

        self.driver.get(os.getenv("SENATE_SEARCH_URL"))

        print("...acknowledging terms of usage...")
        self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[@id='agree_statement']"))
        ).click()

    def load_PTR_search(self, start_date: str) -> None:
        """
        Pre-search prep.
        - load driver and wait
        - navigating search params
        - adjust pagination
        """
        self.load_senate_driver()

        print("...selecting all states...")
        senate_check = self.wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '.senator_filer')
            ))
        senate_check.click()

        print("...selecting doc types...")
        PTR_field = self.driver.find_element(By.ID, 'reportTypeLabelPtr')
        PTR_field.click()

        print("...selecting start date...")
        fromDatefield = self.driver.find_element(By.ID, 'fromDate')
        fromDatefield.clear()
        fromDatefield.send_keys(start_date)

        if 'end_date' in self.__dict__:
            print("...selecting end date...")
            fromDatefield = self.driver.find_element(By.ID, 'fromDate')
            fromDatefield.clear()
            fromDatefield.send_keys(self.end_date)

        print('...submitting...')
        button = self.driver.find_element(
            By.XPATH,
            '/html/body/div[1]/main/div/div/div[5]/div/form/div/button'
        )
        button.click()

        print('..adjusting pagination...')
        pages_menu = self.driver.find_element(By.NAME, 'filedReports_length')
        for option in pages_menu.find_elements(By.TAG_NAME, 'option'):
            if option.text == '100':
                option.click()

        self.wait.until(EC.element_to_be_clickable(
            (By.ID, 'filedReports_next')))

    def scrape_PTR_search(self) -> List[str]:
        """
        Iterates through search results.
        Saves source of each page.
        """
        page_count = 1

        search_results = []
        while not disabled_check(self.driver.page_source):
            print(page_count)
            search_results.append(self.driver.page_source)
            next_button = self.driver.find_element(By.ID, 'filedReports_next')
            next_button.click()
            time.sleep(2)
            page_count += 1

        # last row
        search_results.append(self.driver.page_source)
        if not search_results:
            print("no search results!")
        return search_results

    def get_all_search_row_data(self, search_results):
        search_row_dicts = []
        for s in search_results:
            soup = BeautifulSoup(s, 'lxml')
            search_rows = soup.find_all('tr')
            for search_row in search_rows:
                search_row_dict = scrape_senate_row(search_row)  # from helpers
                if search_row_dict is not None:
                    search_row_dicts.append(search_row_dict)
        print(f"{len(search_row_dicts)} search row dicts...")
        return search_row_dicts

    def process_search_data(self, search_row_dicts):
        row_df = pd.DataFrame(search_row_dicts)
        row_df['Handwritten'] = row_df['Filing Code'].map(
            lambda c: True if 'H' in c else False)
        row_df['Filing Date'] = pd.to_datetime(row_df['Filing Date']).map(str)
        row_df['File Name'] = row_df.apply(
            lambda r: "_".join(
                [
                    r['Name (Last)'],
                    r['State'],
                    r['Filing Code'],
                    r['Filing Date']
                ]).split(' ')[0] + ".html", 1
        )
        return row_df

    def get_PTR_data(self, row_dict):
        link = os.getenv("SENATE_SEARCH_URL") + row_dict['URL']
        if "/ptr/" in link:
            print(link)
            self.driver.get(link)
            time.sleep(1)
            row_dict['html'] = self.driver.page_source
            return row_dict  # make a function to collect these

    def read_PTR_row(self, ptr_row):
        """
        ptr_list = pd.read_html(ptr_data[5]['html'])
        for p_ in ptr_list:
            for p_ in p.to_dict('records'):
                print(p_)
        """
        output_ptr_list = []
        ptr_list = pd.read_html(ptr_row['html'])
        for ptr in ptr_list:
            # add addn data
            for p in ptr.to_dict('records'):
                p['Name_'] = ' '.join(
                    [ptr_row['Name (First)'], ptr_row['Name (Last)']])
                p['File Name'] = ptr_row['File Name']
                p['Filing Type_'] = ptr_row['Filing Type']
                p['Filing Date_'] = ptr_row['Filing Date']
                output_ptr_list.append(p)
        return output_ptr_list

    def process_PTR_df(self, full_ptr_list):
        ptr_df = pd.DataFrame(full_ptr_list)
        ptr_df['Sale'] = ptr_df['Type'].map(
            lambda x: True if 'Sale' in x else False)
        ptr_df['Amount Min'] = ptr_df.apply(
            lambda r: parse_ptr(r['Amount'], r['Sale'])[0], 1)
        ptr_df['Amount Max'] = ptr_df.apply(
            lambda r: parse_ptr(r['Amount'], r['Sale'])[1], 1)
        return ptr_df
