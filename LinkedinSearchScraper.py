from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import Proxy, ProxyType
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import logging
import pickle
import os
import csv

class LinkedInSearch:
    def __init__(self, delay=5):
        if not os.path.exists("data"):
            os.makedirs("data")

        log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(level=logging.INFO, format=log_fmt)
        self.delay=delay
        logging.info("Starting driver")
        self.driver = webdriver.Chrome(executable_path="chromedriver.exe")

    def login(self, email, password):
        """Go to linkedin and login
        
        Parameters
        ----------
        email : str
        password : str
        """
        # go to linkedin:
        logging.info("Logging in")
        self.driver.maximize_window()
        self.driver.get('https://www.linkedin.com/login')
        time.sleep(self.delay)

        self.driver.find_element_by_id('username').send_keys(email)
        self.driver.find_element_by_id('password').send_keys(password)

        self.driver.find_element_by_id('password').send_keys(Keys.RETURN)

        try:
            if self.driver.find_element_by_class_name('msg-overlay-list-bubble--is-minimized') is not None:
                pass
        except NoSuchElementException:
            try:
                if self.driver.find_element_by_class_name('msg-overlay-bubble-header') is not None:
                    self.driver.find_element_by_class_name('msg-overlay-bubble-header').click()
            except NoSuchElementException:
                pass


        time.sleep(self.delay)

    def save_cookie(self, path):
        """Saves browser cookies.
        Parameters
        ----------
        path : str
            path must exist (except for file)
        """
        with open(path, 'wb') as filehandler:
            pickle.dump(self.driver.get_cookies(), filehandler)

    def load_cookie(self, path):
        """Loads cookies from file
        Parameters
        ----------
        path : str
            Path must exist
        """
        with open(path, 'rb') as cookiesfile:
            cookies = pickle.load(cookiesfile)
            for cookie in cookies:
                self.driver.add_cookie(cookie)

    def search_linkedin(self, keywords, location):
        """Enter keywords into search bar.
        Parameters
        ----------
        keywords : str
        location : str
        """
        logging.info("Searching jobs page")
        self.driver.get("https://www.linkedin.com/jobs/")
        # search based on keywords and location and hit enter
        self.wait_for_element_ready(By.CLASS_NAME, 'jobs-search-box__text-input')
        time.sleep(self.delay)
        search_bars = self.driver.find_elements_by_class_name('jobs-search-box__text-input')
        search_keywords = search_bars[0]
        search_keywords.send_keys(keywords)
        search_location = search_bars[3]
        search_location.send_keys(location)
        time.sleep(self.delay)
        search_location.send_keys(Keys.RETURN)
        logging.info("Keyword search successful")
        time.sleep(self.delay)
    
    def wait(self, t_delay=None):
        """Make bot wait for t_delay seconds.
        Parameters
        ----------
        t_delay : int, optional
            seconds to wait.
        """
        delay = self.delay if t_delay == None else t_delay
        time.sleep(delay)

    def scroll_to(self, job_list_item):
        """Scroll to the list item in the column 
        Parameters
        ----------
        job_list_item : selenium element
        """
        self.driver.execute_script("arguments[0].scrollIntoView();", job_list_item)
        job_list_item.click()
        time.sleep(self.delay)
    
    def get_position_data(self, job):
        """Gets the position data for a posting.
        Parameters
        ----------
        job : Selenium webelement
        Returns
        -------
        list of str : [position, company, location, details]
        """

        
        [position, company, location] = job.text.split('\n')[:3]
        details = self.driver.find_element_by_id("job-details").text
        return [position, company, location, details]

    def wait_for_element_ready(self, by, text):
        """Waits for an element to be ready
        Parameters
        ----------
        by : Selenium BY object
        text : str
        """

        try:
            WebDriverWait(self.driver, self.delay).until(EC.presence_of_element_located((by, text)))
        except TimeoutException:
            logging.debug("wait_for_element_ready TimeoutException")
            pass

    def close_session(self):
        """Closes session
        """
        logging.info("Closing session")
        self.driver.close()

    def run(self, email, password, keywords, location):
        """Searchs keywords + location, then scrapes first 8 pages of LinkedIn.
        After completed, will just post message "Done Scraping".
        Parameters
        ----------
        keywords : str
        location : str
        """
        log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(level=logging.INFO, format=log_fmt)

        if os.path.exists("data/cookies.txt"):
            self.driver.get("https://www.linkedin.com/")
            self.load_cookie("data/cookies.txt")
            self.driver.get("https://www.linkedin.com/")
        else:
            self.login(
                email=email,
                password=password
            )
            self.save_cookie("data/cookies.txt")

        logging.info("Begin linkedin keyword search")
        self.search_linkedin(keywords, location)
        self.wait()

        # scrape pages,only do first 8 pages since after that the data isn't 
        # well suited for me anyways:
        csv_file = open('Data.csv', 'w',encoding="utf8", errors='ignore')
        headers = ['Position', 'Company', 'Location', 'Details']
        csv_dict_writer = csv.DictWriter(csv_file,fieldnames = headers,delimiter=',')
        csv_dict_writer.writeheader()

        for page in range(1, 2):
            # get the jobs list items to scroll through:
            jobs = self.driver.find_elements_by_class_name("occludable-update")
            for job in jobs:
                self.scroll_to(job)
                [position, company, location, details] = self.get_position_data(job)
                data = {'Position':'{}'.format(position), 'Company':'{}'.format(company), 'Location':'{}'.format(location), 'Details':'{}'.format(details)}
                #write data to csv
                csv_dict_writer.writerow(data)
            # go to next page:
            self.driver.find_element_by_xpath(f"//button[@aria-label='Page {page}']").click()
            self.wait()
        logging.info("Done scraping.")
        logging.info("Closing Data.csv file.")
        csv_file.close()
        self.close_session()


if __name__ == "__main__":
    email="user@gmail.com" 
    password = "password"
    search = LinkedInSearch()
    search.run(email, password, "Data Scientist", "India")