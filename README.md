# TikTok Automation System 🎵

## 🌟 Overview

A complete, self-hosted TikTok automation system built on Linux with AI-powered content generation, scheduled publishing, and multi-account management.

## 🏗️ System Architecture

### Domain Structure

- **Primary Domain**: `[your-domain.com]`
- **Automation Dashboard**: `automation.[your-domain.com]` (n8n)
- **API Gateway**: `api.[your-domain.com]` (TikTok API & Webhooks)
- **Monitoring**: `logs.[your-domain.com]` (Public logs & monitoring)

### Core Components

1. **Content Generation Engine** - AI-powered video/image creation
2. **API Management System** - TikTok token rotation & validation
3. **Scheduling Pipeline** - Automated publishing workflows
4. **Multi-Account Support** - Concurrent account management
5. **Self-Healing System** - Auto-repair and recovery
6. **Centralized Logging** - Complete operation tracking

## 📁 Project Structure

```text
TikTok_Automation_System/
├── core/                    # Core system modules
│   ├── api/                # TikTok API integration
│   ├── auth/               # Authentication & security
│   ├── config/             # Configuration management
│   ├── content/            # Content generation engine
│   ├── logging/            # Centralized logging
│   └── monitoring/         # System monitoring
├── scripts/                # Automation scripts
│   ├── automation/         # Main automation workflows
│   ├── content/            # Content creation scripts
│   ├── deployment/         # Deployment & setup
│   └── maintenance/        # System maintenance
├── data/                   # Data storage
│   ├── templates/          # Content templates
│   ├── media/              # Generated media
│   ├── logs/               # System logs
│   └── backups/            # System backups
├── docs/                   # Documentation
│   ├── setup/              # Setup guides
│   ├── api/                # API documentation
│   └── deployment/         # Deployment guides
├── tests/                  # Test suite
└── assets/                 # Static assets
    ├── images/             # Image resources
    ├── sounds/             # Audio resources
    └── fonts/              # Font resources
```

## 🚀 Quick Start

### Prerequisites

- Linux (Ubuntu/Debian) with root access
- Domain with DNS control
- Node.js, Python3, FFmpeg, ImageMagick
- PostgreSQL/Redis (optional)

### Installation

```bash
# Clone and setup
cd /home/geeky/Desktop/TikTok_Automation_System
chmod +x scripts/deployment/setup.sh
sudo ./scripts/deployment/setup.sh

# Configure domain
sudo ./scripts/deployment/configure_domain.sh [your-domain.com]

# Initialize API keys
./scripts/automation/gm-api new --platform=tiktok --alias=main
```

## 🔧 Configuration

### Environment Variables

```bash
# Core Configuration
GM_DOMAIN=[your-domain.com]
GM_API_BASE=https://api.[your-domain.com]
GM_N8N_URL=https://automation.[your-domain.com]

# AI Services
OPENAI_API_KEY=your_openai_key
STABLE_DIFFUSION_URL=http://localhost:7860

# TikTok API
TIKTOK_CLIENT_KEY=your_client_key
TIKTOK_CLIENT_SECRET=your_client_secret
```

## 📊 Features

### ✅ Content Generation

- AI-powered video creation
- Automated caption generation
- Multi-format support (MP4, MOV, images)
- Template-based content
- Custom branding

### ✅ API Management

- Automatic token rotation
- Multi-account support
- Health monitoring
- Rate limiting
- Error recovery

### ✅ Scheduling & Publishing

- Cron-based scheduling
- n8n workflow integration
- Bulk publishing
- Time zone optimization
- Retry mechanisms

### ✅ Monitoring & Logging

- Real-time dashboards
- Performance metrics
- Error tracking
- Success rates
- System health

## 🔐 Security Features

- 4-layer security architecture
- Encrypted credential storage
- GPG encryption for sensitive data
- SSL/TLS enforcement
- API rate limiting
- Access logging

## 📈 Monitoring Dashboard

Access your monitoring dashboard at:
`https://logs.[your-domain.com]`

## 🛠️ API Commands

```bash
# API Management
gm-api new --platform=tiktok --alias=main
gm-api rotate --platform=tiktok
gm-api list
gm-api delete --alias=old_key

# Content Generation
gm-content generate --template=viral --count=10
gm-content schedule --time="2024-01-01 12:00"
gm-content publish --account=@yourusername

# System Control
gm-system status
gm-system heal
gm-system backup
gm-system restore
```

## 📞 Support

- **Documentation**: `/docs/`
- **API Reference**: `/docs/api/`
- **Troubleshooting**: `/docs/setup/troubleshooting.md`

---

**Built by Geeky Master** 🚀  
*Autonomous AI Automation Engineer*
