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
        updateLog();
    }

    poll();
    pollTimer = setInterval(poll, POLL_INTERVAL);
})();
