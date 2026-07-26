import math
from typing import Dict, List, Any
from shared.logger import get_logger

log = get_logger("shared.telemetry")

class TelemetryStore:
    """
    Centralized, in-memory telemetry store.
    Tracks global API hits, error counts, and recent backend latencies.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TelemetryStore, cls).__new__(cls)
            cls._instance._init_store()
        return cls._instance
        
    def _init_store(self):
        self.api_hits = 0
        self.error_count = 0
        self.latencies: List[int] = []
        self.max_latency_history = 1000 # Prevent memory bloat
        
    def record_hit(self):
        self.api_hits += 1
        
    def record_error(self):
        self.error_count += 1
        
    def record_latency(self, latency_ms: int):
        self.latencies.append(latency_ms)
        if len(self.latencies) > self.max_latency_history:
            self.latencies.pop(0)
            
    def _calculate_percentile(self, sorted_data: List[int], percentile: int) -> int:
        if not sorted_data:
            return 0
        index = math.ceil((percentile / 100.0) * len(sorted_data)) - 1
        return sorted_data[index]

    def get_metrics(self) -> Dict[str, Any]:
        """
        Calculates and returns standard telemetry metrics.
        Offloads the heavy sorting/math from the frontend UI thread.
        """
        avg = 0
        p50 = 0
        p95 = 0
        current_e2e = 0
        
        if self.latencies:
            current_e2e = self.latencies[-1]
            avg = sum(self.latencies) // len(self.latencies)
            sorted_latencies = sorted(self.latencies)
            p50 = self._calculate_percentile(sorted_latencies, 50)
            p95 = self._calculate_percentile(sorted_latencies, 95)
            
        error_rate = 0.0
        if self.api_hits > 0:
            error_rate = round((self.error_count / self.api_hits) * 100, 2)
            
        return {
            "api_hits": self.api_hits,
            "error_rate_percent": error_rate,
            "current_e2e_ms": current_e2e,
            "avg_e2e_ms": avg,
            "p50_ms": p50,
            "p95_ms": p95
        }

# Singleton instance
store = TelemetryStore()
