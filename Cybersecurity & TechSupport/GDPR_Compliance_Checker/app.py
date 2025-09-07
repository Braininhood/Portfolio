import sys
import warnings
import random
import time

# Suppress PyQt5 deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import requests
from bs4 import BeautifulSoup
import tldextract
import csv
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QTableWidget, QTableWidgetItem, QTabWidget, 
                             QTextEdit, QMessageBox, QFileDialog, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

# List of common user agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/121.0.0.0 Safari/537.36'
]

class ScannerThread(QThread):
    update_progress = pyqtSignal(int)
    update_results = pyqtSignal(dict)
    scan_complete = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
    
    def run(self):
        try:
            self.update_progress.emit(10)
            
            # Make request to the website with headers that mimic a browser
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
                'Referer': 'https://www.google.com/'
            }
            
            # Add retry mechanism for better success rate
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Rotate user agent on retry
                    if attempt > 0:
                        headers['User-Agent'] = random.choice(USER_AGENTS)
                        self.update_progress.emit(10 + attempt * 5)
                    
                    response = requests.get(self.url, headers=headers, timeout=10)
                    response.raise_for_status()
                    break  # Success, exit retry loop
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:  # Last attempt failed
                        self.error_occurred.emit(f"Failed to connect to {self.url} after {max_retries} attempts: {str(e)}")
                        return
                    # Wait a bit before retrying
                    time.sleep(1)
            
            self.update_progress.emit(30)
            
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract domain information
            domain_info = tldextract.extract(self.url)
            domain = f"{domain_info.domain}.{domain_info.suffix}"
            
            self.update_progress.emit(40)
            
            # Check for various GDPR compliance issues
            results = {
                'cookies': self.check_cookies(soup),
                'privacy_policy': self.check_privacy_policy(soup),
                'data_collection': self.check_data_collection_forms(soup),
                'third_party': self.check_third_party_services(soup),
                'data_rights': self.check_data_rights(soup),
                'legal_basis': self.check_legal_basis(soup),
                'data_transfers': self.check_data_transfers(soup),
                'security_measures': self.check_security_measures(soup, response),
                'domain': domain
            }
            
            self.update_progress.emit(90)
            self.update_results.emit(results)
            self.update_progress.emit(100)
            self.scan_complete.emit()
            
        except Exception as e:
            self.error_occurred.emit(f"Error during scan: {str(e)}")
    
    def check_cookies(self, soup):
        # Check for cookie consent notices
        cookie_terms = ['cookie', 'cookies', 'consent', 'accept cookies', 'gdpr']
        cookie_elements = soup.find_all(string=lambda text: text and any(term in text.lower() for term in cookie_terms))
        
        # Check for cookie banner
        cookie_banner = False
        banner_elements = soup.find_all(['div', 'section', 'header', 'footer'], class_=lambda c: c and any(term in str(c).lower() for term in ['cookie', 'consent', 'banner', 'notice', 'gdpr']))
        if banner_elements:
            cookie_banner = True
        
        # Check for granular consent options
        granular_consent = False
        checkbox_elements = soup.find_all(['input'], type='checkbox')
        toggle_elements = soup.find_all(['button', 'div'], class_=lambda c: c and any(term in str(c).lower() for term in ['toggle', 'switch', 'slider']))
        if checkbox_elements or toggle_elements:
            granular_consent = True
        
        # Check for cookie policy link
        cookie_policy = False
        policy_links = soup.find_all('a', string=lambda text: text and any(term in text.lower() for term in ['cookie policy', 'cookies policy', 'cookie notice']))
        if policy_links:
            cookie_policy = True
        
        has_cookie_notice = len(cookie_elements) > 0 or cookie_banner
        
        # Determine compliance status
        if has_cookie_notice and granular_consent and cookie_policy:
            status = 'Pass'
            recommendation = ''
        elif has_cookie_notice and not granular_consent:
            status = 'Fail'
            recommendation = 'Website must provide granular consent options for different cookie categories (necessary, preferences, statistics, marketing).'
        elif has_cookie_notice and not cookie_policy:
            status = 'Fail'
            recommendation = 'Website should provide a detailed cookie policy explaining all cookies used, their purposes, duration, and how to opt out.'
        else:
            status = 'Fail'
            recommendation = 'Website should include a cookie consent notice before setting non-essential cookies. The notice should explain cookie usage and provide user options to accept or decline.'
        
        return {
            'has_cookie_notice': has_cookie_notice,
            'has_granular_consent': granular_consent,
            'has_cookie_policy': cookie_policy,
            'cookie_elements_count': len(cookie_elements),
            'status': status,
            'recommendation': recommendation
        }
    
    def check_privacy_policy(self, soup):
        # Check for privacy policy links
        privacy_terms = ['privacy policy', 'privacy notice', 'data protection']
        privacy_links = soup.find_all('a', string=lambda text: text and any(term in text.lower() for term in privacy_terms))
        
        has_privacy_policy = len(privacy_links) > 0
        
        return {
            'has_privacy_policy': has_privacy_policy,
            'policy_links_count': len(privacy_links),
            'status': 'Pass' if has_privacy_policy else 'Fail',
            'recommendation': 'Website should include a privacy policy' if not has_privacy_policy else ''
        }
    
    def check_data_collection_forms(self, soup):
        # Look for forms that collect personal data
        forms = soup.find_all('form')
        data_inputs = ['name', 'email', 'phone', 'address', 'password']
        
        form_issues = []
        for form in forms:
            inputs = form.find_all('input')
            data_collection_fields = [inp for inp in inputs if inp.get('name') and 
                                     any(field in inp.get('name', '').lower() for field in data_inputs)]
            
            if data_collection_fields:
                # Check if form has consent checkbox
                checkbox = form.find('input', {'type': 'checkbox'})
                if not checkbox:
                    form_issues.append({
                        'form_action': form.get('action', 'Unknown'),
                        'collects_data': True,
                        'has_consent': False
                    })
        
        return {
            'forms_total': len(forms),
            'forms_with_issues': len(form_issues),
            'form_details': form_issues,
            'status': 'Pass' if len(form_issues) == 0 else 'Fail',
            'recommendation': 'Add consent checkboxes to all forms collecting personal data' if form_issues else ''
        }
    
    def check_third_party_services(self, soup):
        # Check for third-party scripts/services
        scripts = soup.find_all('script')
        
        known_third_parties = [
            'google-analytics', 'googletagmanager', 'facebook', 'twitter', 
            'linkedin', 'hotjar', 'segment', 'mixpanel', 'amplitude'
        ]
        
        third_party_services = []
        for script in scripts:
            src = script.get('src', '')
            if src and any(service in src.lower() for service in known_third_parties):
                third_party_services.append({
                    'service': next((service for service in known_third_parties if service in src.lower()), 'unknown'),
                    'source': src
                })
        
        return {
            'third_party_count': len(third_party_services),
            'services': third_party_services,
            'status': 'Warning' if third_party_services else 'Pass',
            'recommendation': 'Ensure all third-party services comply with GDPR and are disclosed in privacy policy' 
                              if third_party_services else ''
        }

    def check_data_rights(self, soup):
        # Check for data subject rights information
        rights_terms = ['right to access', 'right to erasure', 'right to be forgotten', 'data subject rights', 
                        'your rights', 'user rights', 'access request', 'deletion request', 'data rights']
        
        rights_elements = soup.find_all(string=lambda text: text and any(term in text.lower() for term in rights_terms))
        
        # Check for data rights links or contact information
        rights_links = soup.find_all('a', string=lambda text: text and any(term in text.lower() for term in 
                                                                      ['contact us', 'access request', 'delete my data', 
                                                                       'data protection', 'privacy rights', 'data subject access']))
        
        has_rights_info = len(rights_elements) > 0
        has_rights_contact = len(rights_links) > 0
        
        if has_rights_info and has_rights_contact:
            status = 'Pass'
            recommendation = ''
        elif has_rights_info and not has_rights_contact:
            status = 'Warning'
            recommendation = 'Website should provide a clear mechanism for users to exercise their data rights (access, erasure, etc.).'
        else:
            status = 'Fail'
            recommendation = 'Website should inform users about their data rights under GDPR and provide a way to exercise these rights.'
        
        return {
            'has_rights_info': has_rights_info,
            'has_rights_contact': has_rights_contact,
            'rights_elements_count': len(rights_elements),
            'status': status,
            'recommendation': recommendation
        }

    def check_legal_basis(self, soup):
        # Check for legal basis information
        legal_basis_terms = ['legal basis', 'lawful basis', 'legitimate interest', 'consent', 'contract', 
                            'legal obligation', 'vital interests', 'public task', 'official authority']
        
        legal_basis_elements = soup.find_all(string=lambda text: text and any(term in text.lower() for term in legal_basis_terms))
        
        has_legal_basis = len(legal_basis_elements) > 0
        
        if has_legal_basis:
            status = 'Pass'
            recommendation = ''
        else:
            status = 'Fail'
            recommendation = 'Website should clearly state the legal basis for processing personal data (e.g., consent, legitimate interest, contractual necessity).'
        
        return {
            'has_legal_basis': has_legal_basis,
            'legal_basis_elements_count': len(legal_basis_elements),
            'status': status,
            'recommendation': recommendation
        }

    def check_data_transfers(self, soup):
        # Check for international data transfer information
        transfer_terms = ['data transfer', 'international transfer', 'outside the EU', 'outside the EEA', 
                         'third country', 'standard contractual clauses', 'privacy shield', 'adequacy decision']
        
        transfer_elements = soup.find_all(string=lambda text: text and any(term in text.lower() for term in transfer_terms))
        
        has_transfer_info = len(transfer_elements) > 0
        
        if has_transfer_info:
            status = 'Pass'
            recommendation = ''
        else:
            status = 'Warning'
            recommendation = 'If data is transferred outside the EU/EEA, website should disclose this and explain the safeguards in place.'
        
        return {
            'has_transfer_info': has_transfer_info,
            'transfer_elements_count': len(transfer_elements),
            'status': status,
            'recommendation': recommendation
        }

    def check_security_measures(self, soup, response):
        # Check for SSL/TLS
        has_https = response.url.startswith('https')
        
        # Check for security information
        security_terms = ['data security', 'information security', 'security measures', 'protect your data', 
                         'safeguards', 'encryption', 'secure socket layer', 'ssl', 'tls']
        
        security_elements = soup.find_all(string=lambda text: text and any(term in text.lower() for term in security_terms))
        
        has_security_info = len(security_elements) > 0
        
        if has_https and has_security_info:
            status = 'Pass'
            recommendation = ''
        elif has_https and not has_security_info:
            status = 'Warning'
            recommendation = 'Website should provide information about security measures used to protect personal data.'
        else:
            status = 'Fail'
            recommendation = 'Website should use HTTPS encryption and disclose security measures taken to protect user data.'
        
        return {
            'has_https': has_https,
            'has_security_info': has_security_info,
            'security_elements_count': len(security_elements),
            'status': status,
            'recommendation': recommendation
        }

class GDPRComplianceChecker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GDPR Compliance Checker")
        self.setMinimumSize(900, 700)
        
        # Set up the central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create UI components
        self.setup_ui()
    
    def setup_ui(self):
        # Header section
        header_layout = QVBoxLayout()
        title_label = QLabel("GDPR Compliance Checker")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        subtitle_label = QLabel("Scan websites for potential GDPR compliance issues")
        subtitle_label.setFont(QFont("Arial", 12))
        subtitle_label.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        self.main_layout.addLayout(header_layout)
        
        # URL input section
        url_layout = QHBoxLayout()
        url_label = QLabel("Website URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com")
        scan_button = QPushButton("Scan")
        scan_button.clicked.connect(self.start_scan)
        
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input, 3)
        url_layout.addWidget(scan_button)
        self.main_layout.addLayout(url_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.main_layout.addWidget(self.progress_bar)
        
        # Tabs for different results
        self.results_tabs = QTabWidget()
        
        # Summary tab
        self.summary_tab = QWidget()
        summary_layout = QVBoxLayout(self.summary_tab)
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        summary_layout.addWidget(self.summary_text)
        
        # Details tab
        self.details_tab = QWidget()
        details_layout = QVBoxLayout(self.details_tab)
        self.details_table = QTableWidget()
        self.details_table.setColumnCount(3)
        self.details_table.setHorizontalHeaderLabels(["Check", "Status", "Recommendation"])
        self.details_table.horizontalHeader().setStretchLastSection(True)
        details_layout.addWidget(self.details_table)
        
        # Raw data tab
        self.raw_tab = QWidget()
        raw_layout = QVBoxLayout(self.raw_tab)
        self.raw_text = QTextEdit()
        self.raw_text.setReadOnly(True)
        raw_layout.addWidget(self.raw_text)
        
        # Add tabs to tab widget
        self.results_tabs.addTab(self.summary_tab, "Summary")
        self.results_tabs.addTab(self.details_tab, "Details")
        self.results_tabs.addTab(self.raw_tab, "Raw Data")
        
        self.main_layout.addWidget(self.results_tabs)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        save_report_button = QPushButton("Save Report")
        save_report_button.clicked.connect(self.save_report)
        
        action_layout.addWidget(save_report_button)
        self.main_layout.addLayout(action_layout)
    
    def start_scan(self):
        url = self.url_input.text().strip()
        
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a valid URL.")
            return
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            self.url_input.setText(url)
        
        # Reset UI elements
        self.progress_bar.setValue(0)
        self.summary_text.clear()
        self.details_table.setRowCount(0)
        self.raw_text.clear()
        
        # Start the scanner thread
        self.scanner_thread = ScannerThread(url)
        self.scanner_thread.update_progress.connect(self.update_progress)
        self.scanner_thread.update_results.connect(self.display_results)
        self.scanner_thread.scan_complete.connect(self.scan_completed)
        self.scanner_thread.error_occurred.connect(self.show_error)
        
        self.scanner_thread.start()
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def display_results(self, results):
        # Summary tab
        domain = results.get('domain', 'Unknown')
        
        summary = f"GDPR Compliance Scan Results for {domain}\n\n"
        
        compliance_issues = 0
        warnings = 0
        
        # Count issues
        checks = ['cookies', 'privacy_policy', 'data_collection', 'third_party', 
                  'data_rights', 'legal_basis', 'data_transfers', 'security_measures']
        for check in checks:
            if check in results:
                status = results[check].get('status', '')
                if status == 'Fail':
                    compliance_issues += 1
                elif status == 'Warning':
                    warnings += 1
        
        summary += f"Compliance Issues Found: {compliance_issues}\n"
        summary += f"Warnings: {warnings}\n\n"
        
        if compliance_issues > 0:
            summary += "This website may not be fully GDPR compliant. Please review the details tab for specific issues.\n\n"
        else:
            summary += "No major compliance issues detected. Review warnings for potential improvements.\n\n"
        
        # Add issue details to summary
        summary += "== FINDINGS SUMMARY ==\n\n"
        
        if 'cookies' in results:
            cookie_result = results['cookies']
            summary += "🍪 COOKIE CONSENT:\n"
            summary += f"  Status: {cookie_result.get('status', 'Unknown')}\n"
            if cookie_result.get('has_cookie_notice', False):
                summary += f"  Found cookie consent notice/banner: Yes\n"
                summary += f"  Granular consent options: {'Yes' if cookie_result.get('has_granular_consent', False) else 'No'}\n"
                summary += f"  Cookie policy found: {'Yes' if cookie_result.get('has_cookie_policy', False) else 'No'}\n"
            else:
                summary += "  No cookie consent notice detected\n"
            if cookie_result.get('recommendation'):
                summary += f"  Recommendation: {cookie_result.get('recommendation')}\n"
            summary += "\n"
        
        if 'privacy_policy' in results:
            privacy_result = results['privacy_policy']
            summary += "📜 PRIVACY POLICY:\n"
            summary += f"  Status: {privacy_result.get('status', 'Unknown')}\n"
            if privacy_result.get('has_privacy_policy', False):
                summary += f"  Found {privacy_result.get('policy_links_count', 0)} privacy policy links\n"
            else:
                summary += "  No privacy policy found\n"
            if privacy_result.get('recommendation'):
                summary += f"  Recommendation: {privacy_result.get('recommendation')}\n"
            summary += "\n"
        
        if 'data_collection' in results:
            forms_result = results['data_collection']
            summary += "📝 DATA COLLECTION FORMS:\n"
            summary += f"  Status: {forms_result.get('status', 'Unknown')}\n"
            summary += f"  Total forms found: {forms_result.get('forms_total', 0)}\n"
            summary += f"  Forms with issues: {forms_result.get('forms_with_issues', 0)}\n"
            if forms_result.get('recommendation'):
                summary += f"  Recommendation: {forms_result.get('recommendation')}\n"
            summary += "\n"
        
        if 'third_party' in results:
            third_party_result = results['third_party']
            summary += "🔄 THIRD-PARTY SERVICES:\n"
            summary += f"  Status: {third_party_result.get('status', 'Unknown')}\n"
            summary += f"  Third-party services detected: {third_party_result.get('third_party_count', 0)}\n"
            if third_party_result.get('services'):
                for service in third_party_result.get('services', []):
                    summary += f"    - {service.get('service', 'unknown')} ({service.get('source', '')})\n"
            if third_party_result.get('recommendation'):
                summary += f"  Recommendation: {third_party_result.get('recommendation')}\n"
            summary += "\n"
        
        if 'data_rights' in results:
            rights_result = results['data_rights']
            summary += "⚖️ DATA SUBJECT RIGHTS:\n"
            summary += f"  Status: {rights_result.get('status', 'Unknown')}\n"
            summary += f"  Information about data rights: {'Yes' if rights_result.get('has_rights_info', False) else 'No'}\n"
            summary += f"  Contact for exercising rights: {'Yes' if rights_result.get('has_rights_contact', False) else 'No'}\n"
            if rights_result.get('recommendation'):
                summary += f"  Recommendation: {rights_result.get('recommendation')}\n"
            summary += "\n"
        
        if 'legal_basis' in results:
            legal_basis_result = results['legal_basis']
            summary += "📋 LEGAL BASIS FOR PROCESSING:\n"
            summary += f"  Status: {legal_basis_result.get('status', 'Unknown')}\n"
            summary += f"  Legal basis information found: {'Yes' if legal_basis_result.get('has_legal_basis', False) else 'No'}\n"
            if legal_basis_result.get('recommendation'):
                summary += f"  Recommendation: {legal_basis_result.get('recommendation')}\n"
            summary += "\n"
        
        if 'data_transfers' in results:
            transfers_result = results['data_transfers']
            summary += " INTERNATIONAL DATA TRANSFERS:\n"
            summary += f"  Status: {transfers_result.get('status', 'Unknown')}\n"
            summary += f"  Information about transfers found: {'Yes' if transfers_result.get('has_transfer_info', False) else 'No'}\n"
            if transfers_result.get('recommendation'):
                summary += f"  Recommendation: {transfers_result.get('recommendation')}\n"
            summary += "\n"
        
        if 'security_measures' in results:
            security_result = results['security_measures']
            summary += "🔒 SECURITY MEASURES:\n"
            summary += f"  Status: {security_result.get('status', 'Unknown')}\n"
            summary += f"  HTTPS encryption: {'Yes' if security_result.get('has_https', False) else 'No'}\n"
            summary += f"  Security information disclosed: {'Yes' if security_result.get('has_security_info', False) else 'No'}\n"
            if security_result.get('recommendation'):
                summary += f"  Recommendation: {security_result.get('recommendation')}\n"
            summary += "\n"
        
        self.summary_text.setText(summary)
        
        # Details tab
        self.details_table.setRowCount(len(checks))
        
        for i, check in enumerate(checks):
            if check in results:
                check_name = QTableWidgetItem(check.replace('_', ' ').title())
                status = QTableWidgetItem(results[check].get('status', 'Unknown'))
                recommendation = QTableWidgetItem(results[check].get('recommendation', ''))
                
                self.details_table.setItem(i, 0, check_name)
                self.details_table.setItem(i, 1, status)
                self.details_table.setItem(i, 2, recommendation)
        
        # Raw data tab
        self.raw_text.setText(str(results))
    
    def scan_completed(self):
        QMessageBox.information(self, "Scan Complete", "Website scan has been completed successfully.")
    
    def show_error(self, error_message):
        QMessageBox.critical(self, "Scan Error", error_message)
        self.progress_bar.setValue(0)
    
    def save_report(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Report", "", "CSV Files (*.csv);;Text Files (*.txt);;PDF Files (*.pdf);;All Files (*)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    # Create a CSV file with detailed findings
                    with open(file_path, 'w', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(["Category", "Status", "Finding", "Recommendation"])
                        
                        # Get the results from raw data tab (using eval to convert string to dict)
                        try:
                            results_str = self.raw_text.toPlainText()
                            results = eval(results_str)
                            
                            # Write cookie findings
                            if 'cookies' in results:
                                cookie_result = results['cookies']
                                writer.writerow([
                                    "Cookies", 
                                    cookie_result.get('status', 'Unknown'),
                                    f"Cookie Notice: {'Yes' if cookie_result.get('has_cookie_notice', False) else 'No'}, " +
                                    f"Granular Consent: {'Yes' if cookie_result.get('has_granular_consent', False) else 'No'}, " +
                                    f"Cookie Policy: {'Yes' if cookie_result.get('has_cookie_policy', False) else 'No'}",
                                    cookie_result.get('recommendation', '')
                                ])
                            
                            # Write privacy policy findings
                            if 'privacy_policy' in results:
                                privacy_result = results['privacy_policy']
                                writer.writerow([
                                    "Privacy Policy", 
                                    privacy_result.get('status', 'Unknown'),
                                    f"Policy Found: {'Yes' if privacy_result.get('has_privacy_policy', False) else 'No'}, Links: {privacy_result.get('policy_links_count', 0)}",
                                    privacy_result.get('recommendation', '')
                                ])
                            
                            # Write data collection form findings
                            if 'data_collection' in results:
                                forms_result = results['data_collection']
                                writer.writerow([
                                    "Data Collection Forms", 
                                    forms_result.get('status', 'Unknown'),
                                    f"Total Forms: {forms_result.get('forms_total', 0)}, Forms with Issues: {forms_result.get('forms_with_issues', 0)}",
                                    forms_result.get('recommendation', '')
                                ])
                                
                                # Add details for each form with issues
                                for i, form in enumerate(forms_result.get('form_details', [])):
                                    writer.writerow([
                                        f"  Form {i+1}", 
                                        "Fail",
                                        f"Action: {form.get('form_action', 'Unknown')}, Consent: {'Yes' if form.get('has_consent', False) else 'No'}",
                                        "Add consent checkbox to this form"
                                    ])
                            
                            # Write third-party service findings
                            if 'third_party' in results:
                                third_party_result = results['third_party']
                                writer.writerow([
                                    "Third-Party Services", 
                                    third_party_result.get('status', 'Unknown'),
                                    f"Services Detected: {third_party_result.get('third_party_count', 0)}",
                                    third_party_result.get('recommendation', '')
                                ])
                                
                                # Add details for each third-party service
                                for i, service in enumerate(third_party_result.get('services', [])):
                                    writer.writerow([
                                        f"  Service {i+1}", 
                                        "Info",
                                        f"Type: {service.get('service', 'unknown')}",
                                        f"Source: {service.get('source', '')}"
                                    ])

                            # Write data subject rights findings
                            if 'data_rights' in results:
                                rights_result = results['data_rights']
                                writer.writerow([
                                    "Data Subject Rights", 
                                    rights_result.get('status', 'Unknown'),
                                    f"Rights Info: {'Yes' if rights_result.get('has_rights_info', False) else 'No'}, " +
                                    f"Contact Method: {'Yes' if rights_result.get('has_rights_contact', False) else 'No'}",
                                    rights_result.get('recommendation', '')
                                ])

                            # Write legal basis findings
                            if 'legal_basis' in results:
                                legal_basis_result = results['legal_basis']
                                writer.writerow([
                                    "Legal Basis", 
                                    legal_basis_result.get('status', 'Unknown'),
                                    f"Legal Basis Info: {'Yes' if legal_basis_result.get('has_legal_basis', False) else 'No'}",
                                    legal_basis_result.get('recommendation', '')
                                ])

                            # Write data transfers findings
                            if 'data_transfers' in results:
                                data_transfers_result = results['data_transfers']
                                writer.writerow([
                                    "International Data Transfers", 
                                    data_transfers_result.get('status', 'Unknown'),
                                    f"Transfer Info: {'Yes' if data_transfers_result.get('has_transfer_info', False) else 'No'}",
                                    data_transfers_result.get('recommendation', '')
                                ])

                            # Write security measures findings
                            if 'security_measures' in results:
                                security_measures_result = results['security_measures']
                                writer.writerow([
                                    "Security Measures", 
                                    security_measures_result.get('status', 'Unknown'),
                                    f"HTTPS: {'Yes' if security_measures_result.get('has_https', False) else 'No'}, " +
                                    f"Security Info: {'Yes' if security_measures_result.get('has_security_info', False) else 'No'}",
                                    security_measures_result.get('recommendation', '')
                                ])
                        except:
                            # Fallback if parsing fails
                            for row in range(self.details_table.rowCount()):
                                writer.writerow([
                                    self.details_table.item(row, 0).text(),
                                    self.details_table.item(row, 1).text(),
                                    "",
                                    self.details_table.item(row, 2).text()
                                ])
                else:
                    # Save as text file with complete report
                    with open(file_path, 'w') as f:
                        domain = "Unknown"
                        try:
                            results_str = self.raw_text.toPlainText()
                            results = eval(results_str)
                            domain = results.get('domain', 'Unknown')
                        except:
                            pass
                        
                        f.write(f"GDPR COMPLIANCE SCAN REPORT\n")
                        f.write(f"=============================\n")
                        f.write(f"Website: {domain}\n")
                        f.write(f"Scan Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"=============================\n\n")
                        
                        f.write(self.summary_text.toPlainText())
                        
                        f.write("\n\n=== DETAILED COMPLIANCE ANALYSIS ===\n\n")
                        
                        f.write("GDPR COMPLIANCE REQUIREMENTS:\n\n")
                        
                        f.write("1. COOKIE CONSENT (GDPR Art. 6, ePrivacy Directive)\n")
                        f.write("   Requirement: Websites must obtain user consent before using non-essential cookies.\n")
                        f.write("   Solution: Implement a cookie consent banner that allows users to accept/reject cookies with granular options.\n\n")
                        
                        f.write("2. PRIVACY POLICY (GDPR Art. 12-14)\n")
                        f.write("   Requirement: Clear and accessible privacy policy detailing how user data is collected and processed.\n")
                        f.write("   Solution: Create a comprehensive privacy policy and link it prominently throughout the website.\n\n")
                        
                        f.write("3. DATA COLLECTION FORMS (GDPR Art. 6-7)\n")
                        f.write("   Requirement: Explicit consent must be obtained when collecting personal data.\n")
                        f.write("   Solution: Add consent checkboxes to forms collecting personal data with clear explanation of data usage.\n\n")
                        
                        f.write("4. THIRD-PARTY SERVICES (GDPR Art. 28)\n")
                        f.write("   Requirement: Ensure third-party data processors comply with GDPR.\n")
                        f.write("   Solution: Audit third-party services, obtain data processing agreements, and disclose usage in privacy policy.\n\n")
                        
                        f.write("5. DATA SUBJECT RIGHTS (GDPR Art. 15-22)\n")
                        f.write("   Requirement: Users must be able to exercise their rights including access, rectification, erasure, etc.\n")
                        f.write("   Solution: Provide clear information about these rights and a straightforward way to exercise them.\n\n")
                        
                        f.write("6. LEGAL BASIS FOR PROCESSING (GDPR Art. 6)\n")
                        f.write("   Requirement: All personal data processing must have a lawful basis.\n")
                        f.write("   Solution: Clearly state the legal basis for each type of data processing in your privacy policy.\n\n")
                        
                        f.write("7. INTERNATIONAL DATA TRANSFERS (GDPR Art. 44-50)\n")
                        f.write("   Requirement: Transfers of personal data outside the EU/EEA must have appropriate safeguards.\n")
                        f.write("   Solution: Implement appropriate transfer mechanisms and disclose these in your privacy policy.\n\n")
                        
                        f.write("8. SECURITY MEASURES (GDPR Art. 32)\n")
                        f.write("   Requirement: Implement appropriate technical and organizational measures to protect personal data.\n")
                        f.write("   Solution: Use HTTPS encryption, secure storage, and other security measures, and disclose these to users.\n\n")
                        
                        f.write("=== SCAN RESULTS ===\n\n")
                        
                        for row in range(self.details_table.rowCount()):
                            check = self.details_table.item(row, 0).text()
                            status = self.details_table.item(row, 1).text()
                            recommendation = self.details_table.item(row, 2).text()
                            
                            f.write(f"{check}: {status}\n")
                            if recommendation:
                                f.write(f"  Recommendation: {recommendation}\n")
                            f.write("\n")
                        
                        f.write("\n=== REMEDIATION GUIDELINES ===\n\n")
                        
                        f.write("COOKIE COMPLIANCE:\n")
                        f.write("- Implement a cookie consent banner with 'Accept', 'Reject', and 'Preferences' options\n")
                        f.write("- Ensure cookies are not loaded before consent is given (prior opt-in)\n")
                        f.write("- Provide granular consent options for different cookie categories (necessary, preferences, statistics, marketing)\n")
                        f.write("- Make consent preferences as easy to withdraw as they are to give\n")
                        f.write("- Create a comprehensive cookie policy listing all cookies used, their purpose, duration, and provider\n")
                        f.write("- Store user consent securely for documentation purposes (consent receipt)\n")
                        f.write("- Respect user choices by not setting rejected cookies\n")
                        f.write("- Ensure consent renewal at appropriate intervals (6-12 months)\n\n")
                        
                        f.write("PRIVACY POLICY REQUIREMENTS:\n")
                        f.write("- Clearly identify the data controller and provide contact information\n")
                        f.write("- List all types of personal data collected and processed\n")
                        f.write("- Explain the legal basis for each type of processing\n")
                        f.write("- Detail any third-party data sharing and the purposes\n")
                        f.write("- Include information about data retention periods\n")
                        f.write("- Explain user rights (access, correction, deletion, portability, etc.) and how to exercise them\n")
                        f.write("- Disclose international data transfers and safeguards\n")
                        f.write("- Use clear, plain language understandable by the average person\n")
                        f.write("- Make the policy easily accessible from all pages\n\n")
                        
                        f.write("FORM CONSENT IMPLEMENTATION:\n")
                        f.write("- Add unticked consent checkboxes to all data collection forms\n")
                        f.write("- Use clear language explaining how the data will be used\n")
                        f.write("- Separate essential data collection from optional data collection\n")
                        f.write("- Separate marketing consent from service provisioning consent\n")
                        f.write("- Implement age verification for services directed at minors\n")
                        f.write("- Store consent records securely\n")
                        f.write("- Make it easy to withdraw consent and delete submitted data\n\n")
                        
                        f.write("THIRD-PARTY COMPLIANCE:\n")
                        f.write("- List all third-party services in your privacy policy\n")
                        f.write("- Sign data processing agreements (DPAs) with all data processors\n")
                        f.write("- Only choose processors that provide sufficient guarantees of GDPR compliance\n")
                        f.write("- Conduct due diligence on third-party services before integration\n")
                        f.write("- Only share necessary data with third parties (data minimization)\n")
                        f.write("- Consider EU-based alternatives for essential services\n")
                        f.write("- Implement proper data transfer mechanisms for non-EU services\n\n")
                        
                        f.write("DATA SUBJECT RIGHTS IMPLEMENTATION:\n")
                        f.write("- Create a specific page or section explaining user rights\n")
                        f.write("- Provide a dedicated email address or form for rights requests\n")
                        f.write("- Implement procedures to verify the identity of requesters\n")
                        f.write("- Establish processes to respond to requests within one month\n")
                        f.write("- Create templates for different types of rights responses\n")
                        f.write("- Train staff on handling data subject requests correctly\n")
                        f.write("- Keep records of all requests and responses\n\n")
                        
                        f.write("LEGAL BASIS DOCUMENTATION:\n")
                        f.write("- Document the legal basis for each processing activity\n")
                        f.write("- If using legitimate interests, conduct and document legitimate interest assessments (LIAs)\n")
                        f.write("- If using consent, ensure it meets all GDPR requirements (freely given, specific, informed, unambiguous)\n")
                        f.write("- For contractual necessity, clearly explain which data is essential for the contract\n")
                        f.write("- For legal obligations, cite the specific laws requiring the processing\n")
                        f.write("- Review and update legal bases regularly as processing activities change\n\n")
                        
                        f.write("INTERNATIONAL DATA TRANSFERS:\n")
                        f.write("- Map all data flows to identify international transfers\n")
                        f.write("- Implement appropriate safeguards for transfers (SCCs, BCRs, adequacy decisions)\n")
                        f.write("- Conduct transfer impact assessments (TIAs) for each transfer\n")
                        f.write("- Consider data localization within the EU where feasible\n")
                        f.write("- Update privacy policies to clearly disclose international transfers\n")
                        f.write("- Monitor changes in international data transfer laws\n\n")
                        
                        f.write("SECURITY MEASURES IMPLEMENTATION:\n")
                        f.write("- Implement HTTPS encryption across the entire website\n")
                        f.write("- Use strong encryption for stored personal data\n")
                        f.write("- Implement access controls and authentication measures\n")
                        f.write("- Conduct regular security assessments and penetration testing\n")
                        f.write("- Establish data breach detection and notification procedures\n")
                        f.write("- Train staff on security best practices\n")
                        f.write("- Document all security measures for accountability\n")
                        f.write("- Implement data backup and disaster recovery procedures\n\n")
                        
                        f.write("ADDITIONAL CONSIDERATIONS:\n")
                        f.write("- Implement data protection by design and by default principles\n")
                        f.write("- Consider appointing a Data Protection Officer (DPO) if required\n")
                        f.write("- Conduct Data Protection Impact Assessments (DPIAs) for high-risk processing\n")
                        f.write("- Maintain records of processing activities\n")
                        f.write("- Regular staff training on data protection\n")
                        f.write("- Regular review and update of all privacy practices\n")
                        f.write("- Document all compliance efforts for accountability\n\n")
                        
                        f.write("This report is for informational purposes only and does not constitute legal advice. For specific legal guidance, consult with a qualified legal professional specialized in data protection.")
                
                QMessageBox.information(self, "Report Saved", f"Enhanced GDPR compliance report has been saved to {file_path}")
            
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save report: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = GDPRComplianceChecker()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 