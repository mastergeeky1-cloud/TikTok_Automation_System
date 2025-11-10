# TikTok Automation System - Installation Guide

**Geeky Workflow Core v2.0**

## 🚀 Quick Start

### Prerequisites
- **OS**: Ubuntu 20.04+ or Debian 10+
- **RAM**: Minimum 4GB, recommended 8GB+
- **Storage**: Minimum 10GB free space
- **Network**: Internet connection for API access
- **Permissions**: sudo access for system installation

### One-Click Installation
```bash
# Clone or extract the system to your desktop
cd /home/geeky/Desktop/TikTok_Automation_System

# Run the automated setup
chmod +x scripts/deployment/setup.sh
./scripts/deployment/setup.sh
```

## 📋 Manual Installation

### 1. System Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install core packages
sudo apt install -y python3 python3-pip python3-venv nodejs npm curl wget git build-essential

# Install media processing tools
sudo apt install -y ffmpeg imagemagick libmagickwand-dev

# Install database systems
sudo apt install -y sqlite3 postgresql redis-server

# Install utilities
sudo apt install -y jq htop net-tools unzip
```

### 2. Python Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install flask requests pillow opencv-python moviepy whisper openai psutil schedule python-dotenv cryptography psycopg2-binary redis
```

### 3. Node.js Environment
```bash
# Install n8n and PM2
sudo npm install -g n8n pm2
```

### 4. System Configuration
```bash
# Create service user
sudo useradd -r -s /bin/false gm_automation

# Setup secrets directory
sudo mkdir -p /etc/gm-secrets
sudo chmod 700 /etc/gm-secrets
sudo chown gm_automation:gm_automation /etc/gm-secrets

# Create API keys file
sudo touch /etc/gm-secrets/tiktok_keys.env
sudo chmod 600 /etc/gm-secrets/tiktok_keys.env
```

### 5. Environment Configuration
Create `.env` file in project root:
```bash
# Domain Configuration
GM_DOMAIN=[your-domain.com]
GM_API_BASE=https://api.[your-domain.com]
GM_N8N_URL=https://automation.[your-domain.com]

# AI Services
OPENAI_API_KEY=your_openai_api_key_here
STABLE_DIFFUSION_URL=http://localhost:7860

# Database
POSTGRES_PASSWORD=secure_password_here
REDIS_HOST=localhost
REDIS_PORT=6379

# Logging
LOG_LEVEL=INFO

# Security
MASTER_PASSWORD=1507
```

## 🔧 Service Configuration

### Systemd Services

#### n8n Service
```bash
sudo tee /etc/systemd/system/n8n.service > /dev/null <<EOF
[Unit]
Description=n8n workflow automation
After=network.target

[Service]
Type=simple
User=gm_automation
WorkingDirectory=/path/to/TikTok_Automation_System
Environment=NODE_ENV=production
ExecStart=/usr/bin/n8n start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

#### Monitoring Dashboard Service
```bash
sudo tee /etc/systemd/system/gm-dashboard.service > /dev/null <<EOF
[Unit]
Description=GM Monitoring Dashboard
After=network.target

[Service]
Type=simple
User=gm_automation
WorkingDirectory=/path/to/TikTok_Automation_System
Environment=PATH=/path/to/TikTok_Automation_System/venv/bin
ExecStart=/path/to/TikTok_Automation_System/venv/bin/python3 core/monitoring/dashboard.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### Enable Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable n8n gm-dashboard
sudo systemctl start n8n gm-dashboard
```

## 🔐 Security Setup

### Firewall Configuration
```bash
# Enable firewall
sudo ufw enable

# Allow essential ports
sudo ufw allow ssh
sudo ufw allow 5678/tcp  # n8n
sudo ufw allow 8080/tcp  # monitoring
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
```

### SSL Certificate Setup
```bash
# Install Let's Encrypt
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d [your-domain.com] -d automation.[your-domain.com] -d api.[your-domain.com] -d logs.[your-domain.com]
```

## 🌐 Domain Configuration

### DNS Records
Configure these DNS records for your domain:

| Type | Host | Value |
|------|------|-------|
| A | @ | Your server IP |
| A | automation | Your server IP |
| A | api | Your server IP |
| A | logs | Your server IP |

### NGINX Configuration
```nginx
# Main domain
server {
    listen 80;
    server_name [your-domain.com];
    return 301 https://$server_name$request_uri;
}

# Automation subdomain (n8n)
server {
    listen 80;
    server_name automation.[your-domain.com];
    location / {
        proxy_pass http://localhost:5678;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# API subdomain
server {
    listen 80;
    server_name api.[your-domain.com];
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Logs subdomain (monitoring)
server {
    listen 80;
    server_name logs.[your-domain.com];
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📊 Initial Configuration

### 1. Generate API Keys
```bash
# Generate TikTok API key
./scripts/automation/gm-api new --platform=tiktok --alias=main

# List configured keys
./scripts/automation/gm-api list
```

### 2. Test Content Generation
```bash
# Generate test content
./scripts/automation/gm-content --topic="test video" --template=viral_facts --count=1

# List generated content
./scripts/automation/gm-content list
```

### 3. Verify System Health
```bash
# Check system status
./scripts/automation/gm-system status

# Run health check
./scripts/automation/gm-system health
```

## 🔍 Verification

### Service Status
```bash
# Check all services
systemctl status n8n gm-dashboard

# Check ports
netstat -tlnp | grep -E ':(5678|8080|3000)'
```

### Access Points
After installation, you should be able to access:

- **n8n Dashboard**: `http://localhost:5678`
- **Monitoring Dashboard**: `http://localhost:8080`
- **System Logs**: `./data/logs/system.log`

## 🛠️ Troubleshooting

### Common Issues

#### Permission Errors
```bash
# Fix permissions
sudo chown -R gm_automation:gm_automation /path/to/TikTok_Automation_System
sudo chmod +x scripts/automation/*
```

#### Service Won't Start
```bash
# Check service logs
sudo journalctl -u n8n -f
sudo journalctl -u gm-dashboard -f

# Restart services
sudo systemctl restart n8n gm-dashboard
```

#### Python Module Errors
```bash
# Reinstall Python packages
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

#### Port Conflicts
```bash
# Check what's using ports
sudo lsof -i :5678
sudo lsof -i :8080

# Kill conflicting processes
sudo kill -9 <PID>
```

### Log Locations
- **System Logs**: `./data/logs/system.log`
- **API Logs**: `./data/logs/api_manager.log`
- **Content Logs**: `./data/logs/content_manager.log`
- **Service Logs**: `sudo journalctl -u <service-name>`

## 📈 Performance Optimization

### Database Optimization
```bash
# PostgreSQL tuning
sudo -u postgres psql -c "ALTER SYSTEM SET shared_buffers = '256MB';"
sudo -u postgres psql -c "ALTER SYSTEM SET effective_cache_size = '1GB';"
sudo systemctl restart postgresql
```

### Resource Limits
```bash
# Increase file limits
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf
```

## 🔄 Maintenance

### Automated Tasks
The system includes automated maintenance via cron:
- Health checks every 6 hours
- Backups daily at 2 AM
- Content generation every 30 minutes

### Manual Maintenance
```bash
# System healing
./scripts/automation/gm-system heal

# Create backup
./scripts/automation/gm-system backup

# Clean old logs
find ./data/logs -name "*.log" -mtime +30 -delete
```

## 📞 Support

### Getting Help
1. Check the logs: `./data/logs/system.log`
2. Run health check: `./scripts/automation/gm-system health`
3. Review documentation: `./docs/`
4. Check system status: `./scripts/automation/gm-system status`

### Configuration Files
- **Main Config**: `./core/config/main_config.py`
- **Environment**: `.env`
- **API Keys**: `/etc/gm-secrets/tiktok_keys.env`
- **Service Config**: `/etc/systemd/system/`

---

**Installation completed! 🎉**

Next: Configure your API keys and domain settings to start automating your TikTok content.
