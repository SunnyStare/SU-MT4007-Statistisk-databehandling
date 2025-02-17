import os
import pandas as pd
import requests
##############################################################################################
def read_in_data_antagningsdel(data_antagning_info, download_dir):
    
    # Download and read Excel files
    dataframes_antagning = []  # List to store DataFrames for each year
    for year, download_url in data_antagning_info.items():
        file_name = f"{download_dir}/Slutantagningsresultat_{year}.xlsx"
    
        # Check if the file already exists
        if not os.path.exists(file_name):
            try:
                # Download the file
                response = requests.get(download_url)
                response.raise_for_status()  # Ensure the request was successful
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
            dataframes_antagning.append(df_antagning)
        except Exception as e:
            print(f"Failed to read {file_name}: {e}")
    
    # Combine data from all years
    if dataframes_antagning:
        df_antagning = pd.concat(dataframes_antagning, ignore_index=True)
        # print("Final DataFrame:")
        # print(df_antagning.head())  # Display the first few rows
    
        # Save combined data to a CSV file
        output_file = f"{download_dir}/combined_antagningsstatistik.csv"
        df_antagning.to_csv(output_file, index=False)
        print(f"Combined data saved to {output_file}")
    else:
        print("No data downloaded.")
        df_antagning = pd.DataFrame()  # Create an empty DataFrame to avoid errors
    return df_antagning
#######################################################################################
def filter_data(df_antagning, years, kommuner, program_keyword):
    # Filter rows where the year is in the specified range
    df_antagning = df_antagning[df_antagning["Year"].isin(years)]

    # Filter rows where the municipality is in the specified list
    df_antagning = df_antagning[df_antagning["Kommun"].isin(kommuner)]

    # Filter rows where the Studievag column contains the specified keyword
    df_antagning = df_antagning[df_antagning["Studievag"].str.contains(program_keyword, na=False)]

    # Exclude rows where Studievag contains specific keywords (strict matching)
    excluded_keywords = ["estetiska", "samhälle", "Hållbar utveckling", "Idrott", "Musik", "Dans", "Miljö", "Innovation"]
    pattern = r'\b(?:' + '|'.join(excluded_keywords) + r')\b'  # Match whole words only
    df_antagning = df_antagning[~df_antagning["Studievag"].str.contains(pattern, case=False, na=False)]

    # Drop unwanted columns
    columns_to_drop = ["\u00c5r", "Organistionsform", "StudieVagKod", "\u00c5rtal", "Unnamed: 12"]
    df_antagning = df_antagning.drop(columns=[col for col in columns_to_drop if col in df_antagning.columns], errors='ignore')

    return df_antagning
########################################################################################
def calculate_the_averages(filtered_df_antagning):  
    # Calculate the 5-year median and antagningsgrans averages for each school, program, and municipality 
    # and sort data according to the average of median
    
    if not filtered_df_antagning.empty:
        # Ensure Median and Antagningsgrans columns are numeric
        filtered_df_antagning["Median"] = pd.to_numeric(filtered_df_antagning["Median"], errors='coerce')
        filtered_df_antagning["Antagningsgrans"] = pd.to_numeric(filtered_df_antagning["Antagningsgrans"], errors='coerce')
    
        # Calculate the averages
        median_avg_df = (
            filtered_df_antagning.groupby(["Kommun", "Studievag", "Skola"])
            .agg({"Median": "mean", "Antagningsgrans": "mean"})  # Automatically ignores NaN values
            .reset_index()
        )
    
        # Filter out rows where the 5-year median average is below 300
        median_avg_df = median_avg_df[median_avg_df["Median"] >= 300]
    
        # Add a column for the ratio of Antagningsgrans average to Median average
        median_avg_df["Ratio"] = median_avg_df["Antagningsgrans"] / median_avg_df["Median"]
    
        # Sort results by the ratio column
        median_avg_df = median_avg_df.sort_values(by="Ratio", ascending=True)
    
        # Print the number of rows in the resulting DataFrame
        print(f"Total rows in median_avg_df: {len(median_avg_df)}")
    
        # return df of the 5-year averages
        pd.set_option("display.max_colwidth", None)  # Ensure full display of Studievag content
        # print("5-Year Averages by Municipality, Program, and School (Sorted by Ratio):")
        return median_avg_df
    else:
        print("Filtered dataset is empty.")
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
    dataframe_antagning = read_in_data_antagningsdel(data_antagning_info, download_dir)
    
    # Define parameters
    years = range(2020, 2025)  # Range of years to include in the filter
    kommuner = [  # List of municipalities to include in the filter
        "Botkyrka", "Danderyd", "Haninge", "Huddinge", "Järfälla", "Lidingö", "Nacka", "Sollentuna", "Solna", 
        "Stockholm", "Sundbyberg", "Södertälje", "Tyresö", "Täby", "Upplands Väsby", "Vallentuna", "Vaxholm", "Värmdö"
    ]
    program_keyword = "Naturvetenskapsprogrammet"  # Keyword to filter specific programs
    
    # Apply the filter function
    filtered_df_antagning = filter_data(dataframe_antagning, years, kommuner, program_keyword)
    # print(filtered_df_antagning)
    
    # Calculate the 5-year median and antagningsgrans averages for each school, program, and municipality 
    # and sort data according to the average of median
    median_avg_df = calculate_the_averages(filtered_df_antagning)

     # Manually define a name mapping table
    df_name_trans = name_trans(median_avg_df)
    return median_avg_df