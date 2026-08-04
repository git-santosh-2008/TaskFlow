"""
Custom Middleware
====================
Logs method, path, processing time and status code for every request.
"""

import time
import logging
from fastapi import Request


logger = logging.getLogger("api_logger")


async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time_ms = (time.time() - start_time) * 1000


    logger.info(
        f"Method: {request.method} | Path: {request.url.path} | "
        f"Processing Time: {process_time_ms:.2f}ms | Status Code: {response.status_code}"
    )
    return response

