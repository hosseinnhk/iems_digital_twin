import pandas as pd

dataset = pd.read_csv('data/dataset.csv', index_col='time', parse_dates=True)
print(dataset.head())