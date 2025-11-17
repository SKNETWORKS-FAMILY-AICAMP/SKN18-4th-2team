document.addEventListener('DOMContentLoaded', () => {
    const layout = document.querySelector('.chat-layout');
    const detailUrl = layout?.dataset.chatDetailUrl || '';
    const conversationList = document.querySelector('[data-conversation-list]');
    const newChatButton = document.querySelector('[data-add-conversation]');
    const form = document.querySelector('.user-info-form');
    const stageGroup = document.querySelector('[data-stage-select]');
    const majorGroup = document.querySelector('[data-major-select]');
    const studentOnlySections = document.querySelectorAll('[data-student-only]');
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
        if (!conversationList) return;
        ConversationStore.renderList(conversationList, {
            onSelect: (conversation) => redirectToConversation(conversation),
        });
    }

    renderConversations();

    newChatButton?.addEventListener('click', () => {
        requestProfile({ title: '새 대화', profile: {}, forceBlank: true }).then((result) => {
            if (!result) return;
            const conversation = ConversationStore.create(
                result.title || '새 대화',
                [],
                result.profile || null,
            );
            if (result.profile) {
                sessionStorage.setItem('chatbotUserProfile', JSON.stringify(result.profile));
            }
            renderConversations();
        });
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
