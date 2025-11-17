document.addEventListener('DOMContentLoaded', () => {
    const layout = document.querySelector('.chat-layout');
    const detailUrl = layout?.dataset.chatDetailUrl || '';
    const conversationList = document.querySelector('[data-conversation-list]');
    const newChatButton = document.querySelector('[data-add-conversation]');
    const messageField = document.querySelector('[data-message-field]');
    const sendButton = document.querySelector('[data-send-message]');
    const promptItems = document.querySelectorAll('[data-template]');

    function getDefaultProfile() {
        try {
            return JSON.parse(sessionStorage.getItem('chatbotUserProfile') || '{}');
        } catch (error) {
            return {};
        }
    }

    function ensureProfile() {
        const profile = getDefaultProfile();
        if (!profile.stageType) {
            alert('먼저 사용자 정보를 입력해주세요.');
            return null;
        }
        return profile;
    }

    function redirectToConversation(conversation) {
        if (!conversation || !detailUrl) return;
        const url = new URL(detailUrl, window.location.origin);
        url.searchParams.set('conversation', conversation.id);
        window.location.href = url.toString();
    }

    function renderConversations() {
        ConversationStore.renderList(conversationList, {
            onSelect: redirectToConversation,
        });
    }

    function createConversation({ title, initialMessage }) {
        const profile = ensureProfile();
        if (!profile) return null;
        const messages = initialMessage ? [{ sender: 'user', text: initialMessage }] : [];
        const conversation = ConversationStore.create(title || '새 대화', messages, profile);
        if (initialMessage) {
            sessionStorage.setItem('chatbotPendingConversation', JSON.stringify({
                conversationId: conversation.id,
                question: initialMessage,
            }));
            redirectToConversation(conversation);
        } else {
            renderConversations();
        }
        return conversation;
    }

    renderConversations();

    newChatButton?.addEventListener('click', () => {
        createConversation({ title: '새 대화' });
    });

    promptItems.forEach((item) => {
        item.addEventListener('click', () => {
            const templateTitle = item.dataset.template || item.textContent.trim() || '새 대화';
            const body = item.dataset.body || templateTitle;
            createConversation({ title: templateTitle, initialMessage: body });
        });
    });

    function handleSend() {
        const value = messageField?.value.trim();
        if (!value) return;
        createConversation({ title: '사용자 메시지', initialMessage: value });
    }

    sendButton?.addEventListener('click', handleSend);
    messageField?.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            handleSend();
        }
    });
});
