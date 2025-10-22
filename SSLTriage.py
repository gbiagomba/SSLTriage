#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Burp Suite Extension for SSL Triage using SSLyze
This extension provides a GUI for configuring SSLyze, performs passive and active scans,
and logs results in Burp Suite.
Author: SSLTriage Team
Version: 1.0.0
License: MIT
"""

from burp import IBurpExtender, IScannerCheck, IScanIssue, IContextMenuFactory, IHttpRequestResponse, ITab
from java.util import ArrayList
from javax.swing import JPanel, JLabel, JCheckBox, JTextField, JScrollPane, JTextArea, BoxLayout, JButton, JComboBox
from java.awt import FlowLayout, Dimension
from javax.swing import JMenuItem, Box
import subprocess
import json
import os
import sys
import re

# Constants
VERSION = "1.0.0"
CONFIG_FILE = os.path.expanduser("~/.ssltriage_config.json")
TEMP_DIR = os.path.expanduser("~/tmp") if not os.path.exists("/tmp") else "/tmp"

def find_sslyze_path():
    """
    Automatically detect sslyze binary in PATH
    Returns the full path if found, None otherwise
    """
    paths_to_check = []

    # Get PATH environment variable
    path_env = os.environ.get('PATH', '')
    if path_env:
        paths_to_check.extend(path_env.split(os.pathsep))

    # Add common installation locations
    common_paths = [
        '/usr/local/bin',
        '/usr/bin',
        '/opt/homebrew/bin',
        os.path.expanduser('~/.local/bin'),
        os.path.expanduser('~/bin')
    ]
    paths_to_check.extend(common_paths)

    # Search for sslyze in all paths
    for path_dir in paths_to_check:
        if not path_dir:
            continue
        sslyze_path = os.path.join(path_dir, 'sslyze')
        if os.path.isfile(sslyze_path) and os.access(sslyze_path, os.X_OK):
            return sslyze_path

    return None

def sanitize_filename(name):
    """
    Sanitize a string to be safe for use in filenames
    Replaces problematic characters with underscores
    """
    # Replace colons, slashes, and other problematic characters
    sanitized = re.sub(r'[:/\\?%*|"<>]', '_', name)
    # Remove any remaining non-alphanumeric characters except dots, dashes, and underscores
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', sanitized)
    return sanitized

def validate_sslyze_path(path):
    """
    Validate that the sslyze path exists and is executable
    Returns tuple (is_valid, error_message)
    """
    if not path or path.strip() == "":
        return (False, "SSLyze path is empty")

    if not os.path.exists(path):
        return (False, "SSLyze binary not found at: {}".format(path))

    if not os.path.isfile(path):
        return (False, "SSLyze path is not a file: {}".format(path))

    if not os.access(path, os.X_OK):
        return (False, "SSLyze binary is not executable: {}".format(path))

    return (True, "")


class SSLTriageTab(ITab):
    """
    GUI Tab for SSLTriage configuration and logging
    """
    def __init__(self, callbacks):
        self._callbacks = callbacks
        self._panel = JPanel()
        self._panel.setLayout(BoxLayout(self._panel, BoxLayout.Y_AXIS))

        # Load configuration
        self._config = self.load_config()

        # Initialize GUI components
        self._init_gui()

        # Register tab
        callbacks.addSuiteTab(self)

        # Auto-detect sslyze if not configured
        if not self.ssl_path.getText() or self.ssl_path.getText().strip() == "":
            detected_path = find_sslyze_path()
            if detected_path:
                self.ssl_path.setText(detected_path)
                self.log("[+] Auto-detected sslyze at: {}".format(detected_path))
            else:
                self.log("[!] Could not auto-detect sslyze. Please configure path manually.")

    def _init_gui(self):
        """Initialize GUI components"""
        # Title
        title_panel = JPanel(FlowLayout(FlowLayout.LEFT))
        title_label = JLabel("SSLTriage v{} - SSL/TLS Security Scanner".format(VERSION))
        title_panel.add(title_label)
        self._panel.add(title_panel)

        self._panel.add(Box.createRigidArea(Dimension(0, 10)))

        # SSLyze path configuration
        path_panel = JPanel(FlowLayout(FlowLayout.LEFT))
        path_panel.add(JLabel("Path to sslyze binary:"))
        self.ssl_path = JTextField(self._config.get("sslyze_path", ""), 40)
        path_panel.add(self.ssl_path)

        # Auto-detect button
        self.detect_btn = JButton("Auto-detect", actionPerformed=self._auto_detect_sslyze)
        path_panel.add(self.detect_btn)

        # Validate button
        self.validate_btn = JButton("Validate", actionPerformed=self._validate_sslyze)
        path_panel.add(self.validate_btn)

        self._panel.add(path_panel)

        self._panel.add(Box.createRigidArea(Dimension(0, 10)))

        # Scan options
        options_panel = JPanel(FlowLayout(FlowLayout.LEFT))
        self.passive_box = JCheckBox("Enable Passive Scanning", self._config.get("enable_passive", True))
        self.active_box = JCheckBox("Enable Active Scanning", self._config.get("enable_active", False))
        options_panel.add(self.passive_box)
        options_panel.add(self.active_box)
        self._panel.add(options_panel)

        self._panel.add(Box.createRigidArea(Dimension(0, 10)))

        # Scan mode dropdown
        mode_panel = JPanel(FlowLayout(FlowLayout.LEFT))
        mode_panel.add(JLabel("Scan mode:"))
        scan_modes = ["--regular", "--full"]
        default_mode = self._config.get("scan_mode", "--regular")
        self.scan_mode_combo = JComboBox(scan_modes)
        if default_mode in scan_modes:
            self.scan_mode_combo.setSelectedItem(default_mode)
        mode_panel.add(self.scan_mode_combo)
        self._panel.add(mode_panel)

        self._panel.add(Box.createRigidArea(Dimension(0, 10)))

        # Save configuration button
        save_panel = JPanel(FlowLayout(FlowLayout.LEFT))
        self.save_btn = JButton("Save Configuration", actionPerformed=self._save_config_action)
        save_panel.add(self.save_btn)
        self._panel.add(save_panel)

        self._panel.add(Box.createRigidArea(Dimension(0, 10)))

        # Log area
        log_label_panel = JPanel(FlowLayout(FlowLayout.LEFT))
        log_label_panel.add(JLabel("Scan Log:"))
        self._panel.add(log_label_panel)

        self.log_area = JTextArea(15, 80)
        self.log_area.setEditable(False)
        self.log_area.setLineWrap(True)
        self.log_area.setWrapStyleWord(True)
        scroll_pane = JScrollPane(self.log_area)
        scroll_pane.setPreferredSize(Dimension(800, 300))
        self._panel.add(scroll_pane)

        # Clear log button
        clear_panel = JPanel(FlowLayout(FlowLayout.LEFT))
        self.clear_btn = JButton("Clear Log", actionPerformed=self._clear_log)
        clear_panel.add(self.clear_btn)
        self._panel.add(clear_panel)

    def _auto_detect_sslyze(self, event):
        """Auto-detect sslyze binary"""
        detected_path = find_sslyze_path()
        if detected_path:
            self.ssl_path.setText(detected_path)
            self.log("[+] Auto-detected sslyze at: {}".format(detected_path))
        else:
            self.log("[!] Could not auto-detect sslyze in PATH")
            self.log("[!] Common locations checked: /usr/local/bin, /usr/bin, ~/.local/bin")

    def _validate_sslyze(self, event):
        """Validate sslyze path"""
        path = self.ssl_path.getText()
        is_valid, error_msg = validate_sslyze_path(path)
        if is_valid:
            self.log("[+] SSLyze binary is valid and executable: {}".format(path))
        else:
            self.log("[-] SSLyze validation failed: {}".format(error_msg))

    def _save_config_action(self, event):
        """Save configuration button handler"""
        self.save_config()
        self.log("[+] Configuration saved to: {}".format(CONFIG_FILE))

    def _clear_log(self, event):
        """Clear the log area"""
        self.log_area.setText("")

    def getTabCaption(self):
        """Return tab title"""
        return "SSLTriage"

    def getUiComponent(self):
        """Return UI component"""
        return self._panel

    def log(self, text):
        """Append text to log area"""
        current = self.log_area.getText()
        if current:
            self.log_area.setText(current + "\n" + text)
        else:
            self.log_area.setText(text)
        # Auto-scroll to bottom
        self.log_area.setCaretPosition(self.log_area.getDocument().getLength())

    def get_settings(self):
        """Get current settings from GUI"""
        return {
            "sslyze_path": self.ssl_path.getText(),
            "enable_passive": self.passive_box.isSelected(),
            "enable_active": self.active_box.isSelected(),
            "scan_mode": str(self.scan_mode_combo.getSelectedItem())
        }

    def save_config(self):
        """Save configuration to JSON file"""
        try:
            config = self.get_settings()
            config_dir = os.path.dirname(CONFIG_FILE)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)

            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            self.log("[-] Failed to save config: {}".format(str(e)))
            return False

    def load_config(self):
        """Load configuration from JSON file"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
        except Exception as e:
            print("[!] Failed to load config: {}".format(str(e)))
        return {}


class BurpExtender(IBurpExtender, IScannerCheck, IContextMenuFactory):
    """
    Main Burp Extension class
    """
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        callbacks.setExtensionName("SSLTriage")

        # Initialize UI
        self._ui = SSLTriageTab(callbacks)

        # Register scanner and context menu
        callbacks.registerScannerCheck(self)
        callbacks.registerContextMenuFactory(self)

        # Ensure temp directory exists
        if not os.path.exists(TEMP_DIR):
            try:
                os.makedirs(TEMP_DIR)
            except:
                pass

        print("[+] SSLTriage v{} extension loaded".format(VERSION))
        self._ui.log("[+] SSLTriage v{} extension loaded".format(VERSION))

    def doPassiveScan(self, baseRequestResponse):
        """Passive scan implementation"""
        if not self._ui.passive_box.isSelected():
            return None
        return self._run_ssl_scan(baseRequestResponse.getHttpService())

    def doActiveScan(self, baseRequestResponse, insertionPoint):
        """Active scan implementation"""
        if not self._ui.active_box.isSelected():
            return None
        return self._run_ssl_scan(baseRequestResponse.getHttpService())

    def consolidateDuplicateIssues(self, existingIssue, newIssue):
        """Consolidate duplicate issues"""
        if existingIssue.getIssueName() == newIssue.getIssueName():
            return -1
        return 0

    def createMenuItems(self, invocation):
        """Create context menu items"""
        menu = ArrayList()
        menuItem = JMenuItem("Send to SSLTriage", actionPerformed=lambda x: self._handle_context(invocation))
        menu.add(menuItem)
        return menu

    def _handle_context(self, invocation):
        """Handle context menu selection"""
        messages = invocation.getSelectedMessages()
        if messages:
            service = messages[0].getHttpService()
            self._run_ssl_scan(service)

    def _run_ssl_scan(self, service):
        """
        Execute SSLyze scan on the target
        Returns list of IScanIssue objects or None
        """
        host = service.getHost()
        port = service.getPort()
        protocol = service.getProtocol()

        # Only scan HTTPS targets
        if protocol != "https":
            return None

        # Validate sslyze path
        sslyze_path = self._ui.ssl_path.getText()
        is_valid, error_msg = validate_sslyze_path(sslyze_path)

        if not is_valid:
            self._ui.log("[-] Cannot scan {}:{} - {}".format(host, port, error_msg))
            return None

        try:
            # Sanitize hostname for filename
            safe_host = sanitize_filename(host)
            safe_port = str(port)

            # Create output file path
            outfile = os.path.join(TEMP_DIR, "sslt_{}_{}.json".format(safe_host, safe_port))
            target = "{}:{}".format(host, port)
            scan_mode = str(self._ui.scan_mode_combo.getSelectedItem())

            # Build command
            cmd = [sslyze_path, scan_mode, target, "--json_out", outfile]

            # Log command being executed
            cmd_str = " ".join(cmd)
            self._ui.log("[*] Scanning {}:{} ...".format(host, port))
            self._ui.log("[*] Command: {}".format(cmd_str))

            # Execute sslyze
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()

            # Log stdout if present
            if stdout:
                stdout_str = stdout.decode('utf-8', errors='replace').strip()
                if stdout_str:
                    self._ui.log("[*] SSLyze stdout: {}".format(stdout_str[:500]))

            # Check for errors
            if process.returncode != 0:
                stderr_str = stderr.decode('utf-8', errors='replace').strip() if stderr else "Unknown error"
                self._ui.log("[-] SSLyze exited with code {}: {}".format(process.returncode, stderr_str))

                # Common error explanations
                if process.returncode == 2:
                    self._ui.log("[!] Exit code 2 typically means:")
                    self._ui.log("    - Target refused connection (firewall/not listening)")
                    self._ui.log("    - TLS handshake failed")
                    self._ui.log("    - Invalid command-line arguments")

                return None

            # Read and parse JSON output
            if not os.path.exists(outfile):
                self._ui.log("[-] SSLyze output file not created: {}".format(outfile))
                return None

            with open(outfile, "r") as f:
                results = json.load(f)

            self._ui.log("[+] Successfully scanned {}:{}".format(host, port))

            # Parse results and create issues
            issues = self._parse_results(results, host, port)

            if issues and issues.size() > 0:
                self._ui.log("[+] Found {} issue(s) on {}:{}".format(issues.size(), host, port))
            else:
                self._ui.log("[+] No vulnerabilities found on {}:{}".format(host, port))

            # Clean up temp file
            try:
                os.remove(outfile)
            except:
                pass

            return issues

        except subprocess.CalledProcessError as e:
            error_detail = "Command failed with exit code {}".format(e.returncode)
            if hasattr(e, 'stderr') and e.stderr:
                error_detail += "\nStderr: {}".format(e.stderr.decode('utf-8', errors='replace'))
            if hasattr(e, 'stdout') and e.stdout:
                error_detail += "\nStdout: {}".format(e.stdout.decode('utf-8', errors='replace'))
            self._ui.log("[-] SSLyze subprocess error on {}:{}: {}".format(host, port, error_detail))
            return None
        except Exception as e:
            import traceback
            error_msg = str(e)
            stack_trace = traceback.format_exc()
            self._ui.log("[-] Unexpected error scanning {}:{}: {}".format(host, port, error_msg))
            self._ui.log("[!] Stack trace: {}".format(stack_trace))
            return None

    def _parse_results(self, results, host, port):
        """
        Parse SSLyze JSON results and create Burp issues
        """
        issues = ArrayList()

        # Try multiple formats for server identification
        server_id_formats = [
            "{}:{}".format(host, port),
            host,
            "{}:{}".format(host, str(port))
        ]

        scan_data = None
        for server_id in server_id_formats:
            scan_data = results.get("server_scan_results", {}).get(server_id)
            if scan_data:
                break

        if not scan_data:
            self._ui.log("[!] No scan results found in JSON output for {}:{}".format(host, port))
            return None

        # Define vulnerability checks
        findings = {
            "ssl_2_0_cipher_suites": ("SSLv2 Supported - Deprecated Protocol", "High", "CWE-310"),
            "ssl_3_0_cipher_suites": ("SSLv3 Supported - POODLE Vulnerable", "High", "CWE-310"),
            "tls_1_0_cipher_suites": ("TLS 1.0 Supported - Deprecated", "Medium", "CWE-327"),
            "tls_1_1_cipher_suites": ("TLS 1.1 Supported - Deprecated", "Medium", "CWE-327"),
        }

        for key, (desc, severity, cwe) in findings.items():
            result = scan_data.get(key)
            if result:
                # Check if protocol is supported
                if isinstance(result, dict):
                    # Check for accepted cipher suites
                    accepted_suites = result.get("accepted_cipher_suites", [])
                    if accepted_suites and len(accepted_suites) > 0:
                        cipher_list = ", ".join([suite.get("cipher_suite", {}).get("name", "Unknown")
                                                 for suite in accepted_suites[:5]])
                        detail = "{} (CWE: {})\nAccepted ciphers: {}".format(desc, cwe, cipher_list)

                        issues.add(SSLTriageIssue(
                            "{} - TLS/SSL Misconfiguration".format(desc),
                            detail,
                            severity,
                            host,
                            port
                        ))

        # Check for certificate issues
        cert_info = scan_data.get("certificate_info")
        if cert_info and isinstance(cert_info, dict):
            cert_deployments = cert_info.get("certificate_deployments", [])
            for deployment in cert_deployments:
                verified_chain = deployment.get("verified_certificate_chain")
                if verified_chain is None or not verified_chain:
                    issues.add(SSLTriageIssue(
                        "Invalid Certificate Chain",
                        "The SSL/TLS certificate chain could not be verified (CWE: CWE-295)",
                        "High",
                        host,
                        port
                    ))

        return issues if issues.size() > 0 else None


class SSLTriageIssue(IScanIssue):
    """
    Represents a security issue found by SSLTriage
    """
    def __init__(self, name, detail, severity, host, port):
        self._name = name
        self._detail = detail
        self._severity = severity
        self._host = host
        self._port = port

    def getUrl(self):
        """Return URL of the issue"""
        return None

    def getIssueName(self):
        """Return issue name"""
        return self._name

    def getIssueType(self):
        """Return issue type (custom)"""
        return 0x08000000

    def getSeverity(self):
        """Return severity level"""
        return self._severity

    def getConfidence(self):
        """Return confidence level"""
        return "Certain"

    def getIssueBackground(self):
        """Return issue background information"""
        return ("This SSL/TLS security issue was detected by SSLTriage using SSLyze scanner. "
                "The scan identified deprecated protocols, weak cipher suites, or certificate validation issues.")

    def getRemediationBackground(self):
        """Return remediation background"""
        return ("Update your SSL/TLS server configuration to:\n"
                "- Disable SSLv2, SSLv3, TLS 1.0, and TLS 1.1\n"
                "- Enable only TLS 1.2 and TLS 1.3\n"
                "- Use strong cipher suites (ECDHE with AES-GCM)\n"
                "- Ensure valid certificate chain\n"
                "- Keep certificates up to date")

    def getIssueDetail(self):
        """Return detailed issue description"""
        return self._detail

    def getRemediationDetail(self):
        """Return remediation details"""
        return None

    def getHttpMessages(self):
        """Return HTTP messages"""
        return None

    def getHttpService(self):
        """Return HTTP service"""
        return None
