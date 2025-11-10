#!/usr/bin/env python3
"""
TikTok Automation System - Centralized Logging
Geeky Workflow Core v2.0
"""

import os
import sys
import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import threading
import queue
import time

# Import configuration
sys.path.append(str(Path(__file__).parent.parent / "config"))
from main_config import config

@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: str
    level: str
    module: str
    message: str
    details: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging"""
    
    def format(self, record):
        log_entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created).isoformat(),
            level=record.levelname,
            module=record.name,
            message=record.getMessage(),
            details=getattr(record, 'details', None),
            user_id=getattr(record, 'user_id', None),
            session_id=getattr(record, 'session_id', None)
        )
        
        return json.dumps(log_entry.to_dict())

class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)

class LogQueueHandler(logging.Handler):
    """Async logging handler using queue"""
    
    def __init__(self, queue):
        super().__init__()
        self.queue = queue
    
    def emit(self, record):
        try:
            self.queue.put_nowait(record)
        except queue.Full:
            # If queue is full, drop the log entry
            pass

class AsyncLogWorker(threading.Thread):
    """Background worker for async log processing"""
    
    def __init__(self, log_queue, handlers):
        super().__init__(daemon=True)
        self.log_queue = log_queue
        self.handlers = handlers
        self.running = True
    
    def run(self):
        while self.running:
            try:
                record = self.log_queue.get(timeout=1)
                for handler in self.handlers:
                    handler.emit(record)
                self.log_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Logging worker error: {e}")
    
    def stop(self):
        self.running = False

class SystemLogger:
    """Centralized logging system"""
    
    def __init__(self):
        self.loggers = {}
        self.log_queue = queue.Queue(maxsize=1000)
        self.worker = None
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Create log directory
        log_dir = Path(config.logging.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup handlers
        handlers = []
        
        # File handler (structured JSON)
        if config.logging.enable_file:
            file_handler = logging.handlers.RotatingFileHandler(
                log_dir / "system.log",
                maxBytes=config.logging.max_log_size,
                backupCount=config.logging.backup_count
            )
            file_handler.setFormatter(StructuredFormatter())
            handlers.append(file_handler)
        
        # Console handler (colored)
        if config.logging.enable_console:
            console_handler = logging.StreamHandler()
            console_formatter = ColoredFormatter(
                '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            handlers.append(console_handler)
        
        # Start async worker
        self.worker = AsyncLogWorker(self.log_queue, handlers)
        self.worker.start()
        
        # Setup queue handler
        queue_handler = LogQueueHandler(self.log_queue)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, config.logging.log_level))
        root_logger.addHandler(queue_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger for a specific module"""
        if name not in self.loggers:
            logger = logging.getLogger(name)
            self.loggers[name] = logger
        return self.loggers[name]
    
    def log_with_details(self, 
                        logger_name: str,
                        level: str,
                        message: str,
                        details: Optional[Dict[str, Any]] = None,
                        user_id: Optional[str] = None,
                        session_id: Optional[str] = None):
        """Log with additional structured details"""
        logger = self.get_logger(logger_name)
        
        # Create log record with extra details
        record = logger.makeRecord(
            logger.name,
            getattr(logging, level.upper()),
            pathname='',
            lineno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        
        record.details = details
        record.user_id = user_id
        record.session_id = session_id
        
        logger.handle(record)
    
    def log_api_call(self, 
                    endpoint: str,
                    method: str,
                    status_code: int,
                    response_time: float,
                    user_id: Optional[str] = None):
        """Log API call details"""
        self.log_with_details(
            "api",
            "INFO",
            f"API call: {method} {endpoint}",
            details={
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "response_time_ms": response_time * 1000
            },
            user_id=user_id
        )
    
    def log_content_generation(self,
                              topic: str,
                              template: str,
                              content_count: int,
                              success: bool,
                              error: Optional[str] = None):
        """Log content generation events"""
        level = "INFO" if success else "ERROR"
        message = f"Content generation: {topic} ({template})"
        
        details = {
            "topic": topic,
            "template": template,
            "content_count": content_count,
            "success": success
        }
        
        if error:
            details["error"] = error
        
        self.log_with_details("content_generator", level, message, details)
    
    def log_publishing_event(self,
                           video_path: str,
                           account: str,
                           success: bool,
                           video_id: Optional[str] = None,
                           error: Optional[str] = None):
        """Log publishing events"""
        level = "INFO" if success else "ERROR"
        message = f"Publishing: {video_path} to {account}"
        
        details = {
            "video_path": video_path,
            "account": account,
            "success": success
        }
        
        if video_id:
            details["video_id"] = video_id
        
        if error:
            details["error"] = error
        
        self.log_with_details("publisher", level, message, details)
    
    def log_system_event(self,
                        event_type: str,
                        message: str,
                        details: Optional[Dict[str, Any]] = None):
        """Log system-level events"""
        self.log_with_details("system", "INFO", message, details)
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Get logging statistics"""
        log_dir = Path(config.logging.log_dir)
        stats = {
            "log_directory": str(log_dir),
            "total_loggers": len(self.loggers),
            "queue_size": self.log_queue.qsize(),
            "log_files": []
        }
        
        # Get log file information
        for log_file in log_dir.glob("*.log*"):
            file_stat = log_file.stat()
            stats["log_files"].append({
                "name": log_file.name,
                "size_bytes": file_stat.st_size,
                "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            })
        
        return stats
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up old log files"""
        log_dir = Path(config.logging.log_dir)
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        
        cleaned_count = 0
        for log_file in log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    cleaned_count += 1
                    self.log_system_event(
                        "cleanup",
                        f"Deleted old log file: {log_file.name}"
                    )
                except Exception as e:
                    self.log_with_details(
                        "system",
                        "ERROR",
                        f"Failed to delete log file: {log_file.name}",
                        {"error": str(e)}
                    )
        
        if cleaned_count > 0:
            self.log_system_event(
                "cleanup",
                f"Cleaned up {cleaned_count} old log files"
            )
        
        return cleaned_count
    
    def search_logs(self,
                   query: str,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   level: Optional[str] = None) -> list:
        """Search log entries"""
        log_file = Path(config.logging.log_dir) / "system.log"
        
        if not log_file.exists():
            return []
        
        results = []
        
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        
                        # Apply filters
                        if level and entry.get('level') != level:
                            continue
                        
                        if start_time:
                            entry_time = datetime.fromisoformat(entry['timestamp'])
                            if entry_time < start_time:
                                continue
                        
                        if end_time:
                            entry_time = datetime.fromisoformat(entry['timestamp'])
                            if entry_time > end_time:
                                continue
                        
                        # Search query
                        if query.lower() in entry.get('message', '').lower():
                            results.append(entry)
                    
                    except json.JSONDecodeError:
                        continue
        
        except Exception as e:
            self.get_logger("log_search").error(f"Log search failed: {e}")
        
        return results
    
    def shutdown(self):
        """Shutdown the logging system"""
        if self.worker:
            self.worker.stop()
            self.worker.join(timeout=5)

# Global logger instance
system_logger = SystemLogger()

# Convenience functions
def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return system_logger.get_logger(name)

def log_api_call(endpoint: str, method: str, status_code: int, response_time: float, user_id: str = None):
    """Log an API call"""
    system_logger.log_api_call(endpoint, method, status_code, response_time, user_id)

def log_content_generation(topic: str, template: str, content_count: int, success: bool, error: str = None):
    """Log content generation"""
    system_logger.log_content_generation(topic, template, content_count, success, error)

def log_publishing_event(video_path: str, account: str, success: bool, video_id: str = None, error: str = None):
    """Log publishing event"""
    system_logger.log_publishing_event(video_path, account, success, video_id, error)

def log_system_event(event_type: str, message: str, details: Dict[str, Any] = None):
    """Log system event"""
    system_logger.log_system_event(event_type, message, details)

# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="System logging utility")
    parser.add_argument("--stats", action="store_true", help="Show logging statistics")
    parser.add_argument("--search", help="Search logs for query")
    parser.add_argument("--level", help="Filter by log level")
    parser.add_argument("--cleanup", type=int, help="Clean up logs older than N days")
    
    args = parser.parse_args()
    
    if args.stats:
        stats = system_logger.get_log_stats()
        print(json.dumps(stats, indent=2))
    
    elif args.search:
        results = system_logger.search_logs(args.search, level=args.level)
        print(f"Found {len(results)} matching log entries:")
        for entry in results[-10:]:  # Show last 10 results
            print(f"{entry['timestamp']} [{entry['level']}] {entry['module']}: {entry['message']}")
    
    elif args.cleanup:
        cleaned = system_logger.cleanup_old_logs(args.cleanup)
        print(f"Cleaned up {cleaned} old log files")
    
    else:
        print("Use --help to see available options")
