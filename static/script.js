document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.bar-fill[data-width]').forEach(bar => {
        const width = bar.getAttribute('data-width');
        bar.style.width = width + '%';
    });

    document.querySelectorAll('.ai-summary').forEach(summary => {
        let text = summary.textContent.trim();
        
        if (text.includes('Transcription:') || text.includes('Category:')) {
            const lines = text.split('\n').filter(line => line.trim());
            let html = '';
            
            lines.forEach(line => {
                line = line.trim();
                if (line.startsWith('Transcription:')) {
                    const value = line.replace('Transcription:', '').trim();
                    html += `<div class="ai-field"><span class="ai-label">Transcription:</span><span class="ai-value">${value}</span></div>`;
                } else if (line.startsWith('Category:')) {
                    const value = line.replace('Category:', '').trim();
                    const match = value.match(/\[(.*?)\]/);
                    const category = match ? match[1] : value;
                    html += `<div class="ai-field"><span class="ai-label">Category:</span><span class="ai-category">${category}</span></div>`;
                } else if (line.startsWith('Summary:')) {
                    const value = line.replace('Summary:', '').trim();
                    html += `<div class="ai-field"><span class="ai-label">Summary:</span><span class="ai-value">${value}</span></div>`;
                } else if (line.startsWith('Sentiment:')) {
                    const value = line.replace('Sentiment:', '').trim();
                    html += `<div class="ai-field"><span class="ai-label">Sentiment:</span><span class="ai-value">${value}</span></div>`;
                } else if (line.startsWith('Priority:')) {
                    const value = line.replace('Priority:', '').trim();
                    html += `<div class="ai-field"><span class="ai-label">Priority:</span><span class="ai-value">${value}</span></div>`;
                } else if (line.length > 0) {
                    html += `<div class="ai-field"><span class="ai-value">${line}</span></div>`;
                }
            });
            
            summary.innerHTML = html;
        } else {
            summary.innerHTML = `<div class="ai-value">${text}</div>`;
        }
    });
});

const searchInput = document.getElementById('globalSearch');
const grievanceItems = document.querySelectorAll('.grievance-item');

searchInput.addEventListener('input', (e) => {
    const searchTerm = e.target.value.toLowerCase().trim();
    
    grievanceItems.forEach(item => {
        const id = item.dataset.id.toLowerCase();
        const status = item.dataset.status.toLowerCase();
        const content = item.dataset.content.toLowerCase();
        
        const matches = id.includes(searchTerm) || 
                       status.includes(searchTerm) || 
                       content.includes(searchTerm);
        
        item.classList.toggle('hidden', !matches);
    });
});

document.querySelectorAll('.audio-player').forEach(player => {
    const playBtn = player.querySelector('.play-btn');
    const playIcon = player.querySelector('.play-icon');
    const pauseIcon = player.querySelector('.pause-icon');
    const progressBar = player.querySelector('.progress-bar');
    const progressContainer = player.querySelector('.audio-progress');
    const audio = player.querySelector('audio');
    
    let isPlaying = false;
    
    playBtn.addEventListener('click', () => {
        if (isPlaying) {
            audio.pause();
            playIcon.style.display = 'block';
            pauseIcon.style.display = 'none';
            isPlaying = false;
        } else {
            document.querySelectorAll('audio').forEach(a => {
                if (a !== audio) a.pause();
            });
            document.querySelectorAll('.play-icon').forEach(icon => icon.style.display = 'block');
            document.querySelectorAll('.pause-icon').forEach(icon => icon.style.display = 'none');
            
            audio.play();
            playIcon.style.display = 'none';
            pauseIcon.style.display = 'block';
            isPlaying = true;
        }
    });
    
    audio.addEventListener('timeupdate', () => {
        const progress = (audio.currentTime / audio.duration) * 100;
        progressBar.style.width = `${progress}%`;
    });
    
    audio.addEventListener('ended', () => {
        playIcon.style.display = 'block';
        pauseIcon.style.display = 'none';
        isPlaying = false;
        progressBar.style.width = '0%';
    });
    
    progressContainer.addEventListener('click', (e) => {
        const rect = progressContainer.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const percentage = clickX / rect.width;
        audio.currentTime = percentage * audio.duration;
    });
});

document.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const hash = btn.dataset.hash;
        
        navigator.clipboard.writeText(hash).then(() => {
            const originalText = btn.textContent;
            btn.textContent = 'Copied!';
            btn.classList.add('copied');
            
            setTimeout(() => {
                btn.textContent = originalText;
                btn.classList.remove('copied');
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy:', err);
        });
    });
});

document.querySelectorAll('.save-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
        const gId = btn.dataset.id;
        const select = document.querySelector(`.status-select[data-id="${gId}"]`);
        const newStatus = select.value;
        
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
                badge.className = `status-badge status-${newStatus.toLowerCase()}`;
                
                item.dataset.status = newStatus;
                
                const originalText = btn.textContent;
                btn.textContent = 'Saved!';
                btn.style.background = '#10b981';
                
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.style.background = '';
                }, 2000);
            } else {
                alert('Failed to update status');
            }
        } catch (error) {
            console.error('Error updating status:', error);
            alert('Error updating status');
        }
    });
});
