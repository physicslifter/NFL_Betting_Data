"""Script for pulling spread and total data
"""
import os
from selenium.webdriver.common import keys, by
Keys,  By = keys.Keys(), by.By()
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from pdb import set_trace as st
import time
from webdriver_manager.chrome import ChromeDriverManager
import json
import shutil

def save_to_json(my_dict, fname):
    my_json = json.dumps(my_dict)
    with open(fname, "w") as f:
        f.write(my_json)
        
def load_json(fname): #function for loading in json files
    with open(fname) as json_file: #assign opened file to object json_file
        data=json.load(json_file) #load data
    return data

class DriverHandler:
    """
    class for smoothly handling the opening of the webdriver
    """
    def __init__(self, headerless = False, op_sys = "linux"):
       #import os
       #os.chmod('/usr/local/bin/chromedriver', 0o755)
        """
        headerless:bool
            True if we don't want to display the webpage
            this is the default
            not displaying the webpage makes it faster
        """
        if op_sys == "windows":
            driver_loc = "chromedriver_win32/chromedriver.exe"
        elif op_sys == "linux":
            homedir = os.path.expanduser("~")
            driver_loc = "chromedriver_liux64/chromedriver"
            from pdb import set_trace as s 
            #s()
            driver_loc = f"/usr/local/bin/chromedriver"
        else:
            raise Exception("Only handled for linux and windows currently")
        self.s = Service(driver_loc)
        self.headerless = headerless
        self.op_sys = op_sys
        
    def get_http(self, http_address):
        self.options = webdriver.ChromeOptions()
        if self.headerless == True:
            self.options.add_argument("--headless")
            self.options.add_argument('--window-size=1920,1080')
        max_tries = 3 #maximum number of tries at getting the url
        tries = 0
        while tries < max_tries:
            try:
                self.driver = webdriver.Chrome(service=self.s, options = self.options)
                self.driver = webdriver.Chrome(ChromeDriverManager().install(), options = self.options)
                self.driver.get(http_address)
                tries = max_tries #set tries equal to max to escape the loop
            except:
                tries += 1 #add attempt
        
    def close(self):
        self.driver.close()
        
def check_valid_odds_type(odds_type:str):
    valid_types = ["lines", "odds"]
    valid = True
    if odds_type not in valid_types:
        raise Exception(f"{odds_type} not valid. must be one of {[i for i in valid_types]}")
        
class Game:
    def __init__(self, element, labels):
        self.game_element = element
        self.labels = labels
        
    def retrieve_data(self):
        info = {}
        data_elements = self.game_element.find_elements(By.CSS_SELECTOR, "td")
        for c, data_item in enumerate(data_elements):
            info[self.labels[c]] = data_item.text
        self.info = info
        return info
        
class YearTable:
    def __init__(self, element):
        self.table_element = element
        self.colnames_retrieved = False
        self.games_retrieved = False
        
    def get_title(self):
        table_title_element = self.table_element.find_element(By.CSS_SELECTOR, "caption")
        self.title = table_title_element.text
        self.year = int(self.title[-4:])
        
    def get_col_names(self):
        column_names_element = self.table_element.find_element(By.CSS_SELECTOR, "thead")
        column_names_elements = column_names_element.find_elements(By.CSS_SELECTOR, "th")
        colnames = [name.text for name in column_names_elements]
        #st()
        self.column_names = colnames
        self.colnames_retrieved = True
        
    def get_games(self):
        if self.colnames_retrieved == False:
            self.get_col_names()
        self.body = self.table_element.find_element(By.CSS_SELECTOR, "tbody")
        self.games = [Game(element, self.column_names) for element in self.body.find_elements(By.CSS_SELECTOR, "tr")]
        self.games_retrieved = True
        
    def get_data(self):
        if self.games_retrieved == False:
            self.get_games()
        data = []
        for game in self.games:
            data.append(game.retrieve_data())
        return data
        
class WeekPage:
    def __init__(self, week_num:int=1, odds_type:str="odds"):
        check_valid_odds_type(odds_type)
        self.odds_type = odds_type
        self.week_num = week_num
        self.url = f"https://thefootballlines.com/nfl-{odds_type}/week-{week_num}"
        self.d = DriverHandler()
        self.page_retrieved = False
        
    def get_url(self):
        self.d.get_http(self.url)
        self.page_retrieved = True
        self.d.driver.fullscreen_window()
        time.sleep(0.5)
    
    def get_table(self, year:int):
        if self.page_retrieved == False:
            self.get_url()
        self.tables = [YearTable(i) for i in self.d.driver.find_elements(By.CSS_SELECTOR, "table")]
        found_table = False
        for table in self.tables:
            table.get_title()
            if table.year == year:
                my_table = table
                found_table = True
        if found_table == False:
            raise Exception(f"Table not found for year {year} week {self.week_num}")
        return my_table
    
    def get_all_tables(self):
        if self.page_retrieved == False:
            self.get_url()
        self.tables = [YearTable(i) for i in self.d.driver.find_elements(By.CSS_SELECTOR, "table")]

class Scraper:
    def __init__(self):
        if os.path.exists(f"Data") == False:
            os.mkdir("Data")
    def scrape(self, week, year):
        if not os.path.exists(f"Data/{year}"):
            os.mkdir(f"Data/{year}")
        if not os.path.exists(f"Data/{year}/{week}"):
            os.mkdir(f"Data/{year}/{week}")
        for odds_type in ["lines", "odds"]:
            page = WeekPage(week, odds_type = odds_type)
            table = page.get_table(year)
            info = table.get_data()
            #st()
            for c, item in enumerate(info):
                save_to_json(item, f"Data/{year}/{week}/{c}_{odds_type}.json")
            
    def scrape_all(self):
        weeks = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
        years = [2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021]
        for year in years:
            if os.path.exists(f"Data/{year}"):
                most_recent_week = max([int(i) for i in os.listdir(f"Data/{year}")])
                shutil.rmtree(f"Data/{year}/{most_recent_week}") #remove the most recent week from the data directory
            else:
                most_recent_week = 0
            for week in weeks:
                if week >= most_recent_week:
                    self.scrape(week=week, year=year)
        self.scrape(week=18, year=2021)
#===================
#TESTS

test_driver = 0
test_table = 0
test_week_page = 0
test_row = 0
test_table_title = 0
test_scraper = 1
scrape = 0
test_odds_page = 0

if test_driver == True:
    d = DriverHandler()
    d.get_http("https://thefootballlines.com/nfl-lines/week-18")
    print("Done")
    
if test_table == True:
    w = WeekPage(1)
    w.get_all_tables()
    table = w.tables[0]
    table.get_games()
    print(table.get_data())
    
if test_week_page == True:
    w = WeekPage(1)
    w.get_all_tables()
    for table in w.tables:
        table.get_title()
        print(table.title)
        
if test_row == True:
    w = WeekPage(1)
    w.get_table(2021)
    table = w.tables[0]
    table.get_games()
    game = table.games[0]
    game.retrieve_data()
    for key in game.info.keys():
        print(f"{key}: {game.info[key]}")
        
if test_table_title == True:
    w = WeekPage(1)
    w.get_all_tables()
    table = w.tables[0]
    table.get_title()
    print(table.title)

if test_scraper == True:
    s = Scraper()
    s.scrape(3, 2020)
    
if scrape == True:
    s = Scraper()
    s.scrape_all()
    