import Vapi from 'https://esm.sh/@vapi-ai/web';

document.addEventListener("DOMContentLoaded", () => {
    
    // --- Navigation & State Persistence Logic ---
    const navButtons = document.querySelectorAll('.nav-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    function switchTab(targetId) {
        navButtons.forEach(b => b.classList.remove('active'));
        tabPanes.forEach(p => p.classList.remove('active'));

        const activeBtn = document.querySelector(`.nav-btn[data-target="${targetId}"]`);
        const activePane = document.getElementById(targetId);
        
        if (activeBtn) activeBtn.classList.add('active');
        if (activePane) activePane.classList.add('active');
        
        localStorage.setItem('activeTab', targetId);
    }

    // Restore last active tab
    const savedTab = localStorage.getItem('activeTab') || 'q1';
    switchTab(savedTab);

    navButtons.forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.getAttribute('data-target')));
    });

    // --- Global Telemetry State ---
    let telemetryState = {
        apiHits: 0,
        latencies: []
    };

    function calculatePercentile(arr, p) {
        if (arr.length === 0) return 0;
        const sorted = [...arr].sort((a, b) => a - b);
        const index = Math.ceil((p / 100) * sorted.length) - 1;
        return sorted[index];
    }

    function updateTelemetry(hitsIncrement = 0, newE2ELatency = null) {
        telemetryState.apiHits += hitsIncrement;
        document.getElementById('metric-api-hits').innerText = telemetryState.apiHits;

        if (newE2ELatency !== null) {
            telemetryState.latencies.push(newE2ELatency);
            
            // Calculate Avg
            const sum = telemetryState.latencies.reduce((a, b) => a + b, 0);
            const avg = Math.round(sum / telemetryState.latencies.length);
            
            // Calculate P50 (Median) and P95
            const p50 = calculatePercentile(telemetryState.latencies, 50);
            const p95 = calculatePercentile(telemetryState.latencies, 95);

            document.getElementById('metric-avg-e2e').innerText = `${avg}ms`;
            document.getElementById('metric-p50').innerText = `${p50}ms`;
            document.getElementById('metric-p95').innerText = `${p95}ms`;
        }
    }


    // --- Q2: Knowledge Base Retrieval ---
    const searchBtn = document.getElementById('btn-q2-search');
    const searchInput = document.getElementById('q2-search-input');
    const resultsContainer = document.getElementById('q2-results');

    searchBtn.addEventListener('click', async () => {
        const query = searchInput.value.trim();
        if (!query) return;

        resultsContainer.innerHTML = '<p class="empty-state">Searching...</p>';

        try {
            updateTelemetry(1); // Track Q2 Search API Hit
            // Fetch from Q2 API mounted on unified server
            const res = await fetch('/q2/api/v1/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // Assuming testing key or fallback from backend
                    'X-API-Key': 'health-shield-secret-123'
                },
                body: JSON.stringify({ query: query, limit: 3 })
            });

            if (!res.ok) throw new Error("Search failed");
            const data = await res.json();
            
            if (data.results && data.results.length > 0) {
                resultsContainer.innerHTML = '';
                data.results.forEach(record => {
                    // Pre-process collapsed markdown strings to ensure proper parsing
                    let rawContent = record.content;
                    rawContent = rawContent.replace(/(#{1,6}\s)/g, '\n$1'); // Newlines before headers
                    rawContent = rawContent.replace(/( - )/g, '\n- '); // Newlines before list items
                    rawContent = rawContent.replace(/(\*\*.*?\*\*)/g, '$1'); // Preserve bolding

                    // Render to HTML using marked.js
                    const htmlContent = marked.parse(rawContent);

                    const card = document.createElement('div');
                    card.className = 'search-result-card';
                    card.innerHTML = `
                        <h4>${record.title}</h4>
                        <div class="kb-markdown-content">${htmlContent}</div>
                        <div class="search-result-source">
                            <span>FILE</span> ${record.source_url}
                        </div>
                    `;
                    resultsContainer.appendChild(card);
                });
            } else {
                resultsContainer.innerHTML = '<p class="empty-state">No relevant documents found.</p>';
            }

        } catch (err) {
            resultsContainer.innerHTML = `<p class="empty-state" style="color:var(--danger)">Error: ${err.message}</p>`;
        }
    });


    // --- Q4: Live Insights (WebSocket) ---
    const startQ4Btn = document.getElementById('btn-q4-start');
    const transcriptBox = document.getElementById('q4-transcript-box');
    const nudgeBox = document.getElementById('q4-nudge-box');
    
    let ws = null;

    function connectWebSocket() {
        if (ws) return;
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // Connect to Q4 router mounted at /q4
        ws = new WebSocket(`${protocol}//${window.location.host}/q4/ws/nudges`);

        ws.onopen = () => {
            console.log("WebSocket connected");
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === "transcript") {
                const isFinal = data.is_final;
                const text = data.text;
                
                // Remove pending partials
                const partials = transcriptBox.querySelectorAll('.partial');
                partials.forEach(p => p.remove());

                const p = document.createElement('p');
                p.className = `transcript-line ${isFinal ? 'final' : 'partial'}`;
                p.textContent = text;
                transcriptBox.appendChild(p);
                transcriptBox.scrollTop = transcriptBox.scrollHeight;
                
            } else {
                const type = data.type || "alert";
                const message = data.message || "";
                
                let cssClass = "alert";
                if (type.includes("cross_sell") || type === "SUGGESTION") cssClass = "suggestion";
                if (type.includes("compliance") || type === "COMPLIANCE") cssClass = "compliance";
                
                const card = document.createElement('div');
                card.className = `nudge-card ${cssClass}`;
                
                let latencyBadge = "";
                if (data.context && data.context.e2e_ms) {
                    latencyBadge = `<span style="float:right; font-size: 0.75rem; color: #64748b;">E2E: ${data.context.e2e_ms}ms</span>`;
                }

                card.innerHTML = `
                    <strong>${type.toUpperCase().replace(/_/g, ' ')}</strong> ${latencyBadge}
                    <p>${message}</p>
                `;
                nudgeBox.appendChild(card);
                nudgeBox.scrollTop = nudgeBox.scrollHeight;
                
                // Track Telemetry
                if (data.context && data.context.e2e_ms) {
                    updateTelemetry(1, data.context.e2e_ms); // Extractor call counts as hit
                }
            }
        };

        ws.onclose = () => {
            console.log("WebSocket disconnected");
            ws = null;
            setTimeout(connectWebSocket, 3000); // Auto-reconnect
        };
    }

    // Start WebSocket on load
    connectWebSocket();

    startQ4Btn.addEventListener('click', async () => {
        transcriptBox.innerHTML = '';
        nudgeBox.innerHTML = '';
        startQ4Btn.disabled = true;
        startQ4Btn.textContent = 'Streaming...';

        try {
            updateTelemetry(1); // Track Q4 Stream API Hit
            await fetch('/q4/start_stream', { method: 'POST' });
        } catch (e) {
            console.error("Failed to start stream", e);
        }
        
        // Re-enable button after 10s for simulation purposes
        setTimeout(() => {
            startQ4Btn.disabled = false;
            startQ4Btn.textContent = 'Start Simulated Call';
        }, 10000);
    });

    // --- Vapi Voice SDK (Q1, Q3) ---
    let vapi = null;
    try {
        vapi = new Vapi("39834d71-c855-4eeb-a434-c077c4856e24");
        console.log("Vapi SDK initialized successfully.");
    } catch (e) {
        console.error("Failed to initialize Vapi SDK:", e);
        alert("Failed to load Vapi Web SDK. Check your internet connection or browser console for errors.");
    }
    
    const ASSISTANTS = {
        q1: '05d2ae77-a71f-431d-9b73-1eb908f4f3d9',
        q3_ph: '8ba3d253-55dc-4fbe-8970-e894cebd05e9',
        q3_id: '3cbcfe7d-8bd9-4711-b9e2-870666d9c248'
    };

    let currentCallButton = null;
    let originalButtonText = "";

    // Vapi Event Listeners
    if (vapi) {
        vapi.on('call-start', () => {
            if (currentCallButton) {
                currentCallButton.textContent = '🔴 End Call';
                currentCallButton.style.backgroundColor = '#ef4444'; // Red
                currentCallButton.style.color = '#fff';
            }
        });

    vapi.on('call-end', () => {
        if (currentCallButton) {
            currentCallButton.textContent = originalButtonText;
            currentCallButton.style.backgroundColor = ''; // Reset to default
            currentCallButton.style.color = '';
            currentCallButton = null;
        }
    });

        vapi.on('error', (e) => {
            console.error("Vapi Error:", e);
            if (currentCallButton) {
                currentCallButton.textContent = originalButtonText;
                currentCallButton.style.backgroundColor = '';
                currentCallButton.style.color = '';
                currentCallButton = null;
            }
        });

        // Intercept Vapi Live Transcripts and push to Q4 Pipeline
        vapi.on('message', async (message) => {
            if (message.type === 'transcript' && message.transcriptType === 'final') {
                try {
                    await fetch('/analyze_transcript_direct', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ text: message.transcript, is_final: true })
                    });
                } catch (e) {
                    console.error("Failed to push transcript to Q4", e);
                }
            }
        });
    }

    // Button Handlers
    function setupCallButton(buttonId, assistantId) {
        const btn = document.getElementById(buttonId);
        if (!btn) return;
        
        btn.addEventListener('click', () => {
            if (!vapi) {
                alert("Vapi SDK is not loaded. Cannot start call. Ensure the CDN script is not blocked.");
                return;
            }
            if (currentCallButton === btn) {
                // If it's already running on this button, end it
                vapi.stop();
            } else if (currentCallButton) {
                // If a different call is running, stop it first
                vapi.stop();
                setTimeout(() => {
                    originalButtonText = btn.textContent;
                    currentCallButton = btn;
                    btn.textContent = 'Connecting...';
                    vapi.start(assistantId);
                }, 500);
            } else {
                originalButtonText = btn.textContent;
                currentCallButton = btn;
                btn.textContent = 'Connecting...';
                vapi.start(assistantId);
            }
        });
    }

    setupCallButton('btn-q1-call', ASSISTANTS.q1);
    setupCallButton('btn-q3-ph', ASSISTANTS.q3_ph);
    setupCallButton('btn-q3-id', ASSISTANTS.q3_id);

});
