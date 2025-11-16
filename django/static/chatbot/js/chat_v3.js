document.addEventListener('DOMContentLoaded', () => {
    const layout = document.querySelector('.chat-layout');
    const apiEndpoint = layout?.dataset.apiEndpoint || '';
    const conversationList = document.querySelector('[data-conversation-list]');
    const newChatButton = document.querySelector('[data-add-conversation]');
    const messageList = document.querySelector('[data-message-list]');
    const messageInput = document.querySelector('[data-message-input]');
    const sendButton = document.querySelector('[data-send-message]');
    const titleEl = document.querySelector('[data-conversation-title]');
    const deleteActiveBtn = document.querySelector('[data-delete-active]');
    const clearActiveBtn = document.querySelector('[data-clear-active]');
    const profileModal = window.initProfileModal?.('[data-profile-modal]');
    let isRequesting = false;
    let thinkingBubble = null;

    const params = new URLSearchParams(window.location.search);
    const requestedConversation = params.get('conversation');

    if (requestedConversation) {
        const exists = ConversationStore.getAll().some((conv) => conv.id === requestedConversation);
        if (exists) {
            ConversationStore.setActive(requestedConversation);
        }
    }

    function renderMessages(conversation) {
        if (!messageList) return;
        messageList.innerHTML = '';

        if (!conversation) {
            const placeholder = document.createElement('div');
            placeholder.className = 'chat-placeholder';
            placeholder.innerHTML = '<p>대화를 선택하거나 새로 만들어보세요.</p>';
            messageList.appendChild(placeholder);
            return;
        }

        conversation.messages.forEach((msg) => {
            const bubble = document.createElement('div');
            bubble.className = `message ${msg.sender === 'user' ? 'user' : 'bot'}`;
            bubble.textContent = msg.text;
            messageList.appendChild(bubble);
        });

        if (thinkingBubble) {
            messageList.appendChild(thinkingBubble);
        }

        messageList.scrollTop = messageList.scrollHeight;
    }

    function setActive(conversation) {
        if (!conversation) {
            titleEl.textContent = '새 대화';
            renderMessages(null);
            return;
        }
        titleEl.textContent = conversation.title;
        renderMessages(conversation);
    }

    function renderConversations() {
        ConversationStore.renderList(conversationList, {
            activeId: ConversationStore.getActiveId(),
            onSelect: (conversation) => {
                ConversationStore.setActive(conversation.id);
                setActive(ConversationStore.getActive());
                renderConversations();
            },
            onDelete: () => {
                setActive(ConversationStore.getActive());
            },
        });
        setActive(ConversationStore.getActive());
    }

    function getDefaultProfile() {
        try {
            return JSON.parse(sessionStorage.getItem('chatbotUserProfile') || '{}');
        } catch (error) {
            return {};
        }
    }

    function getConversationProfile(conversation) {
        if (!conversation) return getDefaultProfile();
        const stored = ConversationStore.getProfile(conversation.id);
        if (stored && Object.keys(stored).length) {
            return stored;
        }
        return getDefaultProfile();
    }

    function requestProfile(options = {}) {
        return new Promise((resolve) => {
            const forceBlank = !!options.forceBlank;
            const providedProfile = options.profile;
            const hasProvided = providedProfile && Object.keys(providedProfile).length > 0;
            const baseProfile = forceBlank || !hasProvided
                ? {}
                : (providedProfile || getDefaultProfile());
            const fallbackTitle = options.title || (baseProfile.name ? `${baseProfile.name}님의 새 대화` : '새 대화');
            if (!profileModal) {
                resolve({ title: fallbackTitle, profile: baseProfile });
                return;
            }
            profileModal.open({
                initialProfile: baseProfile,
                initialTitle: fallbackTitle,
                onSubmit: resolve,
                onUseExisting: () => resolve({ title: fallbackTitle, profile: getDefaultProfile() }),
            });
        });
    }

    function getCookie(name) {
        if (!document.cookie) return null;
        const cookies = document.cookie.split(';');
        for (const cookie of cookies) {
            const [key, value] = cookie.trim().split('=');
            if (key === name) {
                return decodeURIComponent(value);
            }
        }
        return null;
    }

    async function requestAnswer(questionText, profile) {
        if (!apiEndpoint) {
            throw new Error('API endpoint가 설정되지 않았습니다.');
        }
        const response = await fetch(apiEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') || '',
            },
            body: JSON.stringify({
                question: questionText,
                profile: profile || {},
            }),
        });
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.error || '답변을 가져오지 못했습니다.');
        }
        return response.json();
    }

    function showThinking() {
        if (!messageList) return;
        thinkingBubble = document.createElement('div');
        thinkingBubble.className = 'message bot';
        thinkingBubble.textContent = '답변을 생성하는 중입니다...';
        messageList.appendChild(thinkingBubble);
        messageList.scrollTop = messageList.scrollHeight;
    }

    function hideThinking() {
        if (thinkingBubble?.parentNode) {
            thinkingBubble.parentNode.removeChild(thinkingBubble);
        }
        thinkingBubble = null;
    }

    async function sendQuestion(text, { persistUserMessage = true } = {}) {
        const conversation = ConversationStore.getActive();
        if (!conversation) {
            alert('먼저 대화를 생성해주세요.');
            return;
        }
        if (isRequesting) {
            return;
        }
        const question = text.trim();
        if (!question) return;

        if (persistUserMessage) {
            ConversationStore.addMessage(conversation.id, 'user', question);
        }
        messageInput.value = '';
        renderMessages(ConversationStore.getActive());

        isRequesting = true;
        sendButton?.setAttribute('disabled', 'disabled');
        showThinking();

        const conversationProfile = getConversationProfile(conversation);

        try {
            const data = await requestAnswer(question, conversationProfile);
            const answerText = data.answer || '답변을 생성하지 못했습니다.';
            ConversationStore.addMessage(conversation.id, 'bot', answerText);
        } catch (error) {
            const message = error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.';
            ConversationStore.addMessage(conversation.id, 'bot', message);
        } finally {
            isRequesting = false;
            sendButton?.removeAttribute('disabled');
            hideThinking();
            renderMessages(ConversationStore.getActive());
        }
    }

    newChatButton?.addEventListener('click', () => {
        requestProfile({ title: '새 대화', profile: {}, forceBlank: true }).then((result) => {
            if (!result) return;
            const conversation = ConversationStore.create(result.title, [], result.profile);
            renderConversations();
            setActive(conversation);
        });
    });

    deleteActiveBtn?.addEventListener('click', () => {
        const active = ConversationStore.getActive();
        if (!active) return;
        if (confirm(`"${active.title}" 대화를 삭제할까요?`)) {
            ConversationStore.delete(active.id);
            renderConversations();
        }
    });

    clearActiveBtn?.addEventListener('click', () => {
        const active = ConversationStore.getActive();
        if (!active) return;
        if (confirm('현재 대화를 초기화할까요?')) {
            ConversationStore.setMessages(active.id, [
                { sender: 'bot', text: '대화가 초기화되었습니다. 무엇을 도와드릴까요?' },
            ]);
            renderMessages(ConversationStore.getActive());
        }
    });

    sendButton?.addEventListener('click', () => sendQuestion(messageInput.value));
    messageInput?.addEventListener('keypress', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendQuestion(messageInput.value);
        }
    });

    function checkPendingConversation() {
        try {
            const pending = JSON.parse(sessionStorage.getItem('chatbotPendingConversation') || 'null');
            if (!pending) return;
            const active = ConversationStore.getActive();
            if (active && active.id === pending.conversationId) {
                sessionStorage.removeItem('chatbotPendingConversation');
                sendQuestion(pending.question, { persistUserMessage: false });
            }
        } catch (error) {
            sessionStorage.removeItem('chatbotPendingConversation');
        }
    }

    renderConversations();
    checkPendingConversation();
});
