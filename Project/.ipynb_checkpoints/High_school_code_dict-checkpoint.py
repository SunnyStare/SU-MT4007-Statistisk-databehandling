import os
import requests
import pandas as pd
from collections import defaultdict
from io import BytesIO

###############################################################################################
class DataSourceAndParameters:
    """
    A class that stores URLs and parameters for data sources and filtering criteria.
    """

    # URLs for final admission statistics
    antagning_info = {
        2020: "https://gymnasieantagningen.storsthlm.se/media/yiobheds/slutantagningsresultat-2020.xlsx",
        2021: "https://gymnasieantagningen.storsthlm.se/media/pvob5j1l/slutantagningsresultat-2021.xlsx",
        2022: "https://gymnasieantagningen.storsthlm.se/media/xhvap2io/slutantagning-2022.xlsx",
        2023: "https://gymnasieantagningen.storsthlm.se/media/zksfvysz/slutantagningsresultat-2023.xlsx",
        2024: "https://gymnasieantagningen.storsthlm.se/media/opnfe50w/slutantagningsresultat-2024.xlsx",
    }

    # Directory for storing downloaded files
    antagning_dir = "antagningsstatistik"

    # Filtering parameters
    years = list(range(2020, 2025))  # Ensure it's a list, not a range object
    kommuner = [
        "Botkyrka", "Danderyd", "Haninge", "Huddinge", "Järfälla", "Lidingö", "Nacka", "Sollentuna", "Solna",
        "Stockholm", "Sundbyberg", "Södertälje", "Tyresö", "Täby", "Upplands Väsby", "Vallentuna", "Vaxholm", "Värmdö"
    ]
    program_keyword = "Naturvetenskapsprogrammet"

    # Excluded keywords to filter out unwanted programs
    excluded_keywords = ["estetiska", "samhälle", "Hållbar utveckling", "Idrott", "Musik", "Dans", "Miljö", "Innovation"]

    # URLs for graduation statistics
    avgang_info = {
        2020: "https://siris.skolverket.se/siris/reports/export_api/runexport/?pFormat=xls&pExportID=88&pAr=2020&pLan=&pKommun=&pHmantyp=&pUttag=null&pToken=29A296189217EE63E06311BA650A8DC5&pFlikar=1&pVerkform=21",
        2021: "https://siris.skolverket.se/siris/reports/export_api/runexport/?pFormat=xls&pExportID=88&pAr=2021&pLan=&pKommun=&pHmantyp=&pUttag=null&pToken=29A296189217EE63E06311BA650A8DC5&pFlikar=1&pVerkform=21",
        2022: "https://siris.skolverket.se/siris/reports/export_api/runexport/?pFormat=xls&pExportID=88&pAr=2022&pLan=&pKommun=&pHmantyp=&pUttag=null&pToken=29A296189217EE63E06311BA650A8DC5&pFlikar=1&pVerkform=21",
        2023: "https://siris.skolverket.se/siris/reports/export_api/runexport/?pFormat=xls&pExportID=88&pAr=2023&pLan=&pKommun=&pHmantyp=&pUttag=null&pToken=29A296189217EE63E06311BA650A8DC5&pFlikar=1&pVerkform=21",
        2024: "https://siris.skolverket.se/siris/reports/export_api/runexport/?pFormat=xls&pExportID=88&pAr=2024&pLan=&pKommun=&pHmantyp=&pUttag=null&pToken=29A296189217EE63E06311BA650A8DC5&pFlikar=1&pVerkform=21",
    }

    @classmethod
    def get_avgang_parameters(cls):
        """
        Returns relevant parameters for the graduation dataset.
        """
        return {
            "sheet_name": "Naturvetenskapsprogrammet",
            "column_name": "GBP för elever med examen"
        }

data = DataSourceAndParameters()

##############################################################################################

def read_in_data_antagningsdel(data_antagning_info, download_dir):
    # List to store dictionaries (one per row)
    data_list = []
    
    # Download and read Excel files
    for year, download_url in data_antagning_info.items():
        file_name = f"{download_dir}/Slutantagningsresultat_{year}.xlsx"
    
        # Check if the file already exists
        if not os.path.exists(file_name):
            try:
                # Download the file
                response = requests.get(download_url)
                response.raise_for_status()
                with open(file_name, "wb") as file:
                    file.write(response.content)
                print(f"Downloaded: {file_name}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to download {file_name}: {e}")
                continue  # Skip this year if download fails
        else:
            print(f"File already exists: {file_name}")
    
        # Read the Excel file
        try:
            df_antagning = pd.read_excel(file_name)
            df_antagning["Year"] = year  # Add a column for the year
    
            # Convert DataFrame to list of dictionaries
            data_list.extend(df_antagning.to_dict(orient="records"))
    
        except Exception as e:
            print(f"Failed to read {file_name}: {e}")
            
    return data_list
    
#######################################################################################

def filter_data(data_list, years, municipalities, program_keyword, excluded_keywords):
    """
    Filters the dataset based on the specified criteria.

    Parameters:
    - data_list (list of dict): The dataset to filter.
    - years (list of int): List of years to include.
    - municipalities (list of str): List of municipalities to include.
    - program_keyword (str): Keyword to search for in the "Studievag" field.
    - excluded_keywords: Keyword to avoid for in the "Studievag" field.
    Returns:
    - list of dict: Filtered dataset.
    """
    
    # Filter rows where the year is in the specified list
    filtered_data = [
        row for row in data_list
        if row.get("Year") in years
        and row.get("Kommun") in municipalities
        and program_keyword.lower() in str(row.get("Studievag", "")).lower()
    ]

    filtered_data = [
        row for row in filtered_data
        if not any(keyword.lower() in str(row.get("Studievag", "")).lower() for keyword in excluded_keywords)
    ]

    # Remove unwanted columns
    columns_to_drop = ["År", "Organistionsform", "StudieVagKod", "Årtal", "Unnamed: 12"]
    for row in filtered_data:
        for col in columns_to_drop:
            row.pop(col, None)  # Remove column if it exists

    return filtered_data

########################################################################################

def calculate_the_averages(filtered_data):
    """
    Calculates the 5-year averages for median and antagningsgrans values,
    grouped by municipality, program, and school.

    Parameters:
    - filtered_data (list of dict): Filtered dataset.

    Returns:
    - list of dict: Aggregated and sorted dataset.
    """

    if not filtered_data:
        print("Filtered dataset is empty.")
        return []

    # Dictionary to store sum and count for calculating averages
    aggregated_data = defaultdict(lambda: {"Median_sum": 0, "Median_count": 0, "Antagningsgrans_sum": 0, "Antagningsgrans_count": 0})

    # Iterate through filtered data and accumulate values
    for row in filtered_data:
        key = (row["Kommun"], row["Studievag"], row["Skola"])
        
        # Convert Median and Antagningsgrans to numeric values (ignore invalid values)
        median_value = pd.to_numeric(row.get("Median", None), errors="coerce")
        antagningsgrans_value = pd.to_numeric(row.get("Antagningsgrans", None), errors="coerce")

        # Sum up valid values and count occurrences
        if not pd.isna(median_value):
            aggregated_data[key]["Median_sum"] += median_value
            aggregated_data[key]["Median_count"] += 1

        if not pd.isna(antagningsgrans_value):
            aggregated_data[key]["Antagningsgrans_sum"] += antagningsgrans_value
            aggregated_data[key]["Antagningsgrans_count"] += 1

    # Compute averages and filter results
    result_list = []
    for (kommun, studievag, skola), values in aggregated_data.items():
        median_avg = values["Median_sum"] / values["Median_count"] if values["Median_count"] > 0 else None
        antagningsgrans_avg = values["Antagningsgrans_sum"] / values["Antagningsgrans_count"] if values["Antagningsgrans_count"] > 0 else None
        
        # Only include rows where the 5-year median average is at least 300
        if median_avg is not None and median_avg >= 300:
            result_list.append({
                "Kommun": kommun,
                "Studievag": studievag,
                "Skola": skola,
                "Median_Avg": median_avg,
                "Antagningsgrans_Avg": antagningsgrans_avg,
                "Ratio": (antagningsgrans_avg / median_avg) if antagningsgrans_avg is not None else None
            })

    # Sort by the "Ratio" column in ascending order
    result_list.sort(key=lambda x: x["Ratio"] if x["Ratio"] is not None else float("inf"))

    print(f"Total rows in result_list: {len(result_list)}")
    return result_list

########################################################################################
def name_trans():
    """
    Returns a dictionary mapping original school names to standardized names.
    
    Returns:
    - dict: {original_name: standardized_name}
    """
    school_name_mapping = {
        "Danderyds Gymnasium": "Danderyds Gymnasium",
        "Viktor Rydberg gy. Djursholm": "Viktor Rydberg gy. Djursholm",
        "Tullinge gymnasium": "Tullinge gymnasium",
        "Amerikanska Gymnasiet Stockholm": "Amerikanska Gymnasiet Stockholm",
        "Rudbeck Naturvetenskapsprogrammet": "Rudbeck Naturvetenskapsprogrammet",
        "Viktor Rydberg gy. Sundbyberg": "Viktor Rydberg gy. Sundbyberg",
        "Stockholms Idrottsgymnasium": "Stockholms Idrottsgymnasium",
        "Solna Gymnasium": "Solna Gymnasium",
        "Nacka Gymnasium": "Nacka Gymnasium",
        "Tibble Gymnasium Campus Täby": "Tibble Gymnasium Campus Täby",
        "Åva gymnasium": "Åva gymnasium",
        "Tumba gymnasium": "Tumba gymnasium",
        "Blackebergs gymnasium": "Blackebergs gymnasium 85152591",
        "Enskilda gymnasiet": "Enskilda gymnasiet, gy",
        "Sjölins Gymnasium Nacka": "Sjölins Gymnasium Nacka",
        "Campus Manilla Gymnasium": "Campus Manilla Gymnasium",
        "JENSEN Gymnasium Gamla stan": "JENSEN Gymnasium Gamla stan",
        "Värmdö gymnasium": "Värmdö gymnasium",
        "KLARA Teoretiska Gymnasium Stockholm Norra": "KLARA Teoretiska Gymnasium Stockholm Norra",
        "Anna Whitlocks gymnasium": "Anna Whitlocks gymnasium 54040574",
        "Sjölins Gymnasium Södermalm": "Sjölins Gymnasium Södermalm",
        "Kungsholmens gymnasium / Sthlms Musikgymnasium": "Kungsh gy/Sthlms Musikgy 74812809",
        "Östra gymnasiet": "Östra gymnasiet",
        "P A Fogelströms gymnasium": "P A Fogelströms gymnasium 24650116",
        "Viktor Rydberg gy. Odenplan": "Viktor Rydberg gy. Odenplan",
        "Sjölins Gymnasium Vasastan": "Sjölins Gymnasium Vasastan",
        "Östra Reals gymnasium": "Östra Reals gymnasium 99755443",
        "Södra Latins gymnasium": "Södra Latins gymnasium 89370947",
        "Norra Real": "Norra Real 82964090",
        "Täby Enskilda gymnasium": "Täby Enskilda gymnasium",
    }

    return school_name_mapping

#####################################################################################################

def download_and_extract_filtered_data(data_source):
    
    """
    Download the Excel file and extract specific column data that meets the filter criteria.

    Parameters:
    - data_source: An instance of the DataSourceAndParameters class.

    Returns:
    - list[dict]: The filtered data in a list of dictionaries.
    """
    try:
        url = data_source.avgang_info[max(data_source.years)]  # Get the latest year's URL
        sheet_name = data_source.sheet_name
        column_name = data_source.column_name
        filter_schools = data_source.school_name_mapping.keys()  # Use mapped school names
        
        # Download the file
        response = requests.get(url)
        response.raise_for_status()

        # Read in the Excel file
        excel_data = pd.ExcelFile(BytesIO(response.content))

        # Check if the sheet exists
        if sheet_name not in excel_data.sheet_names:
            print(f"Sheet '{sheet_name}' not found in the Excel file.")
            return []
        
        df = excel_data.parse(sheet_name, header=8)  # Using the default header row index 8

        # Check if the required columns exist
        if "Skola" not in df.columns or column_name not in df.columns:
            print(f"Required columns 'Skola' or '{column_name}' not found in sheet '{sheet_name}'.")
            return []

        # Clean the 'Skola' column by removing extra spaces
        df["Skola"] = df["Skola"].str.strip()

        # Filter the dataframe based on the 'Skola' column and filter_schools list
        filtered_df = df[df["Skola"].isin(filter_schools)][["Skola", column_name]]

        # If no data matched the filter
        if filtered_df.empty:
            print("No matching schools found in the dataset.")
            return []
        
        # Convert DataFrame to a list of dictionaries
        filtered_listofdict = filtered_df.to_dict(orient="records")
        
        return filtered_listofdict

    except requests.exceptions.RequestException as e:
        print(f"Error downloading the file: {e}")
        return []
    except Exception as e:
        print(f"Error processing the Excel file: {e}")
        return []
        
#######################################################################################################

def process_gbp_data(avgang_info, sheet_name, column_name, filter_schools):
    """
    Process and extract GBP data for multiple years.

    Parameters:
    - avgang_info: Dictionary mapping years to URLs.
    - sheet_name: The name of the sheet to extract data from.
    - column_name: The column containing GBP values.
    - filter_schools: A list of school names used for filtering.

    Returns:
    - list[dict]: A list of dictionaries containing the filtered GBP data.
    """
    gbp_data_list = []  

    for year, url in avgang_info.items():
        try:
            print(f"Processing data for year {year}...")

            
            filtered_data = download_and_extract_filtered_data(
                url=url,
                sheet_name=sheet_name,
                column_name=column_name,
                filter_schools=filter_schools,
                header_row=8
            )

            if filtered_data:
               
                for entry in filtered_data:
                    entry["Year"] = year 
                gbp_data_list.extend(filtered_data)  
            else:
                print(f"No matching data found for year {year}.")

        except Exception as e:
            print(f"Error processing data for year {year}: {e}")

    return gbp_data_list  

##################################################################################################

def calculate_avg_gbp(gbp_listofdict):
    """
    Calculate the average GBP for each school from 2020 to 2024.

    Parameters:
    - gbp_listofdict: List of dictionaries containing GBP data with columns ["Skola", "GBP för elever med examen", "Year"]

    Returns:
    - list[dict]: A list of dictionaries with average GBP values per school.
    """
    if not gbp_listofdict:
        print("No GBP data available.")
        return []

    df_GBP = pd.DataFrame(gbp_listofdict)

    avg_df_GBP = df_GBP.groupby("Skola")["GBP för elever med examen"].mean().reset_index()

    avg_df_GBP.rename(columns={"GBP för elever med examen": "Average GBP (2020-2024)"}, inplace=True)

    avg_gbp_listofdict = avg_df_GBP.to_dict(orient="records")

    return avg_gbp_listofdict


#####################################################################################################

def data_processing(data_source):
    """
    Processes the admission data by:
    1. Reading the raw data
    2. Filtering based on given parameters
    3. Calculating median and admission score averages
    4.
    5.
    6.

    Parameters:
        data_source (DataSourceAndParameters): Class containing URLs and filtering parameters.

    Returns:
        list[dict]: Processed list of dictionaries with calculated averages and GBP.
    """
    
    # Read in admission data
    antagning_listofdict = read_in_data_antagningsdel(data_source.antagning_info, data_source.antagning_dir)
    
    # Apply filtering based on class parameters
    filtered_antagning_listofdict = filter_data(
        antagning_listofdict, 
        data_source.years, 
        data_source.kommuner, 
        data_source.program_keyword, 
        data_source.excluded_keywords
    )
    
    # Calculate the 5-year median and admission averages
    median_avg_listofdict = calculate_the_averages(filtered_antagning_listofdict)

    # Manually define a name mapping table
    name_trans_listofdict = name_trans(median_avg_listofdict)

    # # Read in GBP för elever med examen for the relevant schools from 2020 to 2024
    gbp_listofdict = process_gbp_data(avgang_info, sheet_name, column_name, filter_schools)

    # Calculate the average GBP för elever med examen for the relevant schools from 2020 to 2024
    avg_gbp_listofdict = calculate_avg_gbp(gbp_listofdict)
    
    return avg_gbp_listofdict

   

    
    




    
   