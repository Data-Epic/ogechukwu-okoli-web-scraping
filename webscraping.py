#importing necessary modules
import logging
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='web-scraping.log', # logging file
    filemode='w' #mode for writing file
)
logger = logging.getLogger(__name__)
url = "https://fbref.com/en/comps/9/Premier-League-Stats"
# Base class for web scraping
class PremierLeagueScraper:
    def __init__(self, driver_path):
        # options to imitate human behaviour
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--incognito")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/135.0.0.0 Safari/537.36")

        service = Service(driver_path)#initializing webdriver path
        self.driver = webdriver.Chrome(service=service, options=options)
        logger.info("Initialized Chrome WebDriver.")# logging .info

    def scrape_overviewtable(self):
        #try,except block to scrape data
        try:
            self.driver.get(url)
            logger.info("Navigated to Premier League stats page.")
            time.sleep(15)# sleeping time for website to laod
        except Exception as e: # exception if the driver failed to navigate to the webpage
            logger.error(f"Failed to load page: {e}") #logging error
            return #output
        # try except to slocat the block
        try:
            table1 = self.driver.find_element(By.ID, "results2024-202591_overall") # accessing table id
            logger.info("Located the overview stats table.") #logging message if the table has been located

            headers = [th.text for th in table1.find_element(By.TAG_NAME, "thead").find_element(By.TAG_NAME, "tr").find_elements(By.TAG_NAME, "th")]# headers for the overview table
            rows = table1.find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr")# accessing the row data
            data = [] # list for holding the rows
             # looping through each row
            for i, row in enumerate(rows):
                rk = row.find_element(By.TAG_NAME, "th").text# acessing the rank located in the thead
                cells = [td.text for td in row.find_elements(By.TAG_NAME, "td")]# other row data located in table data tag
                full_row = [rk] + cells # string concatation

                if len(full_row) != len(headers): #loop to handle inconsistent row and column data if any
                    logger.warning(f"Row {i} has {len(full_row)} values but expected {len(headers)}. Skipping.")# warning message
                    continue
                data.append(full_row) #adding scrapped row to the list

            self.df = pd.DataFrame(data, columns=headers)# dataframe for overview table
            logger.info("Overview DataFrame created.")# logger info for created datafram
            self.df.rename(columns={ #renaming the columns for the overview table according to the glossary
                "Rk": "Rank",
                "Squad": "Team",
                "MP": "Matches Played",
                "W": "Wins",
                "D": "Draws",
                "L": "Losses",
                "GF": "Goals For",
                "GA": "Goals Against",
                "GD": "Goal Difference",
                "Pts": "Points",
                "Pts/MP": "Points/Match",
                "xG": "Expected Goals",
                "xGA": "Expected Goals Allowed",
                "xGD": "Expected Goal Difference",
                "xGD/90": "xGD per 90",
                "Last 5": "Last 5 Matches",
                "Attendance": "Attendance per Game",
                "Team Top Scorer": "Top Scorer",
                "Goalkeeper": "Main Goalkeeper"
            }, inplace=True)
            logger.info("Columns renamed successfully.") #info message

            if "Notes" in self.df.columns:  #checking if 'Notes' is in the dataframe
                self.df.drop(columns="Notes", inplace=True)# dropping the last column(empty)
                logger.info("Dropped 'Notes' column.")
        except Exception as e:
            logger.error(f"An error occurred during scraping Overview table: {e}")

    def scrape_squadgoalkeeper(self):
        # scraping goalkeepers table
        try:
            self.driver.get(url) #initializing url
            logger.info("Navigated to Premier League stats page for goalkeepers.")# info message if successfully located goalkeepers table
            time.sleep(15)

            table2 = self.driver.find_element(By.ID, "stats_squads_keeper_for") #
            logger.info("Keeper stats table located.")
            #accessing the over head row
            over_header_row = table2.find_element(By.CSS_SELECTOR, "tr.over_header")
            thead_rows = table2.find_element(By.TAG_NAME, "thead").find_elements(By.TAG_NAME, "tr")# finding all rows in the table head tag
            header_cells = over_header_row.find_elements(By.TAG_NAME, "th")# finding the table heads i.e the actual names of the over head rows
            cells_overhead = [cell.text.strip() for cell in header_cells]# looping through the row to get each row name

            # Scrape the inner headers before
            inner_overhead = []
            unwanted_text = ['', 'Playing Time', 'Performance', 'Penalty Kicks']# removing unwanted rows data
            for row in thead_rows: #looping through thead_rows to get the inner header names
                header_cells2 = row.find_elements(By.TAG_NAME, "th")# locating the tag that contains the inner header names
                for cell in header_cells2:
                    text = cell.text.strip()# names of the headers
                    if text not in unwanted_text:# if statement for data validation
                        inner_overhead.append(text)# appending wanted list of data
            '''
            Lines 161 -166 checks if the correct overhead header and inner headers are in the desired numbers
            columns = [] for tuples of overhead headers and theircorressponsing roows
            '''
            # Ensure we have the correct number of headers
            if len(cells_overhead) >= 4 and len(inner_overhead) >= 21:
                columns = []
                columns += [(cells_overhead[0], col) for col in inner_overhead[0:2]] #for overhead header 1 grouping and their corresspomding rows using their positions
                columns += [(cells_overhead[1], col) for col in inner_overhead[2:6]] #for overhead header 2 grouping and their corresspomding rows using their positions
                columns += [(cells_overhead[2], col) for col in inner_overhead[6:16]] #for overhead header 3 grouping and their corresspomding rows using their positions
                columns += [(cells_overhead[3], col) for col in inner_overhead[16:]] #for overhead header 4 grouping and their corresspomding rows using their positions

                #method used to create a MultiIndex (a hierarchical index) in a Pandas DataFrame or Series from a list of tuples.
                multi_index = pd.MultiIndex.from_tuples(columns)

                # Scraping rows data in the table
                row_data = table2.find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr")
                dat_a = []
                for row in row_data:
                    squaddata = row.find_element(By.TAG_NAME, "th").text# accessing the rowdata that is stored in the th tag
                    cells = [td.text for td in row.find_elements(By.TAG_NAME, "td")]# other row data located in table data tag
                    full_row = [squaddata] + cells# string concatation
                    dat_a.append(full_row)


                # Create the DataFrame for table2
                self.df2 = pd.DataFrame(dat_a, columns=multi_index)
                #renaming columns
                self.df2.rename(columns={
                ('', '# Pl'): ('', 'Number of Players'),
                ('Playing Time','MP'): ('Playing Time', 'Matches Played'),
                ('Playing Time','90s'): ('Playing Time', '90s Played'),
                ('Playing Time','Min'): ('Playing Time', 'Minutes'),
                ('Performance','GA'): ('Performance', 'Goals Against'),
                ('Performance','GA90'): ('Performance', 'Goals Against/90'),
                ('Performance','SoTA'): ('Performance', 'Shots on Target Against'),
                ('Performance','Save%'): ('Performance', 'Save Percentage'),
                ('Performance','CS%'): ('Performance', 'Clean Sheet %'),
                ('Performance','W'): ('Performance', 'Wins'),
                ('Performance','D'): ('Performance', 'Draws'),
                ('Performance','L'): ('Performance', 'Losses'),
                ('Performance','CS'): ('Performance', 'Clean Sheets'),
                ('Penalty Kicks','PKatt'): ('Penalty Kicks', 'Pen Kicks Attempted'),
                ('Penalty Kicks','PKA'): ('Penalty Kicks', 'Pen Kicks Allowed'),
                ('Penalty Kicks','PKsv'): ('Penalty Kicks', 'Pen Kicks Saved'),
                ('Penalty Kicks','PKm'): ('Penalty Kicks', 'Pen Kicks Missed'),
                ('Penalty Kicks','Save%'): ('Penalty Kicks', 'Save % (PK)')
            }, inplace=True)
                # Log DataFrame preview and save it
                logger.info("Renaming files successful")
                self.df2.to_csv("goalkeepers.csv")
                logger.info("Goalkeeper CSV file created and saved.")
                logger.info(f"First few rows of DataFrame:\n{self.df2.head()}")

        except Exception as e:
            logger.error(f"An error occurred during goalkeeper scraping: {e}")
        finally:
            self.driver.quit()# closing webdriver
            logger.info("Driver closed.")# logging message indicating the closure of the webdriver
