# SSLTriage

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-2.7%20%7C%203.x-blue.svg)](https://www.python.org/)
[![Burp Suite](https://img.shields.io/badge/Burp%20Suite-Extension-orange.svg)](https://portswigger.net/burp)

**SSLTriage** is a comprehensive SSL/TLS security scanner extension for Burp Suite that leverages SSLyze to identify misconfigurations, deprecated protocols, weak cipher suites, and certificate validation issues.

## Features

- **Automated SSL/TLS Scanning**: Passive and active scanning modes integrated with Burp Suite
- **Comprehensive Detection**: Identifies:
  - Deprecated protocols (SSLv2, SSLv3, TLS 1.0, TLS 1.1)
  - Weak cipher suites
  - Certificate chain validation issues
- **User-Friendly GUI**:
  - Visual configuration tab in Burp Suite
  - Real-time scan logging
  - Persistent configuration storage
- **Smart Detection**:
  - Auto-detects SSLyze binary from PATH
  - Path validation and executable checks
  - Sanitizes filenames for cross-platform compatibility
- **Enhanced Error Handling**:
  - Detailed subprocess error logging
  - stdout/stderr capture and display
  - Helpful error explanations
- **Context Menu Integration**: Right-click to scan specific targets
- **Issue Reporting**: Automatically adds findings to Burp's Target > Issue Activity

## Requirements

### System Requirements
- **Burp Suite**: Professional or Community Edition
- **Jython**: 2.7.x (standalone JAR) - configured in Burp Suite
- **SSLyze**: 5.0.0 or newer
- **Operating Systems**: Linux, macOS, Windows

### Dependencies
- SSLyze must be installed and accessible
- Python 2.7 compatible (Jython)

## Installation

### 1. Install SSLyze

#### macOS (Homebrew)
```bash
brew install sslyze
```

#### Linux (pip)
```bash
pip install sslyze
# or
pip3 install sslyze
```

#### Windows (pip)
```cmd
pip install sslyze
```

#### From Source
```bash
git clone https://github.com/nabla-c0d3/sslyze.git
cd sslyze
pip install .
```

### 2. Install Jython in Burp Suite

1. Download Jython standalone JAR from: https://www.jython.org/download.html
2. In Burp Suite, go to: **Extensions > Extension Settings**
3. Under "Python Environment", set the location of Jython standalone JAR
4. Click "Select file" and choose the downloaded JAR file

### 3. Load SSLTriage Extension

**Option A: Using Burp Suite GUI**
1. Download `SSLTriage.py`
2. In Burp Suite, go to: **Extensions > Installed**
3. Click **Add**
4. Extension type: **Python**
5. Select `SSLTriage.py`
6. Click **Next**

**Option B: Using Installation Script**
```bash
# Clone the repository
git clone https://github.com/yourusername/SSLTriage.git
cd SSLTriage

# Run the installation script
chmod +x install.sh
./install.sh
```

## Configuration

### First-Time Setup

1. After loading the extension, navigate to the **SSLTriage** tab in Burp Suite
2. The extension will attempt to auto-detect SSLyze
3. If auto-detection fails:
   - Click **Auto-detect** button, or
   - Manually enter the path to SSLyze binary
   - Click **Validate** to verify the path

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| **SSLyze Path** | Full path to SSLyze binary | Auto-detected |
| **Enable Passive Scanning** | Scan all HTTPS traffic passively | Enabled |
| **Enable Active Scanning** | Scan during active scans | Disabled |
| **Scan Mode** | `--regular` or `--full` | `--regular` |

### Persistent Configuration

Configuration is automatically saved to `~/.ssltriage_config.json`. Click **Save Configuration** to persist changes.

## Usage

### Passive Scanning
1. Enable "Enable Passive Scanning" in the SSLTriage tab
2. Browse HTTPS sites through Burp Proxy
3. SSLTriage will automatically scan SSL/TLS configurations
4. View findings in **Target > Issue Activity**

### Active Scanning
1. Enable "Enable Active Scanning" in the SSLTriage tab
2. Right-click on a request and select "Do active scan"
3. SSL/TLS issues will be included in scan results

### Manual Scanning
1. Right-click on any HTTPS request in Burp
2. Select **"Send to SSLTriage"**
3. View scan progress in the SSLTriage tab
4. Issues appear in **Target > Issue Activity**

### Scan Modes

#### Regular Mode (`--regular`)
- Faster scanning
- Checks common protocols and cipher suites
- Recommended for most use cases

#### Full Mode (`--full`)
- Comprehensive scanning
- Tests all protocols and cipher suites
- Longer scan time
- Recommended for thorough audits

## Detected Issues

SSLTriage detects the following security issues:

| Issue | Severity | CWE |
|-------|----------|-----|
| SSLv2 Support | High | CWE-310 |
| SSLv3 Support (POODLE) | High | CWE-310 |
| TLS 1.0 Support | Medium | CWE-327 |
| TLS 1.1 Support | Medium | CWE-327 |
| Invalid Certificate Chain | High | CWE-295 |
| Weak Cipher Suites | Medium | CWE-326 |

## Troubleshooting

### SSLyze Exit Code 2

Exit code 2 typically indicates:
- Target refused connection (firewall blocking)
- TLS handshake failed (incompatible protocols)
- Target not listening on specified port
- Invalid command-line arguments

**Solutions:**
1. Verify target is accessible
2. Check firewall rules
3. Ensure target supports TLS
4. Validate SSLyze path and version

### SSLyze Not Found

**Error:** `SSLyze binary not found`

**Solutions:**
1. Click **Auto-detect** in SSLTriage tab
2. Verify SSLyze is installed: `which sslyze` or `where sslyze`
3. Manually specify the full path
4. Add SSLyze to PATH

### Permission Denied

**Error:** `SSLyze binary is not executable`

**Solution:**
```bash
chmod +x /path/to/sslyze
```

### Jython Not Configured

**Error:** Extension fails to load

**Solution:**
1. Download Jython standalone JAR
2. Configure in Burp: Extensions > Extension Settings > Python Environment
3. Reload extension

## Development

### Project Structure
```
SSLTriage/
├── SSLTriage.py          # Main extension file
├── README.md             # Documentation
├── CHANGELOG.md          # Version history
├── Makefile              # Build automation
├── Dockerfile            # Container for testing
├── install.sh            # Cross-platform installer
├── install.bat           # Windows installer
├── .gitignore            # Git ignore rules
└── .github/
    └── workflows/
        └── ci.yml        # GitHub Actions CI/CD
```

### Building from Source

```bash
# Clone repository
git clone https://github.com/yourusername/SSLTriage.git
cd SSLTriage

# Run tests
make test

# Build distribution
make build
```

### Running Tests

```bash
# Unit tests
make test

# Integration tests
make integration-test

# All tests
make test-all
```

### Docker Testing

```bash
# Build container
docker build -t ssltriage:latest .

# Run tests in container
docker run --rm ssltriage:latest make test
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/your-feature`
5. Submit a Pull Request

### Code Standards
- Follow PEP 8 style guide
- Maintain Jython 2.7 compatibility
- Add docstrings to all functions
- Include unit tests for new features

## Security Considerations

### Authorized Use Only
SSLTriage is designed for:
- Security testing with proper authorization
- Penetration testing engagements
- Security audits and compliance checks
- Educational purposes
- CTF competitions

**DO NOT use this tool for:**
- Unauthorized scanning or testing
- Attacking systems without permission
- Malicious purposes

### Secure Defaults
- Configuration stored in user home directory
- Temp files use sanitized filenames
- No sensitive data logged
- Subprocess execution with validated paths

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Authors

- **SSLTriage Team** - Initial work

## Acknowledgments

- [SSLyze](https://github.com/nabla-c0d3/sslyze) - Powerful SSL/TLS scanner
- [PortSwigger](https://portswigger.net/) - Burp Suite platform
- Security community for feedback and contributions

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/SSLTriage/issues)
- **Documentation**: [Wiki](https://github.com/yourusername/SSLTriage/wiki)
- **Security Issues**: security@yourdomain.com

## Roadmap

### Version 1.1.0 (Planned)
- [ ] Support for custom SSLyze scan profiles
- [ ] Export scan results to CSV/JSON
- [ ] Scheduled scanning
- [ ] Multi-threaded scanning
- [ ] Enhanced certificate analysis

### Version 1.2.0 (Planned)
- [ ] Integration with other Burp extensions
- [ ] Custom vulnerability rules
- [ ] Scan result comparison
- [ ] Detailed reporting engine

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

## Version

Current version: **1.0.0**

---

**Happy Scanning!** 🔒🔍
