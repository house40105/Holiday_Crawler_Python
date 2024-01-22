# Holiday_Crawler_Python

`holiday_crawler.py` is a Python script designed to scrape holiday information for Taiwan from the [Office Holidays](https://www.officeholidays.com/) website. The script retrieves data for multiple years, processes and enhances it, and finally exports the result to a CSV file.

### Features
1. Scraping Holidays by Year
   * The script fetches holiday data for specified years from the Office Holidays website.
   * It utilizes the requests library for making HTTP requests.
   * HTML content parsing is performed using BeautifulSoup, a powerful library for web scraping in Python.
2. Compensated Holidays Handling
   * Compensated holidays are identified based on the presence of the "Compensated by" string in the Comments column.
   * The script extracts and adds compensated holidays, considering the original holiday's date.
3. Extended Weekends Handling
   * Extended weekends are added for Fridays and Mondays to provide additional context about long weekends.
   * The script checks for Fridays and Mondays in the original dataset and adds corresponding extended weekends.
4. Export to CSV
   * The final processed data is exported to a CSV file for further analysis or integration with other applications.

### Dependencies
* **`requests`:** For making HTTP requests.  
* **`BeautifulSoup`:** For parsing HTML content.  
* **`pandas`:** For data manipulation and analysis.  
* **`datetime`:** For handling date-related operations.  
* **`time`:** For introducing delays during web scraping.

### Usage
1. Clone the Repository:
   ```sh
   git clone https://github.com/house40105/Holiday_Crawler_Python.git
   cd Holiday_Crawler_Python
   ```
2. Install Dependencies:
   ```sh
   pip install requests beautifulsoup4 pandas
   ```
3. Run the Script:
   ```sh
   python holiday_crawler.py
   ```
4. Output:
   * The script will generate a CSV file named out_python.csv in the specified directory.

### Configuration
* You can customize the number of years to scrape by modifying the `generate_year_list` function parameters.
* Adjust the output filename and directory in the `export_to_csv` function.

### Notes
* Ensure proper internet connectivity during execution as the script fetches data from an external website.
* Respect the website's terms of service and scraping policies.
