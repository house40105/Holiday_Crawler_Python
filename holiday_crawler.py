import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time


date_format= '%Y%m%d'


def get_html(url):
    # Send a request to get HTML content from the specified URL.
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'TE': 'Trailers'
    }

    try:
        # Send the request with specified headers
        response = requests.get(url,headers=headers)
        # Check if the request was successful
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")
        return None

def extract_data_from_row(row):
    # Extract data from a row in the table.
    columns = row.find_all('td')
    holiday_column = columns[2]

    # Extract data from each column
    day = columns[0].text.strip()
    date = columns[1].find('time')['datetime']
    holiday = holiday_column.find('a').text.strip()
    holiday_type = columns[3].text.strip()
    comments = columns[4].text.strip()

    # Convert date string to datetime object
    date = datetime.strptime(date, '%Y-%m-%d')

    return {
        # 'Day': datetime.strptime(date, date_format).strftime('%A'),
        'Day': date.strftime('%A'),
        'Date': date.strftime(date_format),
        'Holiday': holiday,
        'Type': holiday_type,
        'Is Holiday': check_is_holiday(date,holiday_type),
        'Comments': comments
    }

def scrape_holidays_for_year(year):
    # Scrape holiday information for a specific year based on the provided year.
    holiday_url = f"https://www.officeholidays.com/countries/taiwan/{year}"
    print(holiday_url)

    data = {
        'Day': [],
        'Date': [],
        'Holiday': [],
        'Type': [],
        'Is Holiday': [],
        'Comments': []
    }

    # Retrieve HTML content from the holiday URL
    html = get_html(holiday_url)
    # If HTML content is retrieved successfully, parse it using BeautifulSoup
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        # Extract holiday data from the parsed HTML
        for row in soup.select('tbody tr'):
            holiday_data = extract_data_from_row(row)
            for key, value in holiday_data.items():
                data[key].append(value)

    return pd.DataFrame(data)

def add_compensated_holidays(original_holidays):
    # Process compensated holidays by adding them based on the presence of the "Compensated by" string in the Comments column.
    compensated_holidays = pd.DataFrame(columns=original_holidays.columns)

    for _, row in original_holidays.iterrows():
        # Check if the Comments column contains the "Compensated by" string
        if "Compensated by" in row['Comments']:
            compensated_date_str = extract_compensated_date(row['Comments'],datetime.strptime(row['Date'],date_format).year)
            compensated_date = pd.to_datetime(compensated_date_str, errors='coerce')

             # If the extracted date is valid, add the compensated holiday
            if pd.notna(compensated_date):
                compensated_data = {
                    'Day': compensated_date.strftime('%A'),
                    'Date': compensated_date.strftime(date_format),
                    'Holiday': "Compensatory workday",
                    'Type': "Compensated",
                    'Is Holiday': check_is_holiday(compensated_date,"Compensated"),
                    'Comments': f"Makeup day for {row['Holiday']}"
                }

                compensated_holidays = pd.concat([compensated_holidays, pd.DataFrame([compensated_data])], ignore_index=True)
                compensated_holidays['Is Holiday'] = compensated_holidays['Is Holiday'].astype("boolean")
            else:
                print("ERROR: compensated_date NaT")
    # Combine the original holidays and compensated holidays
    result_df = pd.concat([original_holidays, compensated_holidays], ignore_index=True)
    
    return result_df

def extract_compensated_date(comments, current_year):
    # Extract the compensated date from comments using regular expressions and add the current year.

    try:
        str_arr = comments.split(' ')[-3:]

        if str_arr:
            if not "." in str_arr[0]:
                str_arr[0] = str_arr[0] +"."
            if "." in str_arr[1]:
                str_arr[1] = str_arr[1].replace(".", "")
            if str_arr[1].isnumeric():
                str_arr[1], str_arr[2] = str_arr[2], str_arr[1]

            result_str = ' '.join(str_arr)
        return f"{result_str} {current_year}"
    except Exception as e:
        print(f"Error occurred while extracting compensated date from comments {comments}: {e}")

    return None

def check_is_holiday(date, holiday_type):
    # Check if a given date is a holiday based on its type.
    holiday_list=["National Holiday", "Extended Weekend"]

    if holiday_type in holiday_list:
        return True

    if "Compensated" in holiday_type:
        return False

    if "Not A Public Holiday" in holiday_type:
        date_obj = pd.to_datetime(date, errors='coerce')
        is_weekend = (date_obj.weekday() >= 5)

        return is_weekend

    return False
    

def create_extended_data(date_obj, offset_days, holiday_name):
    # Create extended weekend data for a given holiday.

    extended_date_obj = date_obj + pd.DateOffset(days=offset_days)
    extended_data = pd.DataFrame({
        'Day': extended_date_obj.strftime('%A'),
        'Date': extended_date_obj.strftime(date_format),
        'Holiday': "Extended Weekend",
        'Type': "Extended Weekend",
        'Is Holiday': True,
        'Comments': f"Extended Weekend for {holiday_name}"
    },index=[0])
    extended_data['Is Holiday'] = extended_data['Is Holiday'].astype("boolean")
    return extended_data

def add_extended_days(original_holidays):
    # Add extended weekend information to the DataFrame.
    extended_holidays = pd.DataFrame(columns=original_holidays.columns)

    for _, row in original_holidays[original_holidays['Is Holiday']].iterrows():
        date_obj = pd.to_datetime(row['Date'], errors='coerce')

        # Extended Weekend for Friday
        if "Friday" in row['Day']:
            for i in range(2):  # Saturday and Sunday
                extended_date_str = date_obj + pd.DateOffset(days=i + 1)
                if extended_date_str.strftime(date_format) not in original_holidays['Date'].values:
                    extended_data = create_extended_data(date_obj, i + 1, row['Holiday'])
                    extended_holidays = pd.concat([extended_holidays, extended_data], ignore_index=True)

        # Extended Weekend for Monday
        elif "Monday" in row['Day']:
            for i in range(2):  # Sunday and Saturday
                extended_date_str = date_obj - pd.DateOffset(days=i + 1)
                if extended_date_str.strftime(date_format) not in original_holidays['Date'].values:
                    extended_data = create_extended_data( date_obj, -(i + 1), row['Holiday'])
                    extended_holidays = pd.concat([extended_holidays, extended_data], ignore_index=True)

    result_df = pd.concat([original_holidays, extended_holidays], ignore_index=True)
    return result_df

def export_to_csv(dataframe, filename="/home/miot/train_data/holiday/out_python.csv"):

    try:
        dataframe.to_csv(filename, index=False)
        print(f"DataFrame saved {filename}")
    except Exception as e:
        print(f"Error occurred while saving DataFrame to {filename}: {e}")

def generate_year_list(pre_years=5, foll_years=1):
    current_year = datetime.now().year

    years_list = list(map(str, range(current_year - pre_years, current_year + foll_years + 1)))

    return years_list



def main():
    # years = ["2023","2024","2022","2025","2029","2021"]
    years = generate_year_list()
    result_df=[]
    
    print("years =",years)

    for year in years:
        result_df.append(scrape_holidays_for_year(year))
        time.sleep(1)

    all_years_df = pd.concat(result_df, ignore_index=True)
    all_years_df['Is Holiday'] = all_years_df['Is Holiday'].astype("boolean")

    all_years_df = add_compensated_holidays(all_years_df)
    all_years_df = add_extended_days(all_years_df)
    df_sorted = all_years_df.sort_values(by='Date')

    export_to_csv(df_sorted)
    

if __name__ == "__main__":
    main()
