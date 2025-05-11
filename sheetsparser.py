#importing necessary modules
import gspread
from google.oauth2.service_account import Credentials  #authentication
import logging # importing logging module
import os #os module
from webscraping import PremierLeagueScraper  # Importing the PremierLeagueScraper class from the webscraping file
from dotenv import load_dotenv #dotenv
load_dotenv()#load dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
class SheetsManager:
    def __init__(self):
        #initializing scope,cred,client
        self.scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        self.creds = Credentials.from_service_account_file(
            'crested-pursuit-457714-c8-012a42374576.json',
            scopes=self.scope
        )
        self.client = gspread.authorize(self.creds)
        self.sheet1 = None  # Initialize sheet1
        self.sheet2 = None  # Initialize sheet2

    def get_or_create_sheet(self, title="Premier League Statistics for 2024-2025 Football Season"):
        try: #checking if the spreadsheet exists
            spreadsheet = self.client.open(title)
            logging.info(f"Spreadsheet '{title}' already exists.") #Log message if spreadsheet exists
            # Setting references to existing sheets
            self.sheet1 = spreadsheet.worksheet("Overview Table")
            self.sheet2 = spreadsheet.worksheet("Goalkeepers Table")

        except gspread.exceptions.SpreadsheetNotFound:
            spreadsheet = self.client.create(title)
            logging.info(f"Spreadsheet '{title}' created successfully.")

            # Share with email
            email_address = os.getenv("MY_EMAIL")
            if email_address:
                spreadsheet.share(email_address, perm_type='user', role='writer')
            # Create and assign sheets
            sheet1 = spreadsheet.sheet1
            sheet1.update_title("Overview Table")
            sheet2 = spreadsheet.add_worksheet(title="Goalkeepers Table", rows="50", cols="30")
            self.sheet1 = sheet1
            self.sheet2 = sheet2

            logging.info("Sheets initialized and renamed.")

        return spreadsheet

    def add_sheets(self, scraper):
        """
        Function flattens the structure of the dataframe(turning them into lists) and afterwards updatting the sheet
        """
        df = scraper.df  # This is the dataframe for the overview table
        if not df.empty and self.sheet1:  # Ensure sheet1 exists
            sheetdata = [df.columns.values.tolist()] + df.values.tolist()
            self.sheet1.update(range_name="A1", values=sheetdata)  # Update the sheet with data from df
            logging.info("Overview Table updated in Google Sheets.")

        df2 = scraper.df2  # df2 from the webscraping file
        if not df2.empty and self.sheet2:
            # Flatten the MultiIndex headers for suit spreahseet format
            flat_headers = [' '.join(col).strip() for col in df2.columns.values]
            # Combine headers and data
            all_data = [flat_headers] + df2.values.tolist()
            try:
                self.sheet2.clear()  #Clear old content if any
                self.sheet2.update(range_name="A1", values=all_data) #adding data to the sheet
                logging.info("Goalkeepers Table updated in Google Sheets with flattened headers.") # logging info
            except Exception as e:
                logging.error(f"Failed to update Goalkeepers sheet:{e}")

# Main script
if __name__ == "__main__":
    driver_path = r"C:\\Users\\HP\\Downloads\\chromedriver-win64 (1)\\chromedriver-win64\\chromedriver.exe" #driver path
    scraper = PremierLeagueScraper(driver_path)  # Initialize scraper
    scraper.scrape_overviewtable()  # Scrape overview table
    scraper.scrape_squadgoalkeeper()  # Scrape goalkeeper table

    sheet_manager = SheetsManager()
    spreadsheet = sheet_manager.get_or_create_sheet()  # Get or create the sheet
    sheet_manager.add_sheets(scraper)  # Add data from scraper to sheets
