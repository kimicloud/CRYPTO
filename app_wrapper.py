from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
import pandas as pd
import numpy as np
import json
import subprocess
import tempfile
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET'])
def index():
    """Serve the HTML page for uploading files"""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FraudShield - Upload Data</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background-color: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .upload-container {
                margin-bottom: 30px;
            }
            .file-input {
                margin: 20px 0;
                display: flex;
                align-items: center;
            }
            button {
                background-color: #4CAF50;
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                margin-left: 10px;
            }
            button:hover {
                background-color: #45a049;
            }
            #loading {
                margin: 20px 0;
                color: #666;
            }
            #results {
                margin-top: 20px;
            }
            .result-summary {
                margin-bottom: 20px;
                padding: 15px;
                background-color: #f0f0f0;
                border-radius: 4px;
            }
            .fraud-transaction {
                margin-bottom: 30px;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #fff8f8;
            }
            .transaction-details {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 10px;
                margin-bottom: 15px;
            }
            .fraud-reason {
                background-color: #ffeeee;
                padding: 10px;
                border-radius: 4px;
                margin-bottom: 15px;
            }
            .prevention-methods {
                background-color: #eeffee;
                padding: 10px;
                border-radius: 4px;
            }
            .error {
                color: red;
                padding: 10px;
                background-color: #ffeeee;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>FraudShield - Transaction Analysis</h1>
            
            <div class="upload-container">
                <h2>Upload Transaction Data</h2>
                <p>Upload a CSV file containing transaction data to analyze for potential fraud.</p>
                
                <div class="file-input">
                    <input type="file" id="csvFile" accept=".csv" />
                    <button id="uploadButton">Analyze for Fraud</button>
                </div>
                
                <div id="loading" style="display: none;">
                    Processing data... This may take a moment.
                </div>
                
                <div id="results"></div>
            </div>
        </div>

        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const fileInput = document.getElementById('csvFile');
                const uploadButton = document.getElementById('uploadButton');
                const resultsDiv = document.getElementById('results');
                const loadingIndicator = document.getElementById('loading');
                
                if (uploadButton) {
                    uploadButton.addEventListener('click', function() {
                        if (!fileInput.files[0]) {
                            alert('Please select a CSV file to upload');
                            return;
                        }
                        
                        // Show loading indicator
                        if (loadingIndicator) loadingIndicator.style.display = 'block';
                        if (resultsDiv) resultsDiv.innerHTML = '';
                        
                        const formData = new FormData();
                        formData.append('file', fileInput.files[0]);
                        
                        fetch('/process-csv', {
                            method: 'POST',
                            body: formData
                        })
                        .then(response => response.json())
                        .then(data => {
                            // Hide loading indicator
                            if (loadingIndicator) loadingIndicator.style.display = 'none';
                            
                            if (data.error) {
                                if (resultsDiv) resultsDiv.innerHTML = `<div class="error">${data.error}</div>`;
                                return;
                            }
                            
                            // Display results
                            if (resultsDiv) {
                                let html = `
                                    <div class="result-summary">
                                        <h3>Analysis Complete</h3>
                                        <p>Found ${data.fraudCount} fraudulent transactions out of ${data.totalCount} total transactions.</p>
                                    </div>
                                `;
                                
                                if (data.fraudCount > 0) {
                                    html += '<h3>Fraudulent Transactions</h3>';
                                    
                                    data.fraudTransactions.forEach((item, index) => {
                                        html += `
                                            <div class="fraud-transaction">
                                                <h4>Fraudulent Transaction #${index + 1}</h4>
                                                <div class="transaction-details">
                                                    <p><strong>Transaction ID:</strong> ${item.transaction_id || 'N/A'}</p>
                                                    <p><strong>Card Number:</strong> ${item.card_number || 'N/A'}</p>
                                                    <p><strong>Amount:</strong> $${item.amount || 'N/A'}</p>
                                                    <p><strong>Date:</strong> ${item.date || 'N/A'}</p>
                                                    <p><strong>Merchant:</strong> ${item.merchant || 'N/A'}</p>
                                                    <p><strong>Fraud Type:</strong> ${item.fraud_type || 'N/A'}</p>
                                                </div>
                                                <div class="fraud-reason">
                                                    <h5>Why This Is Flagged as Fraud:</h5>
                                                    <p>${item.reason}</p>
                                                </div>
                                                <div class="prevention-methods">
                                                    <h5>Prevention Methods:</h5>
                                                    <ul>
                                                        ${item.prevention.map(method => `<li>${method}</li>`).join('')}
                                                    </ul>
                                                </div>
                                            </div>
                                        `;
                                    });
                                } else {
                                    html += '<p>No fraudulent transactions detected.</p>';
                                }
                                
                                resultsDiv.innerHTML = html;
                            }
                        })
                        .catch(error => {
                            // Hide loading indicator
                            if (loadingIndicator) loadingIndicator.style.display = 'none';
                            if (resultsDiv) resultsDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
                            console.error('Error:', error);
                        });
                    });
                }
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/process-csv', methods=['POST'])
def process_csv():
    try:
        # Check if the POST request has the file part
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        
        # If user doesn't select file, browser might submit an empty part without filename
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        # Save the file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Create a Python script to analyze the data
        analysis_script = """
import pandas as pd
import numpy as np
import json
import os
import sys
import traceback

# Wrap everything in try/except to catch and report errors
try:
    # Set the file path from command line argument
    csv_path = sys.argv[1]
    output_path = sys.argv[2]

    # Read the CSV file
    df = pd.read_csv(csv_path)
    
    # Uncomment the following if you want to use your GMM module directly
    # Set up path to import your GMM module if needed
    # sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # try:
    #     import GMM.GMM as gmm_module
    #     # If GMM module has functions we can call directly:
    #     # fraudulent_indices = gmm_module.detect_fraud(df)
    # except ImportError:
    #     print("Warning: Could not import GMM module. Using fallback analysis.")
    
    # Process the data (this would be replaced by your GMM model)
    fraud_transactions = []
    
    # Clean column names - remove any ObjectId entries and standardize keys
    clean_df = pd.DataFrame()
    for col in df.columns:
        # Skip columns that contain ObjectId
        if 'ObjectId' in str(col):
            continue
        # Clean the column name and add to clean_df
        clean_name = col.strip()
        clean_df[clean_name] = df[col]
    
    # Replace df with our cleaned dataframe
    df = clean_df

    # Identify suspicious transactions
    for idx, row in df.iterrows():
        fraud_score = 0
        fraud_reasons = []
        
        # Convert values to appropriate types safely
        try:
            amount = float(row.get('Transaction Amount', 0))
        except (ValueError, TypeError):
            amount = 0
            
        # Get transaction source safely
        transaction_source = str(row.get('Transaction Source', '')).strip()
        
        # Get transaction notes safely
        transaction_notes = str(row.get('Transaction Notes', '')).strip()
        
        # Get fraud flag safely
        try:
            fraud_flag = int(row.get('Fraud Flag or Label', 0))
        except (ValueError, TypeError):
            fraud_flag = 0
        
        # Apply fraud detection rules
        if amount > 5000:
            fraud_score += 0.5
            fraud_reasons.append("High transaction amount ($" + str(amount) + ")")
        
        if transaction_source.lower() == 'online':
            fraud_score += 0.3
            fraud_reasons.append("Online transaction risk")
        
        if 'suspicious' in transaction_notes.lower():
            fraud_score += 0.8
            fraud_reasons.append("Explicitly marked as suspicious")
        
        # Check if the transaction is marked as fraud in the dataset
        if fraud_flag == 1:
            fraud_score = 1.0
            fraud_reasons.append("fraud transaction")
        
        # If fraud score exceeds threshold, mark as fraud
        if fraud_score >= 0.5:
            fraud_type = "General Fraud"
            
            # Determine fraud type (example logic)
            if transaction_source.lower() == 'online':
                fraud_type = "Card Not Present"
            elif amount > 10000:
                fraud_type = "High-Value Fraud"
            
            # Get transaction details safely
            card_number = str(row.get('Card Number', 'Unknown'))
            # Mask all but the last 4 digits of the card number for security
            if len(card_number) > 4:
                card_number = '*' * (len(card_number) - 4) + card_number[-4:]
                
            transaction_data = {
                'transaction_id': str(row.get('Transaction ID', f"TX{idx}")),
                'card_number': card_number,
                'amount': amount,
                'date': str(row.get('Transaction Date and Time', 'Unknown')),
                'merchant': str(row.get('Merchant Name', 'Unknown')),
                'fraud_type': fraud_type,
                'reason': " & ".join(fraud_reasons) if fraud_reasons else "Suspicious pattern detected",
                'prevention': [
                    'Verify cardholder identity with additional authentication',
                    'Contact cardholder to confirm transaction',
                    'Temporarily block card until verification',
                    'Monitor account for additional suspicious activity'
                ]
            }
            fraud_transactions.append(transaction_data)

    # Write results to output file
    with open(output_path, 'w') as f:
        json.dump({
            'total_count': len(df),
            'fraud_count': len(fraud_transactions),
            'fraud_transactions': fraud_transactions
        }, f)
        
except Exception as e:
    # Print the full traceback for debugging
    traceback.print_exc()
    # Write error to output file so it can be displayed to the user
    with open(output_path, 'w') as f:
        json.dump({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, f)
    # Exit with error code
    sys.exit(1)
        """
        
        # Create a temporary file for the analysis script
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            f.write(analysis_script.encode('utf-8'))
            analysis_script_path = f.name
        
        # Create a temporary file for the output
        output_file = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
        output_path = output_file.name
        output_file.close()
        
        # Run the analysis script
        command = f"python {analysis_script_path} {filepath} {output_path}"
        process = subprocess.run(command, shell=True, capture_output=True)
        
        # Read the output
        with open(output_path, 'r') as f:
            results = json.load(f)
        
        # Check if there was an error in the analysis script
        if 'error' in results:
            error_message = f"Analysis error: {results['error']}\n\nDetails: {results.get('traceback', 'No traceback available')}"
            # Clean up temporary files
            os.remove(filepath)
            os.remove(analysis_script_path)
            os.remove(output_path)
            return jsonify({'error': error_message}), 500
        
        # Clean up temporary files
        os.remove(filepath)
        os.remove(analysis_script_path)
        os.remove(output_path)
        
        return jsonify({
            'success': True,
            'totalCount': results['total_count'],
            'fraudCount': results['fraud_count'],
            'fraudTransactions': results['fraud_transactions']
        })
    
    except Exception as e:
        print(f"Error processing file: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)