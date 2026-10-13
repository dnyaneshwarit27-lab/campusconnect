/**
 * CampusConnect Interactive Client Script
 * Includes Audio feedback synthesizer, Copy Helpers, and Scanner utilities
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize Bootstrap tooltips if any
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map((tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl));

    // Clipboard copy buttons
    document.querySelectorAll('[data-copy-target]').forEach(button => {
        button.addEventListener('click', () => {
            const textToCopy = button.getAttribute('data-copy-target');
            if (textToCopy) {
                navigator.clipboard.writeText(textToCopy).then(() => {
                    const originalHtml = button.innerHTML;
                    button.innerHTML = '<i class="bi bi-check2"></i> Copied!';
                    button.classList.add('btn-success');
                    setTimeout(() => {
                        button.innerHTML = originalHtml;
                        button.classList.remove('btn-success');
                    }, 2000);
                }).catch(err => {
                    console.error('Copy failed:', err);
                });
            }
        });
    });

    // Smooth scroll for nav links targeting #events-section on current page
    document.querySelectorAll('a[href*="#events-section"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const currentPath = window.location.pathname;
            const targetUrl = new URL(this.href, window.location.origin);
            if (targetUrl.pathname === currentPath && targetUrl.search === window.location.search) {
                const targetEl = document.getElementById('events-section');
                if (targetEl) {
                    e.preventDefault();
                    targetEl.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });
});


// Audio Feedback Synthesizer using Web Audio API (Zero external MP3 dependency)
class FeedbackAudio {
    static playSuccess() {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const now = ctx.currentTime;
            
            // Dual chime (High melodious beep)
            const osc1 = ctx.createOscillator();
            const osc2 = ctx.createOscillator();
            const gainNode = ctx.createGain();

            osc1.type = 'sine';
            osc1.frequency.setValueAtTime(587.33, now); // D5
            osc1.frequency.exponentialRampToValueAtTime(880.00, now + 0.15); // A5

            osc2.type = 'triangle';
            osc2.frequency.setValueAtTime(880.00, now + 0.05);
            osc2.frequency.exponentialRampToValueAtTime(1174.66, now + 0.25); // D6

            gainNode.gain.setValueAtTime(0.15, now);
            gainNode.gain.exponentialRampToValueAtTime(0.001, now + 0.35);

            osc1.connect(gainNode);
            osc2.connect(gainNode);
            gainNode.connect(ctx.destination);

            osc1.start(now);
            osc2.start(now + 0.05);
            osc1.stop(now + 0.35);
            osc2.stop(now + 0.35);
        } catch (e) {
            console.warn('AudioContext not allowed without user gesture yet', e);
        }
    }

    static playWarning() {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const now = ctx.currentTime;
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();

            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(320, now);
            osc.frequency.setValueAtTime(260, now + 0.15);

            gain.gain.setValueAtTime(0.2, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.3);

            osc.connect(gain);
            gain.connect(ctx.destination);

            osc.start(now);
            osc.stop(now + 0.3);
        } catch (e) {
            console.warn(e);
        }
    }

    static playError() {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const now = ctx.currentTime;
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();

            osc.type = 'square';
            osc.frequency.setValueAtTime(180, now);
            osc.frequency.setValueAtTime(120, now + 0.12);

            gain.gain.setValueAtTime(0.25, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.35);

            osc.connect(gain);
            gain.connect(ctx.destination);

            osc.start(now);
            osc.stop(now + 0.35);
        } catch (e) {
            console.warn(e);
        }
    }
}
window.FeedbackAudio = FeedbackAudio;
