(function (window) {
    const STORAGE_KEY = 'chatbotConversations';
    const ACTIVE_KEY = 'chatbotActiveConversation';

    const DEFAULT_CONVERSATIONS = [
        {
            id: 'conv-sample-1',
            title: '면접 준비 가이드',
            messages: [
                { sender: 'user', text: '백엔드 면접을 준비하려면 무엇부터 해야 할까요?' },
                { sender: 'bot', text: '현재 실력을 점검하고 자주 등장하는 주제를 정리해보는 것이 좋아요.' }
            ],
            profile: null,
        },
        {
            id: 'conv-sample-2',
            title: '진로 탐색 상담',
            messages: [
                { sender: 'user', text: '인문계 학생인데 개발 직무에 관심이 있어요.' },
                { sender: 'bot', text: '관심 있는 프로젝트 경험을 쌓고 코딩 테스트 기초를 준비하면 좋아요.' }
            ],
            profile: null,
        },
    ];

    function readStorage(key) {
        try {
            const value = window.localStorage.getItem(key);
            return value ? JSON.parse(value) : null;
        } catch (error) {
            console.warn('LocalStorage read failed', error);
            return null;
        }
    }

    function writeStorage(key, value) {
        try {
            window.localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.warn('LocalStorage write failed', error);
        }
    }

    function normalizeConversation(conversation) {
        const normalized = Object.assign(
            {
                id: generateId(),
                title: '새 대화',
                messages: [],
                profile: null,
            },
            conversation || {}
        );
        if (!Array.isArray(normalized.messages)) {
            normalized.messages = [];
        }
        return normalized;
    }

    function ensureConversations() {
        let conversations = readStorage(STORAGE_KEY);
        if (!conversations) {
            conversations = DEFAULT_CONVERSATIONS;
            writeStorage(STORAGE_KEY, conversations);
            writeStorage(ACTIVE_KEY, conversations[0]?.id ?? null);
        }
        return conversations.map(normalizeConversation);
    }

    function generateId() {
        return `conv-${Date.now().toString(36)}-${Math.floor(Math.random() * 1000)}`;
    }

    function saveConversations(conversations) {
        writeStorage(STORAGE_KEY, conversations);
    }

    function findConversation(id) {
        const conversations = ensureConversations();
        return conversations.find((conv) => conv.id === id) || null;
    }

    const ConversationStore = {
        getAll() {
            return ensureConversations();
        },
        getActiveId() {
            return readStorage(ACTIVE_KEY);
        },
        setActive(id) {
            writeStorage(ACTIVE_KEY, id);
        },
        getActive() {
            const conversations = ensureConversations();
            const activeId = ConversationStore.getActiveId();
            if (!activeId) {
                const first = conversations[0] || null;
                if (first) {
                    ConversationStore.setActive(first.id);
                }
                return first;
            }
            return findConversation(activeId) || conversations[0] || null;
        },
        create(title = '새 대화', initialMessages = [], profile = null) {
            const conversations = ensureConversations();
            const conversation = {
                id: generateId(),
                title,
                messages: initialMessages,
                profile: profile || null,
            };
            conversations.unshift(conversation);
            saveConversations(conversations);
            ConversationStore.setActive(conversation.id);
            return conversation;
        },
        delete(id) {
            let conversations = ensureConversations();
            conversations = conversations.filter((conv) => conv.id !== id);
            saveConversations(conversations);
            const activeId = ConversationStore.getActiveId();
            if (activeId === id) {
                ConversationStore.setActive(conversations[0]?.id ?? null);
            }
            return conversations;
        },
        addMessage(id, sender, text) {
            const conversations = ensureConversations();
            const target = conversations.find((conv) => conv.id === id);
            if (!target) {
                return;
            }
            target.messages.push({ sender, text });
            saveConversations(conversations);
        },
        setMessages(id, messages) {
            const conversations = ensureConversations();
            const target = conversations.find((conv) => conv.id === id);
            if (!target) {
                return;
            }
            target.messages = messages;
            saveConversations(conversations);
        },
        setProfile(id, profile) {
            const conversations = ensureConversations();
            const target = conversations.find((conv) => conv.id === id);
            if (!target) {
                return;
            }
            target.profile = profile;
            saveConversations(conversations);
        },
        getProfile(id) {
            const conversation = findConversation(id);
            return conversation ? conversation.profile : null;
        },
        rename(id, title) {
            const conversations = ensureConversations();
            const target = conversations.find((conv) => conv.id === id);
            if (target) {
                target.title = title;
                saveConversations(conversations);
            }
        },
        renderList(container, { activeId = ConversationStore.getActiveId(), onSelect, onDelete, emptyLabel = '대화가 없습니다.' } = {}) {
            if (!container) return;

            const conversations = ensureConversations();
            container.innerHTML = '';

            if (!conversations.length) {
                const placeholder = document.createElement('li');
                placeholder.className = 'conversation-empty';
                placeholder.textContent = emptyLabel;
                container.appendChild(placeholder);
                return;
            }

            conversations.forEach((conversation) => {
                const item = document.createElement('li');
                item.className = `conversation-item${conversation.id === activeId ? ' active' : ''}`;

                const label = document.createElement('span');
                label.textContent = conversation.title;

                const deleteBtn = document.createElement('button');
                deleteBtn.className = 'conversation-delete';
                deleteBtn.setAttribute('type', 'button');
                deleteBtn.setAttribute('aria-label', '대화 삭제');
                deleteBtn.innerHTML = '&times;';
                deleteBtn.addEventListener('click', (event) => {
                    event.stopPropagation();
                    ConversationStore.delete(conversation.id);
                    ConversationStore.renderList(container, { activeId, onSelect, onDelete, emptyLabel });
                    if (typeof onDelete === 'function') {
                        onDelete(conversation.id);
                    }
                });

                item.appendChild(label);
                item.appendChild(deleteBtn);
                item.addEventListener('click', () => {
                    ConversationStore.setActive(conversation.id);
                    if (typeof onSelect === 'function') {
                        onSelect(conversation);
                    }
                });

                container.appendChild(item);
            });
        },
    };

    window.ConversationStore = ConversationStore;
})(window);
