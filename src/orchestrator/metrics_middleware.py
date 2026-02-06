import time
from starlette.middleware.base import BaseHTTPMiddleware
from metrics import MetricsCollector

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        metrics = MetricsCollector.get_instance()

        start_time = time.time()

        try:
            response = await call_next(request)
            status = response.status_code
        except Exception:
            metrics.record_request(time.time() - start_time, 500)
            raise

        duration = time.time() - start_time
        metrics.record_request(duration, status)

        return response
