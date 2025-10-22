# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-10-22

### Fixed
- **CRITICAL**: Fixed SSLyze command-line arguments for SSLyze 6.x compatibility
  - Replaced deprecated `--regular` and `--full` flags
  - Now uses individual scan flags (`--sslv2`, `--sslv3`, `--tlsv1`, etc.)
- Updated JSON parsing logic for SSLyze 6.x output format
  - Fixed `server_scan_results` parsing (now expects array instead of dict)
  - Updated cipher suite detection to use nested `result` object
  - Fixed certificate validation checking using new `path_validation_results` structure
- Fixed Python interpreter detection in Makefile
  - Auto-detects python3/python instead of hardcoded python2
  - CI/CD compatibility improved

### Changed
- Scan mode dropdown now shows user-friendly names:
  - "Quick Scan" - Only deprecated protocols (SSLv2, SSLv3, TLS 1.0, TLS 1.1)
  - "Standard Scan" - Protocols + basic vulnerabilities (Heartbleed, ROBOT, etc.)
  - "Full Scan" - Comprehensive testing of all TLS features
- Improved error messages and logging for scan failures
- Enhanced cipher suite reporting (shows count when > 5 ciphers)

### Technical
- Compatible with SSLyze 6.1.0 and newer
- Maintains backward compatibility with Jython 2.7
- Updated GitHub Actions CI/CD to pass all platform tests

## [1.0.0] - 2025-10-22

### Added
- Initial release of SSLTriage Burp Suite Extension
- SSL/TLS security scanning using SSLyze
- Passive and active scanning modes
- Comprehensive GUI configuration tab
- Auto-detection of SSLyze binary from PATH
- SSLyze path validation and executable check
- Persistent configuration storage in JSON format
- Dropdown menu for scan mode selection (--regular or --full)
- Enhanced error logging with stdout/stderr capture
- Detailed subprocess error messages
- Hostname sanitization for temp file paths
- Support for colons and special characters in hostnames
- Context menu integration (Send to SSLTriage)
- Issue reporting in Burp Target > Issue Activity
- Detection of deprecated protocols (SSLv2, SSLv3, TLS 1.0, TLS 1.1)
- Weak cipher suite detection
- Certificate chain validation
- Real-time scan logging in GUI
- Clear log functionality
- Jython 2.7 compatibility
- Cross-platform support (Linux, macOS, Windows)
- Comprehensive error handling for:
  - Connection refused errors
  - TLS handshake failures
  - Invalid command-line arguments
  - Permission issues
- Auto-scroll log area
- Configuration save/load functionality
- Temp directory creation and management
- Automatic temp file cleanup

### Security
- Secure subprocess execution with path validation
- No sensitive data logging
- Sanitized filenames prevent path traversal
- Configuration stored in user home directory
- Validated executable permissions

### Documentation
- Comprehensive README with installation instructions
- Usage examples and troubleshooting guide
- Security considerations and authorized use disclaimer
- Development guidelines and contribution standards
- Roadmap for future features

## [Unreleased]

### Planned for 1.1.0
- Custom SSLyze scan profiles
- Export scan results to CSV/JSON
- Scheduled scanning capabilities
- Multi-threaded scanning for performance
- Enhanced certificate analysis
- Support for custom certificate stores

### Planned for 1.2.0
- Integration with other Burp extensions
- Custom vulnerability rules engine
- Scan result comparison and diff
- Detailed reporting engine with templates
- REST API for automation
- Dashboard with statistics

---

## Version History

- **1.0.0** (2025-10-22): Initial release with core functionality
