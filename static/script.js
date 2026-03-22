document.addEventListener('DOMContentLoaded', () => {
    // Animate analytics bars
    document.querySelectorAll('.bar-fill[data-width]').forEach(bar => {
        const width = bar.getAttribute('data-width');
        setTimeout(() => {
            bar.style.width = width + '%';
        }, 300);
    });

    // Format AI Reports
    document.querySelectorAll('.ai-summary').forEach(summary => {
        const text = summary.textContent.trim();
        
        if (text.includes('Transcription:') || text.includes('Category:')) {
            const lines = text.split('\n').filter(line => line.trim());
            let html = '<div class="ai-report-content">';
            
            lines.forEach(line => {
                line = line.trim();
                const parts = line.split(':');
                if (parts.length >= 2) {
                    const label = parts[0].trim();
                    const value = parts.slice(1).join(':').trim();
                    
                    if (label === 'Category') {
                        const cleanCategory = value.replace(/[\[\]]/g, '');
                        html += `<div class="ai-field"><span class="ai-label">${label}:</span><span class="ai-category">${cleanCategory}</span></div>`;
                    } else if (label === 'Transcription' || label === 'Summary' || label === 'Sentiment' || label === 'Priority') {
                        html += `<div class="ai-field"><span class="ai-label">${label}:</span><span class="ai-value">${value}</span></div>`;
                    } else {
                        html += `<div class="ai-field"><span class="ai-value">${line}</span></div>`;
                    }
                } else {
                    html += `<div class="ai-field"><span class="ai-value">${line}</span></div>`;
                }
            });
            
            html += '</div>';
            summary.innerHTML = html;
        }
    });

    // Search Filtering
    const searchInput = document.getElementById('globalSearch');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase().trim();
            document.querySelectorAll('.grievance-item').forEach(item => {
                const id = item.dataset.id.toLowerCase();
                const status = item.dataset.status.toLowerCase();
                const content = item.dataset.content.toLowerCase();
                
                const matches = id.includes(searchTerm) || 
                               status.includes(searchTerm) || 
                               content.includes(searchTerm);
                
                item.style.display = matches ? 'block' : 'none';
            });
        });
    }

    // Audio Player Logic
    document.querySelectorAll('.audio-player').forEach(player => {
        const playBtn = player.querySelector('.play-btn');
        const playIcon = player.querySelector('.play-icon');
        const pauseIcon = player.querySelector('.pause-icon');
        const progressBar = player.querySelector('.progress-bar');
        const progressContainer = player.querySelector('.audio-progress');
        const audio = player.querySelector('audio');
        
        if (!audio) return;

        playBtn.addEventListener('click', () => {
            if (!audio.paused) {
                audio.pause();
                playIcon.style.display = 'block';
                pauseIcon.style.display = 'none';
            } else {
                document.querySelectorAll('audio').forEach(a => {
                    if (a !== audio) {
                        a.pause();
                        const otherPlayer = a.closest('.audio-player');
                        if (otherPlayer) {
                            otherPlayer.querySelector('.play-icon').style.display = 'block';
                            otherPlayer.querySelector('.pause-icon').style.display = 'none';
                        }
                    }
                });
                
                audio.play();
                playIcon.style.display = 'none';
                pauseIcon.style.display = 'block';
            }
        });
        
        audio.addEventListener('timeupdate', () => {
            const progress = (audio.currentTime / audio.duration) * 100;
            progressBar.style.width = `${progress}%`;
        });
        
        audio.addEventListener('ended', () => {
            playIcon.style.display = 'block';
            pauseIcon.style.display = 'none';
            progressBar.style.width = '0%';
        });
        
        progressContainer.addEventListener('click', (e) => {
            const rect = progressContainer.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const percentage = clickX / rect.width;
            if (audio.duration) {
                audio.currentTime = percentage * audio.duration;
            }
        });
    });

    // Copy Hash Logic
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const hash = btn.dataset.hash;
            navigator.clipboard.writeText(hash).then(() => {
                const originalText = btn.textContent;
                btn.textContent = 'Verified & Copied';
                btn.classList.add('active');
                
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.classList.remove('active');
                }, 2000);
            });
        });
    });

    // Status Update Logic
    document.querySelectorAll('.save-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const gId = btn.dataset.id;
            const select = document.querySelector(`.status-select[data-id="${gId}"]`);
            const newStatus = select.value;
            const originalText = btn.textContent;
            
            btn.disabled = true;
            btn.textContent = 'Updating...';
            
            try {
                const formData = new FormData();
                formData.append('g_id', gId);
                formData.append('new_status', newStatus);
                
                const response = await fetch('/update_status', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    const item = btn.closest('.grievance-item');
                    const badge = item.querySelector('.status-badge');
                    badge.textContent = newStatus;
                    item.dataset.status = newStatus;
                    
                    btn.textContent = 'CONFIRMED';
                    btn.style.background = '#000';
                    btn.style.color = '#fff';
                    btn.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
                    
                    setTimeout(() => {
                        btn.textContent = originalText;
                        btn.disabled = false;
                        btn.style.background = '';
                        btn.style.color = '';
                        btn.style.boxShadow = '';
                    }, 2000);
                } else {
                    throw new Error('Failed to update');
                }
            } catch (error) {
                console.error('Error:', error);
                btn.textContent = 'SYSTEM ERROR';
                btn.style.background = '#444';
                btn.style.color = '#fff';
                btn.style.borderColor = '#000';
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.disabled = false;
                    btn.style.background = '';
                    btn.style.color = '';
                    btn.style.borderColor = '';
                }, 2000);
            }
        });
    });
});
