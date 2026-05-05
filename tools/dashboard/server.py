"""
FastAPI Dashboard Server for BBB (Bio Body Band)
Real-time EMG monitoring with WebSocket broadcasting and UDP reverse transmission
"""

import asyncio
import json
import socket
import logging
from datetime import datetime
from collections import deque
from typing import Dict, List

import numpy as np
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from scipy import signal
import uvicorn

# Configuration
UDP_PORT = 5005
WS_BROADCAST_INTERVAL = 0.1  # 100ms
EMG_SAMPLE_BUFFER_SIZE = 100
FATIGUE_THRESHOLD_WARNING = 80.0
FATIGUE_THRESHOLD_CRITICAL = 95.0

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
app = FastAPI(title="BBB Dashboard Server")
active_connections: List[WebSocket] = []
emg_buffer = deque(maxlen=EMG_SAMPLE_BUFFER_SIZE)
current_status = {
    "timestamp": 0,
    "fatigue_pct": 0.0,
    "median_freq": 0.0,
    "level": "normal",
    "emg_raw": [],
}
esp32_address = None


class FatigueAnalyzer:
    """EMG signal processing and fatigue estimation"""

    def __init__(self, sample_rate: int = 1000):
        self.sample_rate = sample_rate
        self.baseline_mf = None

    def process_emg_chunk(self, emg_data: List[float]) -> Dict:
        """
        Process EMG chunk and calculate fatigue metrics

        Args:
            emg_data: Raw EMG samples

        Returns:
            {
                "median_freq": float,
                "fatigue_pct": float,
                "level": str,  # "normal" | "warning" | "critical"
            }
        """
        if len(emg_data) < 128:
            return {
                "median_freq": 0.0,
                "fatigue_pct": 0.0,
                "level": "normal",
            }

        # Band-pass filter 20~450 Hz (must be < Nyquist 500Hz)
        sos = signal.butter(4, [20, 450], btype="band", fs=self.sample_rate, output="sos")
        filtered = signal.sosfilt(sos, emg_data)

        # FFT and Median Frequency calculation
        freqs, pxx = signal.periodogram(filtered, fs=self.sample_rate)
        # Filter to useful band
        mask = (freqs > 20) & (freqs < 450)
        freqs = freqs[mask]
        pxx = pxx[mask]

        # Median Frequency (50% spectral power)
        cumsum_pxx = np.cumsum(pxx)
        median_idx = np.argmin(np.abs(cumsum_pxx - cumsum_pxx[-1] / 2))
        median_freq = freqs[median_idx] if len(freqs) > 0 else 0.0

        # Initialize baseline on first run
        if self.baseline_mf is None:
            self.baseline_mf = median_freq if median_freq > 0 else 100.0

        # Fatigue calculation: percentage of baseline MF
        fatigue_pct = (self.baseline_mf - median_freq) / self.baseline_mf * 100.0
        fatigue_pct = max(0.0, min(100.0, fatigue_pct))  # Clamp 0~100

        # Level determination
        if fatigue_pct >= FATIGUE_THRESHOLD_CRITICAL:
            level = "critical"
        elif fatigue_pct >= FATIGUE_THRESHOLD_WARNING:
            level = "warning"
        else:
            level = "normal"

        return {
            "median_freq": round(median_freq, 2),
            "fatigue_pct": round(fatigue_pct, 1),
            "level": level,
        }


analyzer = FatigueAnalyzer(sample_rate=1000)


async def udp_receiver():
    """Listen for UDP packets from ESP32"""
    global esp32_address, current_status

    loop = asyncio.get_event_loop()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", UDP_PORT))
    sock.setblocking(False)

    logger.info(f"UDP receiver listening on port {UDP_PORT}")

    while True:
        try:
            try:
                data, addr = sock.recvfrom(4096)
            except (BlockingIOError, OSError):
                await asyncio.sleep(0.01)
                continue

            esp32_address = addr
            try:
                packet = json.loads(data.decode())
                emg_samples = packet.get("emg", [])
                if emg_samples:
                    emg_buffer.extend(emg_samples)

                    # Process if buffer has enough samples (100ms of 1kHz data = 100 samples)
                    if len(emg_buffer) >= 100:
                        result = analyzer.process_emg_chunk(list(emg_buffer)[-100:])
                        current_status.update(
                            {
                                "timestamp": datetime.now().timestamp(),
                                "fatigue_pct": result["fatigue_pct"],
                                "median_freq": result["median_freq"],
                                "level": result["level"],
                                "emg_raw": list(emg_buffer)[-100:],
                            }
                        )
                        logger.info(
                            f"EMG: {result['fatigue_pct']:.1f}% ({result['level'].upper()})"
                        )
            except json.JSONDecodeError:
                logger.warning("Invalid JSON from ESP32")

        except Exception as e:
            logger.error(f"UDP receiver error: {e}")

        await asyncio.sleep(0.001)


async def websocket_broadcaster():
    """Broadcast current status to all connected clients"""
    while True:
        if active_connections:
            message = {
                "timestamp": current_status["timestamp"],
                "fatigue_pct": current_status["fatigue_pct"],
                "median_freq": current_status["median_freq"],
                "level": current_status["level"],
                "emg_raw": current_status["emg_raw"],
            }
            for connection in active_connections[:]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"WebSocket send error: {e}")
                    active_connections.remove(connection)

        await asyncio.sleep(WS_BROADCAST_INTERVAL)


async def esp32_feedback_sender():
    """Send analysis results back to ESP32 via UDP"""
    while True:
        if esp32_address:
            try:
                payload = {
                    "fatigue_pct": current_status["fatigue_pct"],
                    "mf": current_status["median_freq"],
                    "level": current_status["level"],
                }
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(
                    json.dumps(payload).encode(),
                    (esp32_address[0], UDP_PORT),
                )
                sock.close()
            except Exception as e:
                logger.error(f"ESP32 feedback error: {e}")

        await asyncio.sleep(0.1)


@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(udp_receiver())
    asyncio.create_task(websocket_broadcaster())
    asyncio.create_task(esp32_feedback_sender())
    logger.info("Background tasks started")


@app.get("/")
async def get_dashboard():
    """Serve dashboard HTML"""
    return FileResponse("tools/dashboard/static/index.html", media_type="text/html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)
    logger.info("WebSocket client connected")

    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        active_connections.remove(websocket)
        logger.info("WebSocket client disconnected")


@app.get("/api/status")
async def get_status():
    """Get current status (HTTP fallback)"""
    return {
        "timestamp": current_status["timestamp"],
        "fatigue_pct": current_status["fatigue_pct"],
        "median_freq": current_status["median_freq"],
        "level": current_status["level"],
    }


# Mount static files
app.mount("/static", StaticFiles(directory="tools/dashboard/static"), name="static")


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
