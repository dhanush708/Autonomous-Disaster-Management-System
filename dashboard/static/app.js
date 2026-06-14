// =====================================================
// CHART STORAGE
// =====================================================

// Two charts per disaster: raw sensor + confidence
const rawCharts  = {};
const confCharts = {};

// =====================================================
// PREVIOUS STATE TRACKING (for event timeline)
// =====================================================

const prevStates = {
    landslide:  null,
    earthquake: null,
    cloudburst: null,
    forest_fire: null
};

// =====================================================
// RAW CHART Y-AXIS CONFIG PER DISASTER
// (display ranges — brain already computed values)
// =====================================================

const rawChartConfig = {
    landslide:   { label: 'Tilt (°)',      color: '#0ea5e9', suggestedMax: 30  },
    earthquake:  { label: 'Vibration',     color: '#f97316', suggestedMax: 1   },
    cloudburst:  { label: 'Humidity (%)',  color: '#3b82f6', suggestedMax: 100 },
    forest_fire: { label: 'Smoke (ADC)',   color: '#ef4444', suggestedMax: 2000}
};

// =====================================================
// CHART FACTORY
// =====================================================

function makeChart(canvasId, color, suggestedMax, yLabel) {

    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                data: [],
                borderColor: color,
                borderWidth: 2.5,
                tension: 0.45,
                fill: true,
                backgroundColor: color + '18',
                pointRadius: 0,
                pointHoverRadius: 4
            }]
        },
        options: {
            responsive: true,
            animation: { duration: 0 },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => `${yLabel}: ${ctx.parsed.y}`
                    }
                }
            },
            scales: {
                x: { display: false },
                y: {
                    min: 0,
                    suggestedMax: suggestedMax,
                    ticks: {
                        font: { size: 10 },
                        maxTicksLimit: 4,
                        color: '#94a3b8'
                    },
                    grid: {
                        color: 'rgba(148,163,184,.15)'
                    }
                }
            }
        }
    });
}

function makeConfChart(canvasId) {

    return makeChart(canvasId, '#16a34a', 100, 'Confidence %');
}

// =====================================================
// INIT ON LOAD
// =====================================================

window.onload = () => {

    const disasters = ['landslide', 'earthquake', 'cloudburst', 'forest_fire'];

    disasters.forEach(d => {

        const cfg = rawChartConfig[d];

        rawCharts[d]  = makeChart(
            `${d}-raw-chart`,
            cfg.color,
            cfg.suggestedMax,
            cfg.label
        );

        confCharts[d] = makeConfChart(`${d}-conf-chart`);
    });

    // Live clock
    setInterval(updateClock, 1000);
    updateClock();

    // Data polling — every 1 second
    loadData();
    setInterval(loadData, 1000);
};

// =====================================================
// CLOCK
// =====================================================

function updateClock() {
    const el = document.getElementById('header-clock');
    if (el) el.innerText = new Date().toLocaleTimeString();
}

// =====================================================
// STATE → CSS CLASS MAPPING
// =====================================================

function stateToClass(state) {

    const map = {
        'SAFE':          'state-safe',
        'SUSPICIOUS':    'state-suspicious',
        'WARNING':       'state-warning',
        'VERIFYING':     'state-verifying',
        'CONFIRMED':     'state-confirmed',
        'FALSE_POSITIVE':'state-false-positive'
    };

    return map[state] || 'state-safe';
}

function stateToMapClass(state) {

    const map = {
        'SAFE':          'safe-node',
        'SUSPICIOUS':    'susp-node',
        'WARNING':       'warning-node',
        'VERIFYING':     'verify-node',
        'CONFIRMED':     'confirm-node',
        'FALSE_POSITIVE':'fp-node'
    };

    return map[state] || 'safe-node';
}

function stateToCardClass(state) {

    const map = {
        'SAFE':          'card-safe',
        'SUSPICIOUS':    'card-suspicious',
        'WARNING':       'card-warning',
        'VERIFYING':     'card-verifying',
        'CONFIRMED':     'card-confirmed',
        'FALSE_POSITIVE':'card-false-positive'
    };

    return map[state] || 'card-safe';
}

// =====================================================
// UPDATE MAP NODE
// =====================================================

function updateMap(name, state) {

    const node = document.getElementById(`map-${name}`);
    if (!node) return;

    node.className = `location-node ${stateToMapClass(state)}`;
}

// =====================================================
// EVENT TIMELINE
// =====================================================

const eventClassMap = {
    'SAFE':           '',
    'SUSPICIOUS':     'event-warn',
    'WARNING':        'event-warn',
    'VERIFYING':      'event-verify',
    'CONFIRMED':      'event-alert',
    'FALSE_POSITIVE': 'event-fp'
};

const disasterLabels = {
    landslide:   '🏔 Landslide',
    earthquake:  '🌍 Earthquake',
    cloudburst:  '🌧 Cloudburst',
    forest_fire: '🌲 Forest Fire'
};

function addEvent(text, type) {

    const feed = document.getElementById('event-feed');
    if (!feed) return;

    const now  = new Date().toLocaleTimeString();
    const cls  = eventClassMap[type] || '';

    const div  = document.createElement('div');
    div.className = `event-item ${cls}`;
    div.innerText = `[${now}] ${text}`;

    feed.insertBefore(div, feed.firstChild);

    // Keep feed at max 40 entries
    while (feed.children.length > 40) {
        feed.removeChild(feed.lastChild);
    }
}

// =====================================================
// UPDATE CHART FROM HISTORY ARRAY
// =====================================================

function updateChartFromHistory(chart, history) {

    if (!chart || !history || history.length === 0) return;

    chart.data.labels               = history.map(h => h.t);
    chart.data.datasets[0].data     = history.map(h => h.v);
    chart.update('none');
}

// =====================================================
// UPDATE RAW DATA PANEL — per disaster
// =====================================================

function updateRawData(disaster, raw) {

    if (!raw) return;

    if (disaster === 'landslide') {

        const set = (id, val, suffix) => {
            const el = document.getElementById(id);
            if (el && val !== undefined && val !== null)
                el.innerText = val + (suffix || '');
        };

        set('ls-pitch',   raw.pitch,         '°');
        set('ls-roll',    raw.roll,           '°');
        set('ls-tilt',    raw.tilt,           '°');
        set('ls-avg-tilt',raw.avg_tilt,       '°');
        set('ls-vib',     raw.vibration,      '');
        set('ls-avg-vib', raw.avg_vibration,  '');
    }

    if (disaster === 'earthquake') {

        const eq_vib = document.getElementById('eq-vib');
        const eq_avg = document.getElementById('eq-avg-vib');

        if (eq_vib && raw.vibration     !== undefined) eq_vib.innerText = raw.vibration;
        if (eq_avg && raw.avg_vibration !== undefined) eq_avg.innerText = raw.avg_vibration;
    }

    if (disaster === 'cloudburst') {

        const set = (id, val, suffix) => {
            const el = document.getElementById(id);
            if (el && val !== undefined && val !== null)
                el.innerText = val + (suffix || '');
        };

        set('cb-humidity', raw.humidity,          '%');
        set('cb-temp',     raw.temperature,       '°C');
        set('cb-avg-hum',  raw.avg_humidity,      '%');
        set('cb-change',   raw.humidity_change,   '%');

        const base   = document.getElementById('cb-baseline');
        const baseRd = document.getElementById('cb-baseline-ready');

        if (raw.baseline_ready) {
            if (base)   base.innerText   = raw.baseline_humidity + '%';
            if (baseRd) baseRd.innerText = 'Ready';
        } else {
            if (base)   base.innerText   = '--';
            if (baseRd) baseRd.innerText = 'Learning...';
        }
    }

    if (disaster === 'forest_fire') {

        const ff_s  = document.getElementById('ff-smoke');
        const ff_a  = document.getElementById('ff-avg-smoke');
        const ff_l  = document.getElementById('ff-level');

        if (ff_s && raw.smoke     !== undefined) ff_s.innerText = raw.smoke;
        if (ff_a && raw.avg_smoke !== undefined) ff_a.innerText = raw.avg_smoke;
        if (ff_l && raw.smoke_level !== undefined) ff_l.innerText = raw.smoke_level;
    }
}

// =====================================================
// UPDATE KPI
// =====================================================

function updateKPI(data) {

    let active    = 0;
    let verifying = 0;
    let confirmed = 0;
    let online    = 0;

    Object.values(data).forEach(item => {

        if (item.state !== 'SAFE') active++;
        if (item.state === 'VERIFYING')      verifying++;
        if (item.state === 'CONFIRMED')      confirmed++;
        if (item.online) online++;
    });

    const set = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.innerText = val;
    };

    set('active-risks',    active);
    set('verify-count',    verifying);
    set('confirmed-count', confirmed);
    set('system-health',   Math.round((online / 4) * 100) + '%');
}

// =====================================================
// UPDATE CARD — main per-disaster update function
// =====================================================

function updateCard(disaster, item) {

    if (!item) return;

    const state = item.state;

    // Confidence display
    const confEl = document.getElementById(`${disaster}-confidence`);
    if (confEl) confEl.innerText = `${Math.round(item.confidence)}%`;

    // State badge — apply correct colour class
    const stateBadge = document.getElementById(`${disaster}-state`);
    if (stateBadge) {
        stateBadge.innerText  = state;
        stateBadge.className  = `state-badge ${stateToClass(state)}`;
    }

    // Card border accent
    const card = document.getElementById(`card-${disaster}`);
    if (card) {
        card.className = `disaster-card ${stateToCardClass(state)}`;
    }

    // Last update time
    const luEl = document.getElementById(`${disaster}-last-update`);
    if (luEl && item.last_update) {
        const d = new Date(item.last_update * 1000);
        luEl.innerText = 'Last update: ' + d.toLocaleTimeString();
    }

    // Sensor badge
    const statusEl = document.getElementById(`status-${disaster}`);
    if (statusEl) {
        statusEl.innerText   = item.online ? '● ONLINE' : '● OFFLINE';
        statusEl.className   = item.online ? 'sensor-badge online-badge' : 'sensor-badge offline-badge';
    }

    // Sensor health panel (upper section)
    const healthEl = document.getElementById(`health-${disaster}`);
    if (healthEl) {
        healthEl.innerText   = item.online ? '● ONLINE' : '● OFFLINE';
        healthEl.className   = item.online ? 'sensor-online' : 'sensor-offline';
    }

    // Map update
    updateMap(disaster, state);

    // Raw data display
    updateRawData(disaster, item.raw);

    // Charts — full history from backend
    updateChartFromHistory(rawCharts[disaster],  item.raw_history);
    updateChartFromHistory(confCharts[disaster], item.conf_history);

    // Verification section — show only when VERIFYING
    const verifySection = document.getElementById(`${disaster}-verify`);
    if (verifySection) {
        verifySection.style.display =
            (state === 'VERIFYING') ? 'block' : 'none';
    }

    // Event timeline — log state transitions
    if (prevStates[disaster] !== null && prevStates[disaster] !== state) {

        const label = disasterLabels[disaster] || disaster;
        addEvent(`${label} → ${state}`, state);
    }

    prevStates[disaster] = state;
}

// =====================================================
// LOAD DATA (main polling function — 1s interval)
// =====================================================

async function loadData() {

    try {

        const response = await fetch('/api/status');

        if (!response.ok) return;

        const data = await response.json();

        updateKPI(data);

        [
            'landslide',
            'earthquake',
            'cloudburst',
            'forest_fire'
        ].forEach(d => updateCard(d, data[d]));

    } catch (err) {
        // Backend unreachable — fail silently
    }
}

// =====================================================
// VERIFICATION ACTIONS
// These POST to backend which queues the action.
// Brain polls backend and applies the action itself.
// Flask never directly modifies brain state.
// =====================================================

async function confirmDisaster(disaster) {

    addEvent(`Admin confirmed ${disasterLabels[disaster]} — awaiting brain`, 'CONFIRMED');

    try {
        await fetch(`/api/confirm/${disaster}`, { method: 'POST' });
    } catch (err) {}
}

async function rejectDisaster(disaster) {

    addEvent(`Admin rejected ${disasterLabels[disaster]} — awaiting brain`, 'FALSE_POSITIVE');

    try {
        await fetch(`/api/reject/${disaster}`, { method: 'POST' });
    } catch (err) {}
}

async function resetDisaster(disaster) {

    addEvent(`Admin reset ${disasterLabels[disaster]} — awaiting brain`, 'SAFE');

    try {
        await fetch(`/api/reset/${disaster}`, { method: 'POST' });
    } catch (err) {}
}