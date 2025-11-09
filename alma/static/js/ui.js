/**
 * UI/UX enhancements
 * Toast notifications, loading states, and user feedback
 */

// Toast notification system
class ToastManager {
    constructor() {
        this.container = this.createContainer();
        this.toasts = [];
    }

    createContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 10px;
            pointer-events: none;
        `;
        document.body.appendChild(container);
        return container;
    }

    show(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.style.cssText = `
            background: ${this.getBackgroundColor(type)};
            color: white;
            padding: 12px 20px;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            font-size: 14px;
            max-width: 300px;
            word-wrap: break-word;
            pointer-events: auto;
            animation: slideIn 0.3s ease;
            display: flex;
            align-items: center;
            gap: 10px;
        `;

        const icon = this.getIcon(type);
        toast.innerHTML = `
            <span style="font-size: 18px;">${icon}</span>
            <span>${message}</span>
        `;

        this.container.appendChild(toast);
        this.toasts.push(toast);

        // Auto-dismiss
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                this.container.removeChild(toast);
                this.toasts = this.toasts.filter(t => t !== toast);
            }, 300);
        }, duration);
    }

    getBackgroundColor(type) {
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };
        return colors[type] || colors.info;
    }

    getIcon(type) {
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };
        return icons[type] || icons.info;
    }

    success(message, duration) {
        this.show(message, 'success', duration);
    }

    error(message, duration) {
        this.show(message, 'error', duration);
    }

    warning(message, duration) {
        this.show(message, 'warning', duration);
    }

    info(message, duration) {
        this.show(message, 'info', duration);
    }
}

// Global toast instance
window.toast = new ToastManager();

// Add toast animations to stylesheet
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }

    @media (max-width: 768px) {
        #toast-container {
            top: 10px;
            right: 10px;
            left: 10px;
        }

        .toast {
            max-width: 100% !important;
        }
    }
`;
document.head.appendChild(style);

// HTMX event listeners for user feedback
document.addEventListener('DOMContentLoaded', () => {
    // Show success message after successful operations
    document.body.addEventListener('htmx:afterSwap', (event) => {
        const trigger = event.detail.xhr.responseURL;

        // Note created
        if (trigger.includes('/notes') && event.detail.xhr.status === 200) {
            const method = event.detail.requestConfig.verb;
            if (method === 'post') {
                toast.success('Note created successfully');
            } else if (method === 'put') {
                toast.success('Note updated successfully');
            }
        }

        // Project created/updated
        if (trigger.includes('/projects') && event.detail.xhr.status === 200) {
            const method = event.detail.requestConfig.verb;
            if (method === 'post') {
                toast.success('Project created successfully');
            } else if (method === 'put') {
                toast.success('Project updated successfully');
            }
        }
    });

    // Note deleted
    document.body.addEventListener('htmx:afterOnLoad', (event) => {
        if (event.detail.xhr.responseURL.includes('/notes/') &&
            event.detail.requestConfig.verb === 'delete') {
            toast.success('Note deleted successfully');
        }

        if (event.detail.xhr.responseURL.includes('/projects/') &&
            event.detail.requestConfig.verb === 'delete') {
            toast.success('Project deleted successfully');
        }
    });

    // Show error messages
    document.body.addEventListener('htmx:responseError', (event) => {
        const status = event.detail.xhr.status;
        let message = 'An error occurred';

        if (status === 404) {
            message = 'Not found';
        } else if (status === 400) {
            message = 'Invalid request';
        } else if (status === 500) {
            message = 'Server error';
        }

        toast.error(message);
    });

    // Network errors
    document.body.addEventListener('htmx:sendError', () => {
        toast.error('Network error. Please check your connection.');
    });
});

// Auto-save functionality for forms
class AutoSave {
    constructor(formSelector, key, interval = 30000) {
        this.form = document.querySelector(formSelector);
        this.key = key;
        this.interval = interval;
        this.timer = null;

        if (this.form) {
            this.init();
        }
    }

    init() {
        // Load saved draft on page load
        this.loadDraft();

        // Listen for input changes
        this.form.addEventListener('input', () => {
            this.scheduleAutoSave();
            this.showUnsavedIndicator();
        });

        // Clear draft on successful submit
        this.form.addEventListener('htmx:afterSwap', () => {
            this.clearDraft();
            this.hideUnsavedIndicator();
        });
    }

    scheduleAutoSave() {
        clearTimeout(this.timer);
        this.timer = setTimeout(() => {
            this.saveDraft();
        }, this.interval);
    }

    saveDraft() {
        const formData = new FormData(this.form);
        const data = {};
        formData.forEach((value, key) => {
            data[key] = value;
        });

        localStorage.setItem(this.key, JSON.stringify({
            data: data,
            timestamp: Date.now()
        }));

        this.showSavedIndicator();
    }

    loadDraft() {
        const saved = localStorage.getItem(this.key);
        if (!saved) return;

        try {
            const { data, timestamp } = JSON.parse(saved);

            // Only restore if less than 24 hours old
            const age = Date.now() - timestamp;
            if (age > 24 * 60 * 60 * 1000) {
                this.clearDraft();
                return;
            }

            // Ask user if they want to restore
            if (confirm('Restore unsaved draft?')) {
                Object.entries(data).forEach(([key, value]) => {
                    const field = this.form.querySelector(`[name="${key}"]`);
                    if (field) {
                        field.value = value;
                    }
                });
                toast.info('Draft restored');
            } else {
                this.clearDraft();
            }
        } catch (e) {
            console.error('Failed to load draft:', e);
            this.clearDraft();
        }
    }

    clearDraft() {
        localStorage.removeItem(this.key);
    }

    showUnsavedIndicator() {
        let indicator = document.getElementById('unsaved-indicator');
        if (!indicator) {
            indicator = document.createElement('span');
            indicator.id = 'unsaved-indicator';
            indicator.textContent = ' • Unsaved changes';
            indicator.style.color = 'var(--color-unsaved, #ef4444)';
            indicator.style.fontSize = '12px';
            indicator.style.marginLeft = '8px';

            const submitButton = this.form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.parentNode.insertBefore(indicator, submitButton);
            }
        }
    }

    hideUnsavedIndicator() {
        const indicator = document.getElementById('unsaved-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    showSavedIndicator() {
        let indicator = document.getElementById('saved-indicator');
        if (!indicator) {
            indicator = document.createElement('span');
            indicator.id = 'saved-indicator';
            indicator.textContent = '✓ Draft saved';
            indicator.style.color = 'var(--color-saved, #6b7280)';
            indicator.style.fontSize = '11px';
            indicator.style.marginLeft = '8px';
            indicator.style.opacity = '0';
            indicator.style.transition = 'opacity 0.3s';

            const submitButton = this.form.querySelector('button[type="submit"]');
            if (submitButton && submitButton.parentNode) {
                submitButton.parentNode.insertBefore(indicator, submitButton);
            }
        }

        // Flash the indicator
        indicator.style.opacity = '1';
        setTimeout(() => {
            indicator.style.opacity = '0';
        }, 2000);
    }
}

// Initialize auto-save for note form
document.addEventListener('DOMContentLoaded', () => {
    new AutoSave('form[hx-post="/notes"]', 'note-draft', 30000);
});

// Empty state improvements
document.addEventListener('DOMContentLoaded', () => {
    const notesList = document.getElementById('notes-list');
    if (notesList && notesList.children.length === 0) {
        notesList.innerHTML = `
            <div class="empty-state" style="
                text-align: center;
                padding: 60px 20px;
                color: var(--text-tertiary, #6b7280);
            ">
                <div style="font-size: 48px; margin-bottom: 16px;">📝</div>
                <h3 style="margin-bottom: 8px; color: var(--text-secondary, #374151);">
                    No notes yet
                </h3>
                <p style="margin-bottom: 20px;">
                    Create your first note to get started
                </p>
                <p style="font-size: 12px;">
                    Tip: Press <kbd>⌘N</kbd> or <kbd>Ctrl+N</kbd> to focus the form
                </p>
            </div>
        `;
    }
});
