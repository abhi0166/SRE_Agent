# Enterprise Storage Monitoring & Alerting System

An advanced enterprise-grade storage monitoring solution with intelligent alerting, automated JIRA ticketing, interactive Slack assignment, and comprehensive analytics dashboard.

## Demo: https://youtu.be/y8xeC-W-K3o

## 🚀 Key Features

### Core Monitoring
- **Real-time Storage Analytics**: Advanced disk usage, inode consumption, and system performance tracking
- **Multi-threshold Alerting**: Configurable warning/critical thresholds with intelligent escalation
- **Enterprise Dashboard**: Professional-grade monitoring interface with 20+ years storage engineering expertise
- **Continuous Monitoring**: Automated alert generation with configurable intervals

### Integration & Automation
- **Smart JIRA Integration**: Automatic ticket creation with deduplication prevention
- **Interactive Slack Assignment**: 2-way communication with emoji reaction handling
- **Webhook Processing**: Prometheus-compatible alert ingestion
- **Database Persistence**: Complete audit trails and metrics history

### Advanced Capabilities
- **Ticket Deduplication**: Prevents duplicate JIRA tickets for identical alerts
- **Interactive Assignment**: Team members can claim alerts using emoji reactions (👀 🔍 🔨 🛠️ ⚙️)
- **Rich Slack Formatting**: Enterprise-grade message layouts with visual hierarchy
- **Manual Ticket Creation**: On-demand JIRA ticket generation from Slack alerts

## 📊 Enterprise Dashboard Features

- **Live Metrics Visualization**: Real-time system performance indicators
- **Alert Analytics**: Historical trends and pattern analysis
- **Capacity Planning**: Storage growth projections and recommendations
- **Performance Monitoring**: System load, memory, and I/O analytics
- **Interactive Management**: Alert status updates and assignment tracking

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8+
- macOS/Linux system
- JIRA account with API access
- Slack workspace with bot permissions

### Quick Start
```bash
# Clone and setup
git clone <repository-url>
cd storage-monitoring
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your API keys and credentials to .env
```

### Environment Configuration
```bash
# JIRA Integration
JIRA_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT=SCRUM

# Slack Integration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_CHANNEL_ID=C1234567890
```

## 🏃‍♂️ Running the System

### Start All Services
```bash
# Webhook server (port 5000)
python run.py

# Enterprise dashboard (port 3000)
python monitoring/enterprise_storage_dashboard.py

# Continuous monitoring (60-second intervals)
cd monitoring && python storage_alert_generator.py --interval 60
```

### Service Architecture
- **Webhook Server**: Handles alert ingestion and processing
- **Enterprise Dashboard**: Professional monitoring interface
- **Continuous Monitor**: Automated alert generation and dispatch

## 📱 API Endpoints

### Core Endpoints
- `POST /webhook/alert` - Process Prometheus-style alerts
- `GET /api/alerts` - Retrieve alert history with filtering
- `GET /api/metrics` - System performance data
- `GET /api/database-status` - Database connection health

### Management Endpoints
- `GET /create-jira-ticket` - Manual JIRA ticket creation
- `POST /slack/events` - Slack Events API for interactive features
- `PUT /api/alerts/<id>/status` - Update alert status
- `GET /api/alert-stats` - Alert statistics and analytics

## 🎯 Smart Alert Processing

### Alert Types & Thresholds
| Alert Type | Warning | Critical | Description |
|------------|---------|----------|-------------|
| **DiskSpaceUsage** | 80% | 90% | Storage capacity monitoring |
| **InodeUsage** | 85% | 95% | File system inode exhaustion |
| **HighSystemLoad** | 5.0 | 10.0 | CPU load average monitoring |

### Intelligent Features
- **Signature-based Deduplication**: Prevents duplicate tickets using `alertname_instance` matching
- **Automatic Escalation**: Critical alerts trigger immediate JIRA ticket creation
- **Context-aware Formatting**: Rich descriptions with system metrics and remediation steps

## 🎫 JIRA Integration Features

### Automatic Ticket Creation
- **Smart Deduplication**: Checks existing tickets before creating duplicates
- **Rich Descriptions**: Detailed problem analysis with system context
- **Intelligent Labeling**: Automated categorization and priority assignment
- **Sequential Numbering**: Maintains proper ticket numbering (SCRUM-XX)

### Manual Ticket Creation
- **Slack Button Integration**: Create tickets directly from Slack alerts
- **Permission Handling**: Graceful fallback when API permissions are insufficient
- **Template Generation**: Manual ticket templates when automation fails

## 💬 Interactive Slack Integration

### Enterprise-Grade Formatting
- **Visual Hierarchy**: Professional message layouts with clear severity indicators
- **System Context**: Comprehensive metrics and diagnostic information
- **Action Buttons**: Interactive elements for ticket creation and assignment

### 2-Way Communication Features
- **Emoji Assignment**: Team members react with 👀 🔍 🔨 🛠️ ⚙️ to claim alerts
- **Automatic Updates**: Messages update to show assignment status
- **User Recognition**: Displays assigned team member names
- **Event Processing**: Slack Events API integration for real-time interaction

### Supported Reactions
| Emoji | Meaning | Action |
|-------|---------|--------|
| 👀 | Taking a look | Assigns alert to reacting user |
| 🔍 | Investigating | Assigns alert to reacting user |
| 🔨 | Working on fix | Assigns alert to reacting user |
| 🛠️ | Troubleshooting | Assigns alert to reacting user |
| ⚙️ | System maintenance | Assigns alert to reacting user |

## 📈 Database Architecture

### Core Tables
```sql
alerts: Alert records and metadata
├── alert_id (PRIMARY KEY)
├── alertname, instance, severity
├── status, labels, annotations
├── created_at, updated_at
└── jira_data (JSON)

jira_tickets: JIRA integration tracking
├── alert_id (FOREIGN KEY)
├── ticket_key, ticket_url
├── status, created_at
└── UNIQUE constraint on ticket_key

alert_history: Complete audit trail
├── alert_id, timestamp
├── action, metadata
└── Change tracking

system_metrics: Performance data
├── hostname, timestamp
├── cpu_usage, memory_usage
├── disk_metrics (JSON)
└── load_averages
```

### Advanced Features
- **ACID Compliance**: SQLite with proper transaction handling
- **Relationship Integrity**: Foreign key constraints and referential integrity
- **JSON Storage**: Flexible metadata and configuration storage
- **Indexing**: Optimized queries for performance at scale

## 🔍 Monitoring & Analytics

### Real-time Metrics
- **Storage Capacity**: Usage trends and capacity planning
- **System Performance**: CPU, memory, and I/O monitoring
- **Alert Patterns**: Frequency analysis and trend identification
- **Response Times**: JIRA ticket creation and resolution tracking

### Historical Analysis
- **Alert Trends**: Pattern recognition and predictive analysis
- **System Health**: Long-term performance monitoring
- **Capacity Planning**: Growth projections and recommendations
- **Team Performance**: Assignment and resolution metrics

## 🧪 Testing & Validation

### Comprehensive Test Suite
```bash
# Complete system testing
python test_monitoring.py

# Database integration testing
python test_database.py

# JIRA functionality testing
python test_jira_fix.py

# Generate realistic test alerts
python generate_test_alerts.py
```

### Test Coverage
- **Alert Processing**: End-to-end webhook processing
- **Database Operations**: CRUD operations and data integrity
- **JIRA Integration**: Ticket creation and deduplication
- **Slack Notifications**: Message formatting and delivery

## 🔒 Security & Compliance

### Security Features
- **Environment-based Configuration**: Secure credential management
- **API Token Encryption**: Secure storage and transmission
- **Input Validation**: Comprehensive data sanitization
- **Error Handling**: Secure error responses without information leakage

### Compliance Ready
- **Audit Trails**: Complete activity logging
- **Data Retention**: Configurable retention policies
- **Access Control**: Role-based permission handling
- **Monitoring**: Security event tracking and alerting

## 📚 Documentation Suite

### Setup Guides
- [Detailed Setup Guide](SETUP_GUIDE.md) - Complete installation instructions
- [Slack Events Setup](SLACK_EVENTS_SETUP.md) - Interactive features configuration
- [Database Integration](DATABASE_INTEGRATION.md) - Database setup and management

### Technical Documentation
- [Storage Metrics Architecture](STORAGE_METRICS_ARCHITECTURE.md) - System design details
- [Monitoring Status](MONITORING_STATUS.md) - Current system status
- [API Documentation](API_DOCS.md) - Complete endpoint reference

## 🏗️ System Architecture

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│  Continuous Monitor │───▶│   Webhook Server     │───▶│     Database        │
│  (Alert Generation) │    │   (Flask/Processing) │    │   (SQLite/Audit)    │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
                                      │                           │
                                      ▼                           ▼
                           ┌──────────────────────┐    ┌─────────────────────┐
                           │   Enterprise Integrations    │    │   Analytics Dashboard  │
                           │                      │    │   (Real-time Metrics)  │
                           │  ┌─────────────────┐ │    └─────────────────────┘
                           │  │ JIRA Ticketing │ │
                           │  │ (Deduplication) │ │
                           │  └─────────────────┘ │
                           │  ┌─────────────────┐ │
                           │  │ Slack Assignment│ │
                           │  │ (2-way Comms)   │ │
                           │  └─────────────────┘ │
                           └──────────────────────┘
```

## 🔄 Workflow Integration

### Alert Lifecycle
1. **Detection**: Continuous monitoring detects threshold breach
2. **Processing**: Webhook server validates and formats alert
3. **Notification**: Slack message sent with enterprise formatting
4. **Assignment**: Team member reacts with emoji to claim alert
5. **Ticketing**: JIRA ticket created automatically (if new) or linked (if existing)
6. **Tracking**: Complete audit trail maintained in database
7. **Resolution**: Status updates tracked through integration points

### Deduplication Process
1. **Signature Generation**: `alertname_instance` key created
2. **Database Lookup**: Check for existing open tickets
3. **Decision Logic**: Create new ticket or reference existing
4. **User Notification**: Clear messaging about ticket status
5. **Audit Trail**: All decisions logged for compliance

## 🤝 Contributing

### Development Guidelines
1. **Fork Repository**: Create feature branch from main
2. **Code Standards**: Follow PEP 8 and enterprise coding practices
3. **Testing Required**: Add comprehensive tests for new features
4. **Documentation**: Update relevant documentation files
5. **Pull Request**: Submit with detailed description and test results

### Feature Requests
- **Slack Integration**: Additional reaction types and workflows
- **JIRA Enhancements**: Custom field mapping and workflow integration
- **Analytics**: Advanced reporting and trend analysis
- **Scalability**: Multi-tenant and distributed deployment options

## 📄 License

MIT License - Enterprise features available under commercial licensing

---

**Enterprise Support**: Contact for professional services, custom integrations, and enterprise licensing options.
