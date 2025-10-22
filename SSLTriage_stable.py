#!/usr/bin/env python3
# Burp Suite Extension for SSL/TLS Misconfiguration Detection
# Requires SSLyze installed and in PATH
# This script scans for common SSL/TLS misconfigurations using SSLyze

from burp import IBurpExtender, IScannerCheck, IScanIssue, IHttpRequestResponse, IContextMenuFactory
from java.util import ArrayList
from javax.swing import JMenuItem
import subprocess
import json
import os

class BurpExtender(IBurpExtender, IScannerCheck, IContextMenuFactory):
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        callbacks.setExtensionName("SSLTriage")

        callbacks.registerScannerCheck(self)
        callbacks.registerContextMenuFactory(self)

        print("[+] SSLTriage extension loaded.")

    def doPassiveScan(self, baseRequestResponse):
        service = baseRequestResponse.getHttpService()
        host = service.getHost()
        port = service.getPort()

        # Only scan HTTPS targets
        if port != 443:
            return None

        return self._run_ssl_scan(host, port)

    def doActiveScan(self, baseRequestResponse, insertionPoint):
        # Optionally do active scanning (same logic)
        service = baseRequestResponse.getHttpService()
        host = service.getHost()
        port = service.getPort()

        return self._run_ssl_scan(host, port)

    def createMenuItems(self, invocation):
        menu = ArrayList()
        menuItem = JMenuItem("Send to SSLTriage", actionPerformed=lambda x: self._handle_context(invocation))
        menu.add(menuItem)
        return menu

    def _handle_context(self, invocation):
        messages = invocation.getSelectedMessages()
        if messages:
            service = messages[0].getHttpService()
            host = service.getHost()
            port = service.getPort()
            print("[*] Manual scan triggered on {}:{}".format(host, port))
            self._run_ssl_scan(host, port)

    def _run_ssl_scan(self, host, port):
        try:
            outfile = "/tmp/sslt_{}_{}.json".format(host, port)
            target = "{}:{}".format(host, port)
            subprocess.check_output(["sslyze", "--regular", target, "--json_out", outfile])

            with open(outfile, "r") as f:
                results = json.load(f)

            return self._parse_results(results, host, port)

        except Exception as e:
            print("[-] Error running SSLyze: {}".format(e))
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
        return 0x08000000  # Custom
    def getSeverity(self):
        return self._severity
    def getConfidence(self):
        return "Certain"
    def getIssueBackground(self):
        return "This issue was detected by SSLTriage using SSLyze full scan."
    def getRemediationBackground(self):
        return "Disable deprecated protocols and weak ciphers in your SSL/TLS server config."
    def getIssueDetail(self):
        return self._detail
    def getRemediationDetail(self):
        return None
    def getHttpMessages(self):
        return None
    def getHttpService(self):
        return None
