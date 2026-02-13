
// Global Chart Instances
let charts = {
    macros: null,
    calories: null,
    trend: null
};

document.addEventListener('DOMContentLoaded', () => {
    // Only run if on dashboard
    if (document.getElementById('macrosChart')) {
        initDashboardCharts();
    }

    // Form Wizard Logic
    if (document.querySelector('.wizard-form')) {
        initWizard();
    }
});

function initDashboardCharts() {
    // Macros Chart (Doughnut)
    const ctxMacros = document.getElementById('macrosChart').getContext('2d');
    charts.macros = new Chart(ctxMacros, {
        type: 'doughnut',
        data: {
            labels: ['Protein', 'Carbs', 'Fats'],
            datasets: [{
                data: [userMacros.protein, userMacros.carbs, userMacros.fats],
                backgroundColor: ['#10b981', '#84cc16', '#059669'],
                borderWidth: 0,
                hoverOffset: 15
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '75%',
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (context) => ` ${context.label}: ${context.raw}g`
                    }
                }
            }
        }
    });

    // Calories Chart (Doughnut)
    const ctxCals = document.getElementById('caloriesChart').getContext('2d');
    charts.calories = new Chart(ctxCals, {
        type: 'doughnut',
        data: {
            labels: ['Consumed', 'Remaining'],
            datasets: [{
                data: [consumedCalories, Math.max(0, dailyCalories - consumedCalories)],
                backgroundColor: ['#10b981', 'rgba(0, 0, 0, 0.05)'],
                borderWidth: 0,
                borderRadius: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '85%',
            plugins: {
                legend: { display: false }
            }
        }
    });

    // Trend Chart (Line)
    initTrendChart('calories');
}

function initTrendChart(type) {
    const ctxTrend = document.getElementById('trendChart').getContext('2d');
    if (charts.trend) charts.trend.destroy();

    let data, label, color;
    if (type === 'calories') {
        data = trendCalories;
        label = 'Calories (kcal)';
        color = '#10b981';
    } else if (type === 'weight') {
        data = trendWeight;
        label = 'Weight (kg)';
        color = '#84cc16';
    } else {
        data = trendBMI;
        label = 'BMI';
        color = '#059669';
    }

    charts.trend = new Chart(ctxTrend, {
        type: 'line',
        data: {
            labels: trendLabels,
            datasets: [{
                label: label,
                data: data,
                borderColor: color,
                backgroundColor: color + '20',
                borderWidth: 3,
                pointBackgroundColor: color,
                pointBorderColor: '#fff',
                pointHoverRadius: 6,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                }
            }
        }
    });
}

function showTrend(type) {
    // Update Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    initTrendChart(type);
}

// Chat Logic
function toggleChat() {
    const widget = document.getElementById('chatWidget');
    if (widget.style.display === 'flex') {
        widget.style.display = 'none';
    } else {
        widget.style.display = 'flex';
        document.querySelector('.chat-badge').style.display = 'none';
    }
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const text = input.value.trim();
    if (!text) return;

    appendMessage(text, 'user');
    input.value = '';

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, user_id: userId })
        });
        const data = await response.json();

        appendMessage(data.response, 'bot');

        if (data.action) {
            handleAction(data.action);
        }
    } catch (e) {
        appendMessage("Sorry, I'm offline. Please check your connection.", 'bot');
    }
}

function appendMessage(text, sender) {
    const body = document.getElementById('chatBody');
    const msg = document.createElement('div');
    msg.className = `chat-message ${sender}`;
    msg.textContent = text;
    body.appendChild(msg);
    body.scrollTop = body.scrollHeight;
}

function handleAction(action) {
    console.log("Action triggered:", action);
    if (action.type === 'update_water') {
        document.getElementById('display-water').textContent = action.value + 'L';
        document.getElementById('water-level').style.height = (action.value / 3.0 * 100) + '%';
    } else if (action.type === 'update_calories') {
        document.getElementById('display-consumed').textContent = action.value + ' kcal';
        charts.calories.data.datasets[0].data[0] = action.value;
        charts.calories.data.datasets[0].data[1] = Math.max(0, dailyCalories - action.value);
        charts.calories.update();
    } else if (action.type === 'update_weight') {
        document.getElementById('display-weight').textContent = action.value;
        document.getElementById('display-bmi').textContent = action.bmi;
        // Optionally update trend charts if they are visible
        trendWeight[trendWeight.length - 1] = action.value;
        trendBMI[trendBMI.length - 1] = action.bmi;
    }
}

async function logWater() {
    // Manually trigger a 0.5L add
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: 'add 0.5L water', user_id: userId })
        });
        const data = await response.json();
        handleAction(data.action);
    } catch (e) {
        console.error("Water log failed");
    }
}

// Wizard Logic (legacy/preserved)
let currentStep = 1;
function initWizard() {
    showStep(currentStep);
}
function showStep(s) {
    document.querySelectorAll('.form-step').forEach(el => el.style.display = 'none');
    document.querySelector(`#step-${s}`).style.display = 'block';
}
function nextStep() {
    currentStep++;
    showStep(currentStep);
}
function prevStep() {
    currentStep--;
    showStep(currentStep);
}
