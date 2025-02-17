import os
import requests
import pandas as pd
from collections import defaultdict

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

def filter_data(data_list, years, municipalities, program_keyword):
    """
    Filters the dataset based on the specified criteria.

    Parameters:
    - data_list (list of dict): The dataset to filter.
    - years (list of int): List of years to include.
    - municipalities (list of str): List of municipalities to include.
    - program_keyword (str): Keyword to search for in the "Studievag" field.

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

    # Exclude rows where "Studievag" contains specific unwanted keywords
    excluded_keywords = ["estetiska", "samhälle", "Hållbar utveckling", "Idrott", "Musik", "Dans", "Miljö", "Innovation"]
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
def name_trans(median_avg_df): 
    # Manually define a name mapping table
    
    # df_name_trans = pd.DataFrame({
    #     "Skola_antag": median_avg_df["Skola"],
    #     "Kommun": median_avg_df["Kommun"],
    #     "Skola_avgang": ["Danderyds Gymnasium", "Viktor Rydberg gy. Djursholm", "Tullinge gymnasium", "Tullinge gymnasium", 
    #                      "Viktor Rydberg gy. Djursholm", "Amerikanska Gymnasiet Stockholm", "Rudbeck Naturvetenskapsprogrammet","Viktor Rydberg gy. Sundbyberg", 
    #                      "Stockholms Idrottsgymnasium", "Solna Gymnasium", "Nacka Gymnasium", "Tibble Gymnasium Campus Täby", 
    #                      "Åva gymnasium", "Tumba gymnasium", "Blackebergs gymnasium 85152591", "Enskilda gymnasiet, gy", 
    #                      "Sjölins Gymnasium Nacka", "Campus Manilla Gymnasium", "JENSEN Gymnasium Gamla stan", "Värmdö gymnasium", 
    #                     "KLARA Teoretiska Gymnasium Stockholm Norra", "nan", "Nacka Gymnasium", "Anna Whitlocks gymnasium 54040574", 
    #                     "JENSEN Gymnasium Gamla stan", "Sjölins Gymnasium Södermalm", "nan", "Nacka Gymnasium", 
    #                     "Kungsh gy/Sthlms Musikgy 74812809", "Östra gymnasiet", "Kungsh gy/Sthlms Musikgy 74812809", "Anna Whitlocks gymnasium 54040574", 
    #                     "P A Fogelströms gymnasium 24650116", "Viktor Rydberg gy. Odenplan", "Sjölins Gymnasium Vasastan", "Östra Reals gymnasium 99755443", 
    #                     "Södra Latins gymnasium 89370947", "JENSEN Gymnasium Gamla stan", "Norra Real 82964090", "Täby Enskilda gymnasium", 
    #                    "Norra Real 82964090", "Viktor Rydberg gy. Odenplan", "Kungsh gy/Sthlms Musikgy 74812809", "Norra Real 82964090"] 
    # })
    df_name_trans = pd.DataFrame({
        "Skola_antag": median_avg_df["Skola"],
        "Kommun": median_avg_df["Kommun"],
        "Skola_avgang": pd.Series([
            "Danderyds Gymnasium", "Viktor Rydberg gy. Djursholm", "Tullinge gymnasium", 
            "Tullinge gymnasium", "Viktor Rydberg gy. Djursholm", "Amerikanska Gymnasiet Stockholm", 
            "Rudbeck Naturvetenskapsprogrammet", "Viktor Rydberg gy. Sundbyberg", 
            "Stockholms Idrottsgymnasium", "Solna Gymnasium", "Nacka Gymnasium", 
            "Tibble Gymnasium Campus Täby", "Åva gymnasium", "Tumba gymnasium", 
            "Blackebergs gymnasium 85152591", "Enskilda gymnasiet, gy", "Sjölins Gymnasium Nacka", 
            "Campus Manilla Gymnasium", "JENSEN Gymnasium Gamla stan", "Värmdö gymnasium", 
            "KLARA Teoretiska Gymnasium Stockholm Norra", "nan", "Nacka Gymnasium", 
            "Anna Whitlocks gymnasium 54040574", "JENSEN Gymnasium Gamla stan", 
            "Sjölins Gymnasium Södermalm", "nan", "Nacka Gymnasium", 
            "Kungsh gy/Sthlms Musikgy 74812809", "Östra gymnasiet", "Kungsh gy/Sthlms Musikgy 74812809", 
            "Anna Whitlocks gymnasium 54040574", "P A Fogelströms gymnasium 24650116", 
            "Viktor Rydberg gy. Odenplan", "Sjölins Gymnasium Vasastan", "Östra Reals gymnasium 99755443", 
            "Södra Latins gymnasium 89370947", "JENSEN Gymnasium Gamla stan", "Norra Real 82964090", 
            "Täby Enskilda gymnasium", "Norra Real 82964090", "Viktor Rydberg gy. Odenplan", 
            "Kungsh gy/Sthlms Musikgy 74812809", "Norra Real 82964090"
        ], index=median_avg_df.index)  # Ensure index consistency
    })
    return df_name_trans
#####################################################################################################


def data_processing():

    # Define the range of years and corresponding URLs
    data_antagning_info = {
        2020: "https://gymnasieantagningen.storsthlm.se/media/yiobheds/slutantagningsresultat-2020.xlsx",
        2021: "https://gymnasieantagningen.storsthlm.se/media/pvob5j1l/slutantagningsresultat-2021.xlsx",
        2022: "https://gymnasieantagningen.storsthlm.se/media/xhvap2io/slutantagning-2022.xlsx",
        2023: "https://gymnasieantagningen.storsthlm.se/media/zksfvysz/slutantagningsresultat-2023.xlsx",
        2024: "https://gymnasieantagningen.storsthlm.se/media/opnfe50w/slutantagningsresultat-2024.xlsx",
    }
    
    download_dir = "antagningsstatistik"  # Directory to store downloaded files
    
    # Read in antagningsdel data
    antagning_listofdict = read_in_data_antagningsdel(data_antagning_info, download_dir)
    
    # Define parameters
    years = range(2020, 2025)  # Range of years to include in the filter
    kommuner = [  # List of municipalities to include in the filter
        "Botkyrka", "Danderyd", "Haninge", "Huddinge", "Järfälla", "Lidingö", "Nacka", "Sollentuna", "Solna", 
        "Stockholm", "Sundbyberg", "Södertälje", "Tyresö", "Täby", "Upplands Väsby", "Vallentuna", "Vaxholm", "Värmdö"
    ]
    program_keyword = "Naturvetenskapsprogrammet"  # Keyword to filter specific programs
    
    # Apply the filter function
    filtered_antagning_listofdict = filter_data(antagning_listofdict, years, kommuner, program_keyword)
       
    # Calculate the 5-year median and antagningsgrans averages for each school, program, and municipality 
    # and sort data according to the average of median
    median_avg_listofdict = calculate_the_averages(filtered_antagning_listofdict)

     # Manually define a name mapping table
    df_name_trans = name_trans(median_avg_df)
    return median_avg_listofdict