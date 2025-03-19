from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import json
from werkzeug.utils import secure_filename
import os
import time
import sys


# Import your existing GMM model
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from project.GMM.GMM import GaussianMixtureModel  # Import your GMM model class - adjust the import based on your actual class name

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure file upload
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB max

# Initialize your GMM model
gmm_model = GaussianMixtureModel()  # Adjust based on your model's initialization parameters

@app.route('/analyze', methods=['POST'])
def analyze_transactions():
    # Check if file exists in request
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    # Check if filename is empty
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Check if file is a CSV
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400
    
    # Save the file
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Get analysis parameters
    detection_threshold = float(request.form.get('detectionThreshold', 0.7))
    generate_report = request.form.get('generateReport', 'false') == 'true'
    
    try:
        # Read the CSV file
        df = pd.read_csv(filepath)
        
        # Process the data with your GMM model
        # Modify this part to match your GMM model's interface
        predictions, probabilities = gmm_model.predict(df)
        
        # Generate fraud reasons and additional analysis
        reasons = generate_fraud_reasons(df, predictions, probabilities)
        
        # Format transactions for response
        transactions = df.to_dict('records')
        
        # Prepare results dictionary
        results = {
            'transactions': transactions,
            'predictions': predictions,
            'probabilities': probabilities,
            'reasons': reasons
        }
        
        # Generate response
        response = format_results(results, generate_report)
        
        # Clean up - delete the uploaded file
        os.remove(filepath)
        
        return jsonify(response)
    
    except Exception as e:
        # Clean up in case of error
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': str(e)}), 500

def generate_fraud_reasons(df, predictions, probabilities):
    """Generate explanations for why transactions were flagged as fraudulent"""
    all_reasons = []
    
    for i, (is_fraud, prob) in enumerate(zip(predictions, probabilities)):
        if is_fraud:
            transaction = df.iloc[i]
            
            # Initialize reasons list for this transaction
            reasons = []
            
            # Check for high transaction amount
            if 'Transaction Amount' in transaction and transaction['Transaction Amount'] > 5000:
                reasons.append({
                    'factor': 'High Transaction Amount',
                    'details': f"Transaction amount of ${transaction['Transaction Amount']:.2f} is unusually high",
                    'risk_contribution': 'High'
                })
            
            # Check for unusual location
            if 'Transaction Location (City or ZIP Code)' in transaction:
                # In a real system, you'd compare to the user's normal locations
                reasons.append({
                    'factor': 'Unusual Location',
                    'details': f"Transaction occurred in location {transaction['Transaction Location (City or ZIP Code)']}",
                    'risk_contribution': 'Medium'
                })
            
            # Check for unusual currency
            if 'Transaction Currency' in transaction and transaction['Transaction Currency'] != 'USD':
                reasons.append({
                    'factor': 'Foreign Currency',
                    'details': f"Transaction in {transaction['Transaction Currency']} is unusual",
                    'risk_contribution': 'Medium'
                })
            
            # Check for unusual merchant category
            if 'Merchant Category Code (MCC)' in transaction:
                # In a real system, you'd have a list of high-risk MCCs
                reasons.append({
                    'factor': 'Merchant Category',
                    'details': f"Merchant category {transaction['Merchant Category Code (MCC)']} has elevated risk",
                    'risk_contribution': 'Low'
                })
            
            # Add probability as a reason
            reasons.append({
                'factor': 'GMM Model Score',
                'details': f"Our machine learning model assigned a fraud probability of {prob*100:.1f}%",
                'risk_contribution': 'High' if prob > 0.9 else 'Medium' if prob > 0.7 else 'Low'
            })
            
            all_reasons.append(reasons)
        else:
            # Add empty reasons for non-fraudulent transactions
            all_reasons.append([])
    
    return all_reasons

def format_results(results, generate_report=False):
    # Extract data from results
    transactions = results['transactions']
    predictions = results['predictions']
    probabilities = results['probabilities']
    reasons = results['reasons']
    
    # Calculate summary statistics
    total_transactions = len(transactions)
    fraud_count = sum(predictions)
    legitimate_count = total_transactions - fraud_count
    fraud_percentage = (fraud_count / total_transactions * 100) if total_transactions > 0 else 0
    
    # Format transaction results
    transaction_results = []
    for i, (transaction, prediction, probability) in enumerate(zip(transactions, predictions, probabilities)):
        risk_score = probability * 100
        
        # Format the transaction data
        transaction_data = {
            'transaction': transaction,
            'prediction': int(prediction),
            'risk_score': float(risk_score),
            'reasons': reasons[i] if i < len(reasons) else []
        }
        
        transaction_results.append(transaction_data)
    
    # Generate prevention methods
    prevention_methods = generate_prevention_methods(transaction_results) if generate_report else []
    
    # Create response
    response = {
        'totalTransactions': total_transactions,
        'fraudCount': fraud_count,
        'legitimateCount': legitimate_count,
        'fraudPercentage': fraud_percentage,
        'transactionResults': transaction_results,
        'preventionMethods': prevention_methods
    }
    
    return response

def generate_prevention_methods(transaction_results):
    # Extract fraud patterns
    fraud_transactions = [result for result in transaction_results if result['prediction'] == 1]
    
    # Generate prevention methods
    prevention_methods = [
        {
            'title': 'Implement Multi-Factor Authentication',
            'description': 'Require multiple forms of verification for high-risk transactions.',
            'steps': [
                'Deploy SMS or email verification for transactions above a certain threshold',
                'Implement biometric authentication for high-value transactions',
                'Use geolocation verification to confirm transaction location matches user\'s usual pattern'
            ]
        },
        {
            'title': 'Set Up Real-Time Transaction Monitoring',
            'description': 'Monitor transactions in real-time for suspicious activity.',
            'steps': [
                'Implement real-time transaction monitoring with behavioral analytics',
                'Set up alerts for unusual transaction patterns',
                'Create a workflow for reviewing flagged transactions'
            ]
        },
        {
            'title': 'Enhanced Card Security Features',
            'description': 'Implement additional security features for card transactions.',
            'steps': [
                'Use dynamic CVV codes that change periodically',
                'Implement card-present transaction verification',
                'Enable transaction notifications for immediate customer awareness'
            ]
        }
    ]
    
    # Add specific prevention methods based on fraud patterns
    if fraud_transactions:
        # Check if there are specific patterns in the fraud transactions
        has_large_transactions = any(float(t['transaction'].get('Transaction Amount', 0)) > 5000 for t in fraud_transactions)
        has_international = any(t['transaction'].get('Transaction Currency', 'USD') != 'USD' for t in fraud_transactions)
        
        if has_large_transactions:
            prevention_methods.append({
                'title': 'Implement Transaction Limits',
                'description': 'Set up daily or per-transaction limits to prevent large fraudulent transactions.',
                'steps': [
                    'Configure maximum transaction amounts for different account types',
                    'Implement stricter verification for transactions exceeding normal limits',
                    'Allow customers to set their own transaction limits'
                ]
            })
        
        if has_international:
            prevention_methods.append({
                'title': 'Enhance International Transaction Security',
                'description': 'Implement additional security measures for international transactions.',
                'steps': [
                    'Require pre-authorization for international transactions',
                    'Implement country-specific risk scoring',
                    'Use IP geolocation to verify transaction origin'
                ]
            })
    
    return prevention_methods

if __name__ == '__main__':
    app.run(debug=True)