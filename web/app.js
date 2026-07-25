document.addEventListener("DOMContentLoaded", () => {
    
    // --- Navigation Logic ---
    const navButtons = document.querySelectorAll('.nav-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all
            navButtons.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            // Add active class to clicked
            btn.classList.add('active');
            const targetId = btn.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active');
        });
    });


    // --- Q2: Knowledge Base Retrieval ---
    const searchBtn = document.getElementById('btn-q2-search');
    const searchInput = document.getElementById('q2-search-input');
    const resultsContainer = document.getElementById('q2-results');

    searchBtn.addEventListener('click', async () => {
        const query = searchInput.value.trim();
        if (!query) return;

        resultsContainer.innerHTML = '<p class="empty-state">Searching...</p>';

        try {
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
                card.innerHTML = `
                    <strong>${type.toUpperCase().replace(/_/g, ' ')}</strong>
                    <p>${message}</p>
                `;
                nudgeBox.appendChild(card);
                nudgeBox.scrollTop = nudgeBox.scrollHeight;
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
    const vapi = new window.Vapi("39834d71-c855-4eeb-a434-c077c4856e24");
    
    const ASSISTANTS = {
        q1: '05d2ae77-a71f-431d-9b73-1eb908f4f3d9',
        q3_ph: '8ba3d253-55dc-4fbe-8970-e894cebd05e9',
        q3_id: '3cbcfe7d-8bd9-4711-b9e2-870666d9c248'
    };

    let currentCallButton = null;
    let originalButtonText = "";

    // Vapi Event Listeners
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

    // Button Handlers
    function setupCallButton(buttonId, assistantId) {
        const btn = document.getElementById(buttonId);
        if (!btn) return;
        
        btn.addEventListener('click', () => {
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
