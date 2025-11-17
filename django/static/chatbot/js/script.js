document.addEventListener('DOMContentLoaded', () => {
    const layout = document.querySelector('.chat-layout');
    const detailUrl = layout?.dataset.chatDetailUrl || '';
    const conversationList = document.querySelector('[data-conversation-list]');
    const newChatButton = document.querySelector('[data-add-conversation]');
    const form = document.querySelector('.user-info-form');
    const stageGroup = document.querySelector('[data-stage-select]');
    const majorGroup = document.querySelector('[data-major-select]');
    const studentOnlySections = document.querySelectorAll('[data-student-only]');

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
        if (!conversationList) return;
        ConversationStore.renderList(conversationList, {
            onSelect: (conversation) => redirectToConversation(conversation),
        });
    }

    renderConversations();

    newChatButton?.addEventListener('click', () => {
        const profile = ensureProfile();
        if (!profile) return;
        ConversationStore.create('새 대화', [], profile);
        renderConversations();
    });

    document.querySelectorAll('[data-single-select]').forEach((group) => {
        group.addEventListener('click', (event) => {
            const target = event.target.closest('.option-btn');
            if (!target) return;
            group.querySelectorAll('.option-btn').forEach((btn) => btn.classList.remove('selected'));
            target.classList.add('selected');
            if (group === stageGroup) {
                toggleStudentSections();
            }
        });
    });

    document.querySelectorAll('.interest-tags .option-btn').forEach((button) => {
        button.addEventListener('click', () => button.classList.toggle('selected'));
    });

    function toggleStudentSections() {
        const stageType = stageGroup?.querySelector('.option-btn.selected')?.dataset.stage || 'student';
        const isStudent = stageType === 'student';
        studentOnlySections.forEach((section) => {
            section.style.display = isStudent ? '' : 'none';
        });
    }

    toggleStudentSections();

    form?.addEventListener('submit', (event) => {
        event.preventDefault();
        const nextUrl = form.querySelector('.submit-btn')?.dataset.nextUrl;
        const selectedStageBtn = stageGroup?.querySelector('.option-btn.selected');
        const stageLabel = selectedStageBtn?.textContent.trim() || '';
        const stageType = selectedStageBtn?.dataset.stage || 'student';
        const major = stageType === 'student'
            ? majorGroup?.querySelector('.option-btn.selected')?.textContent.trim() || ''
            : '';
        const interests = stageType === 'student'
            ? Array.from(form.querySelectorAll('.interest-tags .option-btn.selected')).map((btn) => btn.textContent.trim())
            : [];

        const profile = {
            name: '',
            careerStage: stageLabel,
            stageType,
            major,
            interests,
        };
        sessionStorage.setItem('chatbotUserProfile', JSON.stringify(profile));

        if (nextUrl) {
            window.location.href = nextUrl;
        }
    });
});
