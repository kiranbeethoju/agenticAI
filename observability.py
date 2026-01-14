"""
Observability Module
Provides logging, tracing, and metrics capabilities
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import os


class Observer:
    """Unified observability class for logging, tracing, and metrics"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.traces = []
        self.metrics = {}
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config.get("logging", {})
        
        if not log_config.get("enabled", True):
            self.logger = None
            return
        
        # Create logs directory
        log_file = log_config.get("file", "logs/agent.log")
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger("AgentObserver")
        self.logger.setLevel(getattr(logging, log_config.get("level", "INFO")))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        
        # Console handler
        console_handler = logging.StreamHandler()
        
        # Format
        if log_config.get("format") == "detailed":
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:
            formatter = logging.Formatter('%(levelname)s: %(message)s')
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log(self, level: str, message: str):
        """Log a message"""
        if self.logger:
            log_method = getattr(self.logger, level.lower(), self.logger.info)
            log_method(message)
    
    def trace_call(self, component: str, input_data: Any):
        """Trace an API call"""
        if not self.config.get("tracing", {}).get("trace_calls", False):
            return
        
        trace = {
            "timestamp": datetime.now().isoformat(),
            "type": "call",
            "component": component,
            "input": str(input_data)[:200]  # Truncate long inputs
        }
        
        self.traces.append(trace)
        self.log("DEBUG", f"TRACE CALL [{component}]: {trace['input']}")
    
    def trace_response(self, component: str, output_data: Dict[str, Any]):
        """Trace an API response"""
        if not self.config.get("tracing", {}).get("trace_responses", False):
            return
        
        trace = {
            "timestamp": datetime.now().isoformat(),
            "type": "response",
            "component": component,
            "output": {
                "latency": output_data.get("latency"),
                "tokens": output_data.get("tokens", 0),
                "error": output_data.get("error"),
                "text_preview": str(output_data.get("text", ""))[:100]
            }
        }
        
        self.traces.append(trace)
        self.log("DEBUG", f"TRACE RESPONSE [{component}]: Latency={trace['output']['latency']:.3f}s")
    
    def record_metric(self, metric_name: str, value: Any):
        """Record a metric"""
        if not self.config.get("metrics", {}).get("enabled", False):
            return
        
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        
        self.metrics[metric_name].append({
            "timestamp": datetime.now().isoformat(),
            "value": value
        })
    
    def get_traces(self) -> list:
        """Get all traces"""
        return self.traces
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        return self.metrics
    
    def export_observability_data(self, filepath: str = "logs/observability.json"):
        """Export all observability data to a file"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "traces": self.traces,
            "metrics": self.metrics
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.log("INFO", f"Observability data exported to {filepath}")
    
    def print_summary(self):
        """Print a summary of observability data"""
        print("\n" + "="*60)
        print("OBSERVABILITY SUMMARY")
        print("="*60)
        
        print(f"\nTotal Traces: {len(self.traces)}")
        print(f"Total Metric Types: {len(self.metrics)}")
        
        if self.traces:
            print("\nRecent Traces:")
            for trace in self.traces[-5:]:
                print(f"  - [{trace['type'].upper()}] {trace['component']} at {trace['timestamp']}")
        
        if self.metrics:
            print("\nMetrics Summary:")
            for metric_name, values in self.metrics.items():
                print(f"  - {metric_name}: {len(values)} entries")
        
        print("="*60 + "\n")
