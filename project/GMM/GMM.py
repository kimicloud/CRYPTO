#!/usr/bin/env python
# coding: utf-8

# In[5]:


# !pip install cryptography
# !pip install xgboost
# !brew install libomp
# !pip install xgboost


# In[6]:


# Imported Modules
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from datetime import datetime
from category_encoders import TargetEncoder
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder,OneHotEncoder
from sklearn.mixture import GaussianMixture
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, confusion_matrix, classification_report, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score


# In[7]:


df = pd.read_csv('synthetic_credit_transactions.csv')


# In[8]:


# Assuming df is your original DataFrame containing 'Card Number' and 'CVV'
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

# Function to encrypt a text (card number or CVV)
def aes_encrypt(plain_text, key):
    backend = default_backend()
    iv = os.urandom(16)  # Initialization vector for AES
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=backend)
    encryptor = cipher.encryptor()
    encrypted_text = encryptor.update(plain_text.encode()) + encryptor.finalize()
    return iv + encrypted_text  # Concatenate IV and encrypted text

# Function to decrypt an encrypted text (if needed later)
def aes_decrypt(encrypted_text, key):
    backend = default_backend()
    iv = encrypted_text[:16]  # Extract IV from the first 16 bytes
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=backend)
    decryptor = cipher.decryptor()
    decrypted_text = decryptor.update(encrypted_text[16:]) + decryptor.finalize()
    return decrypted_text.decode()

# Key for AES encryption (32 bytes for AES-256)
key = os.urandom(32)

# Encrypt the 'Card Number' and 'CVV' columns in the DataFrame
df['Card Number'] = df['Card Number'].apply(lambda x: aes_encrypt(str(x), key))
df['CVV Code'] = df['CVV Code'].apply(lambda x: aes_encrypt(str(x), key))

# Now 'Card Number' and 'CVV' columns in df are replaced with their encrypted values

# Example usage with card number
encrypted_card_number = aes_encrypt('1234567812345678', key)
decrypted_card_number = aes_decrypt(encrypted_card_number, key)

print(f'Encrypted: {encrypted_card_number}')
print(f'Decrypted: {decrypted_card_number}')


# In[9]:


df.head()


# In[10]:


df.shape


# In[11]:


df.columns


# # Data Preprocessing

# ### Checking for missing values

# In[12]:


cleaned_df=df.copy()
#count of missing values in dataframe's column
print(cleaned_df.isnull().sum())


# In[13]:


# Handle missing values (if any)
# cleaned_df.fillna(method='', inplace=True)

# Ensure data types are consistent
cleaned_df['Transaction Amount'] = cleaned_df['Transaction Amount'].astype(float)
cleaned_df['Previous Transactions'] = cleaned_df['Previous Transactions'].astype(int)
cleaned_df['Fraud Flag or Label'] = cleaned_df['Fraud Flag or Label'].astype(int)
cleaned_df['Transaction Date and Time'].head()


# ### Step 4: Feature Engineering

# In[14]:


# Extract time-based features
# Convert 'Transaction Date and Time' to datetime format
cleaned_df['Transaction Date and Time'] = pd.to_datetime(cleaned_df['Transaction Date and Time'])

# Extract hour and day of the week from 'Transaction Date and Time'
cleaned_df['Hour'] = cleaned_df['Transaction Date and Time'].dt.hour
cleaned_df['Day of Week'] = cleaned_df['Transaction Date and Time'].dt.dayofweek

# Calculate time since last transaction
cleaned_df.sort_values(by=['Cardholder Name', 'Transaction Date and Time'], inplace=True)

cleaned_df['Time Since Last Transaction'] = cleaned_df.groupby('Cardholder Name')['Transaction Date and Time'].diff().dt.total_seconds() / 3600  # in hours

# Fill NaN with 0 for the first transaction for each cardholder
cleaned_df['Time Since Last Transaction'].fillna(0, inplace=True)

# Display the first few rows to check the result
cleaned_df.head()


# In[15]:


# Calculate transaction frequency
transaction_frequency = cleaned_df.groupby('Cardholder Name')['Transaction ID'].count().reset_index()
transaction_frequency.columns = ['Cardholder Name', 'Transaction Frequency']
cleaned_df = cleaned_df.merge(transaction_frequency, on='Cardholder Name', how='left')
cleaned_df.head()


# In[16]:


# Calculate average transaction amount
average_transaction_amount = cleaned_df.groupby('Cardholder Name')['Transaction Amount'].mean().reset_index()
average_transaction_amount.columns = ['Cardholder Name', 'Average Transaction Amount']
cleaned_df = cleaned_df.merge(average_transaction_amount, on='Cardholder Name', how='left')
cleaned_df.head()


# In[17]:


# Calculate transaction velocity (number of transactions in the last 24 hours)
cleaned_df.set_index('Transaction Date and Time', inplace=True)
cleaned_df['Transaction Velocity'] = cleaned_df.groupby('Cardholder Name')['Transaction Amount'].rolling('24h').count().reset_index(level=0, drop=True)
cleaned_df.reset_index(inplace=True)
cleaned_df.head()


# In[18]:


transaction_amount_variance = cleaned_df.groupby('Cardholder Name')['Transaction Amount'].var().reset_index()
transaction_amount_variance.columns = ['Cardholder Name', 'Transaction Amount Variance']
cleaned_df = cleaned_df.merge(transaction_amount_variance, on='Cardholder Name', how='left')
cleaned_df.head()


# In[19]:


# Transaction Amount relative to Transaction Frequency
cleaned_df['Transaction_Amount_to_Frequency'] = cleaned_df['Transaction Amount'] / cleaned_df['Transaction Frequency']

# Convert 'Transaction Date and Time' to datetime
cleaned_df['Transaction Date and Time'] = pd.to_datetime(cleaned_df['Transaction Date and Time'])

# Sort by 'Transaction Date and Time'
cleaned_df = cleaned_df.sort_values(by='Transaction Date and Time')



# In[20]:


# Reset index again to ensure no issues with 'Cardholder Name' being both an index and a column
cleaned_df = cleaned_df.reset_index(drop=True)

# Display the new features
new_features = ['Transaction_Amount_to_Frequency']

print(cleaned_df[new_features].head())


# In[21]:


cleaned_df.columns


# ### Step5: Perform Encoding on Specific Categorical Variables

# In[22]:


label_cols = ['Cardholder Name', 'Merchant Name', 'Transaction Currency', 
              'Merchant Category Code (MCC)', 'Transaction Location (City or ZIP Code)', 'User Account Information']
label_encoders = {}
for col in label_cols:
    label_encoders[col] = LabelEncoder()
    cleaned_df[col] = label_encoders[col].fit_transform(cleaned_df[col].astype(str))
cleaned_df.head()


# In[23]:


one_hot_cols = ['Card Type', 'Transaction Source', 'Device Information', 'Transaction Notes']
cleaned_df = pd.get_dummies(cleaned_df, columns=one_hot_cols, drop_first=True)
cleaned_df.head()


# In[24]:


# cleaned_df.dtypes


# ### Step5: Standardization of Numerical Features

# In[ ]:





# In[25]:


# Step 1: Select numerical features for scaling (excluding Card Number and CVV Code)
numerical_cols = ['Transaction Amount', 'Previous Transactions', 'Time Since Last Transaction',
                  'Transaction Frequency', 'Average Transaction Amount', 'Transaction Velocity', 'Transaction Amount Variance','Transaction_Amount_to_Frequency']


# Step 2: Scale the numerical columns
scaler = StandardScaler()
cleaned_df[numerical_cols] = scaler.fit_transform(cleaned_df[numerical_cols])

# Step 3: Ensure that boolean columns are properly encoded as 0/1
# (This is automatically handled in pandas when they are stored as `bool`, but ensure we explicitly handle this)
bool_cols = cleaned_df.select_dtypes(include='bool').columns
cleaned_df[bool_cols] = cleaned_df[bool_cols].astype(int)  # Convert boolean to 0/1

# Step 4: Select the features for the GMM model (excluding Card Number, CVV Code, and 'Fraud Flag or Label')
X = cleaned_df.drop(['Card Number', 'CVV Code', 'Transaction ID', 'Fraud Flag or Label', 'Card Expiration Date', 'Transaction Date and Time', 'IP Address'], axis=1)


# In[26]:


# Step 6: Fit the Gaussian Mixture Model (GMM)
gmm = GaussianMixture(n_components=2, random_state=42)  # n_components=2 for fraud and non-fraud
gmm.fit(X)

# Step 7: Predict the clusters (fraud or non-fraud)
cleaned_df['GMM Cluster'] = gmm.predict(X)

# Display the DataFrame with the predicted GMM cluster labels
print(cleaned_df[['Transaction ID', 'GMM Cluster','Fraud Flag or Label']].tail())


# ###  Model Evaluation 

# In[27]:


# Cross-tabulation to see how clusters align with true labels
print(pd.crosstab(cleaned_df['Fraud Flag or Label'], cleaned_df['GMM Cluster'], rownames=['Actual'], colnames=['Predicted']))

# Confusion matrix
cm = confusion_matrix(cleaned_df['Fraud Flag or Label'], cleaned_df['GMM Cluster'])
print(f'Confusion Matrix:\n{cm}')

# Accuracy
accuracy = accuracy_score(cleaned_df['Fraud Flag or Label'], cleaned_df['GMM Cluster'])
print(f'Accuracy: {accuracy}')

# Classification Report (Precision, Recall, F1-score)
classification_rep = classification_report(cleaned_df['Fraud Flag or Label'], cleaned_df['GMM Cluster'])
print(f'Classification Report:\n{classification_rep}')


# In[28]:


# Calculate the silhouette score to evaluate cluster separation
silhouette_avg = silhouette_score(X, cleaned_df['GMM Cluster'])
print(f'Silhouette Score: {silhouette_avg}')


# In[29]:


# Analyze cluster-wise fraud/non-fraud distribution
cluster_distribution = cleaned_df.groupby(['GMM Cluster', 'Fraud Flag or Label']).size().unstack(fill_value=0)
print(cluster_distribution)


# In[30]:


print(cleaned_df.columns)


# In[31]:


# Filter fraud cluster
fraud_transactions = cleaned_df[cleaned_df['GMM Cluster'] == 1]


# In[32]:


def generate_fraud_type(row):
    # Using GMM Cluster as an initial indicator
    if row['GMM Cluster'] == 1 and row['Transaction Notes_Suspicious activity'] == 1:
        return 'Suspicious Activity'
    
    # High-value fraud: Transactions flagged as high-value or with large amounts
    elif row['Transaction Notes_High-value transaction'] == 1 or row['Transaction Amount'] > 10000:
        return 'High-Value Fraud'
    
    # Card not present fraud: Online or Mobile transactions
    elif row['Transaction Source_Online'] == 1 or row['Transaction Source_Mobile'] == 1:
        return 'Card Not Present'
    
    # Card skimming: International transactions with in-store purchases
    elif row['Transaction Notes_In-store purchase'] == 1 and row['Transaction Notes_International transaction'] == 1:
        return 'Card Skimming'
    
    # Subscription fraud: Regular subscription payments flagged as fraud
    elif row['Transaction Notes_Subscription payment'] == 1:
        return 'Subscription Fraud'
    
    # Routine transaction flagged as fraud
    elif row['Transaction Notes_Routine transaction'] == 1:
        return 'Routine Fraud'
    
    # Default fraud type based on GMM Cluster
    else:
        return 'General Fraud'

# Apply the function to the DataFrame to generate the fraud type column
cleaned_df['fraud_type'] = cleaned_df.apply(generate_fraud_type, axis=1)

# Show the updated DataFrame with the new 'fraud_type' column
print(cleaned_df[['Transaction Amount', 'Transaction Source_Online', 'Transaction Notes_Suspicious activity', 'fraud_type']].head())


# In[33]:


# Assuming df['fraud_type'] has been generated from the previous steps
# and df contains the GMM clusters and all other relevant features

# Select features for Logistic Regression (excluding the fraud_type column)
# Make sure to exclude irrelevant features like Cardholder Name, Card Number, etc.
features = [
    'Transaction Amount', 'Transaction Source_Online', 'Transaction Source_Mobile',
    'Transaction Source_POS', 'Transaction Notes_Bill payment', 'Transaction Notes_High-value transaction',
    'Transaction Notes_In-store purchase', 'Transaction Notes_International transaction',
    'Transaction Notes_Regular purchase', 'Transaction Notes_Routine transaction',
    'Transaction Notes_Subscription payment', 'Transaction Notes_Suspicious activity',
    'GMM Cluster', 'Time Since Last Transaction', 'Transaction Frequency',
    'Average Transaction Amount', 'Transaction Velocity'
]

# One-hot encode categorical columns (if necessary)
categorical_columns = ['Card Type_Diners Club', 'Card Type_Discover', 'Card Type_MasterCard', 'Card Type_Visa']

# Prepare the features (you can include more as per your choice)
X = cleaned_df[features + categorical_columns]

# The target is the 'fraud_type' column
y = cleaned_df['fraud_type']

# Split the data into training and test sets (80% training, 20% testing)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize and train the Logistic Regression model
logistic_model = LogisticRegression(max_iter=1000)  # Increased max_iter to ensure convergence
logistic_model.fit(X_train, y_train)

# Make predictions on the test set
y_pred = logistic_model.predict(X_test)
# Check if model has been fitted properly

# Evaluate the model's performance
print("Accuracy:", accuracy_score(y_test, y_pred))
print("Classification Report:\n", classification_report(y_test, y_pred))

# Example: View the first few predictions
cleaned_df_predictions = pd.DataFrame({'Actual': y_test, 'Predicted': y_pred})


# In[35]:


import joblib
# Save the GMM model
joblib.dump(gmm, 'gmm_model.pkl')
joblib.dump(logistic_model, 'logistic_model.pkl')


# In[38]:


# Save the StandardScaler
joblib.dump(scaler, 'scaler.joblib')

# Save the Label Encoders
joblib.dump(label_encoders, 'label_encoders.joblib')

# Save the list of features used for training
joblib.dump(features, 'features.joblib')


# In[ ]:




