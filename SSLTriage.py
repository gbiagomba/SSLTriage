#!/usr/bin/env python2
# Burp Suite Extension for SSL Triage using SSLyze
# This extension provides a GUI for configuring SSLyze, performs passive and active scans,
# and logs results in Burp Suite.
# Author: [Your Name]
# Version: 1.0
# -*- coding: utf-8 -*-

from burp import IBurpExtender, IScannerCheck, IScanIssue, IContextMenuFactory, IHttpRequestResponse, ITab
from java.util import ArrayList
from javax.swing import JPanel, JLabel, JCheckBox, JTextField, JScrollPane, JTextArea, BoxLayout
from javax.swing import JMenuItem
import subprocess
import json
import os

CONFIG_FILE = "/tmp/sslt_config.json"

class SSLTriageTab(ITab):
    def __init__(self, callbacks):
        self._callbacks = callbacks
        self._panel = JPanel()
        self._panel.setLayout(BoxLayout(self._panel, BoxLayout.Y_AXIS))

        self.ssl_path = JTextField(self.load_config("sslyze_path", "/usr/local/bin/sslyze"), 30)
        self.passive_box = JCheckBox("Enable Passive Scanning", self.load_config("enable_passive", True))
        self.active_box = JCheckBox("Enable Active Scanning", self.load_config("enable_active", False))
        self.scan_mode = JTextField(self.load_config("scan_mode", "--regular"), 15)
        self.log_area = JTextArea(10, 50)
        self.log_area.setEditable(False)

        self._panel.add(JLabel("SSLTriage Config"))
        self._panel.add(JLabel("Path to sslyze binary:"))
        self._panel.add(self.ssl_path)
        self._panel.add(self.passive_box)
        self._panel.add(self.active_box)
        self._panel.add(JLabel("Scan mode (--regular or --full):"))
        self._panel.add(self.scan_mode)
        self._panel.add(JLabel("Scan Log:"))
        self._panel.add(JScrollPane(self.log_area))

        callbacks.addSuiteTab(self)

    def getTabCaption(self):
        return "SSLTriage"

    def getUiComponent(self):
        return self._panel

    def log(self, text):
        self.log_area.append(text + "\n")

    def get_settings(self):
        return {
            "sslyze_path": self.ssl_path.getText(),
            "enable_passive": self.passive_box.isSelected(),
            "enable_active": self.active_box.isSelected(),
            "scan_mode": self.scan_mode.getText()
        }

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.get_settings(), f)
        except:
            pass

    def load_config(self, key, default):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    return data.get(key, default)
        except:
            pass
        return default


class BurpExtender(IBurpExtender, IScannerCheck, IContextMenuFactory):
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        callbacks.setExtensionName("SSLTriage")
        self._ui = SSLTriageTab(callbacks)
        callbacks.registerScannerCheck(self)
        callbacks.registerContextMenuFactory(self)
        print("[+] SSLTriage extension loaded with GUI and config")

    def doPassiveScan(self, baseRequestResponse):
        if not self._ui.passive_box.isSelected():
            return None
        return self._run_ssl_scan(baseRequestResponse.getHttpService())

    def doActiveScan(self, baseRequestResponse, insertionPoint):
        if not self._ui.active_box.isSelected():
            return None
        return self._run_ssl_scan(baseRequestResponse.getHttpService())

    def createMenuItems(self, invocation):
        menu = ArrayList()
        menuItem = JMenuItem("Send to SSLTriage", actionPerformed=lambda x: self._handle_context(invocation))
        menu.add(menuItem)
        return menu

    def _handle_context(self, invocation):
        messages = invocation.getSelectedMessages()
        if messages:
            service = messages[0].getHttpService()
            self._run_ssl_scan(service)

    def _run_ssl_scan(self, service):
        host = service.getHost()
        port = service.getPort()
        if port != 443:
            return None

        try:
            path = self._ui.ssl_path.getText()
            mode = self._ui.scan_mode.getText()
            outfile = "/tmp/sslt_{}_{}.json".format(host, port)
            target = "{}:{}".format(host, port)
            cmd = [path, mode, target, "--json_out", outfile]
            subprocess.check_output(cmd)
            with open(outfile, "r") as f:
                results = json.load(f)
            self._ui.log("[+] Scanned {}:{}".format(host, port))
            return self._parse_results(results, host, port)
        except Exception as e:
            self._ui.log("[-] SSLyze error: {}".format(e))
            return None

    def _parse_results(self, results, host, port):
        issues = ArrayList()
        server_id = "{}:{}".format(host, port)
        scan_data = results.get("server_scan_results", {}).get(server_id)
        if not scan_data:
            return None

        findings = {
            "sslv2": ("SSLv2 Supported - Deprecated Protocol", "High", "CWE-310"),
            "sslv3": ("SSLv3 Supported - POODLE Vulnerable", "High", "CWE-310"),
            "tlsv1_0": ("TLS 1.0 Supported - Deprecated", "Medium", "CWE-327"),
            "tlsv1_1": ("TLS 1.1 Supported - Deprecated", "Medium", "CWE-327"),
            "rc4_cipher": ("RC4 Cipher Supported - Weak Encryption", "Medium", "CWE-326"),
        }

        for key, (desc, severity, cwe) in findings.items():
            result = scan_data.get(key)
            if result and result.get("is_protocol_supported", False):
                issues.add(SSLTriageIssue(
                    "{} TLS/SSL Misconfiguration".format(desc),
                    desc + " (CWE: {})".format(cwe),
                    severity,
                    host,
                    port
                ))

        return issues if issues.size() > 0 else None


class SSLTriageIssue(IScanIssue):
    def __init__(self, name, detail, severity, host, port):
        self._name = name
        self._detail = detail
        self._severity = severity
        self._host = host
        self._port = port

    def getUrl(self):
        return None

    def getIssueName(self):
        return self._name

    def getIssueType(self):
        return 0x08000000
    def getSeverity(self):
        return self._severity
    def getConfidence(self):
        return "Certain"
    def getIssueBackground(self):
        return "Detected by SSLTriage using SSLyze scan."
    def getRemediationBackground(self):
        return "Update TLS config to disable deprecated protocols and ciphers."
    def getIssueDetail(self):
        return self._detail
    def getRemediationDetail(self):
        return None
    def getHttpMessages(self):
        return None
    def getHttpService(self):
        return None
