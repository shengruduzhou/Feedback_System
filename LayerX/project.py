import polars as pl
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

#Data Upload
request_df = pl.read_csv('E:\Project\LayerX\data\requests.csv')
details_df = pl.read_csv('E:\Project\LayerX\data\request_details.csv')
eai_df = pl.read_csv('E:\Project\LayerX\data\expense_account_items.csv')
ocr_df = pl.read_csv('E:\Project\LayerX\data\ocr_results.csv')
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
request_df.glimpse()
print("\n Missing values in requests_df:")
print(request_df.null_count())
print("\n Descriptive statistics of numerical columns:")
print(request_df.describe())
print("\n Value counts of categorical columns:")
for col in request_df.select(pl.col(pl.Utf8)).columns:
    print(f"\n Column: {col}")
    print(request_df[col].value_counts())
    
#EDA rd_df
print("request_details info:")
details_df.glimpse()
print("\n Missing values in request_details:")
print(details_df.null_count())
print("\n Descriptive statistics of numerical columns:")
print(details_df.describe())
print("\n Value counts of categorical columns:")
for col in details_df.select(pl.col(pl.Utf8)).columns:
    print(f"\n Column: {col}")
    print(details_df[col].value_counts())

#EDA ocr_df
print("ocr_results info:")
ocr_df.glimpse()
print("\n Missing values in ocr_results:")
print(ocr_df.null_count())
print("\n Descriptive statistics of numerical columns:")
print(ocr_df.describe())
print("\n Value counts of categorical columns:")
for col in ocr_df.select(pl.col(pl.Utf8)).columns:
    print(f"\n Column: {col}")
    print(ocr_df[col].value_counts())

#Visualization examples
#VE request
plt.figure(figsize=(10, 6))
sns.histplot(request_df['request_amount'], bins=30, kde=True)
plt.title('Distribution of Request Amounts')
plt.show()
#VE request_details
plt.figure(figsize=(10, 6))
sns.histplot(details_df['details_amount'], bins=30, kde=True)
plt.title('Distribution of Details Amounts')
plt.show()
#VE eai
plt.figure(figsize=(10, 6))
sns.histplot(eai_df['expense_amount'], bins=30, kde=True)
plt.title('Distribution of Expense Amounts')
plt.show()
#VE ocr
plt.figure(figsize=(10, 6))
sns.histplot(ocr_df['result_amount'], bins=30, kde=True)
plt.title('Distribution of OCR Results Amounts')
plt.show()