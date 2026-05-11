/**
 * Text Translator - Показує переклад при виділенні слів
 * Використовує MyMemory API через Django backend
 */

class TextTranslator {
  constructor(options = {}) {
    this.sourceLang = options.sourceLang || 'sk';
    this.targetLang = options.targetLang || 'uk';
    this.apiUrl = options.apiUrl || '/api/translate/';
    this.tooltip = null;
    this.lastSelection = null;
    
    this.init();
  }

  init() {
    // Слухаємо mouseup для виділення тексту
    document.addEventListener('mouseup', () => this.handleSelection());
    document.addEventListener('touchend', () => this.handleSelection());
  }

  handleSelection() {
    const selection = window.getSelection();
    const selectedText = selection.toString().trim();

    if (selectedText.length === 0) {
      this.hideTooltip();
      this.lastSelection = null;
      return;
    }

    // Не переводити одне й те ж слово в один час
    if (this.lastSelection === selectedText) {
      return;
    }

    this.lastSelection = selectedText;
    
    // Показуємо позицію tooltip
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    
    this.showTooltip(selectedText, rect);
    this.translateText(selectedText);
  }

  showTooltip(text, rect) {
    if (!this.tooltip) {
      this.tooltip = document.createElement('div');
      this.tooltip.className = 'text-translator-tooltip';
      this.tooltip.innerHTML = `
        <div class="translator-header">
          <span class="translator-source">${this.escapeHtml(text)}</span>
          <svg class="translator-loader" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <path d="M12 6v6l4 2"></path>
          </svg>
        </div>
        <div class="translator-target">Перекладаю...</div>
      `;
      document.body.appendChild(this.tooltip);
    }

    // Позиціонуємо tooltip над вибраним текстом
    const top = rect.top + window.scrollY - 60;
    const left = rect.left + window.scrollX + rect.width / 2 - 100;

    this.tooltip.style.position = 'fixed';
    this.tooltip.style.top = top + 'px';
    this.tooltip.style.left = Math.max(10, left) + 'px';
    this.tooltip.style.display = 'block';
    this.tooltip.style.zIndex = '99999';
  }

  hideTooltip() {
    if (this.tooltip) {
      this.tooltip.style.display = 'none';
    }
  }

  async translateText(text) {
    try {
      const response = await fetch(this.apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCsrfToken(),
        },
        body: JSON.stringify({
          text: text,
          source_lang: this.sourceLang,
          target_lang: this.targetLang,
        }),
      });

      const data = await response.json();
      
      if (this.tooltip && data.translation) {
        this.tooltip.innerHTML = `
          <div class="translator-header">
            <span class="translator-source">${this.escapeHtml(data.text)}</span>
          </div>
          <div class="translator-target">${this.escapeHtml(data.translation)}</div>
        `;
      }
    } catch (error) {
      console.error('Translation error:', error);
      if (this.tooltip) {
        this.tooltip.innerHTML = `
          <div class="translator-error">Помилка перекладу</div>
        `;
      }
    }
  }

  getCsrfToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  escapeHtml(text) {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
  }
}

// Ініціалізуємо при завантаженні сторінки
document.addEventListener('DOMContentLoaded', () => {
  // Лише на сторінках де потрібен переклад (lesson, exercise, texts)
  const shouldTranslate = 
    document.querySelector('.lesson-theory') ||
    document.querySelector('.exercise-card') ||
    document.querySelector('[data-translate="true"]');

  if (shouldTranslate) {
    new TextTranslator({
      sourceLang: 'sk',
      targetLang: 'uk',
      apiUrl: '/api/translate/',
    });
  }
});
