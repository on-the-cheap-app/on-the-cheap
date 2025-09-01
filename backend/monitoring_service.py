"""
Advanced Monitoring and Analytics Service

This service provides:
- Real-time performance monitoring
- API usage analytics
- Error tracking and alerting
- Resource utilization monitoring
- Business metrics tracking
"""

import asyncio
import logging
import psutil
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import os

logger = logging.getLogger(__name__)

@dataclass
class APIMetric:
    endpoint: str
    method: str
    status_code: int
    response_time: float
    timestamp: datetime
    user_type: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class SystemMetric:
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    timestamp: datetime

@dataclass
class BusinessMetric:
    metric_name: str
    value: float
    timestamp: datetime
    metadata: Dict[str, Any]

class MonitoringService:
    """Advanced monitoring service for production applications"""
    
    def __init__(self):
        self.api_metrics = deque(maxlen=10000)  # Keep last 10k API calls
        self.system_metrics = deque(maxlen=1440)  # Keep 24 hours of system metrics (1 per minute)
        self.business_metrics = defaultdict(lambda: deque(maxlen=1000))
        self.error_counts = defaultdict(int)
        self.alert_thresholds = {
            "error_rate": 5.0,  # 5% error rate
            "avg_response_time": 2000,  # 2 seconds
            "cpu_usage": 80.0,  # 80% CPU
            "memory_usage": 85.0,  # 85% memory
            "disk_usage": 90.0,  # 90% disk
        }
        self.alerts_sent = set()  # Track sent alerts to avoid spam
        self.monitoring_enabled = True
        
        # Start background monitoring tasks
        asyncio.create_task(self._system_monitoring_loop())
        asyncio.create_task(self._alert_monitoring_loop())

    async def record_api_call(self, 
                             endpoint: str, 
                             method: str, 
                             status_code: int, 
                             response_time: float,
                             user_type: Optional[str] = None,
                             error_message: Optional[str] = None):
        """Record API call metrics"""
        if not self.monitoring_enabled:
            return
            
        metric = APIMetric(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time=response_time,
            timestamp=datetime.now(timezone.utc),
            user_type=user_type,
            error_message=error_message
        )
        
        self.api_metrics.append(metric)
        
        # Track error counts
        if status_code >= 400:
            error_key = f"{endpoint}:{status_code}"
            self.error_counts[error_key] += 1

    async def record_business_metric(self, metric_name: str, value: float, metadata: Dict[str, Any] = None):
        """Record business metrics"""
        if not self.monitoring_enabled:
            return
            
        metric = BusinessMetric(
            metric_name=metric_name,
            value=value,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata or {}
        )
        
        self.business_metrics[metric_name].append(metric)

    async def _system_monitoring_loop(self):
        """Background task to collect system metrics"""
        while self.monitoring_enabled:
            try:
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                network = psutil.net_io_counters()
                
                metric = SystemMetric(
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    disk_percent=disk.percent,
                    network_io={
                        "bytes_sent": network.bytes_sent,
                        "bytes_recv": network.bytes_recv,
                        "packets_sent": network.packets_sent,
                        "packets_recv": network.packets_recv
                    },
                    timestamp=datetime.now(timezone.utc)
                )
                
                self.system_metrics.append(metric)
                
                # Sleep for 60 seconds
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                await asyncio.sleep(60)

    async def _alert_monitoring_loop(self):
        """Background task to check for alerts"""
        while self.monitoring_enabled:
            try:
                await self._check_alerts()
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Alert monitoring error: {e}")
                await asyncio.sleep(300)

    async def _check_alerts(self):
        """Check for alert conditions and send alerts"""
        alerts = []
        
        # Check API error rate
        if len(self.api_metrics) > 100:
            recent_calls = [m for m in self.api_metrics if 
                          m.timestamp > datetime.now(timezone.utc) - timedelta(minutes=5)]
            if recent_calls:
                error_rate = len([m for m in recent_calls if m.status_code >= 400]) / len(recent_calls) * 100
                if error_rate > self.alert_thresholds["error_rate"]:
                    alert_key = f"error_rate:{int(error_rate)}"
                    if alert_key not in self.alerts_sent:
                        alerts.append(f"High error rate: {error_rate:.1f}% in last 5 minutes")
                        self.alerts_sent.add(alert_key)

        # Check average response time
        if len(self.api_metrics) > 50:
            recent_calls = [m for m in self.api_metrics if 
                          m.timestamp > datetime.now(timezone.utc) - timedelta(minutes=5)]
            if recent_calls:
                avg_response_time = sum(m.response_time for m in recent_calls) / len(recent_calls)
                if avg_response_time > self.alert_thresholds["avg_response_time"]:
                    alert_key = f"response_time:{int(avg_response_time)}"
                    if alert_key not in self.alerts_sent:
                        alerts.append(f"High response time: {avg_response_time:.0f}ms average in last 5 minutes")
                        self.alerts_sent.add(alert_key)

        # Check system metrics
        if self.system_metrics:
            latest_system = self.system_metrics[-1]
            
            if latest_system.cpu_percent > self.alert_thresholds["cpu_usage"]:
                alert_key = f"cpu:{int(latest_system.cpu_percent)}"
                if alert_key not in self.alerts_sent:
                    alerts.append(f"High CPU usage: {latest_system.cpu_percent:.1f}%")
                    self.alerts_sent.add(alert_key)
            
            if latest_system.memory_percent > self.alert_thresholds["memory_usage"]:
                alert_key = f"memory:{int(latest_system.memory_percent)}"
                if alert_key not in self.alerts_sent:
                    alerts.append(f"High memory usage: {latest_system.memory_percent:.1f}%")
                    self.alerts_sent.add(alert_key)
            
            if latest_system.disk_percent > self.alert_thresholds["disk_usage"]:
                alert_key = f"disk:{int(latest_system.disk_percent)}"
                if alert_key not in self.alerts_sent:
                    alerts.append(f"High disk usage: {latest_system.disk_percent:.1f}%")
                    self.alerts_sent.add(alert_key)

        # Send alerts (in production, you would send to external alerting system)
        for alert in alerts:
            logger.warning(f"ALERT: {alert}")
            # TODO: Send to external alerting system (Slack, email, PagerDuty, etc.)

        # Clean up old alert keys (every hour)
        if len(self.alerts_sent) > 1000:
            self.alerts_sent.clear()

    async def get_api_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get API analytics for the specified time period"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_metrics = [m for m in self.api_metrics if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {"message": "No API calls in specified time period", "total_calls": 0}
        
        # Calculate statistics
        total_calls = len(recent_metrics)
        error_calls = len([m for m in recent_metrics if m.status_code >= 400])
        error_rate = (error_calls / total_calls * 100) if total_calls > 0 else 0
        
        avg_response_time = sum(m.response_time for m in recent_metrics) / total_calls
        
        # Endpoint statistics
        endpoint_stats = defaultdict(lambda: {"count": 0, "errors": 0, "total_time": 0})
        for metric in recent_metrics:
            key = f"{metric.method} {metric.endpoint}"
            endpoint_stats[key]["count"] += 1
            endpoint_stats[key]["total_time"] += metric.response_time
            if metric.status_code >= 400:
                endpoint_stats[key]["errors"] += 1
        
        # Convert to final format
        endpoint_analytics = []
        for endpoint, stats in endpoint_stats.items():
            endpoint_analytics.append({
                "endpoint": endpoint,
                "total_calls": stats["count"],
                "error_count": stats["errors"],
                "error_rate": (stats["errors"] / stats["count"] * 100) if stats["count"] > 0 else 0,
                "avg_response_time": stats["total_time"] / stats["count"]
            })
        
        # Sort by call count
        endpoint_analytics.sort(key=lambda x: x["total_calls"], reverse=True)
        
        # Status code distribution
        status_codes = defaultdict(int)
        for metric in recent_metrics:
            status_codes[metric.status_code] += 1
        
        # User type statistics
        user_types = defaultdict(int)
        for metric in recent_metrics:
            user_type = metric.user_type or "anonymous"
            user_types[user_type] += 1
        
        return {
            "time_period_hours": hours,
            "total_calls": total_calls,
            "error_calls": error_calls,
            "error_rate": round(error_rate, 2),
            "avg_response_time": round(avg_response_time, 2),
            "endpoints": endpoint_analytics[:20],  # Top 20 endpoints
            "status_codes": dict(status_codes),
            "user_types": dict(user_types),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def get_system_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get system analytics for the specified time period"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_metrics = [m for m in self.system_metrics if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {"message": "No system metrics in specified time period"}
        
        # Calculate averages and peaks
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        disk_values = [m.disk_percent for m in recent_metrics]
        
        return {
            "time_period_hours": hours,
            "data_points": len(recent_metrics),
            "cpu": {
                "current": cpu_values[-1] if cpu_values else 0,
                "average": round(sum(cpu_values) / len(cpu_values), 2),
                "peak": max(cpu_values),
                "minimum": min(cpu_values)
            },
            "memory": {
                "current": memory_values[-1] if memory_values else 0,
                "average": round(sum(memory_values) / len(memory_values), 2),
                "peak": max(memory_values),
                "minimum": min(memory_values)
            },
            "disk": {
                "current": disk_values[-1] if disk_values else 0,
                "average": round(sum(disk_values) / len(disk_values), 2),
                "peak": max(disk_values),
                "minimum": min(disk_values)
            },
            "network": {
                "latest": recent_metrics[-1].network_io if recent_metrics else {}
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def get_business_analytics(self, metric_name: Optional[str] = None, hours: int = 24) -> Dict[str, Any]:
        """Get business analytics"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        if metric_name:
            metrics = [m for m in self.business_metrics[metric_name] if m.timestamp > cutoff_time]
            if not metrics:
                return {"message": f"No data for metric '{metric_name}' in specified time period"}
            
            values = [m.value for m in metrics]
            return {
                "metric_name": metric_name,
                "time_period_hours": hours,
                "data_points": len(metrics),
                "current": values[-1] if values else 0,
                "average": round(sum(values) / len(values), 2),
                "peak": max(values),
                "minimum": min(values),
                "total": sum(values),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            # Return summary of all metrics
            summary = {}
            for name, metric_list in self.business_metrics.items():
                recent_metrics = [m for m in metric_list if m.timestamp > cutoff_time]
                if recent_metrics:
                    values = [m.value for m in recent_metrics]
                    summary[name] = {
                        "data_points": len(recent_metrics),
                        "current": values[-1],
                        "average": round(sum(values) / len(values), 2),
                        "total": sum(values)
                    }
            
            return {
                "time_period_hours": hours,
                "metrics": summary,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def get_error_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get error analytics"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_errors = [m for m in self.api_metrics if 
                        m.timestamp > cutoff_time and m.status_code >= 400]
        
        if not recent_errors:
            return {"message": "No errors in specified time period", "total_errors": 0}
        
        # Group by endpoint and status code
        error_groups = defaultdict(lambda: {"count": 0, "messages": []})
        for error in recent_errors:
            key = f"{error.endpoint} ({error.status_code})"
            error_groups[key]["count"] += 1
            if error.error_message and len(error_groups[key]["messages"]) < 5:
                error_groups[key]["messages"].append(error.error_message)
        
        # Sort by error count
        sorted_errors = sorted(
            [(k, v) for k, v in error_groups.items()], 
            key=lambda x: x[1]["count"], 
            reverse=True
        )[:20]  # Top 20 error types
        
        return {
            "time_period_hours": hours,
            "total_errors": len(recent_errors),
            "unique_error_types": len(error_groups),
            "top_errors": [
                {
                    "error_type": error_type,
                    "count": stats["count"],
                    "sample_messages": stats["messages"][:3]  # Show max 3 sample messages
                }
                for error_type, stats in sorted_errors
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def stop_monitoring(self):
        """Stop monitoring service"""
        self.monitoring_enabled = False
        logger.info("Monitoring service stopped")

# Global monitoring service instance
_monitoring_service: Optional[MonitoringService] = None

def get_monitoring_service() -> MonitoringService:
    """Get or create global monitoring service instance"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service

def initialize_monitoring_service() -> MonitoringService:
    """Initialize monitoring service on startup"""
    monitoring_service = get_monitoring_service()
    logger.info("Advanced monitoring service initialized")
    return monitoring_service