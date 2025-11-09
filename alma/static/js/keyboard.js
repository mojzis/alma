/**
 * Keyboard shortcuts for the notes app
 * Provides comprehensive keyboard navigation and actions
 */

document.addEventListener('DOMContentLoaded', () => {
    // Track if we're in an input/textarea to avoid conflicts
    function isTyping() {
        const activeElement = document.activeElement;
        return activeElement.tagName === 'INPUT' ||
               activeElement.tagName === 'TEXTAREA' ||
               activeElement.tagName === 'SELECT' ||
               activeElement.isContentEditable;
    }

    // Global keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Cmd/Ctrl + K: Focus search
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[name="q"]');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }

        // Cmd/Ctrl + N: Focus new note form
        if ((e.metaKey || e.ctrlKey) && e.key === 'n') {
            e.preventDefault();
            const contentTextarea = document.querySelector('textarea[name="content"]');
            if (contentTextarea) {
                contentTextarea.focus();
                // Scroll to form on mobile
                contentTextarea.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }

        // Cmd/Ctrl + Enter: Submit form (save note)
        if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
            e.preventDefault();
            // Find the closest form to the active element
            const activeForm = document.activeElement.closest('form');
            if (activeForm) {
                // Trigger HTMX submit or regular submit
                if (activeForm.hasAttribute('hx-post') || activeForm.hasAttribute('hx-put')) {
                    htmx.trigger(activeForm, 'submit');
                } else {
                    activeForm.requestSubmit();
                }
            }
        }

        // Escape: Clear search or cancel edit
        if (e.key === 'Escape') {
            const searchInput = document.querySelector('input[name="q"]');
            if (searchInput && searchInput.value) {
                searchInput.value = '';
                searchInput.dispatchEvent(new Event('input', { bubbles: true }));
            } else if (isTyping()) {
                // Blur active input
                document.activeElement.blur();
            }
        }

        // Question mark: Show keyboard shortcuts help (future enhancement)
        if (e.key === '?' && !isTyping()) {
            e.preventDefault();
            showKeyboardHelp();
        }

        // Arrow navigation in note list (when not typing)
        if (!isTyping()) {
            const notes = Array.from(document.querySelectorAll('.note'));
            const currentIndex = notes.findIndex(note => note.classList.contains('keyboard-focus'));

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                navigateNotes(notes, currentIndex, 1);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                navigateNotes(notes, currentIndex, -1);
            } else if (e.key === 'Enter' && currentIndex >= 0) {
                // Edit focused note
                e.preventDefault();
                const editButton = notes[currentIndex].querySelector('button[hx-get*="/edit"]');
                if (editButton) editButton.click();
            }
        }
    });

    // Navigate through notes with arrow keys
    function navigateNotes(notes, currentIndex, direction) {
        if (notes.length === 0) return;

        // Remove current focus
        if (currentIndex >= 0) {
            notes[currentIndex].classList.remove('keyboard-focus');
        }

        // Calculate new index
        let newIndex = currentIndex + direction;
        if (newIndex < 0) newIndex = 0;
        if (newIndex >= notes.length) newIndex = notes.length - 1;

        // Add focus to new note
        if (notes[newIndex]) {
            notes[newIndex].classList.add('keyboard-focus');
            notes[newIndex].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    // Show keyboard shortcuts help modal
    function showKeyboardHelp() {
        const helpContent = `
            <div class="modal-overlay" onclick="this.remove()">
                <div class="modal-content" onclick="event.stopPropagation()">
                    <h2 style="margin-bottom: 20px;">Keyboard Shortcuts</h2>
                    <div style="display: grid; gap: 12px;">
                        <div style="display: flex; justify-content: space-between;">
                            <span><kbd>⌘ N</kbd> or <kbd>Ctrl N</kbd></span>
                            <span>New note</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span><kbd>⌘ K</kbd> or <kbd>Ctrl K</kbd></span>
                            <span>Focus search</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span><kbd>⌘ Enter</kbd> or <kbd>Ctrl Enter</kbd></span>
                            <span>Save note</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span><kbd>⌘ B</kbd> or <kbd>Ctrl B</kbd></span>
                            <span>Toggle left sidebar</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span><kbd>⌘ /</kbd> or <kbd>Ctrl /</kbd></span>
                            <span>Toggle right sidebar</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span><kbd>↑↓</kbd></span>
                            <span>Navigate notes</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span><kbd>Esc</kbd></span>
                            <span>Clear search / Cancel</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span><kbd>?</kbd></span>
                            <span>Show this help</span>
                        </div>
                    </div>
                    <button onclick="this.closest('.modal-overlay').remove()"
                            style="margin-top: 20px; width: 100%;">
                        Close
                    </button>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', helpContent);
    }

    // Add visual feedback for keyboard focus
    const style = document.createElement('style');
    style.textContent = `
        .keyboard-focus {
            outline: 2px solid var(--color-work, #3b82f6);
            outline-offset: 2px;
        }

        kbd {
            display: inline-block;
            padding: 3px 6px;
            font-family: monospace;
            font-size: 12px;
            background: var(--bg-secondary, #f9fafb);
            border: 1px solid var(--border-medium, #d1d5db);
            border-radius: 4px;
            box-shadow: 0 1px 0 rgba(0, 0, 0, 0.1);
        }
    `;
    document.head.appendChild(style);
});
