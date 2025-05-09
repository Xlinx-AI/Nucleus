document.addEventListener('DOMContentLoaded', () => {
  const chatHistoryDiv = document.getElementById('chat-history');
  const statusDiv = document.getElementById('status');
  const chatForm = document.getElementById('chat-form');
  const userQueryInput = document.getElementById('user-query');
  const sendBtn = document.getElementById('send-btn');

  // Прокрутка вниз
  function scrollToBottom() {
    chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
  }

  // Рендер одного сообщения
  function renderMessage(msg) {
    const div = document.createElement('div');
    div.className = 'bubble ' + (msg.role === 'user' ? 'user' : 'assistant');
    div.textContent = msg.content;
    chatHistoryDiv.appendChild(div);
  }

  // Полная отрисовка истории
  function renderHistory(history) {
    chatHistoryDiv.innerHTML = '';
    (history || []).forEach(renderMessage);
    scrollToBottom();
  }

  // Статус: текст или спиннер
  function setStatus(text, loading = false) {
    if (loading) {
      statusDiv.innerHTML = `<span class="spinner"></span>${text || 'Запрос...'}`;
    } else {
      statusDiv.textContent = text || '';
    }
  }

  // Получить историю с сервера
  async function fetchHistory() {
    setStatus('Загрузка...', true);
    try {
      const resp = await fetch('/history');
      if (!resp.ok) throw new Error('Ошибка сервера');
      const data = await resp.json();
      renderHistory(data.history);
      setStatus('');
    } catch (e) {
      setStatus('Ошибка загрузки истории', false);
    }
  }

  // Отправить новый запрос
  async function submitTask(e) {
    if (e) e.preventDefault();
    const query = userQueryInput.value.trim();
    if (!query) {
      setStatus('Введите запрос.', false);
      userQueryInput.focus();
      return;
    }
    setStatus('Отправка...', true);
    sendBtn.disabled = true;
    userQueryInput.disabled = true;
    try {
      const resp = await fetch('/submit_task', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      if (!resp.ok) throw new Error('Ошибка сервера');
      const data = await resp.json();
      setStatus(`Задача отправлена, ID: ${data.task_id}`);
      userQueryInput.value = '';
      await fetchHistory();
    } catch (e) {
      setStatus('Ошибка отправки запроса', false);
    } finally {
      sendBtn.disabled = false;
      userQueryInput.disabled = false;
      userQueryInput.focus();
    }
  }

  chatForm.addEventListener('submit', submitTask);
  sendBtn.addEventListener('click', submitTask);

  // Автофокус на инпут при клике на историю
  chatHistoryDiv.addEventListener('click', () => userQueryInput.focus());

  fetchHistory();
});