document.addEventListener('DOMContentLoaded', () => {

    const helpBtn = document.getElementById('astrologerHelpBtn');
    const helpModal = document.getElementById('astrologerHelpModal');
    const closeHelpBtn = helpModal.querySelector('.close-help-modal');
    const sendBtn = document.querySelector('.send-btn');
    const messageInput = document.querySelector('.message-input');
    const chatContainer = document.getElementById('chatContainer');
    const chatId = typeof CHAT_ID !== 'undefined' ? CHAT_ID : null;

    helpBtn.addEventListener('click', () => {
        helpModal.style.display = 'flex';
        helpModal.focus();
    });

    closeHelpBtn.addEventListener('click', () => {
        helpModal.style.display = 'none';
        helpBtn.focus();
    });

    window.addEventListener('click', (e) => {
        if (e.target === helpModal) {
            helpModal.style.display = 'none';
            helpBtn.focus();
        }
    });

    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault(); // чтобы не было переноса строки
            sendMessage();
        }
    });

    function appendMessage({ sender, text, timestamp }) {
        const now = new Date(timestamp);
        const todayStr = now.toLocaleDateString('ru-RU');
        const lastDateDiv = chatContainer.querySelector('.message-date:last-of-type');
        const lastDate = lastDateDiv ? lastDateDiv.textContent : '';

        if (lastDate !== todayStr) {
            const dateDiv = document.createElement('div');
            dateDiv.className = 'message-date';
            dateDiv.setAttribute('aria-label', 'Дата сообщений');
            dateDiv.textContent = todayStr;
            chatContainer.appendChild(dateDiv);
        }

        const messageDiv = document.createElement('article');
        messageDiv.className = 'message ' + (sender === 'user' ? 'user-message' : 'astrologer-message');
        messageDiv.setAttribute('role', 'log');
        messageDiv.setAttribute('aria-live', 'polite');
        messageDiv.setAttribute('aria-atomic', 'true');

        const messageP = document.createElement('p');
        messageP.textContent = text;

        const timeDiv = document.createElement('time');
        timeDiv.className = 'message-time';
        timeDiv.setAttribute('datetime', now.toISOString());
        timeDiv.textContent = now.toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'});

        messageDiv.appendChild(messageP);
        messageDiv.appendChild(timeDiv);
        chatContainer.appendChild(messageDiv);

        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function sendMessage() {
        const messageText = messageInput.value.trim();
        if (!messageText) return;

        if (!chatId) {
            alert('Ошибка: отсутствует идентификатор чата');
            return;
        }

        const payload = {
            chat_id: chatId,
            text: messageText
        };

        fetch('/send_message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                appendMessage({ sender: 'user', text: messageText, timestamp: new Date().toISOString() });
            } else if (data.error) {
                alert('Ошибка: ' + data.error);
            } else {
                alert('Неизвестная ошибка при отправке сообщения');
            }
        })
        .catch(() => alert('Ошибка сети при отправке сообщения'));

        messageInput.value = '';
    }
  });