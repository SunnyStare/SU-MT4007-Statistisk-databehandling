import os
import pandas as pd
import requests
##############################################################################################
def read_in_data_antagningsdel():
    # Define the range of years and corresponding URLs
    data_antagning_info = {
        2020: "https://gymnasieantagningen.storsthlm.se/media/yiobheds/slutantagningsresultat-2020.xlsx",
        2021: "https://gymnasieantagningen.storsthlm.se/media/pvob5j1l/slutantagningsresultat-2021.xlsx",
        2022: "https://gymnasieantagningen.storsthlm.se/media/xhvap2io/slutantagning-2022.xlsx",
        2023: "https://gymnasieantagningen.storsthlm.se/media/zksfvysz/slutantagningsresultat-2023.xlsx",
        2024: "https://gymnasieantagningen.storsthlm.se/media/opnfe50w/slutantagningsresultat-2024.xlsx",
    }
    
    download_dir = "antagningsstatistik"  # Directory to store downloaded files
    
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

def data_processing():
    dataframe_antagning = read_in_data_antagningsdel()
    print(dataframe_antagning)