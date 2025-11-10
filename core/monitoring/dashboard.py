#!/usr/bin/env python3
"""
TikTok Automation System - Monitoring Dashboard
Geeky Workflow Core v2.0
"""

import os
import json
import time
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from flask import Flask, render_template, jsonify, request
import threading

# Import configuration and logging
import sys
sys.path.append(str(Path(__file__).parent.parent / "config"))
sys.path.append(str(Path(__file__).parent.parent / "logging"))
from main_config import config
from logger import system_logger

@dataclass
class SystemMetric:
    """System metric data structure"""
    timestamp: datetime
    metric_name: str
    metric_value: float
    unit: str
    tags: Dict[str, str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    metric: str
    operator: str  # >, <, >=, <=, ==
    threshold: float
    severity: str  # info, warning, critical
    enabled: bool = True
    
    def check(self, value: float) -> bool:
        """Check if alert should trigger"""
        operators = {
            '>': lambda x, y: x > y,
            '<': lambda x, y: x < y,
            '>=': lambda x, y: x >= y,
            '<=': lambda x, y: x <= y,
            '==': lambda x, y: x == y
        }
        
        if self.operator in operators:
            return operators[self.operator](value, self.threshold)
        return False

class MetricsCollector:
    """Collects system metrics"""
    
    def __init__(self):
        self.db_path = Path(config.logging.log_dir) / "metrics.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        self.running = False
        self.thread = None
    
    def _init_database(self):
        """Initialize metrics database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    unit TEXT NOT NULL,
                    tags TEXT
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_metric_name 
                ON metrics(metric_name)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON metrics(timestamp)
            ''')
    
    def collect_system_metrics(self) -> List[SystemMetric]:
        """Collect basic system metrics"""
        metrics = []
        timestamp = datetime.now()
        
        try:
            # CPU usage (simplified)
            with open('/proc/loadavg', 'r') as f:
                load_avg = float(f.read().split()[0])
                metrics.append(SystemMetric(
                    timestamp, 'system.load_avg', load_avg, 'count'
                ))
            
            # Memory usage
            with open('/proc/meminfo', 'r') as f:
                meminfo = {}
                for line in f:
                    if ':' in line:
                        key, value = line.split(':')
                        meminfo[key.strip()] = int(value.split()[0])
                
                total_mem = meminfo.get('MemTotal', 0)
                free_mem = meminfo.get('MemFree', 0)
                available_mem = meminfo.get('MemAvailable', free_mem)
                
                if total_mem > 0:
                    memory_usage = ((total_mem - available_mem) / total_mem) * 100
                    metrics.append(SystemMetric(
                        timestamp, 'system.memory_usage', memory_usage, 'percent'
                    ))
            
            # Disk usage
            statvfs = os.statvfs('.')
            total_space = statvfs.f_frsize * statvfs.f_blocks
            free_space = statvfs.f_frsize * statvfs.f_bavail
            
            if total_space > 0:
                disk_usage = ((total_space - free_space) / total_space) * 100
                metrics.append(SystemMetric(
                    timestamp, 'system.disk_usage', disk_usage, 'percent'
                ))
            
            # Application metrics
            metrics.extend(self._collect_app_metrics(timestamp))
            
        except Exception as e:
            system_logger.get_logger("metrics").error(f"Metric collection failed: {e}")
        
        return metrics
    
    def _collect_app_metrics(self, timestamp: datetime) -> List[SystemMetric]:
        """Collect application-specific metrics"""
        metrics = []
        
        try:
            # Content generation metrics
            content_dir = Path(config.content.output_dir)
            if content_dir.exists():
                video_count = len(list(content_dir.glob("*.mp4")))
                metrics.append(SystemMetric(
                    timestamp, 'content.video_count', video_count, 'count'
                ))
            
            # API key metrics
            secrets_dir = Path("/etc/gm-secrets")
            if (secrets_dir / "tiktok_keys.env").exists():
                with open(secrets_dir / "tiktok_keys.env", 'r') as f:
                    key_count = len([line for line in f if line.strip()])
                    metrics.append(SystemMetric(
                        timestamp, 'api.key_count', key_count, 'count'
                    ))
            
            # Log metrics
            log_dir = Path(config.logging.log_dir)
            if log_dir.exists():
                log_size = sum(f.stat().st_size for f in log_dir.glob("*.log*"))
                metrics.append(SystemMetric(
                    timestamp, 'logging.total_size_mb', log_size / (1024*1024), 'MB'
                ))
        
        except Exception as e:
            system_logger.get_logger("metrics").error(f"App metrics collection failed: {e}")
        
        return metrics
    
    def store_metrics(self, metrics: List[SystemMetric]):
        """Store metrics in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for metric in metrics:
                    tags_json = json.dumps(metric.tags) if metric.tags else None
                    conn.execute('''
                        INSERT INTO metrics (timestamp, metric_name, metric_value, unit, tags)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        metric.timestamp.isoformat(),
                        metric.metric_name,
                        metric.metric_value,
                        metric.unit,
                        tags_json
                    ))
                
                conn.commit()
        
        except Exception as e:
            system_logger.get_logger("metrics").error(f"Metric storage failed: {e}")
    
    def get_metrics(self, 
                   metric_name: str,
                   hours: int = 24) -> List[Dict[str, Any]]:
        """Retrieve metrics from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM metrics 
                    WHERE metric_name = ? 
                    AND timestamp > datetime('now', '-{} hours')
                    ORDER BY timestamp DESC
                '''.format(hours), (metric_name,))
                
                return [dict(row) for row in cursor.fetchall()]
        
        except Exception as e:
            system_logger.get_logger("metrics").error(f"Metric retrieval failed: {e}")
            return []
    
    def start_collection(self, interval: int = 60):
        """Start metrics collection thread"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._collection_loop, args=(interval,))
        self.thread.daemon = True
        self.thread.start()
        
        system_logger.log_system_event("monitoring", "Started metrics collection")
    
    def _collection_loop(self, interval: int):
        """Main collection loop"""
        while self.running:
            try:
                metrics = self.collect_system_metrics()
                self.store_metrics(metrics)
                time.sleep(interval)
            except Exception as e:
                system_logger.get_logger("metrics").error(f"Collection loop error: {e}")
                time.sleep(interval)
    
    def stop_collection(self):
        """Stop metrics collection"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        system_logger.log_system_event("monitoring", "Stopped metrics collection")

class AlertManager:
    """Manages alert rules and notifications"""
    
    def __init__(self):
        self.rules = self._load_default_rules()
        self.active_alerts = {}
    
    def _load_default_rules(self) -> List[AlertRule]:
        """Load default alert rules"""
        return [
            AlertRule("High CPU Usage", "system.load_avg", ">", 2.0, "warning"),
            AlertRule("High Memory Usage", "system.memory_usage", ">", 80.0, "warning"),
            AlertRule("Critical Memory Usage", "system.memory_usage", ">", 90.0, "critical"),
            AlertRule("High Disk Usage", "system.disk_usage", ">", 85.0, "warning"),
            AlertRule("Critical Disk Usage", "system.disk_usage", ">", 95.0, "critical"),
        ]
    
    def check_alerts(self, metrics: List[SystemMetric]):
        """Check metrics against alert rules"""
        for metric in metrics:
            for rule in self.rules:
                if not rule.enabled:
                    continue
                
                if rule.metric == metric.metric_name:
                    if rule.check(metric.metric_value):
                        self._trigger_alert(rule, metric)
                    else:
                        self._resolve_alert(rule, metric)
    
    def _trigger_alert(self, rule: AlertRule, metric: SystemMetric):
        """Trigger an alert"""
        alert_key = f"{rule.name}_{rule.metric}"
        
        if alert_key not in self.active_alerts:
            self.active_alerts[alert_key] = {
                'rule': rule,
                'triggered_at': metric.timestamp,
                'current_value': metric.metric_value
            }
            
            system_logger.log_with_details(
                "alerts",
                "WARNING" if rule.severity == "warning" else "CRITICAL",
                f"Alert triggered: {rule.name}",
                {
                    "rule": rule.name,
                    "metric": rule.metric,
                    "threshold": rule.threshold,
                    "current_value": metric.metric_value,
                    "severity": rule.severity
                }
            )
    
    def _resolve_alert(self, rule: AlertRule, metric: SystemMetric):
        """Resolve an alert"""
        alert_key = f"{rule.name}_{rule.metric}"
        
        if alert_key in self.active_alerts:
            del self.active_alerts[alert_key]
            
            system_logger.log_with_details(
                "alerts",
                "INFO",
                f"Alert resolved: {rule.name}",
                {
                    "rule": rule.name,
                    "metric": rule.metric,
                    "current_value": metric.metric_value
                }
            )
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get list of active alerts"""
        return [
            {
                "name": alert["rule"].name,
                "metric": alert["rule"].metric,
                "severity": alert["rule"].severity,
                "threshold": alert["rule"].threshold,
                "current_value": alert["current_value"],
                "triggered_at": alert["triggered_at"].isoformat()
            }
            for alert in self.active_alerts.values()
        ]

# Initialize components
metrics_collector = MetricsCollector()
alert_manager = AlertManager()

# Flask dashboard application
app = Flask(__name__)

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/metrics')
def get_metrics():
    """API endpoint for metrics"""
    metric_name = request.args.get('metric', 'system.load_avg')
    hours = int(request.args.get('hours', 24))
    
    metrics = metrics_collector.get_metrics(metric_name, hours)
    return jsonify(metrics)

@app.route('/api/system_status')
def get_system_status():
    """API endpoint for system status"""
    try:
        current_metrics = metrics_collector.collect_system_metrics()
        alert_manager.check_alerts(current_metrics)
        
        status = {
            "timestamp": datetime.now().isoformat(),
            "metrics": [metric.to_dict() for metric in current_metrics],
            "alerts": alert_manager.get_active_alerts(),
            "status": "healthy" if not alert_manager.active_alerts else "warning"
        }
        
        return jsonify(status)
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/api/logs')
def get_logs():
    """API endpoint for recent logs"""
    try:
        logs = system_logger.search_logs("", level=request.args.get('level'))
        return jsonify(logs[-50:])  # Return last 50 logs
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def create_dashboard_template():
    """Create the dashboard HTML template"""
    template_dir = Path(__file__).parent / "templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    
    template_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TikTok Automation - Monitoring Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2em; font-weight: bold; color: #3498db; }
        .metric-label { color: #7f8c8d; margin-bottom: 10px; }
        .alerts { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .alert { padding: 10px; margin: 5px 0; border-radius: 4px; }
        .alert.warning { background: #fff3cd; border: 1px solid #ffeaa7; }
        .alert.critical { background: #f8d7da; border: 1px solid #f5c6cb; }
        .chart-container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .status-indicator { width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 8px; }
        .status-healthy { background: #27ae60; }
        .status-warning { background: #f39c12; }
        .status-error { background: #e74c3c; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎵 TikTok Automation System</h1>
            <p>Real-time Monitoring Dashboard</p>
            <span id="status-indicator" class="status-indicator"></span>
            <span id="status-text">Loading...</span>
        </div>
        
        <div class="metrics-grid" id="metrics-grid">
            <!-- Metrics will be populated here -->
        </div>
        
        <div class="chart-container">
            <h2>System Performance</h2>
            <canvas id="performanceChart"></canvas>
        </div>
        
        <div class="alerts" id="alerts">
            <h2>Active Alerts</h2>
            <div id="alerts-list">
                <!-- Alerts will be populated here -->
            </div>
        </div>
    </div>

    <script>
        let performanceChart;
        
        function initChart() {
            const ctx = document.getElementById('performanceChart').getContext('2d');
            performanceChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'CPU Load',
                        data: [],
                        borderColor: '#3498db',
                        tension: 0.1
                    }, {
                        label: 'Memory Usage %',
                        data: [],
                        borderColor: '#e74c3c',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
        
        function updateDashboard() {
            fetch('/api/system_status')
                .then(response => response.json())
                .then(data => {
                    updateStatus(data.status);
                    updateMetrics(data.metrics);
                    updateAlerts(data.alerts);
                    updateChart(data.metrics);
                })
                .catch(error => {
                    console.error('Error updating dashboard:', error);
                    updateStatus('error');
                });
        }
        
        function updateStatus(status) {
            const indicator = document.getElementById('status-indicator');
            const text = document.getElementById('status-text');
            
            indicator.className = 'status-indicator status-' + status;
            text.textContent = status.charAt(0).toUpperCase() + status.slice(1);
        }
        
        function updateMetrics(metrics) {
            const grid = document.getElementById('metrics-grid');
            grid.innerHTML = '';
            
            metrics.forEach(metric => {
                const card = document.createElement('div');
                card.className = 'metric-card';
                
                const value = metric.metric_value.toFixed(2);
                const unit = metric.unit === 'percent' ? '%' : metric.unit;
                
                card.innerHTML = `
                    <div class="metric-label">${metric.metric_name.replace('.', ' ').toUpperCase()}</div>
                    <div class="metric-value">${value} ${unit}</div>
                `;
                
                grid.appendChild(card);
            });
        }
        
        function updateAlerts(alerts) {
            const alertsList = document.getElementById('alerts-list');
            
            if (alerts.length === 0) {
                alertsList.innerHTML = '<p>No active alerts</p>';
                return;
            }
            
            alertsList.innerHTML = '';
            alerts.forEach(alert => {
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert ' + alert.severity;
                alertDiv.innerHTML = `
                    <strong>${alert.name}</strong><br>
                    ${alert.metric}: ${alert.current_value.toFixed(2)} (threshold: ${alert.threshold})<br>
                    <small>Triggered: ${new Date(alert.triggered_at).toLocaleString()}</small>
                `;
                alertsList.appendChild(alertDiv);
            });
        }
        
        function updateChart(metrics) {
            if (!performanceChart) return;
            
            const timestamp = new Date().toLocaleTimeString();
            
            // Update chart data
            performanceChart.data.labels.push(timestamp);
            
            const cpuMetric = metrics.find(m => m.metric_name === 'system.load_avg');
            const memoryMetric = metrics.find(m => m.metric_name === 'system.memory_usage');
            
            if (cpuMetric) {
                performanceChart.data.datasets[0].data.push(cpuMetric.metric_value);
            }
            
            if (memoryMetric) {
                performanceChart.data.datasets[1].data.push(memoryMetric.metric_value);
            }
            
            // Keep only last 20 data points
            if (performanceChart.data.labels.length > 20) {
                performanceChart.data.labels.shift();
                performanceChart.data.datasets.forEach(dataset => {
                    dataset.data.shift();
                });
            }
            
            performanceChart.update();
        }
        
        // Initialize dashboard
        initChart();
        updateDashboard();
        
        // Update every 30 seconds
        setInterval(updateDashboard, 30000);
    </script>
</body>
</html>
    '''
    
    with open(template_dir / "dashboard.html", 'w') as f:
        f.write(template_content)

def start_dashboard(host: str = "0.0.0.0", port: int = 8080):
    """Start the monitoring dashboard"""
    # Create template
    create_dashboard_template()
    
    # Start metrics collection
    metrics_collector.start_collection()
    
    # Start Flask app
    system_logger.log_system_event("monitoring", f"Starting dashboard on {host}:{port}")
    
    app.run(host=host, port=port, debug=False)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitoring dashboard")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    
    args = parser.parse_args()
    
    start_dashboard(args.host, args.port)
