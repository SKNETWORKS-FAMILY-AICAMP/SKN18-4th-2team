document.addEventListener('DOMContentLoaded', () => {
    const layout = document.querySelector('.chat-layout');
    const detailUrl = layout?.dataset.chatDetailUrl || '';
    const conversationList = document.querySelector('[data-conversation-list]');
    const newChatButton = document.querySelector('[data-add-conversation]');
    const messageField = document.querySelector('[data-message-field]');
    const sendButton = document.querySelector('[data-send-message]');
    const promptItems = document.querySelectorAll('[data-template]');
    const profileModal = window.initProfileModal?.('[data-profile-modal]');

    function getDefaultProfile() {
        try {
            return JSON.parse(sessionStorage.getItem('chatbotUserProfile') || '{}');
        } catch (error) {
            return {};
        }
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

    function createConversation({ title, profile, initialMessage }) {
        const messages = initialMessage ? [{ sender: 'user', text: initialMessage }] : [];
        const conversation = ConversationStore.create(title || '새 대화', messages, profile || null);
        if (initialMessage) {
            sessionStorage.setItem('chatbotPendingConversation', JSON.stringify({
                conversationId: conversation.id,
                question: initialMessage,
            }));
            redirectToConversation(conversation);
        } else {
            renderConversations();
        }
    }

    renderConversations();

    newChatButton?.addEventListener('click', () => {
        requestProfile({ title: '새 대화', profile: {}, forceBlank: true }).then((result) => {
            if (!result) return;
            createConversation({ title: result.title, profile: result.profile });
        });
    });

    promptItems.forEach((item) => {
        item.addEventListener('click', () => {
            const templateTitle = item.dataset.template || item.textContent.trim() || '새 대화';
            const body = item.dataset.body || templateTitle;
            requestProfile({ title: templateTitle }).then((result) => {
                if (!result) return;
                createConversation({ title: result.title, profile: result.profile, initialMessage: body });
            });
        });
    });

    function handleSend() {
        const value = messageField?.value.trim();
        if (!value) return;
        requestProfile({ title: '사용자 메시지' }).then((result) => {
            if (!result) return;
            createConversation({ title: result.title, profile: result.profile, initialMessage: value });
        });
    }

    sendButton?.addEventListener('click', handleSend);
    messageField?.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            handleSend();
        }
    });
});
