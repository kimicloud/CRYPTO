// upload_handler.js - Handles file upload and GMM model integration

document.addEventListener('DOMContentLoaded', function() {
    // References to HTML elements
    const uploadForm = document.getElementById('uploadForm');
    const fileUpload = document.getElementById('fileUpload');
    const uploadProgress = document.getElementById('uploadProgress');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const analysisResults = document.getElementById('analysisResults');
    
    // Results elements
    const totalTransactionsEl = document.getElementById('totalTransactions');
    const fraudCountEl = document.getElementById('fraudCount');
    const legitimateCountEl = document.getElementById('legitimateCount');
    const fraudPercentageEl = document.getElementById('fraudPercentage');
    const fraudulentTransactionsEl = document.getElementById('fraudulentTransactions');
    const allTransactionsEl = document.getElementById('allTransactions');
    const preventionMethodsEl = document.getElementById('preventionMethods');
    
    // Tab handling
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    // Search inputs
    const fraudSearchInput = document.getElementById('fraudSearchInput');
    const allSearchInput = document.getElementById('allSearchInput');
    
    // Action buttons
    const downloadReportBtn = document.getElementById('downloadReportBtn');
    const newAnalysisBtn = document.getElementById('newAnalysisBtn');
    
    // Store analysis results
    let currentAnalysisResults = null;
    
    // Backend API endpoint
    const API_ENDPOINT = 'http://localhost:5000/analyze';
    
    // Configure tab switching
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to current button and content
            this.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    // Search functionality for fraudulent transactions
    if (fraudSearchInput) {
        fraudSearchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const fraudTransactions = document.querySelectorAll('#fraudulentTransactions .transaction-card');
            
            fraudTransactions.forEach(transaction => {
                const text = transaction.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    transaction.style.display = 'block';
                } else {
                    transaction.style.display = 'none';
                }
            });
        });
    }
    
    // Search functionality for all transactions
    if (allSearchInput) {
        allSearchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const allTransactions = document.querySelectorAll('#allTransactions .transaction-card');
            
            allTransactions.forEach(transaction => {
                const text = transaction.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    transaction.style.display = 'block';
                } else {
                    transaction.style.display = 'none';
                }
            });
        });
    }
    
    // New analysis button
    if (newAnalysisBtn) {
        newAnalysisBtn.addEventListener('click', function() {
            // Reset form
            uploadForm.reset();
            
            // Hide results and show form
            analysisResults.classList.add('hidden');
            uploadForm.style.display = 'block';
            
            // Clear stored results
            currentAnalysisResults = null;
        });
    }
    
    // Download report button
    if (downloadReportBtn) {
        downloadReportBtn.addEventListener('click', function() {
            if (!currentAnalysisResults) {
                showAlert('No analysis results available to download');
                return;
            }
            
            // Format the report data
            const reportData = {
                summary: {
                    totalTransactions: currentAnalysisResults.totalTransactions,
                    fraudCount: currentAnalysisResults.fraudCount,
                    legitimateCount: currentAnalysisResults.legitimateCount,
                    fraudPercentage: currentAnalysisResults.fraudPercentage
                },
                fraudulentTransactions: currentAnalysisResults.transactionResults.filter(
                    result => result.prediction === 1
                ),
                preventionMethods: currentAnalysisResults.preventionMethods
            };
            
            // Convert to JSON string
            const reportJson = JSON.stringify(reportData, null, 2);
            
            // Create blob and download
            const blob = new Blob([reportJson], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'fraud_analysis_report.json';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        });
    }
    
    // Handle form submission
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Check if file is selected
            if (!fileUpload.files || fileUpload.files.length === 0) {
                showAlert('Please select a CSV file to upload');
                return;
            }
            
            const file = fileUpload.files[0];
            
            // Validate file type
            if (file.type !== 'text/csv' && !file.name.toLowerCase().endsWith('.csv')) {
                showAlert('Please upload a valid CSV file');
                return;
            }
            
            // Validate file size (10MB limit)
            const maxFileSize = 10 * 1024 * 1024; // 10MB
            if (file.size > maxFileSize) {
                showAlert('File size exceeds 10MB limit');
                return;
            }
            
            // Show progress indicator
            uploadForm.style.display = 'none';
            uploadProgress.classList.remove('hidden');
            
            // Create form data
            const formData = new FormData();
            formData.append('file', file);
            
            // Add analysis parameters
            formData.append('analysisType', document.getElementById('analysisType').value);
            formData.append('detectionThreshold', document.getElementById('detectionThreshold').value);
            formData.append('generateReport', document.getElementById('generateReport').checked ? 'true' : 'false');
            
            // Simulate progress updates (in a real app, this would be based on actual progress events)
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += 5;
                if (progress > 90) clearInterval(progressInterval);
                progressFill.style.width = `${progress}%`;
                
                if (progress < 40) {
                    progressText.textContent = 'Uploading and processing file...';
                } else if (progress < 70) {
                    progressText.textContent = 'Running GMM model on transactions...';
                } else {
                    progressText.textContent = 'Analyzing results and generating report...';
                }
            }, 200);
            
            // Send the request to the backend
            fetch(API_ENDPOINT, {
                method: 'POST',
                body: formData
            })
            .then(response => {
                clearInterval(progressInterval);
                progressFill.style.width = '100%';
                progressText.textContent = 'Analysis complete!';
                
                // Check if response was successful
                if (!response.ok) {
                    throw new Error(`HTTP error ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Analysis results:', data);
                currentAnalysisResults = data;
                
                // Wait a moment to show 100% completion
                setTimeout(() => {
                    // Hide progress indicator
                    uploadProgress.classList.add('hidden');
                    
                    // Display results
                    displayResults(data);
                    
                    // Show results section
                    analysisResults.classList.remove('hidden');
                }, 1000);
            })
            .catch(error => {
                clearInterval(progressInterval);
                uploadProgress.classList.add('hidden');
                uploadForm.style.display = 'block';
                showAlert(`Error: ${error.message}. Please try again.`);
                console.error('Error:', error);
            });
        });
    }
    
    // Display analysis results
    function displayResults(data) {
        // Update summary
        totalTransactionsEl.textContent = data.totalTransactions;
        fraudCountEl.textContent = data.fraudCount;
        legitimateCountEl.textContent = data.legitimateCount;
        fraudPercentageEl.textContent = `${data.fraudPercentage.toFixed(2)}%`;
        
        // Display fraudulent transactions
        displayFraudulentTransactions(data.transactionResults);
        
        // Display all transactions
        displayAllTransactions(data.transactionResults);
        
        // Display prevention methods
        displayPreventionMethods(data.preventionMethods);
    }
    
    // Display fraudulent transactions
    function displayFraudulentTransactions(results) {
        const fraudulentResults = results.filter(result => result.prediction === 1);
        
        if (fraudulentResults.length === 0) {
            fraudulentTransactionsEl.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-check-circle"></i>
                    <p>No fraudulent transactions detected.</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        fraudulentResults.forEach(result => {
            const transaction = result.transaction;
            
            html += `
                <div class="transaction-card fraud">
                    <div class="transaction-header">
                        <div class="transaction-title">
                            <h3>${formatCardNumber(transaction['Card Number'] || 'Unknown Card')}</h3>
                            <span class="badge fraud">Fraudulent</span>
                        </div>
                        <div class="transaction-amount">
                            ${formatCurrency(transaction['Transaction Amount'] || 0)}
                        </div>
                    </div>
                    
                    <div class="transaction-details">
                        <div class="transaction-info">
                            <p><strong>Date:</strong> ${transaction['Transaction Date and Time'] || 'Unknown'}</p>
                            <p><strong>Cardholder:</strong> ${transaction['Cardholder Name'] || 'Unknown'}</p>
                            <p><strong>Merchant:</strong> ${transaction['Merchant Name'] || 'Unknown'}</p>
                            <p><strong>Location:</strong> ${transaction['Transaction Location (City or ZIP Code)'] || 'Unknown'}</p>
                            <p><strong>Transaction ID:</strong> ${transaction['Transaction ID'] || 'Unknown'}</p>
                        </div>
                        
                        <div class="risk-assessment">
                            <h4>Risk Assessment (${result.risk_score.toFixed(1)}%)</h4>
                            <div class="risk-meter">
                                <div class="risk-fill" style="width: ${result.risk_score}%"></div>
                            </div>
                            
                            <h4>Fraud Indicators</h4>
                            <ul class="fraud-reasons">
                                ${result.reasons.map(reason => `
                                    <li>
                                        <span class="reason-factor">${reason.factor}</span>
                                        <p>${reason.details}</p>
                                        <span class="risk-badge ${reason.risk_contribution.toLowerCase()}">${reason.risk_contribution}</span>
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                    </div>
                </div>
            `;
        });
        
        fraudulentTransactionsEl.innerHTML = html;
    }
    
    // Display all transactions
    function displayAllTransactions(results) {
        if (results.length === 0) {
            allTransactionsEl.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <p>No transactions available.</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        results.forEach(result => {
            const transaction = result.transaction;
            const isFraud = result.prediction === 1;
            
            html += `
                <div class="transaction-card ${isFraud ? 'fraud' : 'legitimate'}">
                    <div class="transaction-header">
                        <div class="transaction-title">
                            <h3>${formatCardNumber(transaction['Card Number'] || 'Unknown Card')}</h3>
                            <span class="badge ${isFraud ? 'fraud' : 'legitimate'}">${isFraud ? 'Fraudulent' : 'Legitimate'}</span>
                        </div>
                        <div class="transaction-amount">
                            ${formatCurrency(transaction['Transaction Amount'] || 0)}
                        </div>
                    </div>
                    
                    <div class="transaction-info">
                        <p><strong>Date:</strong> ${transaction['Transaction Date and Time'] || 'Unknown'}</p>
                        <p><strong>Cardholder:</strong> ${transaction['Cardholder Name'] || 'Unknown'}</p>
                        <p><strong>Merchant:</strong> ${transaction['Merchant Name'] || 'Unknown'}</p>
                        <p><strong>Location:</strong> ${transaction['Transaction Location (City or ZIP Code)'] || 'Unknown'}</p>
                        <p><strong>Transaction ID:</strong> ${transaction['Transaction ID'] || 'Unknown'}</p>
                    </div>
                    
                    ${isFraud ? `
                        <div class="view-details">
                            <button class="btn-text" onclick="showTransactionDetails('${transaction['Transaction ID'] || ''}')">
                                View Fraud Details <i class="fas fa-chevron-right"></i>
                            </button>
                        </div>
                    ` : ''}
                </div>
            `;
        });
        
        allTransactionsEl.innerHTML = html;
    }
    
    // Display prevention methods
    function displayPreventionMethods(methods) {
        if (!methods || methods.length === 0) {
            preventionMethodsEl.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-shield-alt"></i>
                    <p>No prevention methods available.</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        methods.forEach(method => {
            html += `
                <div class="prevention-method">
                    <h3>${method.title}</h3>
                    <p>${method.description}</p>
                    <div class="implementation-steps">
                        <h4>Implementation Steps</h4>
                        <ol>
                            ${method.steps.map(step => `<li>${step}</li>`).join('')}
                        </ol>
                    </div>
                </div>
            `;
        });
        
        preventionMethodsEl.innerHTML = html;
    }
    
    // Show transaction details modal
    window.showTransactionDetails = function(transactionId) {
        if (!currentAnalysisResults) return;
        
        const transaction = currentAnalysisResults.transactionResults.find(
            result => result.transaction['Transaction ID'] === transactionId
        );
        
        if (!transaction) return;
        
        // Create modal content
        const modalContent = `
            <div class="modal-header">
                <h2>Transaction Details</h2>
                <button class="close-modal" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="transaction-details">
                    <div class="transaction-info">
                        <p><strong>Transaction ID:</strong> ${transaction.transaction['Transaction ID'] || 'Unknown'}</p>
                        <p><strong>Card Number:</strong> ${formatCardNumber(transaction.transaction['Card Number'] || 'Unknown')}</p>
                        <p><strong>Amount:</strong> ${formatCurrency(transaction.transaction['Transaction Amount'] || 0)}</p>
                        <p><strong>Date:</strong> ${transaction.transaction['Transaction Date and Time'] || 'Unknown'}</p>
                        <p><strong>Cardholder:</strong> ${transaction.transaction['Cardholder Name'] || 'Unknown'}</p>
                        <p><strong>Merchant:</strong> ${transaction.transaction['Merchant Name'] || 'Unknown'}</p>
                        <p><strong>MCC:</strong> ${transaction.transaction['Merchant Category Code (MCC)'] || 'Unknown'}</p>
                        <p><strong>Location:</strong> ${transaction.transaction['Transaction Location (City or ZIP Code)'] || 'Unknown'}</p>
                        <p><strong>Currency:</strong> ${transaction.transaction['Transaction Currency'] || 'Unknown'}</p>
                        <p><strong>Card Type:</strong> ${transaction.transaction['Card Type'] || 'Unknown'}</p>
                    </div>
                    
                    <div class="risk-assessment">
                        <h4>Risk Assessment (${transaction.risk_score.toFixed(1)}%)</h4>
                        <div class="risk-meter">
                            <div class="risk-fill" style="width: ${transaction.risk_score}%"></div>
                        </div>
                        
                        <h4>Fraud Indicators</h4>
                        <ul class="fraud-reasons">
                            ${transaction.reasons.map(reason => `
                                <li>
                                    <span class="reason-factor">${reason.factor}</span>
                                    <p>${reason.details}</p>
                                    <span class="risk-badge ${reason.risk_contribution.toLowerCase()}">${reason.risk_contribution}</span>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn" onclick="closeModal()">Close</button>
            </div>
        `;
        
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.id = 'transactionModal';
        modal.innerHTML = `
            <div class="modal-content">
                ${modalContent}
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Show modal
        setTimeout(() => {
            modal.style.display = 'flex';
        }, 10);
    };
    
    // Close modal
    window.closeModal = function() {
        const modal = document.getElementById('transactionModal');
        if (modal) {
            modal.style.display = 'none';
            setTimeout(() => {
                document.body.removeChild(modal);
            }, 300);
        }
    };
    
    // Helper function to format card number
    function formatCardNumber(cardNumber) {
        if (!cardNumber || typeof cardNumber !== 'string' && typeof cardNumber !== 'number') {
            return 'Unknown Card';
        }
        
        const cardStr = String(cardNumber);
        const lastFour = cardStr.slice(-4);
        return `**** **** **** ${lastFour}`;
    }
    
    // Helper function to format currency
    function formatCurrency(amount) {
        const num = parseFloat(amount);
        if (isNaN(num)) return '$0.00';
        
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(num);
    }
    
    // Helper function to show alert
    function showAlert(message) {
        const alertEl = document.createElement('div');
        alertEl.className = 'alert';
        alertEl.textContent = message;
        
        document.body.appendChild(alertEl);
        
        setTimeout(() => {
            alertEl.classList.add('show');
        }, 10);
        
        setTimeout(() => {
            alertEl.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(alertEl);
            }, 300);
        }, 3000);
    }
});