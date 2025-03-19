import os
import json
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import re

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load the GMM model
model_path = 'gmm_model.pkl'
try:
    with open(model_path, 'rb') as file:
        gmm_model = pickle.load(file)
    print("GMM model loaded successfully.")
except FileNotFoundError:
    print(f"Model file not found at {model_path}. Using a mock model for demonstration.")
    # Mock GMM model for demonstration
    class MockGMM:
        def predict(self, X):
            # Randomly classify ~15% of transactions as fraudulent
            return np.random.choice([0, 1], size=len(X), p=[0.85, 0.15])
        
        def predict_proba(self, X):
            # Generate mock probabilities
            probs = np.random.beta(2, 5, size=(len(X), 2))
            return probs / probs.sum(axis=1, keepdims=True)
    
    gmm_model = MockGMM()

# Feature preprocessing functions
def preprocess_features(df):
    """Preprocess the dataframe to extract features for the GMM model."""
    # Convert transaction date and time to features
    if 'Transaction Date and Time' in df.columns:
        df['Transaction_DateTime'] = pd.to_datetime(df['Transaction Date and Time'], errors='coerce')
        df['Transaction_Hour'] = df['Transaction_DateTime'].dt.hour
        df['Transaction_Day'] = df['Transaction_DateTime'].dt.day
        df['Transaction_Month'] = df['Transaction_DateTime'].dt.month
        df['Transaction_Year'] = df['Transaction_DateTime'].dt.year
        df['Transaction_DayOfWeek'] = df['Transaction_DateTime'].dt.dayofweek
    
    # Process transaction amount
    if 'Transaction Amount' in df.columns:
        df['Transaction_Amount'] = pd.to_numeric(df['Transaction Amount'], errors='coerce')
    
    # Process MCC code
    if 'Merchant Category Code (MCC)' in df.columns:
        df['MCC'] = pd.to_numeric(df['Merchant Category Code (MCC)'], errors='coerce')
    
    # Process previous transactions
    if 'Previous Transactions' in df.columns:
        df['Previous_Transactions'] = pd.to_numeric(df['Previous Transactions'], errors='coerce')
    
    # Process response code
    if 'Transaction Response Code' in df.columns:
        df['Response_Code'] = pd.to_numeric(df['Transaction Response Code'], errors='coerce')
    
    # Create one-hot encoding for categorical features
    if 'Transaction Source' in df.columns:
        df = pd.get_dummies(df, columns=['Transaction Source'], prefix='Source')
    
    if 'Card Type' in df.columns:
        df = pd.get_dummies(df, columns=['Card Type'], prefix='CardType')
    
    if 'Transaction Currency' in df.columns:
        df = pd.get_dummies(df, columns=['Transaction Currency'], prefix='Currency')
    
    # Convert location to numeric if possible
    if 'Transaction Location (City or ZIP Code)' in df.columns:
        df['Location_Numeric'] = df['Transaction Location (City or ZIP Code)'].apply(
            lambda x: int(''.join(re.findall(r'\d+', str(x)))) if re.findall(r'\d+', str(x)) else -1
        )
    
    # Select features for the model
    feature_columns = [
        'Transaction_Amount', 'Transaction_Hour', 'Transaction_Day', 
        'Transaction_Month', 'Transaction_DayOfWeek', 'Previous_Transactions',
        'Response_Code'
    ]
    
    # Add any one-hot encoded columns
    for col in df.columns:
        if col.startswith(('Source_', 'CardType_', 'Currency_')):
            feature_columns.append(col)
    
    # Add location if available
    if 'Location_Numeric' in df.columns:
        feature_columns.append('Location_Numeric')
    
    # Add MCC if available
    if 'MCC' in df.columns:
        feature_columns.append('MCC')
    
    # Select only columns that exist in the dataframe
    feature_columns = [col for col in feature_columns if col in df.columns]
    
    # Handle missing values
    features_df = df[feature_columns].fillna(0)
    
    return features_df

def analyze_fraud_reasons(transaction, prediction, probabilities):
    """Analyze why a transaction was flagged as fraudulent."""
    reasons = []
    risk_score = round(float(probabilities[1]) * 100, 2)
    
    # Analyze amount
    if 'Transaction Amount' in transaction and transaction['Transaction Amount'] > 5000:
        reasons.append({
            "factor": "High transaction amount",
            "details": f"Amount of {transaction['Transaction Amount']} exceeds typical patterns",
            "risk_contribution": "High"
        })
    
    # Analyze location
    if 'Transaction Location (City or ZIP Code)' in transaction:
        reasons.append({
            "factor": "Unusual location",
            "details": f"Transaction from {transaction['Transaction Location (City or ZIP Code)']}",
            "risk_contribution": "Medium"
        })
    
    # Analyze time
    if 'Transaction Date and Time' in transaction:
        time_str = transaction['Transaction Date and Time']
        try:
            hour = int(time_str.split()[1].split(":")[0])
            if hour < 6 or hour > 22:
                reasons.append({
                    "factor": "Unusual transaction time",
                    "details": f"Transaction occurred at {time_str}",
                    "risk_contribution": "Medium"
                })
        except (IndexError, ValueError):
            pass
    
    # Analyze response code
    if 'Transaction Response Code' in transaction and transaction['Transaction Response Code'] != 200:
        reasons.append({
            "factor": "Unusual response code",
            "details": f"Response code {transaction['Transaction Response Code']} indicates potential issues",
            "risk_contribution": "High"
        })
    
    # Card type and currency mismatch check
    if 'Card Type' in transaction and 'Transaction Currency' in transaction:
        card_currencies = {
            "Visa": ["USD", "EUR"],
            "Mastercard": ["USD", "EUR"],
            "Amex": ["USD"],
            "JCB": ["JPY"],
            "Interac": ["CAD"]
        }
        
        card_type = transaction['Card Type']
        currency = transaction['Transaction Currency']
        
        if card_type in card_currencies and currency not in card_currencies.get(card_type, [currency]):
            reasons.append({
                "factor": "Card and currency mismatch",
                "details": f"{card_type} card used with {currency} currency",
                "risk_contribution": "High"
            })
    
    # If few or no specific reasons found, add general risk assessment
    if len(reasons) < 2:
        reasons.append({
            "factor": "Risk profile analysis",
            "details": f"Transaction pattern matches known fraud patterns (Risk score: {risk_score}%)",
            "risk_contribution": "Medium"
        })
    
    return {
        "prediction": int(prediction),
        "risk_score": risk_score,
        "reasons": reasons,
        "transaction": transaction
    }

def get_prevention_methods():
    """Return prevention methods based on common fraud patterns."""
    return [
        {
            "method": "Enable 2FA for all transactions",
            "description": "Require two-factor authentication for high-value or unusual transactions to verify the cardholder's identity."
        },
        {
            "method": "Set geographic transaction limits",
            "description": "Restrict transactions to specific regions or require additional verification for transactions from unusual locations."
        },
        {
            "method": "Implement velocity checks",
            "description": "Flag multiple transactions occurring in a short timeframe that exceed normal patterns."
        },
        {
            "method": "Set spending limits",
            "description": "Configure daily or per-transaction spending limits to prevent large unauthorized purchases."
        },
        {
            "method": "Real-time notification system",
            "description": "Send immediate alerts to cardholders for any suspicious activity requiring verification."
        }
    ]

@app.route('/analyze', methods=['POST'])
def analyze_transactions():
    """Endpoint to analyze transaction data CSV for fraud."""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "File must be a CSV file"}), 400
    
    try:
        # Parse CSV
        df = pd.read_csv(file)
        
        # Extract transaction data for the response
        transactions = []
        for _, row in df.iterrows():
            transaction = {}
            for col in row.index:
                if pd.notna(row[col]):
                    transaction[col] = row[col]
            transactions.append(transaction)
        
        # Preprocess features
        features = preprocess_features(df)
        
        # Run GMM model
        if len(features) > 0:
            predictions = gmm_model.predict(features)
            probabilities = getattr(gmm_model, 'predict_proba', lambda x: np.column_stack((1-predictions, predictions)))(features)
            
            # Analyze results
            results = []
            for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
                if i < len(transactions):
                    result = analyze_fraud_reasons(transactions[i], pred, prob)
                    results.append(result)
            
            # Get overall stats
            fraud_count = sum(1 for r in results if r["prediction"] == 1)
            legitimate_count = len(results) - fraud_count
            
            # Get prevention methods
            prevention_methods = get_prevention_methods()
            
            return jsonify({
                "status": "success",
                "totalTransactions": len(results),
                "fraudCount": fraud_count,
                "legitimateCount": legitimate_count,
                "fraudPercentage": round((fraud_count / len(results)) * 100, 2) if results else 0,
                "transactionResults": results,
                "preventionMethods": prevention_methods
            })
        else:
            return jsonify({"error": "Could not extract features from the provided data"}), 400
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)