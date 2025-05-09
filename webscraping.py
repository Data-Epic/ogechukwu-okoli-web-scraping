#importing necessary modules
import gspread
from google.oauth2.service_account import Credentials #authentication
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()
# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s', #logging  message style
    filename='web-scraping.log', #log file name
    filemode='w'
)
logger = logging.getLogger(__name__)

# Google Sheets API authentication
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file('crested-pursuit-457714-c8-012a42374576.json', scopes=scope)
client = gspread.authorize(creds)

# Create new spreadsheet
spreadsheet = client.create("2024 - 2025 Premier League Statistics")
logging.info("Spreadsheet created successfully.")
email_address = os.getenv("MY_EMAIL")
#sharing file to google drive
spreadsheet.share(email_address, perm_type='user', role='writer')
#creating sheets
sheet1 = spreadsheet.sheet1
#renaming default shhet
sheet1.update_title("Overview Table")
logging.info("Default sheet renamed.")

# Add a second worksheet
sheet2 = spreadsheet.add_worksheet(title="Goalkeepers Table", rows="50", cols="30")
logging.info("Second worksheet added.")
#Base class
class PremierLeagueScraper:
    def __init__(self, driver_path):# initiallization
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

        service = Service(driver_path) #initializing webdriver path
        self.driver = webdriver.Chrome(service=service, options=options)
        logger.info("Initialized Chrome WebDriver.") # logging .info

    def scrape_overviewtable(self):
        #try,except block to scrape data
        try:
            self.driver.get("https://fbref.com/en/comps/9/Premier-League-Stats")
            logger.info("Navigated to Premier League stats page.")
            time.sleep(15) # Allowing website time to load
        except Exception as e: # excepions that may occur when loading the website
            logger.error(f"Failed to load page: {e}") # error message
            return
        #try,except block to access table,header and rows in the overview table
        try:
            table1 = self.driver.find_element(By.ID, "results2024-202591_overall") # accessing table id
            logger.info("Located the overview stats table.")

            headers = [th.text for th in table1.find_element(By.TAG_NAME, "thead").find_element(By.TAG_NAME, "tr").find_elements(By.TAG_NAME, "th")]# table header
            rows = table1.find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr")# row data
            data = []

            # looping through each row
            for i, row in enumerate(rows):
                rk = row.find_element(By.TAG_NAME, "th").text # acessing the rank located in the thead
                cells = [td.text for td in row.find_elements(By.TAG_NAME, "td")] # other row data located in table data tag
                full_row = [rk] + cells # string concatation

                #loop to handle insincsitent row and column data if any
                if len(full_row) != len(headers):
                    logger.warning(f"Row {i} has {len(full_row)} values but expected {len(headers)}. Skipping.")# warning message
                    continue
                data.append(full_row) # appending rows if they match the number of columns available

            df = pd.DataFrame(data, columns=headers)#creating a dataframe for the overview table
            logger.info("DataFrame created from table rows.")# loging message
            # renaming columns accprding tp the glossary avaialable on the website
            df.rename(columns={
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
            logger.info("Columns renamed successfully.")
            # dropping the last column(empty)
            if "Notes" in df.columns:
                df.drop(columns="Notes", inplace=True)
                logger.info("Dropped 'Notes' column.")

            # Check if df is empty before updating
            if not df.empty:
                sheetdata = [df.columns.values.tolist()] + df.values.tolist() # converting the dataframe to a list of values for spreadsheet to be updated
                sheet1.update(sheetdata)# update sheet1

                logger.info("Data updated in the 'Overview Table'.")
            else:
                logger.warning("No data to update in the 'Overview Table'.")
        except Exception as e:
            logger.error(f"An error occurred during scraping Overview table: {e}")

    def scrape_squadgoalkeeper(self):
        try:
            self.driver.get("https://fbref.com/en/comps/9/Premier-League-Stats")
            logger.info("Navigated to Premier League stats page for goalkeepers.")
            time.sleep(15)
            # accessing table Squad goalkeeper table
            table2 = self.driver.find_element(By.ID, "stats_squads_keeper_for")
            logger.info("Keeper stats table located.")
            #accessing the over head row
            over_header_row = table2.find_element(By.CSS_SELECTOR, "tr.over_header")
            thead_rows = table2.find_element(By.TAG_NAME, "thead").find_elements(By.TAG_NAME, "tr") # finding all rows in the table head tag

            header_cells = over_header_row.find_elements(By.TAG_NAME, "th")# finding the table heads i.e the actual names of the over head rows
            cells_overhead = [cell.text.strip() for cell in header_cells]# looping through the row to get each row name

            inner_overhead = [] #inner heade names
            unwanted_text = ['', 'Playing Time', 'Performance', 'Penalty Kicks'] # remving unwanted rows data
            for row in thead_rows: #looping through thead_rows to get the inner header names
                header_cells2 = row.find_elements(By.TAG_NAME, "th")# locating the tag that contains the inner header names
                for cell in header_cells2:
                    text = cell.text.strip() # names of the headers
                    if text not in unwanted_text: # if statement for data validation
                        inner_overhead.append(text) # appending cwanted lis of data

            logger.debug(f"Top headers: {cells_overhead}")
            logger.debug(f"Inner headers: {inner_overhead}")
            '''
            Lines 161 -166 checks if the correct overhead header and inner headers are in the desired numbers
            columns = [] for tuples of overhead headers and theircorressponsing roows
            '''
            if len(cells_overhead) >= 4 and len(inner_overhead) >= 21:
                columns = []
                columns += [(cells_overhead[0], col) for col in inner_overhead[0:2]] #for overhead header 1 grouping and their corresspomding rows using their positions
                columns += [(cells_overhead[1], col) for col in inner_overhead[2:6]]  #for overhead header 2 grouping and their corresspomding rows using their positions
                columns += [(cells_overhead[2], col) for col in inner_overhead[6:16]] #for overhead header 3 grouping and their corresspomding rows using their positions
                columns += [(cells_overhead[3], col) for col in inner_overhead[16:]] #for overhead header 4 grouping and their corresspomding rows using their positions

                multi_index = pd.MultiIndex.from_tuples(columns)#method used to create a MultiIndex (a hierarchical index) in a Pandas DataFrame or Series from a list of tuples.

                row_data = table2.find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr") # row data fro Squad Goal keeper table
                dat_a = [] # list for each list
                for row in row_data: #loop for accessing each row
                    squaddata = row.find_element(By.TAG_NAME, "th").text# accessing the rowdata that is stored in the th tag
                    cells = [td.text for td in row.find_elements(By.TAG_NAME, "td")]# other row data located in table data tag
                    full_row = [squaddata] + cells# string concatation
                    dat_a.append(full_row)

                df2 = pd.DataFrame(dat_a, columns=multi_index)# creating dataframe for second table
                logger.info("Goalkeeper DataFrame created.")
                df2.to_csv("goalkeepers.csv") # saving df2 to a csv file
                logger.info("Goalkeeper csv file created and saved.")
        except Exception as e: # error message
            logger.error(f"An error occurred during goalkeeper scraping: {e}")
        finally:
            self.driver.quit()# closing the webdriver
            logger.info("Driver closed.") # logging message indicating the closure of the webdriver
# main script
if __name__ == "__main__":
    driver_path = r"C:\\Users\\HP\\Downloads\\chromedriver-win64 (1)\\chromedriver-win64\\chromedriver.exe"
    scraper1 = PremierLeagueScraper(driver_path)
    scraper1.scrape_overviewtable()#scraping the overview table
    scraper2 = PremierLeagueScraper(driver_path)
    scraper2.scrape_squadgoalkeeper()#scraping the squadgoalkeeper table
    #sheet url = https://docs.google.com/spreadsheets/d/1Hd2NzO33-VbKuKOgQ77CCF5HKmG1mefe6GWE3ZWt2g4
    #print(spreadsheet.url)