#!/usr/bin/env bash
# SSLTriage Installation Script
# Supports: Linux, macOS, Unix-like systems
# Version: 1.0.0

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "freebsd"* ]]; then
        OS="freebsd"
    else
        OS="unknown"
    fi
    echo_info "Detected OS: $OS"
}

# Detect package manager
detect_package_manager() {
    if command -v brew &> /dev/null; then
        PKG_MGR="brew"
    elif command -v apt-get &> /dev/null; then
        PKG_MGR="apt"
    elif command -v yum &> /dev/null; then
        PKG_MGR="yum"
    elif command -v dnf &> /dev/null; then
        PKG_MGR="dnf"
    elif command -v pacman &> /dev/null; then
        PKG_MGR="pacman"
    elif command -v zypper &> /dev/null; then
        PKG_MGR="zypper"
    elif command -v apk &> /dev/null; then
        PKG_MGR="apk"
    else
        PKG_MGR="none"
    fi

    if [ "$PKG_MGR" != "none" ]; then
        echo_info "Package manager: $PKG_MGR"
    else
        echo_warn "No package manager detected. Will use pip for installation."
    fi
}

# Install Python if not present
install_python() {
    if command -v python3 &> /dev/null; then
        echo_info "Python3 already installed: $(python3 --version)"
        return 0
    fi

    echo_info "Installing Python3..."
    case $PKG_MGR in
        brew)
            brew install python3
            ;;
        apt)
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip
            ;;
        yum)
            sudo yum install -y python3 python3-pip
            ;;
        dnf)
            sudo dnf install -y python3 python3-pip
            ;;
        pacman)
            sudo pacman -S --noconfirm python python-pip
            ;;
        zypper)
            sudo zypper install -y python3 python3-pip
            ;;
        apk)
            sudo apk add python3 py3-pip
            ;;
        *)
            echo_error "Cannot install Python3. Please install manually."
            exit 1
            ;;
    esac
}

# Install pip if not present
install_pip() {
    if command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
        echo_info "pip already installed"
        return 0
    fi

    echo_info "Installing pip..."
    case $PKG_MGR in
        brew)
            # pip comes with python3 on brew
            :
            ;;
        apt)
            sudo apt-get install -y python3-pip
            ;;
        yum)
            sudo yum install -y python3-pip
            ;;
        dnf)
            sudo dnf install -y python3-pip
            ;;
        pacman)
            sudo pacman -S --noconfirm python-pip
            ;;
        zypper)
            sudo zypper install -y python3-pip
            ;;
        apk)
            sudo apk add py3-pip
            ;;
        *)
            # Try to install pip using get-pip.py
            curl -sS https://bootstrap.pypa.io/get-pip.py | python3
            ;;
    esac
}

# Install SSLyze
install_sslyze() {
    if command -v sslyze &> /dev/null; then
        echo_info "SSLyze already installed: $(sslyze --version 2>&1 | head -n 1)"
        return 0
    fi

    echo_info "Installing SSLyze..."

    # Try package manager first
    case $PKG_MGR in
        brew)
            brew install sslyze
            return 0
            ;;
    esac

    # Fall back to pip
    if command -v pip3 &> /dev/null; then
        pip3 install --user sslyze
    elif command -v pip &> /dev/null; then
        pip install --user sslyze
    else
        echo_error "Cannot install SSLyze. pip not found."
        exit 1
    fi

    # Add to PATH if needed
    if ! command -v sslyze &> /dev/null; then
        echo_warn "SSLyze installed but not in PATH"
        if [ -f "$HOME/.local/bin/sslyze" ]; then
            echo_info "SSLyze location: $HOME/.local/bin/sslyze"
            echo_warn "Add to PATH: export PATH=\"\$HOME/.local/bin:\$PATH\""
        fi
    fi
}

# Verify installation
verify_installation() {
    echo_info "Verifying installation..."

    if ! command -v sslyze &> /dev/null; then
        echo_error "SSLyze not found in PATH"
        return 1
    fi

    SSLYZE_PATH=$(which sslyze)
    echo_info "SSLyze path: $SSLYZE_PATH"

    if [ ! -x "$SSLYZE_PATH" ]; then
        echo_error "SSLyze is not executable"
        return 1
    fi

    echo_info "Testing SSLyze..."
    if sslyze --version &> /dev/null; then
        echo_info "SSLyze is working correctly"
        return 0
    else
        echo_error "SSLyze test failed"
        return 1
    fi
}

# Create config directory
setup_config() {
    CONFIG_DIR="$HOME/.config/ssltriage"
    if [ ! -d "$CONFIG_DIR" ]; then
        echo_info "Creating config directory: $CONFIG_DIR"
        mkdir -p "$CONFIG_DIR"
    fi
}

# Print installation summary
print_summary() {
    echo ""
    echo_info "============================================"
    echo_info "SSLTriage Installation Complete!"
    echo_info "============================================"
    echo ""
    echo_info "Extension file: SSLTriage.py"
    echo_info "SSLyze path: $(which sslyze 2>/dev/null || echo 'Not in PATH')"
    echo ""
    echo_info "Next steps:"
    echo "  1. Open Burp Suite"
    echo "  2. Go to Extensions > Installed"
    echo "  3. Click 'Add'"
    echo "  4. Select 'Python' as extension type"
    echo "  5. Select SSLTriage.py"
    echo "  6. Click 'Next'"
    echo ""
    echo_info "For help, see README.md"
    echo ""
}

# Main installation
main() {
    echo_info "SSLTriage Installation Script"
    echo_info "=============================="
    echo ""

    detect_os
    detect_package_manager

    echo ""
    echo_info "Installing dependencies..."
    install_python
    install_pip
    install_sslyze

    echo ""
    verify_installation || {
        echo_error "Installation verification failed"
        exit 1
    }

    setup_config
    print_summary
}

# Run main
main
