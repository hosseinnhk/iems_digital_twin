from nilmtk import DataSet
import pandas as pd

# Path to the UK-DALE dataset (HDF5 file)
uk_dale_path = "data/ukdale.h5"

# Load the UK-DALE dataset
dataset = DataSet(uk_dale_path)

# Access Building 1 data
building = dataset.buildings[1]

# Access the aggregated power data
electricity_meters = building.elec
aggregate_data = electricity_meters.mains()

# Function to process and save data in 3-month intervals
def process_and_save_data_in_chunks(aggregate_data):
    for chunk in aggregate_data.load():
        # Ensure the index is datetime
        print(f"Processing: {chunk.index[0]} to {chunk.index[-1]}")
        chunk.index = pd.to_datetime(chunk.index)

        # Resample to 1-minute intervals
        downsampled_chunk = chunk.resample('1T').mean()

        # Group by 3-month intervals
        downsampled_chunk['Quarter'] = (downsampled_chunk.index.year.astype(str) +
                                        '-Q' + ((downsampled_chunk.index.month - 1) // 3 + 1).astype(str))
        grouped = downsampled_chunk.groupby('Quarter')

        # Save each 3-month interval to a separate CSV file
        for quarter, data in grouped:
            filename = f"building1_1min_{quarter}.csv"
            filepath = f"data/{filename}"
            data.drop(columns=['Quarter'], inplace=True)
            data.to_csv(filepath)
            print(f"Saved: {filename}")

# Process and save the data in chunks
process_and_save_data_in_chunks(aggregate_data)

# Close the dataset after use
dataset.store.close()