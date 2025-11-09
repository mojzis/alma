import { Editor } from '@tiptap/core'
import StarterKit from '@tiptap/starter-kit'
import { Markdown } from '@tiptap/markdown'

class NoteEditor {
  constructor(element, noteId = null) {
    this.element = element
    this.noteId = noteId
    this.editor = null
    this.autoSaveTimeout = null

    this.initEditor()
    if (noteId) {
      this.loadNote(noteId)
    }
  }

  initEditor() {
    this.editor = new Editor({
      element: this.element,
      extensions: [
        StarterKit,
        Markdown.configure({
          // This config makes wiki-links possible later
          // by keeping the parser extensible
          transformPastedText: true,
          transformCopiedText: true
        })
      ],
      content: '',
      onUpdate: ({ editor }) => {
        this.scheduleAutoSave()
      }
    })
  }

  async loadNote(noteId) {
    try {
      const response = await fetch(`/editor/notes/${noteId}`)
      if (!response.ok) throw new Error('Failed to load note')

      const markdown = await response.text()

      // Load markdown into editor
      // TipTap converts to JSON internally
      this.editor.commands.setContent(markdown)

      this.noteId = noteId
    } catch (error) {
      console.error('Error loading note:', error)
      this.showSaveIndicator('error')
    }
  }

  async saveNote() {
    if (!this.noteId) {
      // Create new note
      return this.createNote()
    }

    // Get markdown from editor
    // This converts internal JSON back to markdown
    const markdown = this.editor.storage.markdown.getMarkdown()

    // Prepare form data
    const formData = new FormData()
    formData.append('content', markdown)

    try {
      const response = await fetch(`/editor/notes/${this.noteId}`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) throw new Error('Save failed')

      this.showSaveIndicator('saved')
      return await response.json()
    } catch (error) {
      console.error('Error saving note:', error)
      this.showSaveIndicator('error')
    }
  }

  async createNote() {
    const markdown = this.editor.storage.markdown.getMarkdown()
    const formData = new FormData()
    formData.append('content', markdown)

    try {
      const response = await fetch('/editor/notes', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) throw new Error('Create failed')

      const data = await response.json()
      this.noteId = data.note_id

      // Update URL without reload
      window.history.pushState({}, '', `/editor/${this.noteId}`)

      this.showSaveIndicator('saved')
      return data
    } catch (error) {
      console.error('Error creating note:', error)
      this.showSaveIndicator('error')
    }
  }

  scheduleAutoSave() {
    // Debounce auto-save
    clearTimeout(this.autoSaveTimeout)
    this.showSaveIndicator('saving')
    this.autoSaveTimeout = setTimeout(() => {
      this.saveNote()
    }, 2000) // Save 2 seconds after last edit
  }

  showSaveIndicator(status) {
    // Implement visual feedback
    const indicator = document.getElementById('save-indicator')
    if (!indicator) return

    indicator.textContent = {
      'saved': '✓ Saved',
      'saving': '⋯ Saving',
      'error': '✗ Error'
    }[status] || ''

    indicator.className = `save-indicator save-indicator--${status}`
  }

  getMarkdown() {
    return this.editor.storage.markdown.getMarkdown()
  }

  destroy() {
    if (this.editor) {
      this.editor.destroy()
    }
  }
}

// Initialize editor when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const editorElement = document.getElementById('editor')
  if (!editorElement) return

  // Get note ID from URL if present
  const pathMatch = window.location.pathname.match(/\/editor\/([^/]+)/)
  const noteId = pathMatch ? pathMatch[1] : null

  // Create global editor instance
  window.noteEditor = new NoteEditor(editorElement, noteId)
})

// Expose for manual save button
window.saveCurrentNote = () => {
  if (window.noteEditor) {
    return window.noteEditor.saveNote()
  }
}

// Expose editor commands for toolbar
window.editorCommands = {
  toggleHeading: (level) => {
    if (window.noteEditor?.editor) {
      window.noteEditor.editor.chain().focus().toggleHeading({ level }).run()
    }
  },
  toggleBold: () => {
    if (window.noteEditor?.editor) {
      window.noteEditor.editor.chain().focus().toggleBold().run()
    }
  },
  toggleItalic: () => {
    if (window.noteEditor?.editor) {
      window.noteEditor.editor.chain().focus().toggleItalic().run()
    }
  },
  toggleCode: () => {
    if (window.noteEditor?.editor) {
      window.noteEditor.editor.chain().focus().toggleCode().run()
    }
  },
  toggleBulletList: () => {
    if (window.noteEditor?.editor) {
      window.noteEditor.editor.chain().focus().toggleBulletList().run()
    }
  },
  toggleOrderedList: () => {
    if (window.noteEditor?.editor) {
      window.noteEditor.editor.chain().focus().toggleOrderedList().run()
    }
  },
  toggleCodeBlock: () => {
    if (window.noteEditor?.editor) {
      window.noteEditor.editor.chain().focus().toggleCodeBlock().run()
    }
  },
  toggleBlockquote: () => {
    if (window.noteEditor?.editor) {
      window.noteEditor.editor.chain().focus().toggleBlockquote().run()
    }
  }
}
