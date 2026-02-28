(function () {
    "use strict";

    var POLL_INTERVAL = 30000;
    var pollTimer = null;

    // -- API helpers --

    function fetchJSON(url, opts) {
        return fetch(url, opts).then(function (r) { return r.json(); });
    }

    function updateStatus() {
        fetchJSON("/api/status").then(function (data) {
            // Heating
            var el = document.getElementById("heating-status");
            if (data.heating) {
                var on = data.heating.on;
                el.className = "status-indicator " + (on ? "status-on" : "status-off");
                el.querySelector(".label").textContent = on ? "PÅ" : "AV";
            }

            // Weather
            if (data.weather) {
                var w = data.weather;
                setText("w-temp", fmt(w.air_temperature, "\u00b0C"));
                setText("w-precip", fmt(w.precipitation_amount, " mm"));
                setText("w-humidity", fmt(w.relative_humidity, "%"));
                setText("w-wind", fmt(w.wind_speed, " m/s"));
            }

            // Sensors
            if (data.sensors) {
                renderSensors(data.sensors);
            }

            document.getElementById("last-update").textContent =
                "Oppdatert " + new Date().toLocaleTimeString("nb-NO");
        }).catch(function () {
            document.getElementById("last-update").textContent = "Feil ved oppdatering";
        });
    }

    function updateForecast() {
        fetchJSON("/api/weather").then(function (data) {
            if (data.forecast) {
                drawChart(data.forecast);
            }
        }).catch(function () { /* ignore */ });
    }

    function updateLog() {
        fetchJSON("/api/log?limit=20").then(function (data) {
            if (data.events) {
                renderEvents(data.events);
            }
        }).catch(function () { /* ignore */ });
    }

    // -- Rendering --

    function setText(id, text) {
        document.getElementById(id).textContent = text;
    }

    function fmt(val, suffix) {
        if (val === null || val === undefined) return "--";
        return (typeof val === "number" ? val.toFixed(1) : val) + suffix;
    }

    var SENSOR_LABELS = {
        loop_inlet: "Sløyfe inn",
        loop_outlet: "Sløyfe ut",
        hp_inlet: "VP inn",
        hp_outlet: "VP ut",
        tank: "Tank"
    };

    function renderSensors(sensors) {
        var grid = document.getElementById("sensor-grid");
        var html = "";
        for (var key in sensors) {
            var label = SENSOR_LABELS[key] || key;
            var val = sensors[key];
            html += '<div class="stat">' +
                '<span class="stat-value">' + fmt(val, "\u00b0C") + '</span>' +
                '<span class="stat-label">' + label + '</span></div>';
        }
        grid.innerHTML = html || '<p class="meta">Ingen sensorer</p>';
    }

    function renderEvents(events) {
        var el = document.getElementById("event-log");
        if (!events.length) {
            el.innerHTML = '<p class="meta">Ingen hendelser</p>';
            return;
        }
        var html = "";
        for (var i = 0; i < events.length; i++) {
            var e = events[i];
            var ts = e.timestamp ? new Date(e.timestamp).toLocaleString("nb-NO") : "";
            html += '<div class="event-item">' +
                '<span class="event-type ' + e.event_type + '">' + e.event_type + '</span>' +
                '<span class="event-msg">' + (e.message || "") + '</span>' +
                '<span class="event-time">' + ts + '</span></div>';
        }
        el.innerHTML = html;
    }

    // -- Forecast chart --

    function drawChart(forecast) {
        var canvas = document.getElementById("forecast-chart");
        var ctx = canvas.getContext("2d");
        var dpr = window.devicePixelRatio || 1;

        canvas.width = canvas.clientWidth * dpr;
        canvas.height = canvas.clientHeight * dpr;
        ctx.scale(dpr, dpr);

        var w = canvas.clientWidth;
        var h = canvas.clientHeight;
        var pad = { top: 20, right: 10, bottom: 30, left: 40 };
        var cw = w - pad.left - pad.right;
        var ch = h - pad.top - pad.bottom;

        // Data
        var temps = [];
        var precips = [];
        var labels = [];
        for (var i = 0; i < forecast.length; i++) {
            var s = forecast[i];
            temps.push(s.air_temperature);
            precips.push(s.precipitation_amount || 0);
            labels.push(new Date(s.time).getHours() + ":00");
        }

        if (!temps.length) return;

        var tMin = Math.floor(Math.min.apply(null, temps) - 2);
        var tMax = Math.ceil(Math.max.apply(null, temps) + 2);
        var pMax = Math.max(Math.max.apply(null, precips), 1);

        ctx.clearRect(0, 0, w, h);

        // Ice zone background
        var style = getComputedStyle(document.documentElement);
        var iceTop = pad.top + ch * (1 - (5 - tMin) / (tMax - tMin));
        var iceBot = pad.top + ch * (1 - (-5 - tMin) / (tMax - tMin));
        iceTop = Math.max(pad.top, Math.min(pad.top + ch, iceTop));
        iceBot = Math.max(pad.top, Math.min(pad.top + ch, iceBot));
        ctx.fillStyle = "rgba(255, 82, 82, 0.08)";
        ctx.fillRect(pad.left, iceTop, cw, iceBot - iceTop);

        // Precip bars
        var barW = cw / temps.length * 0.6;
        ctx.fillStyle = "rgba(33, 150, 243, 0.4)";
        for (var i = 0; i < precips.length; i++) {
            var x = pad.left + (i + 0.5) * cw / temps.length;
            var bh = (precips[i] / pMax) * ch * 0.3;
            ctx.fillRect(x - barW / 2, pad.top + ch - bh, barW, bh);
        }

        // Temperature line
        ctx.beginPath();
        ctx.strokeStyle = "#ff9800";
        ctx.lineWidth = 2;
        for (var i = 0; i < temps.length; i++) {
            var x = pad.left + (i + 0.5) * cw / temps.length;
            var y = pad.top + ch * (1 - (temps[i] - tMin) / (tMax - tMin));
            if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        ctx.stroke();

        // Zero line
        if (tMin < 0 && tMax > 0) {
            var zeroY = pad.top + ch * (1 - (0 - tMin) / (tMax - tMin));
            ctx.beginPath();
            ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
            ctx.lineWidth = 1;
            ctx.setLineDash([4, 4]);
            ctx.moveTo(pad.left, zeroY);
            ctx.lineTo(pad.left + cw, zeroY);
            ctx.stroke();
            ctx.setLineDash([]);
        }

        // Axes labels
        ctx.fillStyle = "#8a8a9a";
        ctx.font = "11px sans-serif";
        ctx.textAlign = "right";
        var steps = 5;
        for (var i = 0; i <= steps; i++) {
            var v = tMin + (tMax - tMin) * (i / steps);
            var y = pad.top + ch * (1 - i / steps);
            ctx.fillText(v.toFixed(0) + "\u00b0", pad.left - 5, y + 4);
        }

        ctx.textAlign = "center";
        var labelStep = Math.max(1, Math.floor(temps.length / 8));
        for (var i = 0; i < labels.length; i += labelStep) {
            var x = pad.left + (i + 0.5) * cw / temps.length;
            ctx.fillText(labels[i], x, h - 5);
        }
    }

    // -- History chart (Chart.js) --

    var historyChart = null;
    var historyHours = 24;

    var SENSOR_COLORS = {
        loop_inlet:  "#42a5f5",
        loop_outlet: "#66bb6a",
        hp_inlet:    "#ef5350",
        hp_outlet:   "#ff9800",
        tank:        "#ab47bc"
    };

    function buildHeatingBands(periods, heatingOn, timeMin, timeMax) {
        var bands = [];
        if (!periods.length && !heatingOn) return bands;

        // Reconstruct on/off periods as annotation boxes
        var on = false;
        var start = null;

        for (var i = 0; i < periods.length; i++) {
            var p = periods[i];
            var isOn = p.event_type === "heating_on" || p.event_type === "manual_on";
            if (isOn && !on) {
                start = new Date(p.timestamp).getTime();
                on = true;
            } else if (!isOn && on) {
                bands.push({
                    type: "box",
                    xMin: start,
                    xMax: new Date(p.timestamp).getTime(),
                    backgroundColor: "rgba(0, 200, 83, 0.10)",
                    borderWidth: 0
                });
                on = false;
                start = null;
            }
        }
        // If still on at the end, extend to now
        if (on && start) {
            bands.push({
                type: "box",
                xMin: start,
                xMax: timeMax,
                backgroundColor: "rgba(0, 200, 83, 0.10)",
                borderWidth: 0
            });
        }
        return bands;
    }

    function updateHistory() {
        fetchJSON("/api/history?hours=" + historyHours).then(function (data) {
            var sensorData = data.sensors || [];
            var periods = data.heating_periods || [];
            var heatingOn = data.heating_on || false;

            if (!sensorData.length) return;

            var timestamps = sensorData.map(function (s) {
                return new Date(s.timestamp).getTime();
            });
            var timeMin = timestamps[0];
            var timeMax = timestamps[timestamps.length - 1];

            var datasets = [];
            var keys = ["loop_inlet", "loop_outlet", "hp_inlet", "hp_outlet", "tank"];
            for (var k = 0; k < keys.length; k++) {
                var key = keys[k];
                var points = [];
                for (var i = 0; i < sensorData.length; i++) {
                    if (sensorData[i][key] !== null && sensorData[i][key] !== undefined) {
                        points.push({
                            x: new Date(sensorData[i].timestamp).getTime(),
                            y: sensorData[i][key]
                        });
                    }
                }
                datasets.push({
                    label: SENSOR_LABELS[key] || key,
                    data: points,
                    borderColor: SENSOR_COLORS[key],
                    backgroundColor: SENSOR_COLORS[key],
                    borderWidth: 1.5,
                    pointRadius: 0,
                    pointHitRadius: 6,
                    tension: 0.3
                });
            }

            // VP status as a separate "dataset" shown in legend
            datasets.push({
                label: "VP på",
                data: [],
                borderColor: "rgba(0, 200, 83, 0.5)",
                backgroundColor: "rgba(0, 200, 83, 0.10)",
                borderWidth: 2,
                pointRadius: 0,
                fill: true
            });

            var bands = buildHeatingBands(periods, heatingOn, timeMin, timeMax);

            var canvas = document.getElementById("history-chart");
            var ctx = canvas.getContext("2d");

            if (historyChart) {
                historyChart.data.datasets = datasets;
                historyChart.options.plugins.annotation.annotations = bands;
                historyChart.update("none");
                return;
            }

            historyChart = new Chart(ctx, {
                type: "line",
                data: { datasets: datasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        mode: "index",
                        intersect: false
                    },
                    scales: {
                        x: {
                            type: "time",
                            time: {
                                tooltipFormat: "HH:mm",
                                displayFormats: {
                                    minute: "HH:mm",
                                    hour: "HH:mm",
                                    day: "dd.MM"
                                }
                            },
                            ticks: { color: "#8a8a9a", maxTicksLimit: 10 },
                            grid: { color: "rgba(255,255,255,0.05)" }
                        },
                        y: {
                            ticks: {
                                color: "#8a8a9a",
                                callback: function (v) { return v + "\u00b0C"; }
                            },
                            grid: { color: "rgba(255,255,255,0.05)" }
                        }
                    },
                    plugins: {
                        legend: {
                            labels: {
                                color: "#e0e0e0",
                                usePointStyle: true,
                                pointStyle: "line",
                                boxWidth: 20,
                                font: { size: 11 }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function (ctx) {
                                    if (ctx.dataset.label === "VP p\u00e5") return null;
                                    return ctx.dataset.label + ": " + ctx.parsed.y.toFixed(1) + "\u00b0C";
                                }
                            }
                        },
                        annotation: {
                            annotations: bands
                        }
                    }
                },
                plugins: [{
                    id: "vpLegendOverride",
                    beforeDraw: function () {}
                }]
            });
        }).catch(function (err) {
            console.error("History fetch error:", err);
        });
    }

    // Period button handlers
    (function () {
        var btns = document.querySelectorAll(".period-btn");
        for (var i = 0; i < btns.length; i++) {
            btns[i].addEventListener("click", function () {
                for (var j = 0; j < btns.length; j++) {
                    btns[j].classList.remove("active");
                }
                this.classList.add("active");
                historyHours = parseInt(this.getAttribute("data-hours"), 10);
                if (historyChart) {
                    historyChart.destroy();
                    historyChart = null;
                }
                updateHistory();
            });
        }
    })();

    // -- Manual controls --

    window.heatingOn = function () {
        fetchJSON("/api/heating/on", { method: "POST" }).then(function () {
            updateStatus();
            updateLog();
        });
    };

    window.heatingOff = function () {
        fetchJSON("/api/heating/off", { method: "POST" }).then(function () {
            updateStatus();
            updateLog();
        });
    };

    // -- Init --

    function poll() {
        updateStatus();
        updateForecast();
        updateHistory();
        updateLog();
    }

    poll();
    pollTimer = setInterval(poll, POLL_INTERVAL);
})();
