#!/bin/bash
"""
TikTok Automation System - Setup Script
Geeky Workflow Core v2.0
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SECRETS_DIR="/etc/gm-secrets"
SERVICE_USER="gm_automation"

# Logging
LOG_FILE="/tmp/tiktok_setup.log"
exec > >(tee -a "$LOG_FILE")
exec 2>&1

echo -e "${BLUE}TikTok Automation System Setup${NC}"
echo "========================================"
echo "Starting installation at $(date)"
echo ""

# Function to print status
print_status() {
    local status=$1
    local message=$2
    case $status in
        "INFO")
            echo -e "${BLUE}[INFO]${NC} $message"
            ;;
        "SUCCESS")
            echo -e "${GREEN}[SUCCESS]${NC} $message"
            ;;
        "WARNING")
            echo -e "${YELLOW}[WARNING]${NC} $message"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} $message"
            ;;
    esac
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_status "ERROR" "This script should not be run as root for security reasons"
        print_status "INFO" "Please run as a regular user with sudo privileges"
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    print_status "INFO" "Checking system requirements..."
    
    # Check OS
    if ! command -v lsb_release &> /dev/null; then
        print_status "WARNING" "Cannot determine OS version"
    else
        local os_name=$(lsb_release -si)
        local os_version=$(lsb_release -sr)
        print_status "INFO" "OS: $os_name $os_version"
        
        if [[ "$os_name" != "Ubuntu" ]] && [[ "$os_name" != "Debian" ]]; then
            print_status "WARNING" "This script is optimized for Ubuntu/Debian"
        fi
    fi
    
    # Check available disk space
    local available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [[ $available_space -lt 2 ]]; then
        print_status "ERROR" "Insufficient disk space. At least 2GB required"
        exit 1
    fi
    
    print_status "SUCCESS" "System requirements check passed"
}

# Update system packages
update_system() {
    print_status "INFO" "Updating system packages..."
    
    sudo apt update
    sudo apt upgrade -y
    
    print_status "SUCCESS" "System packages updated"
}

# Install system dependencies
install_dependencies() {
    print_status "INFO" "Installing system dependencies..."
    
    # Core dependencies
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        nodejs \
        npm \
        curl \
        wget \
        git \
        build-essential \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release
    
    # Media processing
    sudo apt install -y \
        ffmpeg \
        imagemagick \
        libmagickwand-dev \
        libavcodec-dev \
        libavformat-dev \
        libavutil-dev \
        libswscale-dev \
        libavresample-dev
    
    # Database (optional)
    sudo apt install -y \
        sqlite3 \
        postgresql \
        postgresql-contrib \
        redis-server
    
    # System utilities
    sudo apt install -y \
        jq \
        htop \
        iotop \
        net-tools \
        unzip \
        zip
    
    print_status "SUCCESS" "System dependencies installed"
}

# Setup Python environment
setup_python_env() {
    print_status "INFO" "Setting up Python environment..."
    
    cd "$PROJECT_ROOT"
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_status "SUCCESS" "Python virtual environment created"
    fi
    
    # Activate virtual environment and install packages
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install Python packages
    pip install \
        flask \
        requests \
        pillow \
        opencv-python \
        moviepy \
        whisper \
        openai \
        psutil \
        schedule \
        python-dotenv \
        cryptography \
        psycopg2-binary \
        redis
    
    print_status "SUCCESS" "Python environment setup completed"
}

# Setup Node.js environment
setup_nodejs_env() {
    print_status "INFO" "Setting up Node.js environment..."
    
    # Install n8n globally
    sudo npm install -g n8n
    
    # Install additional Node.js tools
    sudo npm install -g pm2
    
    print_status "SUCCESS" "Node.js environment setup completed"
}

# Create service user
create_service_user() {
    print_status "INFO" "Creating service user..."
    
    if ! id "$SERVICE_USER" &>/dev/null; then
        sudo useradd -r -s /bin/false -d "$PROJECT_ROOT" "$SERVICE_USER"
        print_status "SUCCESS" "Service user created: $SERVICE_USER"
    else
        print_status "INFO" "Service user already exists: $SERVICE_USER"
    fi
    
    # Set permissions
    sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_ROOT"
    sudo chmod 755 "$PROJECT_ROOT"
    
    print_status "SUCCESS" "Service user permissions configured"
}

# Setup secrets directory
setup_secrets() {
    print_status "INFO" "Setting up secrets directory..."
    
    if [ ! -d "$SECRETS_DIR" ]; then
        sudo mkdir -p "$SECRETS_DIR"
        sudo chmod 700 "$SECRETS_DIR"
        print_status "SUCCESS" "Secrets directory created: $SECRETS_DIR"
    fi
    
    # Create initial secrets files
    sudo touch "$SECRETS_DIR/tiktok_keys.env"
    sudo chmod 600 "$SECRETS_DIR/tiktok_keys.env"
    sudo chown "$SERVICE_USER:$SERVICE_USER" "$SECRETS_DIR/tiktok_keys.env"
    
    print_status "SUCCESS" "Secrets directory configured"
}

# Setup systemd services
setup_services() {
    print_status "INFO" "Setting up systemd services..."
    
    # Create n8n service
    sudo tee /etc/systemd/system/n8n.service > /dev/null <<EOF
[Unit]
Description=n8n workflow automation
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$PROJECT_ROOT
Environment=NODE_ENV=production
ExecStart=/usr/bin/n8n start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Create monitoring dashboard service
    sudo tee /etc/systemd/system/gm-dashboard.service > /dev/null <<EOF
[Unit]
Description=GM Monitoring Dashboard
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$PROJECT_ROOT
Environment=PATH=$PROJECT_ROOT/venv/bin
ExecStart=$PROJECT_ROOT/venv/bin/python3 core/monitoring/dashboard.py --host=0.0.0.0 --port=8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Create content generator service
    sudo tee /etc/systemd/system/gm-content.service > /dev/null <<EOF
[Unit]
Description=GM Content Generator
After=network.target

[Service]
Type=oneshot
User=$SERVICE_USER
WorkingDirectory=$PROJECT_ROOT
Environment=PATH=$PROJECT_ROOT/venv/bin
ExecStart=$PROJECT_ROOT/scripts/automation/gm-content --topic='automated content' --template=viral_facts --count=1

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable services
    sudo systemctl daemon-reload
    sudo systemctl enable n8n
    sudo systemctl enable gm-dashboard
    
    print_status "SUCCESS" "Systemd services configured"
}

# Setup firewall
setup_firewall() {
    print_status "INFO" "Configuring firewall..."
    
    # Check if ufw is available
    if command -v ufw &> /dev/null; then
        sudo ufw --force enable
        sudo ufw allow ssh
        sudo ufw allow 5678/tcp  # n8n default port
        sudo ufw allow 8080/tcp  # monitoring dashboard
        sudo ufw allow 80/tcp    # HTTP
        sudo ufw allow 443/tcp   # HTTPS
        
        print_status "SUCCESS" "Firewall configured with ufw"
    else
        print_status "WARNING" "ufw not available, please configure firewall manually"
    fi
}

# Setup log rotation
setup_log_rotation() {
    print_status "INFO" "Setting up log rotation..."
    
    sudo tee /etc/logrotate.d/tiktok-automation > /dev/null <<EOF
$PROJECT_ROOT/data/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $SERVICE_USER $SERVICE_USER
    postrotate
        systemctl reload gm-dashboard || true
    endscript
}
EOF
    
    print_status "SUCCESS" "Log rotation configured"
}

# Create environment file
create_env_file() {
    print_status "INFO" "Creating environment configuration..."
    
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        cat > "$PROJECT_ROOT/.env" <<EOF
# TikTok Automation System Configuration
GM_DOMAIN=[your-domain.com]
GM_API_BASE=https://api.[your-domain.com]
GM_N8N_URL=https://automation.[your-domain.com]

# AI Services (Optional)
OPENAI_API_KEY=your_openai_api_key_here
STABLE_DIFFUSION_URL=http://localhost:7860

# Database Configuration
POSTGRES_PASSWORD=secure_password_here
REDIS_HOST=localhost
REDIS_PORT=6379

# Logging
LOG_LEVEL=INFO

# Security
MASTER_PASSWORD=1507
EOF
        
        print_status "SUCCESS" "Environment file created"
        print_status "WARNING" "Please edit .env file with your configuration"
    else
        print_status "INFO" "Environment file already exists"
    fi
}

# Setup cron jobs
setup_cron() {
    print_status "INFO" "Setting up cron jobs..."
    
    # Create temporary cron file
    local temp_cron=$(mktemp)
    
    # Add existing crontab
    crontab -l 2>/dev/null > "$temp_cron" || true
    
    # Add automation jobs
    cat >> "$temp_cron" <<EOF

# TikTok Automation System
0 */6 * * * cd $PROJECT_ROOT && ./scripts/automation/gm-system heal
0 2 * * * cd $PROJECT_ROOT && ./scripts/automation/gm-system backup
*/30 * * * * cd $PROJECT_ROOT && ./scripts/automation/gm-content --topic='scheduled content' --template=viral_facts --count=1
EOF
    
    # Install new crontab
    crontab "$temp_cron"
    rm "$temp_cron"
    
    print_status "SUCCESS" "Cron jobs configured"
}

# Run post-installation tests
run_tests() {
    print_status "INFO" "Running post-installation tests..."
    
    # Test Python environment
    cd "$PROJECT_ROOT"
    source venv/bin/activate
    
    if python3 -c "import flask, requests, psutil"; then
        print_status "SUCCESS" "Python environment test passed"
    else
        print_status "ERROR" "Python environment test failed"
        return 1
    fi
    
    # Test system tools
    local tools=("ffmpeg" "convert" "jq")
    for tool in "${tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            print_status "SUCCESS" "$tool is available"
        else
            print_status "ERROR" "$tool is not available"
            return 1
        fi
    done
    
    # Test services
    if systemctl is-enabled n8n &>/dev/null; then
        print_status "SUCCESS" "n8n service is enabled"
    else
        print_status "ERROR" "n8n service is not enabled"
        return 1
    fi
    
    print_status "SUCCESS" "All post-installation tests passed"
}

# Display completion message
show_completion() {
    print_status "SUCCESS" "Installation completed successfully!"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "1. Edit the configuration file: $PROJECT_ROOT/.env"
    echo "2. Configure your domain and API keys"
    echo "3. Start the services:"
    echo "   sudo systemctl start n8n"
    echo "   sudo systemctl start gm-dashboard"
    echo "4. Access the interfaces:"
    echo "   - n8n Dashboard: http://localhost:5678"
    echo "   - Monitoring Dashboard: http://localhost:8080"
    echo "5. Generate your first API key:"
    echo "   ./scripts/automation/gm-api new --platform=tiktok --alias=main"
    echo ""
    echo -e "${BLUE}Useful Commands:${NC}"
    echo "- System status: ./scripts/automation/gm-system status"
    echo "- Health check: ./scripts/automation/gm-system health"
    echo "- Generate content: ./scripts/automation/gm-content --topic='your topic'"
    echo "- View logs: tail -f data/logs/system.log"
    echo ""
    echo -e "${YELLOW}Important:${NC}"
    echo "- Configure your domain in .env file"
    echo "- Set up SSL certificates for production"
    echo "- Configure firewall rules for your network"
    echo "- Regularly update the system and dependencies"
    echo ""
    echo "Installation log saved to: $LOG_FILE"
}

# Main installation function
main() {
    print_status "INFO" "Starting TikTok Automation System installation..."
    
    check_root
    check_requirements
    update_system
    install_dependencies
    setup_python_env
    setup_nodejs_env
    create_service_user
    setup_secrets
    setup_services
    setup_firewall
    setup_log_rotation
    create_env_file
    setup_cron
    run_tests
    show_completion
    
    print_status "SUCCESS" "Installation completed at $(date)"
}

# Handle script interruption
trap 'print_status "ERROR" "Installation interrupted"; exit 1' INT TERM

# Run main function
main "$@"
