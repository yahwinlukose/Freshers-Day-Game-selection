document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('wheelCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const spinBtn = document.getElementById('spinBtn');
    const resultArea = document.getElementById('resultArea');
    const resultText = document.getElementById('resultText');
    const confettiCanvas = document.getElementById('confettiCanvas');

    let currentAngle = 0;
    let isSpinning = false;
    let audioCtx = null;

    let numSegments = window.activePunishments.length;
    let arc = numSegments > 0 ? (Math.PI * 2) / numSegments : 0;

    // Premium color palette
    const COLORS = [
        '#2563EB', '#7C3AED', '#EC4899', '#F59E0B',
        '#22C55E', '#06B6D4', '#EF4444', '#8B5CF6',
        '#14B8A6', '#F97316', '#6366F1', '#10B981',
        '#E11D48', '#0EA5E9', '#A855F7', '#84CC16',
        '#F43F5E', '#3B82F6', '#D946EF', '#FBBF24'
    ];

    function getColor(index) {
        return COLORS[index % COLORS.length];
    }

    function updateWheelData() {
        numSegments = window.activePunishments.length;
        arc = numSegments > 0 ? (Math.PI * 2) / numSegments : 0;
        
        const wrapper = document.getElementById('wheelWrapper');
        const emptyState = document.getElementById('wheelEmptyState');
        
        if (numSegments === 0) {
            wrapper.classList.add('d-none');
            emptyState.classList.remove('d-none');
            // If we just used the last one, display custom message
            if (isSpinning) {
                document.getElementById('emptyStateMsg').textContent = "All punishments have been used.";
            }
        } else {
            wrapper.classList.remove('d-none');
            emptyState.classList.add('d-none');
        }
        
        spinBtn.disabled = numSegments === 0;
        drawWheel();
    }

    function drawWheel() {
        if (!canvas) return;
        const w = canvas.width;
        const h = canvas.height;
        const cx = w / 2;
        const cy = h / 2;
        const radius = Math.min(cx, cy) - 10;

        ctx.clearRect(0, 0, w, h);

        if (numSegments === 0) {
            ctx.fillStyle = '#F3F4F6';
            ctx.beginPath();
            ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
            ctx.fill();
            return;
        }

        for (let i = 0; i < numSegments; i++) {
            const angle = currentAngle + i * arc;

            // Segment
            ctx.beginPath();
            ctx.arc(cx, cy, radius, angle, angle + arc, false);
            ctx.lineTo(cx, cy);
            ctx.fillStyle = getColor(i);
            ctx.fill();

            // Separator line
            ctx.strokeStyle = 'rgba(255,255,255,0.3)';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.lineTo(
                cx + Math.cos(angle) * radius,
                cy + Math.sin(angle) * radius
            );
            ctx.stroke();

            // Text
            ctx.save();
            const textAngle = angle + arc / 2;
            const textRadius = radius * 0.65;
            ctx.translate(
                cx + Math.cos(textAngle) * textRadius,
                cy + Math.sin(textAngle) * textRadius
            );
            ctx.rotate(textAngle);

            const text = window.activePunishments[i].text;
            const maxLen = numSegments > 12 ? 12 : (numSegments > 6 ? 18 : 24);
            const dispText = text.length > maxLen ? text.substring(0, maxLen - 1) + '…' : text;

            ctx.fillStyle = '#fff';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.font = `bold ${numSegments > 10 ? 11 : 14}px Poppins, sans-serif`;
            ctx.shadowColor = 'rgba(0,0,0,0.3)';
            ctx.shadowBlur = 3;
            ctx.fillText(dispText, 0, 0);
            ctx.restore();
        }

        // Center circle
        ctx.beginPath();
        ctx.arc(cx, cy, 38, 0, 2 * Math.PI);
        ctx.fillStyle = '#fff';
        ctx.shadowColor = 'rgba(0,0,0,0.1)';
        ctx.shadowBlur = 10;
        ctx.fill();
        ctx.shadowBlur = 0;
    }

    drawWheel();
    updateWheelData(); // Set initial button state & visibility

    // Audio
    function initAudio() {
        if (!audioCtx) {
            const AC = window.AudioContext || window.webkitAudioContext;
            audioCtx = new AC();
        }
    }

    function playTick() {
        if (!audioCtx) return;
        try {
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(500 + Math.random() * 200, audioCtx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(150, audioCtx.currentTime + 0.04);
            gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.04);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.04);
        } catch (e) { /* ignore audio errors */ }
    }

    function playCelebration() {
        if (!audioCtx) return;
        const notes = [523.25, 659.25, 783.99, 1046.5]; // C5, E5, G5, C6
        notes.forEach((freq, i) => {
            setTimeout(() => {
                try {
                    const osc = audioCtx.createOscillator();
                    const gain = audioCtx.createGain();
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
                    gain.gain.setValueAtTime(0.25, audioCtx.currentTime);
                    gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.8);
                    osc.connect(gain);
                    gain.connect(audioCtx.destination);
                    osc.start();
                    osc.stop(audioCtx.currentTime + 0.8);
                } catch (e) { /* ignore */ }
            }, i * 120);
        });
    }

    // Confetti
    function launchConfetti() {
        if (!confettiCanvas) return;
        const cCtx = confettiCanvas.getContext('2d');
        confettiCanvas.width = confettiCanvas.parentElement.offsetWidth;
        confettiCanvas.height = confettiCanvas.parentElement.offsetHeight;

        const particles = [];
        const confettiColors = ['#2563EB', '#7C3AED', '#22C55E', '#F59E0B', '#EF4444', '#EC4899', '#06B6D4', '#8B5CF6'];

        for (let i = 0; i < 120; i++) {
            particles.push({
                x: confettiCanvas.width / 2,
                y: confettiCanvas.height / 2,
                vx: (Math.random() - 0.5) * 16,
                vy: (Math.random() - 0.8) * 14,
                w: Math.random() * 8 + 4,
                h: Math.random() * 6 + 3,
                color: confettiColors[Math.floor(Math.random() * confettiColors.length)],
                rotation: Math.random() * 360,
                rotSpeed: (Math.random() - 0.5) * 12,
                gravity: 0.15 + Math.random() * 0.1,
                opacity: 1,
                decay: 0.008 + Math.random() * 0.005,
            });
        }

        let frame = 0;
        const maxFrames = 180;

        function animate() {
            if (frame >= maxFrames) {
                cCtx.clearRect(0, 0, confettiCanvas.width, confettiCanvas.height);
                return;
            }
            cCtx.clearRect(0, 0, confettiCanvas.width, confettiCanvas.height);
            particles.forEach(p => {
                p.x += p.vx;
                p.vy += p.gravity;
                p.y += p.vy;
                p.rotation += p.rotSpeed;
                p.opacity -= p.decay;
                if (p.opacity <= 0) return;

                cCtx.save();
                cCtx.globalAlpha = Math.max(0, p.opacity);
                cCtx.translate(p.x, p.y);
                cCtx.rotate((p.rotation * Math.PI) / 180);
                cCtx.fillStyle = p.color;
                cCtx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
                cCtx.restore();
            });
            frame++;
            requestAnimationFrame(animate);
        }
        animate();
    }

    // Easing: easeOutQuart
    function easeOut(t, b, c, d) {
        t /= d;
        t--;
        return -c * (t * t * t * t - 1) + b;
    }

    if (spinBtn) {
        spinBtn.addEventListener('click', () => {
            if (isSpinning || numSegments === 0) return;
            initAudio();
            isSpinning = true;
            spinBtn.disabled = true;
            resultArea.classList.add('d-none');
            canvas.classList.add('spinning');

            const spinTimeTotal = Math.random() * 2000 + 4000;
            let spinTime = 0;
            const startAngle = currentAngle;
            const spinAngleTotal = (Math.random() * 5 + 5) * 2 * Math.PI;
            let lastTickAngle = currentAngle;

            function rotateWheel() {
                spinTime += 16;
                if (spinTime >= spinTimeTotal) {
                    stopRotateWheel();
                    return;
                }
                const newAngle = easeOut(spinTime, startAngle, spinAngleTotal, spinTimeTotal);

                const prevSeg = Math.floor((-lastTickAngle) / arc) % numSegments;
                const currSeg = Math.floor((-newAngle) / arc) % numSegments;
                if (prevSeg !== currSeg) {
                    playTick();
                }
                lastTickAngle = newAngle;
                currentAngle = newAngle;
                drawWheel();
                requestAnimationFrame(rotateWheel);
            }

            rotateWheel();
        });
    }

    function stopRotateWheel() {
        canvas.classList.remove('spinning');
        const normalizedAngle = ((currentAngle % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);
        const pointerAngle = (3 * Math.PI) / 2;

        let winningIndex = 0;

        for (let i = 0; i < numSegments; i++) {
            let start = (normalizedAngle + i * arc) % (2 * Math.PI);
            let end = (start + arc) % (2 * Math.PI);

            if (start > end) {
                if (pointerAngle >= start || pointerAngle <= end) {
                    winningIndex = i;
                    break;
                }
            } else {
                if (pointerAngle >= start && pointerAngle <= end) {
                    winningIndex = i;
                    break;
                }
            }
        }

        const winner = window.activePunishments[winningIndex];

        playCelebration();
        launchConfetti();

        resultText.textContent = winner.text;
        resultArea.classList.remove('d-none');

        // Post to server using AJAX
        const formData = new FormData();
        formData.append('punishment_id', winner.id);
        formData.append('csrf_token', csrfToken);

        fetch(spinUrl, {
            method: 'POST',
            body: formData,
            headers: { 'Accept': 'application/json' }
        })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    applyStateUpdate(data);
                } else if (data.error) {
                    console.error(data.error);
                }
            })
            .catch(err => console.error(err))
            .finally(() => {
                isSpinning = false;
                // If there are still segments, re-enable the button
                if (window.activePunishments.length > 0) {
                    spinBtn.disabled = false;
                }
            });
    }

    // ==========================================
    // UI UPDATE LOGIC (AJAX)
    // ==========================================
    
    function applyStateUpdate(state) {
        if (!state || !state.stats) return;
        
        // 1. Update stats
        document.getElementById('totalCount').textContent = state.stats.total;
        document.getElementById('activeCount').textContent = state.stats.active;
        document.getElementById('usedCount').textContent = state.stats.used;
        
        // 2. Update wheel
        window.activePunishments = state.active_punishments;
        updateWheelData();
        
        // 3. Update history list
        const historyList = document.getElementById('historyList');
        if (state.history.length === 0) {
            historyList.innerHTML = `
                <li class="list-group-item text-center py-5" style="color: var(--text-muted);">
                    <i class="bi bi-clock" style="font-size: 1.5rem; opacity: 0.4;"></i>
                    <p class="mt-2 mb-0" style="font-size: 0.85rem;">No spins yet.</p>
                </li>
            `;
        } else {
            historyList.innerHTML = state.history.map(h => `
                <li class="list-group-item d-flex align-items-start gap-3" style="border-color: var(--border-light);">
                    <div style="width: 36px; height: 36px; border-radius: 50%; background: var(--secondary-light); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <i class="bi bi-lightning-fill" style="color: var(--secondary); font-size: 0.9rem;"></i>
                    </div>
                    <div>
                        <div class="fw-bold" style="font-size: 0.85rem; color: var(--text-primary);">${escapeHtml(h.text)}</div>
                        <small style="color: var(--text-muted);">${h.spun_at}</small>
                    </div>
                </li>
            `).join('');
        }
        
        // 4. Update punishments table
        const tbody = document.getElementById('punishmentsTableBody');
        if (state.punishments.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center py-5" style="color: var(--text-muted);">
                        <i class="bi bi-inbox" style="font-size: 1.5rem; opacity: 0.4;"></i>
                        <p class="mt-2 mb-0">No punishments found. Add some above!</p>
                    </td>
                </tr>
            `;
        } else {
            tbody.innerHTML = state.punishments.map(p => `
                <tr>
                    <td style="color: var(--text-muted); font-size: 0.8rem;">#${p.id}</td>
                    <td class="fw-bold" style="color: var(--text-primary);">${escapeHtml(p.text)}</td>
                    <td>
                        ${p.is_active 
                            ? '<span class="badge bg-success">🟢 Active</span>'
                            : '<span class="badge bg-secondary" style="background: var(--border-light) !important; color: var(--text-muted) !important;">⚪ Used</span>'}
                    </td>
                    <td style="color: var(--text-muted); font-size: 0.85rem;">${p.created_at}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" data-action="edit" data-id="${p.id}" data-text="${escapeHtml(p.text)}"><i class="bi bi-pencil"></i></button>
                        <button class="btn btn-sm btn-outline-danger" data-action="delete" data-id="${p.id}" data-text="${escapeHtml(p.text)}"><i class="bi bi-trash"></i></button>
                    </td>
                </tr>
            `).join('');
        }
        
        // Hide any open bootstrap modals
        const openModal = document.querySelector('.modal.show');
        if (openModal) {
            const modalInstance = bootstrap.Modal.getInstance(openModal);
            if (modalInstance) {
                modalInstance.hide();
            }
        }
    }
    
    function escapeHtml(unsafe) {
        return (unsafe || '').toString()
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
    }

    function showToast(message, type = 'success') {
        const toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) return;
        
        const toastId = 'toast' + Date.now();
        const icon = type === 'success' ? 'check-circle' : 'exclamation-triangle';
        const bgColor = type === 'success' ? 'bg-success' : 'bg-danger';
        
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-white ${bgColor} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="bi bi-${icon} me-2"></i> ${escapeHtml(message)}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
        toast.show();
        
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }

    // Event Delegation for Edit and Delete buttons
    document.body.addEventListener('click', function(e) {
        const editBtn = e.target.closest('button[data-action="edit"]');
        const deleteBtn = e.target.closest('button[data-action="delete"]');
        
        if (editBtn) {
            const id = editBtn.getAttribute('data-id');
            const text = editBtn.getAttribute('data-text');
            document.getElementById('globalEditForm').action = '/punishment/edit/' + id;
            document.getElementById('editModalInput').value = text;
            const modal = new bootstrap.Modal(document.getElementById('globalEditModal'));
            modal.show();
        } else if (deleteBtn) {
            const id = deleteBtn.getAttribute('data-id');
            const text = deleteBtn.getAttribute('data-text');
            document.getElementById('globalDeleteForm').action = '/punishment/delete/' + id;
            document.getElementById('deleteModalText').textContent = '"' + text + '"';
            const modal = new bootstrap.Modal(document.getElementById('globalDeleteModal'));
            modal.show();
        }
    });

    // Intercept form submissions for AJAX
    document.body.addEventListener('submit', function(e) {
        const form = e.target;
        if (form.id === 'addForm' || form.id === 'resetForm' || form.classList.contains('ajax-form')) {
            e.preventDefault();
            
            const formData = new FormData(form);
            fetch(form.action, {
                method: form.method || 'POST',
                body: formData,
                headers: { 'Accept': 'application/json' }
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    showToast(data.error, 'danger');
                } else {
                    let successMessage = "Action completed successfully.";
                    if (form.id === 'addForm') {
                        successMessage = "Punishment added successfully.";
                        form.reset(); // clear input
                    } else if (form.id === 'globalEditForm') {
                        successMessage = "Punishment updated successfully.";
                    } else if (form.id === 'globalDeleteForm') {
                        successMessage = "Punishment deleted permanently.";
                    } else if (form.id === 'resetForm') {
                        successMessage = "Wheel reset successfully! All punishments deleted.";
                    }
                    
                    showToast(successMessage, 'success');
                    applyStateUpdate(data);
                    
                    if (form.id === 'resetForm') {
                        // Clear the result area on reset
                        resultArea.classList.add('d-none');
                        // And manually clear the empty state message
                        document.getElementById('emptyStateMsg').textContent = "No punishments available.";
                    }
                }
            })
            .catch(err => console.error(err));
        }
    });

    // NOTE: filterForm uses GET and we don't strictly need to AJAX it if user doesn't require,
    // but we can do it if desired. The prompt specifically requested Add, Edit, Delete, Reset, Spin.
});
