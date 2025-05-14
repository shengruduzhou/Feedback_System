import polars as pl
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

#Data Upload
eai_df = pl.read_csv("E:\Project\LayerX\data\expense_account_items.csv",encoding='UTF-8')
requests_df = pl.read_csv("E:\Project\LayerX\data\expense_account_requests.csv",encoding='UTF-8')
rd_df = pl.read_csv("E:\Project\LayerX\data\request_details.csv",encoding='UTF-8')
or_df = pl.read_csv("E:\Project\LayerX\data\ocr_results.csv",encoding='UTF-8')
#CSVファイルはUTF-8で編成されたが、実際に展示と運行していたときに、UTF-8でタクシー�?01JNX015ZQM2RS2Y7QJG9KQ7JEのような編成が出た。CSVファイル編成する時は間違えるかも。

#EDA
#EDA eai_df
print("expense_account_items info:")
eai_df.glimpse()
print("\n Missing values in expense_account_items:")
print(eai_df.null_count())
print("\n Descriptive statistics of numerical columns:")
print(eai_df.describe())
print("\n Value counts of categorical columns:")
for col in eai_df.select(pl.col(pl.Utf8)).columns:
    print(f"\n Column: {col}")
    print(eai_df[col].value_counts())

#EDA requests_df
print("requests_df info:")
requests_df.glimpse()
print("\n Missing values in requests_df:")
print(requests_df.null_count())
print("\n Descriptive statistics of numerical columns:")
print(requests_df.describe())
print("\n Value counts of categorical columns:")
for col in requests_df.select(pl.col(pl.Utf8)).columns:
    print(f"\n Column: {col}")
    print(requests_df[col].value_counts())
    
#EDA rd_df
print("request_details info:")
rd_df.glimpse()
print("\n Missing values in request_details:")
print(rd_df.null_count())
print("\n Descriptive statistics of numerical columns:")
print(rd_df.describe())
print("\n Value counts of categorical columns:")
for col in rd_df.select(pl.col(pl.Utf8)).columns:
    print(f"\n Column: {col}")
    print(rd_df[col].value_counts())

#EDA or_df
print("ocr_results info:")
or_df.glimpse()
print("\n Missing values in ocr_results:")
print(or_df.null_count())
print("\n Descriptive statistics of numerical columns:")
print(or_df.describe())
print("\n Value counts of categorical columns:")
for col in or_df.select(pl.col(pl.Utf8)).columns:
    print(f"\n Column: {col}")
    print(or_df[col].value_counts())

#Visualization examples
plt.figure(figsize=(10, 6))
sns.histplot(requests_df['request_amount'], bins=30, kde=True)
plt.title('Distribution of Request Amounts')
plt.show()