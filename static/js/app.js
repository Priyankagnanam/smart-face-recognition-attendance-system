function csrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.content : '';
}

function apiFetch(url, options) {
    options = options || {};
    options.headers = options.headers || {};
    const method = (options.method || 'GET').toUpperCase();
    if (method !== 'GET') {
        options.headers['X-CSRFToken'] = csrfToken();
    }
    return fetch(url, options);
}

const App = {
    init() {
        this.splashScreen();
        this.initTheme();
        this.initSidebar();
        this.initToast();
        this.initBreadcrumb();
        this.updateClock();
        this.loadPageData();
    },

    splashScreen() {
        const splash = document.getElementById('splash-screen');
        if (splash) {
            setTimeout(() => splash.classList.add('hidden'), 2500);
        }
    },

    initTheme() {
        const saved = localStorage.getItem('theme') || 'dark';
        document.documentElement.setAttribute('data-theme', saved);
        const btn = document.querySelector('.theme-toggle');
        if (btn) {
            btn.innerHTML = saved === 'dark'
                ? '<i class="fas fa-sun"></i>'
                : '<i class="fas fa-moon"></i>';
            btn.addEventListener('click', () => {
                const current = document.documentElement.getAttribute('data-theme');
                const next = current === 'dark' ? 'light' : 'dark';
                document.documentElement.setAttribute('data-theme', next);
                localStorage.setItem('theme', next);
                btn.innerHTML = next === 'dark'
                    ? '<i class="fas fa-sun"></i>'
                    : '<i class="fas fa-moon"></i>';
            });
        }
    },

    initSidebar() {
        const toggle = document.querySelector('.sidebar-toggle');
        const sidebar = document.querySelector('.sidebar');
        if (toggle && sidebar) {
            toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
        }
        const links = document.querySelectorAll('.nav-item');
        links.forEach(link => {
            link.addEventListener('click', () => {
                if (window.innerWidth <= 768) {
                    sidebar.classList.remove('open');
                }
            });
        });
    },

    initToast() {
        const container = document.createElement('div');
        container.className = 'toast-container';
        container.id = 'toast-container';
        document.body.appendChild(container);
    },

    toast(message, type = 'info', duration = 4000) {
        const container = document.getElementById('toast-container');
        if (!container) return;
        const icons = {
            success: 'fa-check-circle',
            danger: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle',
        };
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `<i class="fas ${icons[type] || icons.info}"></i> ${message}`;
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },

    updateClock() {
        const el = document.getElementById('current-time');
        if (!el) return;
        const update = () => {
            const now = new Date();
            const opts = {
                weekday: 'long', year: 'numeric',
                month: 'long', day: 'numeric',
                hour: '2-digit', minute: '2-digit', second: '2-digit'
            };
            el.textContent = now.toLocaleDateString('en-US', opts);
        };
        update();
        setInterval(update, 1000);
    },

    initBreadcrumb() {
        const path = window.location.pathname;
        const breadcrumb = document.querySelector('.breadcrumb');
        if (!breadcrumb) return;
        const pageName = document.querySelector('.page-title');
        if (pageName && !breadcrumb.querySelector('span:last-child')) {
            const span = document.createElement('span');
            span.textContent = pageName.textContent;
            breadcrumb.appendChild(span);
        }
    },

    loadPageData() {
        const page = window.location.pathname;
        if (page === '/' || page === '/dashboard') {
            this.loadDashboard();
        } else if (page === '/students/register') {
            this.initCameraCapture();
        } else if (page === '/students/') {
            this.loadStudents();
        } else if (page === '/attendance/') {
            this.loadAttendance();
        } else if (page === '/attendance/history') {
            this.loadAttendanceHistory();
        } else if (page === '/attendance/live') {
            this.initLiveAttendance();
        } else if (page === '/reports/') {
            this.initReports();
        } else if (page === '/analytics/') {
            this.initAnalytics();
        } else if (page === '/settings/') {
            this.loadSettings();
        }
    },

    // ==================== DASHBOARD ====================
    async loadDashboard() {
        try {
            const res = await apiFetch('/api/dashboard/stats');
            const data = await res.json();
            document.getElementById('total-students').textContent = data.total_students;
            document.getElementById('present-today').textContent = data.present_today;
            document.getElementById('absent-today').textContent = data.absent_today;
            document.getElementById('attendance-pct').textContent = data.attendance_percentage + '%';
            document.getElementById('avg-accuracy').textContent = data.avg_accuracy + '%';

            const tbody = document.querySelector('#recent-attendance tbody');
            if (tbody && data.recent_attendance.length) {
                tbody.innerHTML = data.recent_attendance.map(r => `
                    <tr>
                        <td>${r.student_id}</td>
                        <td>${r.name}</td>
                        <td>${r.department}</td>
                        <td>${r.date}</td>
                        <td>${r.time}</td>
                        <td><span class="badge badge-success">${r.status}</span></td>
                        <td>${r.confidence}%</td>
                    </tr>
                `).join('');
            }

            const trendRes = await apiFetch('/api/dashboard/weekly-trend');
            const trend = await trendRes.json();
            if (document.getElementById('weeklyChart')) {
                const s = getComputedStyle(document.documentElement);
                const tc = s.getPropertyValue('--text-secondary').trim() || '#CBD5E1';
                const gc = s.getPropertyValue('--border-color').trim() || '#334155';
                new Chart(document.getElementById('weeklyChart'), {
                    type: 'line',
                    data: {
                        labels: trend.labels,
                        datasets: [{
                            label: 'Present',
                            data: trend.present,
                            borderColor: '#22C55E',
                            backgroundColor: 'rgba(34,197,94,0.1)',
                            fill: true,
                            tension: 0.4,
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: { legend: { labels: { color: tc } } },
                        scales: {
                            x: { ticks: { color: tc }, grid: { color: gc } },
                            y: { ticks: { color: tc }, grid: { color: gc }, beginAtZero: true }
                        }
                    }
                });
            }
        } catch (e) {
            console.error('Dashboard load error:', e);
        }
    },

    // ==================== STUDENT REGISTRATION ====================
    initCameraCapture() {
        const form = document.getElementById('student-form');
        const btn = document.getElementById('capture-face-btn');
        const status = document.getElementById('capture-status');
        const sidInput = document.getElementById('student_id');
        const nameInput = document.getElementById('name');
        if (!form || !btn || !status) return;

        // Identity of the last student successfully saved via /students/api/add.
        // Face capture is only allowed while the form matches this saved identity.
        let saved = null;
        // Capture success message shown in the status panel until the next save.
        let lastCaptureNote = '';

        const updateCaptureUI = () => {
            const sid = sidInput ? sidInput.value.trim() : '';
            const name = nameInput ? nameInput.value.trim() : '';
            btn.innerHTML = '<i class="fas fa-camera"></i> Capture Face';
            if (!saved) {
                btn.disabled = true;
                status.innerHTML = '<i class="fas fa-info-circle"></i> Save the student first to enable face capture.';
            } else if (!sid && !name) {
                btn.disabled = true;
                status.innerHTML = lastCaptureNote || '<i class="fas fa-check-circle"></i> Student saved. Enter a new student to register, or re-enter the same ID and name to capture face images.';
            } else if (sid !== saved.sid || name !== saved.name) {
                btn.disabled = true;
                status.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Student details changed. Save again to enable face capture.';
            } else {
                btn.disabled = false;
                status.innerHTML = '<i class="fas fa-check-circle"></i> Student saved. Ready to capture face images.';
            }
        };

        updateCaptureUI();
        if (sidInput) sidInput.addEventListener('input', updateCaptureUI);
        if (nameInput) nameInput.addEventListener('input', updateCaptureUI);
        form.addEventListener('reset', updateCaptureUI);

        btn.addEventListener('click', async () => {
            if (!saved) {
                this.toast('Please save the student before capturing face images.', 'warning');
                updateCaptureUI();
                return;
            }
            const sid = sidInput ? sidInput.value.trim() : '';
            const name = nameInput ? nameInput.value.trim() : '';
            if (sid !== saved.sid || name !== saved.name) {
                this.toast('Student details changed. Please save again before capturing.', 'warning');
                updateCaptureUI();
                return;
            }

            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Capturing...';
            status.innerHTML = '<i class="fas fa-camera"></i> Initializing camera...';

            try {
                const res = await apiFetch('/recognition/capture', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ student_id: saved.sid, name: saved.name })
                });
                const data = await res.json();
                if (data.success) {
                    let trainingNote = '';
                    try {
                        const tRes = await apiFetch('/recognition/training-status');
                        const tData = await tRes.json();
                        if (tData && typeof tData.total_images === 'number') {
                            trainingNote = ` Model auto-training is running (${tData.total_images} images in dataset).`;
                        }
                    } catch (e) { /* training status is informational only */ }
                    lastCaptureNote = '<i class="fas fa-check-circle"></i> ' + data.message + trainingNote;
                    status.innerHTML = lastCaptureNote;
                    this.toast(`Captured ${data.count} images for ${saved.name}!`, 'success');
                    form.reset();
                } else {
                    this.toast(data.message, 'danger');
                    status.innerHTML = '<i class="fas fa-exclamation-circle"></i> ' + (data.message || 'Face capture failed.');
                }
            } catch (e) {
                this.toast('Camera capture failed.', 'danger');
                status.innerHTML = '<i class="fas fa-exclamation-circle"></i> Camera capture failed.';
            }
            updateCaptureUI();
        });

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                student_id: form.student_id.value.trim(),
                name: form.name.value.trim(),
                department: form.department.value,
                year: form.year.value,
                section: form.section.value.trim(),
                email: form.email.value.trim(),
                phone: form.phone.value.trim(),
            };
            const res = await apiFetch('/students/api/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            const result = await res.json();
            if (result.success) {
                saved = { sid: data.student_id, name: data.name };
                const msgEl = document.getElementById('save-success-message');
                if (msgEl) msgEl.textContent = result.message;
                this.openModal('save-success-modal');
            } else {
                this.toast(result.message, 'danger');
            }
            updateCaptureUI();
        });
    },

    // ==================== STUDENTS ====================
    loadStudents(page = 1) {
        const tbody = document.querySelector('#students-table tbody');
        if (!tbody) return;

        const search = document.getElementById('student-search');
        const pagination = document.getElementById('students-pagination');

        const fetchStudents = async (p) => {
            const q = search ? search.value.trim() : '';
            const res = await apiFetch(`/students/api/list?page=${p}&per_page=10&search=${encodeURIComponent(q)}`);
            const data = await res.json();

            tbody.innerHTML = data.students.map(s => `
                <tr>
                    <td><strong>${s.student_id}</strong></td>
                    <td>${s.name}</td>
                    <td>${s.department}</td>
                    <td>Year ${s.year}</td>
                    <td>${s.section}</td>
                    <td>${s.email}</td>
                    <td>${s.phone || '-'}</td>
                    <td>
                        <div class="actions">
                            <button class="edit-btn" onclick="App.editStudent('${s.student_id}')"><i class="fas fa-edit"></i></button>
                            <button class="delete-btn" onclick="App.deleteStudent('${s.student_id}')"><i class="fas fa-trash"></i></button>
                        </div>
                    </td>
                </tr>
            `).join('');

            if (pagination) {
                const pages = data.pages;
                let html = `<button class="page-btn" onclick="App.loadStudents(${p - 1})" ${p <= 1 ? 'disabled' : ''}><i class="fas fa-chevron-left"></i></button>`;
                for (let i = 1; i <= pages; i++) {
                    html += `<button class="page-btn ${i === p ? 'active' : ''}" onclick="App.loadStudents(${i})">${i}</button>`;
                }
                html += `<button class="page-btn" onclick="App.loadStudents(${p + 1})" ${p >= pages ? 'disabled' : ''}><i class="fas fa-chevron-right"></i></button>`;
                pagination.innerHTML = html;
            }
        };

        fetchStudents(page);

        if (search) {
            search.addEventListener('input', () => fetchStudents(1));
        }
    },

    async editStudent(id) {
        const res = await apiFetch(`/students/api/get/${id}`);
        const data = await res.json();
        if (!data.success) return;

        const s = data.student;
        const form = document.getElementById('edit-form');
        form.student_id.value = s.student_id;
        form.name.value = s.name;
        form.department.value = s.department;
        form.year.value = s.year;
        form.section.value = s.section;
        form.email.value = s.email;
        form.phone.value = s.phone || '';
        document.getElementById('edit-modal').classList.add('active');
    },

    async deleteStudent(id) {
        if (!confirm('Are you sure you want to delete this student?')) return;
        const res = await apiFetch(`/students/api/delete/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            this.toast(data.message, 'success');
            this.loadStudents();
        } else {
            this.toast(data.message, 'danger');
        }
    },

    // ==================== ATTENDANCE ====================
    loadAttendance() {
        const tbody = document.querySelector('#today-attendance tbody');
        if (!tbody) return;
        const countEl = document.getElementById('today-count');
        const dateEl = document.getElementById('today-date');
        apiFetch('/attendance/api/today')
            .then(r => r.json())
            .then(data => {
                tbody.innerHTML = data.records.map(r => `
                    <tr>
                        <td>${r.student_id}</td>
                        <td>${r.name}</td>
                        <td>${r.department}</td>
                        <td>${r.time}</td>
                        <td><span class="badge badge-success">${r.status}</span></td>
                        <td>${r.confidence}%</td>
                    </tr>
                `).join('');
                if (!data.records.length) {
                    tbody.innerHTML = '<tr><td colspan="6" class="text-center" style="color: var(--text-muted);">No attendance records for today</td></tr>';
                }
                if (countEl) countEl.textContent = data.records.length;
                if (dateEl) dateEl.textContent = data.date;
            });
    },

    loadAttendanceHistory(page = 1) {
        const tbody = document.querySelector('#history-table tbody');
        if (!tbody) return;
        const search = document.getElementById('history-search');
        const deptFilter = document.getElementById('history-dept');
        const dateFrom = document.getElementById('date-from');
        const dateTo = document.getElementById('date-to');
        const pagination = document.getElementById('history-pagination');

        const fetchHistory = async (p) => {
            const params = new URLSearchParams({
                page: p, per_page: 20,
                search: search ? search.value.trim() : '',
                department: deptFilter ? deptFilter.value : '',
                from: dateFrom ? dateFrom.value : '',
                to: dateTo ? dateTo.value : '',
            });
            const res = await apiFetch(`/attendance/api/history?${params}`);
            const data = await res.json();

            tbody.innerHTML = data.records.map(r => `
                <tr>
                    <td>${r.student_id}</td>
                    <td>${r.name}</td>
                    <td>${r.department}</td>
                    <td>${r.date}</td>
                    <td>${r.time}</td>
                    <td><span class="badge badge-${r.status === 'Present' ? 'success' : 'danger'}">${r.status}</span></td>
                    <td>${r.confidence}%</td>
                </tr>
            `).join('');
            if (!data.records.length) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-muted);">No records found</td></tr>';
            }

            if (pagination) {
                let html = `<button class="page-btn" onclick="App.loadAttendanceHistory(${p - 1})" ${p <= 1 ? 'disabled' : ''}><i class="fas fa-chevron-left"></i></button>`;
                for (let i = 1; i <= data.pages; i++) {
                    html += `<button class="page-btn ${i === p ? 'active' : ''}" onclick="App.loadAttendanceHistory(${i})">${i}</button>`;
                }
                html += `<button class="page-btn" onclick="App.loadAttendanceHistory(${p + 1})" ${p >= data.pages ? 'disabled' : ''}><i class="fas fa-chevron-right"></i></button>`;
                pagination.innerHTML = html;
            }
        };

        fetchHistory(page);

        [search, deptFilter, dateFrom, dateTo].forEach(el => {
            if (el) {
                el.addEventListener('change', () => fetchHistory(1));
                if (el.tagName === 'INPUT' && el.type !== 'text') {
                    el.addEventListener('input', () => fetchHistory(1));
                }
            }
        });
        if (search) {
            search.addEventListener('input', () => fetchHistory(1));
        }
    },

    // ==================== LIVE ATTENDANCE ====================
    initLiveAttendance() {
        const startBtn = document.getElementById('start-camera');
        const stopBtn = document.getElementById('stop-camera');
        const videoFeed = document.getElementById('video-feed');
        const camStatusText = document.getElementById('cam-status-text');
        const camStatusDot = document.getElementById('cam-status-dot');
        if (!startBtn || !videoFeed) return;

        // Clear camera state. The camera runs while cameraRunning === true and
        // only stops via the Stop button or when the page is closed/unloaded.
        let cameraRunning = false;
        let frameInterval = null;
        let recognitionPoll = null;

        // Temporary diagnostic logging for the camera lifecycle.
        const camLog = (...args) => console.log('[CAMERA]', ...args);

        const setStatus = (text, active) => {
            if (camStatusText) camStatusText.textContent = text;
            if (camStatusDot) {
                camStatusDot.style.color = active ? 'var(--success)' : 'var(--danger)';
            }
        };

        const emptyState = () => `
            <div class="empty-state">
                <i class="fas fa-user"></i>
                <h3>No faces recognized yet</h3>
                <p>Start the camera to begin face recognition</p>
            </div>`;

        // Renders the recognized-list panel purely from the backend status.
        // faces: array of confirmed recognitions; facesDetected: face in frame.
        const renderRecognized = (faces, facesDetected) => {
            const list = document.getElementById('recognized-list');
            if (!list) return;
            if (faces && faces.length) {
                list.innerHTML = faces.map(f => `
                    <div class="stat-card fade-in">
                        <div style="display:flex;align-items:center;gap:12px;">
                            <div style="width:44px;height:44px;border-radius:12px;background:linear-gradient(135deg,var(--primary),var(--accent));display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:18px;">${f.name.charAt(0)}</div>
                            <div style="flex:1;">
                                <div style="font-size:11px;color:var(--success);font-weight:600;">Face Recognized</div>
                                <div style="font-weight:600;">${f.name}</div>
                                <div style="font-size:12px;color:var(--text-muted);">Student ID: ${f.student_id}</div>
                                <div style="font-size:12px;color:var(--success);">Status: Present &middot; ${(f.confidence * 100).toFixed(1)}% confidence${f.attendance_marked ? '<span style="background:var(--success);color:white;padding:2px 8px;border-radius:10px;font-size:11px;margin-left:6px;">SAVED</span>' : ''}</div>
                            </div>
                        </div>
                    </div>
                `).join('');
            } else if (facesDetected) {
                list.innerHTML = `
                    <div class="stat-card fade-in">
                        <div style="display:flex;align-items:center;gap:12px;">
                            <div style="width:44px;height:44px;border-radius:12px;background:linear-gradient(135deg,#f59e0b,#ef4444);display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:18px;">?</div>
                            <div style="flex:1;">
                                <div style="font-size:11px;color:#f59e0b;font-weight:600;">Face Detected</div>
                                <div style="font-weight:600;">Unknown</div>
                                <div style="font-size:12px;color:var(--text-muted);">No matching student</div>
                            </div>
                        </div>
                    </div>`;
            } else {
                list.innerHTML = emptyState();
            }
        };

        const stopCamera = async () => {
            if (!cameraRunning) return;
            camLog('Stopping');
            clearInterval(frameInterval);
            frameInterval = null;
            clearInterval(recognitionPoll);
            recognitionPoll = null;
            cameraRunning = false;
            try {
                await apiFetch('/recognition/stop', { method: 'POST' });
            } catch (e) {}
            stopBtn.style.display = 'none';
            startBtn.style.display = 'inline-flex';
            startBtn.disabled = false;
            startBtn.innerHTML = '<i class="fas fa-play"></i> Start Camera';
            videoFeed.src = '';
            setStatus('Camera Stopped', false);
            renderRecognized([], false);
            this.toast('Recognition stopped.', 'info');
        };

        startBtn.addEventListener('click', async () => {
            startBtn.disabled = true;
            startBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting...';
            try {
                camLog('Starting');
                const res = await apiFetch('/recognition/start', { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    cameraRunning = true;
                    camLog('Stream active');
                    startBtn.style.display = 'none';
                    stopBtn.style.display = 'inline-flex';
                    setStatus('Face Recognition Active', true);
                    this.toast('Recognition started!', 'success');

                    // Frame-processing loop: keeps requesting the MJPEG feed
                    // while the camera is running. Face detection / recognition
                    // never clears this interval.
                    if (frameInterval) clearInterval(frameInterval);
                    frameInterval = setInterval(() => {
                        if (!cameraRunning) return;
                        videoFeed.src = `/recognition/video_feed?t=${Date.now()}`;
                    }, 100);
                    camLog('Frame processing started');

                    if (recognitionPoll) clearInterval(recognitionPoll);
                    recognitionPoll = setInterval(async () => {
                        if (!cameraRunning) return;
                        try {
                            const r = await apiFetch('/recognition/recognized');
                            const data = await r.json();
                            // New shape: {running, faces_detected, recognized}.
                            // Also tolerate the old bare-list shape.
                            const faces = data && Array.isArray(data.recognized)
                                ? data.recognized
                                : (Array.isArray(data) ? data : []);
                            const facesDetected = data && typeof data === 'object' && !Array.isArray(data)
                                ? !!data.faces_detected
                                : false;
                            if (faces.length) {
                                camLog('Face recognized:', faces[0].student_id);
                                if (faces[0].attendance_marked) {
                                    camLog('[ATTENDANCE] Attendance submitted');
                                }
                            }
                            renderRecognized(faces, facesDetected);
                            camLog('Continuing after recognition');
                        } catch (e) {}
                    }, 2000);
                } else {
                    this.toast(data.message, 'danger');
                    startBtn.disabled = false;
                    startBtn.innerHTML = '<i class="fas fa-play"></i> Start Camera';
                }
            } catch (e) {
                this.toast('Failed to start camera.', 'danger');
                startBtn.disabled = false;
                startBtn.innerHTML = '<i class="fas fa-play"></i> Start Camera';
            }
        });

        stopBtn.addEventListener('click', stopCamera);

        // Cleanup when the page is closed / navigated away so the backend
        // camera is released. keepalive lets the request finish during unload.
        window.addEventListener('pagehide', () => {
            if (!cameraRunning) return;
            const meta = document.querySelector('meta[name="csrf-token"]');
            const token = meta ? meta.content : '';
            camLog('Stopping (page closed)');
            fetch('/recognition/stop', {
                method: 'POST',
                headers: token ? { 'X-CSRFToken': token } : {},
                keepalive: true,
            }).catch(() => {});
        });
    },

    // ==================== REPORTS ====================
    initReports() {
        const typeSelect = document.getElementById('report-type');
        const dateInput = document.getElementById('report-date');
        const deptSelect = document.getElementById('report-dept');
        const generateBtn = document.getElementById('generate-report');
        const tbody = document.querySelector('#report-table tbody');

        const loadReport = async () => {
            if (!tbody) return;
            const params = new URLSearchParams({
                type: typeSelect.value,
                date: dateInput.value,
                department: deptSelect.value,
            });
            const res = await apiFetch(`/reports/api/data?${params}`);
            const data = await res.json();

            tbody.innerHTML = data.records.map(r => `
                <tr>
                    <td>${r.student_id}</td>
                    <td>${r.name}</td>
                    <td>${r.department}</td>
                    <td>${r.date || '-'}</td>
                    <td>${r.time || '-'}</td>
                    <td><span class="badge badge-${r.status === 'Present' ? 'success' : 'danger'}">${r.status || 'N/A'}</span></td>
                    <td>${r.confidence || 0}%</td>
                </tr>
            `).join('');

            document.getElementById('report-count').textContent = data.records.length;
            if (data.present !== undefined) {
                document.getElementById('report-present').textContent = data.present;
            }
        };

        if (generateBtn) {
            generateBtn.addEventListener('click', loadReport);
        }
        if (typeSelect) typeSelect.addEventListener('change', () => {
            dateInput.type = typeSelect.value === 'monthly' ? 'month' : 'date';
        });

        document.getElementById('export-csv')?.addEventListener('click', () => {
            const params = new URLSearchParams({
                type: typeSelect.value,
                date: dateInput.value,
                department: deptSelect.value,
            });
            window.location.href = `/reports/api/export/csv?${params}`;
        });

        document.getElementById('export-excel')?.addEventListener('click', () => {
            const params = new URLSearchParams({
                type: typeSelect.value,
                date: dateInput.value,
                department: deptSelect.value,
            });
            window.location.href = `/reports/api/export/excel?${params}`;
        });

        document.getElementById('print-report')?.addEventListener('click', () => {
            window.print();
        });

        loadReport();
    },

    // ==================== ANALYTICS ====================
    async initAnalytics() {
        try {
            const overview = await apiFetch('/analytics/api/overview').then(r => r.json());
            document.getElementById('analytics-total').textContent = overview.total_students;
            document.getElementById('analytics-today').textContent = overview.today_attendance;
            document.getElementById('analytics-accuracy').textContent = overview.avg_confidence + '%';
            document.getElementById('analytics-weekly').textContent = overview.weekly_count;
            document.getElementById('analytics-monthly').textContent = overview.monthly_count;

            const [monthly, deptData, daily, accuracy] = await Promise.all([
                apiFetch('/analytics/api/monthly-trend').then(r => r.json()),
                apiFetch('/analytics/api/department-stats').then(r => r.json()),
                apiFetch('/analytics/api/daily-trend').then(r => r.json()),
                apiFetch('/analytics/api/accuracy-trend').then(r => r.json()),
            ]);

            this.createChart('monthlyChart', 'bar', {
                labels: monthly.labels,
                datasets: [
                    { label: 'Present', data: monthly.present, backgroundColor: '#22C55E' },
                    { label: 'Absent', data: monthly.absent, backgroundColor: '#EF4444' },
                ]
            });

            this.createChart('dailyChart', 'line', {
                labels: daily.labels,
                datasets: [{
                    label: 'Attendance Count',
                    data: daily.counts,
                    borderColor: '#3B82F6',
                    backgroundColor: 'rgba(59,130,246,0.1)',
                    fill: true,
                    tension: 0.4,
                }]
            });

            this.createChart('accuracyChart', 'line', {
                labels: accuracy.labels,
                datasets: [{
                    label: 'Accuracy %',
                    data: accuracy.accuracy,
                    borderColor: '#06B6D4',
                    backgroundColor: 'rgba(6,182,212,0.1)',
                    fill: true,
                    tension: 0.4,
                }]
            });

            this.createChart('deptChart', 'doughnut', {
                labels: deptData.departments.map(d => d.department),
                datasets: [{
                    data: deptData.departments.map(d => d.percentage),
                    backgroundColor: ['#2563EB', '#22C55E', '#F59E0B', '#EF4444', '#06B6D4', '#8B5CF6'],
                }]
            });

        } catch (e) {
            console.error('Analytics load error:', e);
        }
    },

    createChart(elementId, type, data) {
        const canvas = document.getElementById(elementId);
        if (!canvas) return;
        const style = getComputedStyle(document.documentElement);
        const textColor = style.getPropertyValue('--text-secondary').trim() || '#CBD5E1';
        const gridColor = style.getPropertyValue('--border-color').trim() || '#334155';
        new Chart(canvas, {
            type,
            data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: textColor, font: { size: 12 } }
                    }
                },
                scales: {
                    x: { ticks: { color: textColor }, grid: { color: gridColor } },
                    y: { ticks: { color: textColor }, grid: { color: gridColor }, beginAtZero: true }
                }
            }
        });
    },

    // ==================== SETTINGS ====================
    async loadSettings() {
        try {
            const res = await apiFetch('/settings/api/info');
            const data = await res.json();
            document.getElementById('app-version').textContent = data.app_version;
            document.getElementById('app-name').textContent = data.app_name;
            document.getElementById('company').textContent = data.company_name;
            document.getElementById('support-email').textContent = data.support_email;
            document.getElementById('dataset-count').textContent = data.dataset_count;
            document.getElementById('model-status').textContent = data.model_exists ? 'Trained' : 'Not Trained';
            document.getElementById('model-status').className = `badge ${data.model_exists ? 'badge-success' : 'badge-warning'}`;
            document.getElementById('db-size').textContent = data.db_size + ' KB';
            document.getElementById('python-ver').textContent = data.python_version;
            document.getElementById('flask-ver').textContent = 'Flask ' + data.flask_version;
            document.getElementById('opencv-ver').textContent = 'OpenCV ' + data.opencv_version;
        } catch (e) {
            console.error('Settings load error:', e);
        }
    },

    // ==================== MODEL TRAINING ====================
    async trainModel() {
        const btn = document.getElementById('train-model-btn');
        const progress = document.getElementById('training-progress');
        const bar = document.getElementById('training-bar');
        const pct = document.getElementById('training-pct');
        const status = document.getElementById('training-status');
        const result = document.getElementById('training-result');

        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Training...';
        progress.style.display = 'block';
        result.style.display = 'none';
        bar.style.width = '0%';
        pct.textContent = '0%';
        status.textContent = 'Initializing training...';

        try {
            const res = await apiFetch('/recognition/train', { method: 'POST' });
            const data = await res.json();

            if (data.success) {
                status.textContent = 'Training in progress...';
                App.toast('Training started!', 'success');

                let attempts = 0;
                const maxAttempts = 120;
                const poll = setInterval(async () => {
                    attempts++;
                    if (attempts >= maxAttempts) {
                        clearInterval(poll);
                        btn.disabled = false;
                        btn.innerHTML = '<i class="fas fa-cogs"></i> Train Model';
                        status.textContent = 'Training timed out';
                        return;
                    }

                    try {
                        const trainRes = await apiFetch('/recognition/training-status');
                        const trainData = await trainRes.json();
                        const prog = trainData.training_progress || 0;

                        if (trainData.model_exists && !trainData.training_in_progress) {
                            clearInterval(poll);
                            bar.style.width = '100%';
                            pct.textContent = '100%';
                            status.textContent = 'Training complete!';
                            result.style.display = 'block';
                            result.className = 'alert alert-success';
                            result.innerHTML = '<i class="fas fa-check-circle"></i> Model trained successfully with ' + trainData.total_students_in_dataset + ' students (' + trainData.total_images + ' images).';
                            btn.disabled = false;
                            btn.innerHTML = '<i class="fas fa-cogs"></i> Retrain Model';
                            App.toast('Training completed successfully!', 'success');
                            App.loadSettings();
                        } else if (trainData.training_in_progress) {
                            bar.style.width = prog + '%';
                            pct.textContent = prog + '%';
                            status.textContent = 'Processing student data... (' + prog + '%)';
                        } else {
                            const est = Math.min(90, attempts * 3);
                            bar.style.width = est + '%';
                            pct.textContent = est + '%';
                            status.textContent = 'Preparing training data... (' + trainData.total_images + ' images found)';
                        }
                    } catch (e) {
                        // still training
                    }
                }, 1500);
            } else {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-cogs"></i> Train Model';
                progress.style.display = 'none';
                result.style.display = 'block';
                result.className = 'alert alert-danger';
                result.innerHTML = '<i class="fas fa-exclamation-circle"></i> ' + data.message;
            }
        } catch (e) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-cogs"></i> Train Model';
            progress.style.display = 'none';
            result.style.display = 'block';
            result.className = 'alert-danger';
            result.innerHTML = '<i class="fas fa-exclamation-circle"></i> Failed to start training.';
        }
    },

    closeModal(id) {
        document.getElementById(id)?.classList.remove('active');
    },

    openModal(id) {
        document.getElementById(id)?.classList.add('active');
    },
};

document.addEventListener('DOMContentLoaded', () => App.init());

document.addEventListener('submit', async (e) => {
    const form = e.target;
    if (form.id === 'edit-form') {
        e.preventDefault();
        const data = {
            student_id: form.student_id.value.trim(),
            name: form.name.value.trim(),
            department: form.department.value,
            year: form.year.value,
            section: form.section.value.trim(),
            email: form.email.value.trim(),
            phone: form.phone.value.trim(),
        };
        const res = await apiFetch('/students/api/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        const result = await res.json();
        if (result.success) {
            App.toast(result.message, 'success');
            App.closeModal('edit-modal');
            App.loadStudents();
        } else {
            App.toast(result.message, 'danger');
        }
    }
});
