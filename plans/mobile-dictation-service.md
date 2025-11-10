# Mobile Dictation Service Implementation Plan

## Overview
Add voice dictation capability to the Alma note-taking app, optimized for mobile Safari and other modern browsers.

## Context & Research

### Mobile Safari Support Status (2025)
- **Web Speech API** is supported in Safari 14.1+ (iOS 14.5+)
- Requires `webkit` prefix: `webkitSpeechRecognition`
- User must enable **Dictation** in iOS Settings > General > Keyboard
- Known limitations:
  - PWA mode may have restrictions
  - Event handling requires careful implementation
  - Mobile WebView has limited support

### Current Alma Architecture
- **Frontend**: HTMX + Alpine.js + TipTap editor
- **Backend**: FastAPI (Python)
- **Key Integration Points**:
  - Note form textarea (`alma/templates/partials/note-form.html`)
  - TipTap WYSIWYG editor (`alma/templates/editor.html`)
  - Existing Alpine.js state management

## Recommended Approach

**Use Web Speech API** with progressive enhancement:
1. Feature detection and graceful degradation
2. Clear user feedback when unavailable
3. Works in both textarea and TipTap editor
4. No server costs, respects privacy

## Implementation Plan

### Phase 1: Core Dictation Component (2-3 hours)

#### 1.1 Create Dictation Service Module
**File**: `alma/static/js/dictation.js`

```javascript
// Dictation service with browser compatibility
class DictationService {
  constructor() {
    this.recognition = null;
    this.isSupported = false;
    this.isListening = false;
    this.onResult = null;
    this.onError = null;
    this.onEnd = null;

    this.init();
  }

  init() {
    // Check for Web Speech API support
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      this.isSupported = false;
      return;
    }

    this.isSupported = true;
    this.recognition = new SpeechRecognition();

    // Configuration
    this.recognition.continuous = true;  // Keep listening
    this.recognition.interimResults = true;  // Show partial results
    this.recognition.lang = 'en-US';  // Default language

    // Event handlers
    this.recognition.onresult = (event) => {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript + ' ';
        } else {
          interimTranscript += transcript;
        }
      }

      if (this.onResult) {
        this.onResult(finalTranscript, interimTranscript);
      }
    };

    this.recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      this.isListening = false;

      if (this.onError) {
        this.onError(event.error);
      }
    };

    this.recognition.onend = () => {
      this.isListening = false;

      if (this.onEnd) {
        this.onEnd();
      }
    };
  }

  start() {
    if (!this.isSupported || this.isListening) {
      return false;
    }

    try {
      this.recognition.start();
      this.isListening = true;
      return true;
    } catch (e) {
      console.error('Failed to start recognition:', e);
      return false;
    }
  }

  stop() {
    if (!this.isSupported || !this.isListening) {
      return;
    }

    this.recognition.stop();
    this.isListening = false;
  }

  setLanguage(lang) {
    if (this.recognition) {
      this.recognition.lang = lang;
    }
  }
}

// Export singleton instance
window.dictationService = new DictationService();
```

#### 1.2 Create Dictation Button Component
**File**: `alma/templates/partials/dictation-button.html`

```html
<!-- Dictation button component -->
<div x-data="dictationButton()" class="dictation-button-wrapper">
  <button
    type="button"
    @click="toggleDictation()"
    :disabled="!isSupported"
    :class="{
      'dictation-active': isListening,
      'dictation-inactive': !isListening,
      'dictation-unsupported': !isSupported
    }"
    class="dictation-btn"
    :title="buttonTitle"
  >
    <!-- Microphone icon -->
    <svg x-show="!isListening" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
      <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
      <line x1="12" y1="19" x2="12" y2="23"></line>
      <line x1="8" y1="23" x2="16" y2="23"></line>
    </svg>

    <!-- Recording indicator -->
    <svg x-show="isListening" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="red" stroke="red" stroke-width="2">
      <circle cx="12" cy="12" r="10"></circle>
    </svg>
  </button>

  <!-- Interim transcript display -->
  <div x-show="interimText" class="interim-transcript" x-text="interimText"></div>
</div>

<script>
function dictationButton() {
  return {
    isSupported: false,
    isListening: false,
    interimText: '',
    finalText: '',

    init() {
      this.isSupported = window.dictationService.isSupported;

      if (!this.isSupported) {
        console.warn('Speech recognition not supported in this browser');
        return;
      }

      // Set up event handlers
      window.dictationService.onResult = (final, interim) => {
        if (final) {
          this.handleFinalTranscript(final);
        }
        this.interimText = interim;
      };

      window.dictationService.onError = (error) => {
        this.handleError(error);
      };

      window.dictationService.onEnd = () => {
        this.isListening = false;
        this.interimText = '';
      };
    },

    toggleDictation() {
      if (this.isListening) {
        this.stopDictation();
      } else {
        this.startDictation();
      }
    },

    startDictation() {
      const started = window.dictationService.start();
      if (started) {
        this.isListening = true;
      } else {
        this.showError('Could not start dictation. Please check your browser settings.');
      }
    },

    stopDictation() {
      window.dictationService.stop();
      this.isListening = false;
      this.interimText = '';
    },

    handleFinalTranscript(text) {
      // This will be overridden by specific implementations
      // (textarea vs TipTap editor)
      if (this.$refs.target) {
        this.insertText(text);
      }
    },

    insertText(text) {
      // Default implementation for textarea
      const target = this.$refs.target;
      if (!target) return;

      const start = target.selectionStart;
      const end = target.selectionEnd;
      const currentValue = target.value;

      const newValue = currentValue.substring(0, start) + text + currentValue.substring(end);
      target.value = newValue;

      // Update cursor position
      const newPosition = start + text.length;
      target.setSelectionRange(newPosition, newPosition);

      // Trigger input event for Alpine.js
      target.dispatchEvent(new Event('input'));
    },

    handleError(error) {
      let message = 'Dictation error occurred';

      switch (error) {
        case 'not-allowed':
          message = 'Microphone access denied. Please enable microphone permissions.';
          break;
        case 'no-speech':
          message = 'No speech detected. Please try again.';
          break;
        case 'network':
          message = 'Network error. Please check your connection.';
          break;
        case 'aborted':
          message = 'Dictation was aborted.';
          break;
      }

      this.showError(message);
    },

    showError(message) {
      // Use existing toast notification system
      if (window.showToast) {
        window.showToast(message, 'warning');
      } else {
        console.error(message);
      }
    },

    get buttonTitle() {
      if (!this.isSupported) {
        return 'Dictation not supported in this browser';
      }
      return this.isListening ? 'Stop dictation' : 'Start dictation';
    }
  };
}
</script>
```

#### 1.3 Add Styles
**File**: `alma/static/css/dictation.css` (or add to existing styles)

```css
/* Dictation button styles */
.dictation-button-wrapper {
  position: relative;
  display: inline-block;
}

.dictation-btn {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dictation-btn:hover:not(:disabled) {
  background: #f5f5f5;
  border-color: #999;
}

.dictation-btn.dictation-active {
  background: #fee;
  border-color: #f00;
  animation: pulse 1.5s infinite;
}

.dictation-btn.dictation-unsupported {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.interim-transcript {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 4px;
  padding: 8px 12px;
  background: #f0f0f0;
  border-radius: 4px;
  font-size: 14px;
  color: #666;
  font-style: italic;
  white-space: nowrap;
  z-index: 10;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
```

### Phase 2: Integration with Note Form (1 hour)

#### 2.1 Update Note Form Template
**File**: `alma/templates/partials/note-form.html`

Add dictation button next to textarea:

```html
<!-- Add after content textarea -->
<div class="flex items-center gap-2 mt-2">
  {% include "partials/dictation-button.html" %}
  <span class="text-sm text-gray-500" x-text="content.split(/\s+/).filter(w => w).length + ' words'"></span>
</div>
```

Modify Alpine.js component to handle dictation:

```javascript
// In existing note form Alpine component, add:
dictationTarget: null,

init() {
  this.dictationTarget = this.$refs.contentTextarea;
  // existing init code...
},

// Override handleFinalTranscript in dictationButton
handleFinalTranscript(text) {
  // Append to content model
  this.content += (this.content ? ' ' : '') + text;
}
```

### Phase 3: Integration with TipTap Editor (1-2 hours)

#### 3.1 Update Editor Template
**File**: `alma/templates/editor.html`

Add dictation button to toolbar:

```html
<!-- In toolbar, after existing buttons -->
<div class="toolbar-divider"></div>
{% include "partials/dictation-button.html" %}
```

#### 3.2 Update Editor JavaScript
**File**: `alma/static/js/editor.js`

```javascript
// In editor initialization, add dictation support
const editorElement = document.querySelector('#editor');

// Override dictation handler for TipTap
window.handleEditorDictation = (text) => {
  if (window.editor) {
    // Insert at current cursor position
    window.editor
      .chain()
      .focus()
      .insertContent(text + ' ')
      .run();
  }
};

// Update dictationButton component to use this handler
Alpine.data('dictationButton', () => ({
  // ... existing code ...

  handleFinalTranscript(text) {
    // Check if we're in TipTap editor context
    if (window.handleEditorDictation && window.editor) {
      window.handleEditorDictation(text);
    } else {
      // Fallback to textarea insertion
      this.insertText(text);
    }
  }
}));
```

### Phase 4: Template Integration & Loading (30 min)

#### 4.1 Update Base Template
**File**: `alma/templates/base.html`

Add dictation script and styles:

```html
<!-- In <head>, add dictation CSS -->
<link rel="stylesheet" href="{{ url_for('static', path='css/dictation.css') }}">

<!-- Before closing </body>, add dictation JS -->
<script src="{{ url_for('static', path='js/dictation.js') }}"></script>
```

### Phase 5: User Experience Enhancements (1-2 hours)

#### 5.1 Add Settings/Preferences
- Language selection (en-US, es-ES, fr-FR, etc.)
- Continuous vs. single-phrase mode
- Auto-punctuation preference

#### 5.2 Add Help Text
**File**: `alma/templates/partials/dictation-help.html`

```html
<div class="dictation-help" x-show="showHelp">
  <h4>Using Voice Dictation</h4>
  <ul>
    <li>Click the microphone button to start/stop dictation</li>
    <li>Speak clearly and naturally</li>
    <li>Text will appear as you speak</li>
  </ul>

  <div class="alert alert-info">
    <strong>iOS Safari users:</strong> Enable dictation in Settings > General > Keyboard > Enable Dictation
  </div>

  <h5>Voice Commands (future enhancement):</h5>
  <ul>
    <li>"new line" - Insert line break</li>
    <li>"period" - Insert period</li>
    <li>"comma" - Insert comma</li>
    <li>"question mark" - Insert ?</li>
  </ul>
</div>
```

### Phase 6: Testing & Fallbacks (1-2 hours)

#### 6.1 Browser Compatibility Testing
- Safari iOS 14.5+ ✓
- Safari desktop ✓
- Chrome mobile/desktop ✓
- Firefox (limited support) ⚠️
- Edge ✓

#### 6.2 Graceful Degradation
- Feature detection on page load
- Hide dictation button if not supported
- Show helpful message for unsupported browsers
- Fallback to native keyboard dictation

#### 6.3 Error Handling
- Microphone permission denied
- No speech detected
- Network errors (for cloud recognition)
- Safari-specific issues (PWA mode)

### Phase 7: Mobile Optimization (1 hour)

#### 7.1 Touch-Friendly UI
- Larger dictation button on mobile (min 44x44px)
- Hold-to-record alternative pattern
- Haptic feedback (if supported)

#### 7.2 Mobile-Specific Considerations
```javascript
// Detect mobile Safari
const isMobileSafari = /iPhone|iPad|iPod/.test(navigator.userAgent) && !window.MSStream;

if (isMobileSafari) {
  // Apply mobile-specific settings
  this.recognition.continuous = false;  // Better for mobile
  this.recognition.maxAlternatives = 1;  // Reduce processing
}
```

## Technical Considerations

### Browser Compatibility Matrix
| Browser | Support | Notes |
|---------|---------|-------|
| Safari iOS 14.5+ | ✅ Yes | Requires dictation enabled in settings, webkit prefix |
| Safari Desktop | ✅ Yes | macOS 14.5+ |
| Chrome Mobile | ✅ Yes | Full support |
| Chrome Desktop | ✅ Yes | Full support |
| Firefox | ⚠️ Partial | Desktop only, limited |
| Edge | ✅ Yes | Chromium-based |

### Privacy & Security
- Web Speech API processes locally when available
- Some browsers may use cloud services (Google, Apple)
- Microphone permission required
- No audio data stored by Alma
- Users should be informed about browser's speech processing

### Performance
- Minimal overhead when not active
- Real-time processing
- No server load (client-side only)
- Battery consideration for extended use on mobile

## File Structure

```
alma/
├── static/
│   ├── js/
│   │   ├── dictation.js          [NEW] Core dictation service
│   │   ├── editor.js              [MODIFIED] Add dictation to TipTap
│   │   └── ui.js                  [EXISTING] Toast notifications
│   └── css/
│       └── dictation.css          [NEW] Dictation UI styles
├── templates/
│   ├── base.html                  [MODIFIED] Include dictation assets
│   ├── editor.html                [MODIFIED] Add dictation to editor
│   └── partials/
│       ├── note-form.html         [MODIFIED] Add dictation button
│       ├── dictation-button.html  [NEW] Reusable dictation component
│       └── dictation-help.html    [NEW] Help/info for users
└── plans/
    └── mobile-dictation-service.md [THIS FILE]
```

## Implementation Timeline

| Phase | Time Estimate | Priority |
|-------|---------------|----------|
| 1. Core Dictation Component | 2-3 hours | HIGH |
| 2. Note Form Integration | 1 hour | HIGH |
| 3. TipTap Editor Integration | 1-2 hours | HIGH |
| 4. Template Integration | 30 min | HIGH |
| 5. UX Enhancements | 1-2 hours | MEDIUM |
| 6. Testing & Fallbacks | 1-2 hours | HIGH |
| 7. Mobile Optimization | 1 hour | MEDIUM |
| **TOTAL** | **8-12 hours** | |

## Future Enhancements

### Voice Commands
- "new paragraph" → Insert double newline
- "bold [text]" → Wrap in bold
- "heading [text]" → Create heading
- "bullet point" → Create list item

### Advanced Features
- Voice-activated note creation ("new note about...")
- Multi-language support with auto-detection
- Custom vocabulary/training
- Offline mode with local models
- Voice search functionality

### Analytics
- Track dictation usage
- Error rates by browser/device
- User preference data
- Performance metrics

## Success Metrics

1. **Functionality**: Dictation works in Safari iOS 14.5+
2. **UX**: Clear visual feedback during recording
3. **Accuracy**: Text inserted correctly at cursor position
4. **Reliability**: Graceful handling of errors/unsupported browsers
5. **Performance**: No noticeable lag or battery drain
6. **Accessibility**: Works with existing keyboard shortcuts

## Dependencies

- No new Python/backend dependencies
- No new npm packages required (uses native Web Speech API)
- Compatible with existing HTMX + Alpine.js architecture

## Rollout Strategy

1. **Feature flag**: Add `ENABLE_DICTATION` config option
2. **Gradual rollout**: Start with Safari/Chrome users
3. **User testing**: Beta test with mobile users first
4. **Feedback loop**: Monitor error logs and user reports
5. **Documentation**: Update help docs with dictation instructions

## References

- [Web Speech API - MDN](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)
- [SpeechRecognition API](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition)
- [Safari Web Speech Support](https://webkit.org/blog/11364/introducing-the-web-speech-api/)
- [Browser Compatibility](https://caniuse.com/speech-recognition)

---

## Questions for Review

1. Should we support multiple languages initially or start with English only?
2. Do we want continuous dictation or push-to-talk?
3. Should we add voice commands for formatting (bold, italic, etc.)?
4. Do we need backend logging for dictation usage analytics?
5. Should there be a fallback to cloud services if local recognition fails?

---

**Status**: Ready for implementation
**Estimated LOC**: ~500 lines (JS: ~300, HTML: ~150, CSS: ~50)
**Breaking Changes**: None (purely additive)
