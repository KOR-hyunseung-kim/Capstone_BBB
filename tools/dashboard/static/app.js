/**
 * BBB Dashboard Client
 * Real-time EMG monitoring with WebSocket connection
 */

class BBBDashboard {
    constructor() {
        this.ws = null;
        this.emgChart = null;
        this.fatigueChart = null;
        this.fatigueHistory = [];
        this.maxHistoryLength = 60; // 6 seconds at 100ms interval
        this.lastAlertLevel = null;
        this.maxLogEntries = 20;

        this.initializeCharts();
        this.connectWebSocket();
        this.requestNotificationPermission();
    }

    connectWebSocket() {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log("WebSocket connected");
            this.updateConnectionStatus(true);
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.updateDashboard(data);
            } catch (e) {
                console.error("Failed to parse message:", e);
            }
        };

        this.ws.onerror = (error) => {
            console.error("WebSocket error:", error);
            this.updateConnectionStatus(false);
        };

        this.ws.onclose = () => {
            console.log("WebSocket closed. Reconnecting...");
            this.updateConnectionStatus(false);
            setTimeout(() => this.connectWebSocket(), 2000);
        };
    }

    initializeCharts() {
        // EMG Waveform Chart
        const emgCtx = document.getElementById("emg-chart").getContext("2d");
        this.emgChart = new Chart(emgCtx, {
            type: "line",
            data: {
                labels: [],
                datasets: [
                    {
                        label: "근전도 신호 (EMG)",
                        data: [],
                        borderColor: "#004fa8",
                        backgroundColor: "rgba(0, 79, 168, 0.1)",
                        borderWidth: 2,
                        tension: 0.1,
                        fill: true,
                        pointRadius: 0,
                        pointHoverRadius: 0,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        min: 0,
                        max: 1000,
                        ticks: { color: "#374151" },
                        grid: { color: "rgba(0, 0, 0, 0.05)" },
                    },
                    x: {
                        ticks: { color: "#374151" },
                        grid: { display: false },
                    },
                },
            },
        });

        // Fatigue Trend Chart
        const fatigueCtx = document.getElementById("fatigue-chart").getContext("2d");
        this.fatigueChart = new Chart(fatigueCtx, {
            type: "line",
            data: {
                labels: [],
                datasets: [
                    {
                        label: "피로도 (%)",
                        data: [],
                        borderColor: "#dc2626",
                        backgroundColor: "rgba(220, 38, 38, 0.1)",
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true,
                        pointRadius: 0,
                        pointHoverRadius: 6,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        min: 0,
                        max: 100,
                        ticks: {
                            color: "#374151",
                            callback: (value) => value + "%",
                        },
                        grid: { color: "rgba(0, 0, 0, 0.05)" },
                    },
                    x: {
                        ticks: { color: "#374151" },
                        grid: { display: false },
                    },
                },
            },
        });
    }

    updateDashboard(data) {
        const mode = data.mode || "unknown";

        // Update mode badge
        this.updateModeBadge(mode);

        if (mode === "safety") {
            // Safety Mode Data Processing
            this.updateSafetyMode(data);
            document.getElementById("safety-mode-section").style.display = "block";
            document.getElementById("control-mode-section").style.display = "none";
        } else if (mode === "control") {
            // Control Mode Data Processing
            this.updateControlMode(data);
            document.getElementById("safety-mode-section").style.display = "none";
            document.getElementById("control-mode-section").style.display = "block";
        }
    }

    updateModeBadge(mode) {
        const badge = document.getElementById("mode-badge");
        const modeLabels = {
            safety: "🔴 안전 모드 (Safety Mode)",
            control: "🎮 제어 모드 (Control Mode)",
            unknown: "⏳ 대기 중"
        };
        badge.textContent = modeLabels[mode] || "대기 중";
    }

    updateSafetyMode(data) {
        const {
            fatigue_pct = 0,
            median_freq = 0,
            level = "normal",
            emg_raw = [],
        } = data;

        // Update gauge
        this.updateGauge(fatigue_pct, level);

        // Update info display
        this.updateInfoDisplay(fatigue_pct, median_freq, level);

        // Update EMG waveform chart
        if (emg_raw.length > 0) {
            this.updateEMGChart(emg_raw);
        }

        // Update fatigue trend
        this.updateFatigueTrend(fatigue_pct);

        // Check for alert level change
        this.checkAlertLevelChange(level, fatigue_pct);
    }

    updateControlMode(data) {
        const {
            pitch = 0,
            roll = 0,
            cursor_x = 512,
            cursor_y = 512,
            click_detected = false,
        } = data;

        // Update IMU values
        document.getElementById("pitch-value").textContent = pitch.toFixed(1) + "°";
        document.getElementById("roll-value").textContent = roll.toFixed(1) + "°";

        // Update cursor position
        document.getElementById("cursor-x-value").textContent = Math.round(cursor_x);
        document.getElementById("cursor-y-value").textContent = Math.round(cursor_y);

        // Update cursor dot position in scope
        const cursorDot = document.getElementById("cursor-dot");
        const scopeX = ((cursor_x - 512) / 512) * 100;
        const scopeY = ((512 - cursor_y) / 512) * 100;

        cursorDot.style.left = `calc(50% + ${scopeX}%)`;
        cursorDot.style.top = `calc(50% - ${scopeY}%)`;

        // Update click status
        const clickStatus = document.getElementById("click-status");
        if (click_detected) {
            clickStatus.textContent = "🖱️ CLICK 감지!";
            cursorDot.classList.add("clicked");
            clickStatus.classList.add("active");
        } else {
            clickStatus.textContent = "✋ 준비 중";
            cursorDot.classList.remove("clicked");
            clickStatus.classList.remove("active");
        }
    }

    updateGauge(fatigue_pct, level) {
        // Calculate arc dash offset (0~251 for SVG arc)
        const maxDashoffset = 251;
        const dashoffset = maxDashoffset * (1 - fatigue_pct / 100);

        const arc = document.getElementById("gauge-arc");
        arc.style.strokeDashoffset = dashoffset;

        // Update percentage text
        document.getElementById("fatigue-value").textContent =
            fatigue_pct.toFixed(1) + "%";

        // Update gauge class for color change
        const svg = document.querySelector(".gauge");
        svg.classList.remove("warning", "critical");
        if (level === "critical") {
            svg.classList.add("critical");
        } else if (level === "warning") {
            svg.classList.add("warning");
        }
    }

    updateInfoDisplay(fatigue_pct, median_freq, level) {
        document.getElementById("mf-value").textContent =
            median_freq.toFixed(2) + " Hz";

        const statusText = document.getElementById("status-text");
        const statusLabels = {
            normal: "✅ 정상",
            warning: "⚠️ 주의",
            critical: "🚨 위험",
        };
        statusText.textContent = statusLabels[level] || "알 수 없음";
        statusText.className = `metric-status ${level}`;

        // Update alert level display
        const alertLevel = document.getElementById("alert-level");
        const levelLabels = {
            normal: "정상",
            warning: "주의",
            critical: "위험",
        };
        alertLevel.textContent = levelLabels[level] || "대기 중";
        alertLevel.className = `alert-level ${level}`;

        // Set background color
        if (level === "normal") {
            alertLevel.style.background = "#d1fae5";
            alertLevel.style.color = "#065f46";
        } else if (level === "warning") {
            alertLevel.style.background = "#fef3c7";
            alertLevel.style.color = "#92400e";
        } else if (level === "critical") {
            alertLevel.style.background = "#fee2e2";
            alertLevel.style.color = "#991b1b";
        }
    }

    updateEMGChart(emg_raw) {
        const maxPoints = 100;
        const labels = Array.from({ length: emg_raw.length }, (_, i) =>
            ((i - emg_raw.length) * 1).toString()
        );

        this.emgChart.data.labels = labels;
        this.emgChart.data.datasets[0].data = emg_raw.slice(-maxPoints);
        this.emgChart.update("none"); // No animation for performance
    }

    updateFatigueTrend(fatigue_pct) {
        this.fatigueHistory.push(fatigue_pct);
        if (this.fatigueHistory.length > this.maxHistoryLength) {
            this.fatigueHistory.shift();
        }

        const labels = Array.from({ length: this.fatigueHistory.length }, (_, i) =>
            ((i - this.fatigueHistory.length) * 0.1).toFixed(1)
        );

        this.fatigueChart.data.labels = labels;
        this.fatigueChart.data.datasets[0].data = this.fatigueHistory;
        this.fatigueChart.update("none");
    }

    checkAlertLevelChange(level, fatigue_pct) {
        if (level !== this.lastAlertLevel) {
            this.lastAlertLevel = level;
            this.addAlertLog(level, fatigue_pct);

            if (level === "warning") {
                this.sendNotification(
                    "⚠️ 1차 경고: 피로도 80% 도달",
                    `작업자 피로도 ${fatigue_pct.toFixed(1)}%에 도달했습니다`
                );
            } else if (level === "critical") {
                this.sendNotification(
                    "🚨 긴급 경고: 즉시 휴식 필요",
                    `작업자 피로도 ${fatigue_pct.toFixed(1)}%입니다 - 즉시 휴식을 권장합니다`
                );
            }
        }
    }

    addAlertLog(level, fatigue_pct) {
        const logContainer = document.getElementById("alert-log");
        const now = new Date();
        const timeStr = now.toLocaleTimeString("ko-KR", { hour12: false });

        const logMessages = {
            normal: "피로도 정상 범위로 복귀",
            warning: "피로도 80% 도달 - 1차 경고",
            critical: "피로도 95% 초과 - 긴급 경고",
        };

        const entry = document.createElement("div");
        entry.className = `alert-entry ${level}`;
        entry.innerHTML = `
            <div class="alert-time">${timeStr}</div>
            <div class="alert-content">
                <div class="alert-message">${logMessages[level]}</div>
                <div class="alert-details">피로도: ${fatigue_pct.toFixed(1)}%</div>
            </div>
        `;

        logContainer.insertBefore(entry, logContainer.firstChild);

        // Keep only maxLogEntries
        while (logContainer.children.length > this.maxLogEntries) {
            logContainer.removeChild(logContainer.lastChild);
        }
    }

    sendNotification(title, body) {
        if ("Notification" in window && Notification.permission === "granted") {
            new Notification(title, {
                body,
                icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='45' fill='%23003d7a'/><text x='50' y='60' font-size='60' text-anchor='middle' fill='white' font-weight='bold'>B</text></svg>",
                badge:
                    "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='45' fill='%23003d7a'/></svg>",
                tag: "bbb-alert",
                requireInteraction: true,
            });
        }
    }

    requestNotificationPermission() {
        if ("Notification" in window && Notification.permission === "default") {
            Notification.requestPermission().then((permission) => {
                if (permission === "granted") {
                    console.log("알림 권한이 허용되었습니다");
                }
            });
        }
    }

    updateConnectionStatus(connected) {
        const indicator = document.getElementById("connection-status");
        if (connected) {
            indicator.textContent = "온라인";
            indicator.className = "status-indicator online";
        } else {
            indicator.textContent = "오프라인";
            indicator.className = "status-indicator offline";
        }
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
    new BBBDashboard();
});
