(function (window) {
    function ProfileModal(root) {
        this.root = root;
        this.form = root.querySelector('[data-profile-form]');
        this.titleInput = root.querySelector('[data-profile-title]');
        this.nameInput = root.querySelector('[data-profile-name]');
        this.stageGroup = root.querySelector('[data-modal-stage]');
        this.majorGroup = root.querySelector('[data-modal-major]');
        this.interestsContainer = root.querySelector('[data-modal-interests]');
        this.studentSections = root.querySelectorAll('[data-modal-student]');
        this.useExistingBtn = root.querySelector('[data-profile-use-existing]');
        this.closeButtons = root.querySelectorAll('[data-profile-close]');
        this.stageType = '';
        this.callbacks = {};

        this._bindEvents();
        this._toggleStudentSections();
    }

    ProfileModal.prototype._bindEvents = function () {
        var self = this;

        this.form.addEventListener('submit', function (event) {
            event.preventDefault();
            var payload = self._collectProfile();
            if (self.callbacks.onSubmit) {
                self.callbacks.onSubmit(payload);
            }
            self.close();
        });

        if (this.useExistingBtn) {
            this.useExistingBtn.addEventListener('click', function () {
                if (self.callbacks.onUseExisting) {
                    self.callbacks.onUseExisting();
                }
                self.close();
            });
        }

        this.closeButtons.forEach(function (btn) {
            btn.addEventListener('click', function () {
                self.close();
            });
        });

        this.stageGroup?.addEventListener('click', function (event) {
            var target = event.target.closest('.option-btn');
            if (!target) return;
            self.stageGroup.querySelectorAll('.option-btn').forEach(function (btn) {
                btn.classList.remove('selected');
            });
            target.classList.add('selected');
            self.stageType = target.dataset.stage || '';
            self._toggleStudentSections();
        });

        this.majorGroup?.addEventListener('click', function (event) {
            if (self.stageType !== 'student') return;
            var target = event.target.closest('.option-btn');
            if (!target) return;
            self.majorGroup.querySelectorAll('.option-btn').forEach(function (btn) {
                btn.classList.remove('selected');
            });
            target.classList.add('selected');
        });

        this.interestsContainer?.addEventListener('click', function (event) {
            if (self.stageType !== 'student') return;
            var target = event.target.closest('.option-btn');
            if (!target) return;
            target.classList.toggle('selected');
        });
    };

    ProfileModal.prototype._toggleStudentSections = function () {
        var isStudent = this.stageType === 'student';
        this.studentSections.forEach(function (section) {
            section.style.display = isStudent ? '' : 'none';
        });
        if (!isStudent) {
            this.majorGroup?.querySelectorAll('.option-btn').forEach(function (btn) {
                btn.classList.remove('selected');
            });
            this.interestsContainer?.querySelectorAll('.option-btn').forEach(function (btn) {
                btn.classList.remove('selected');
            });
        }
    };

    ProfileModal.prototype._collectProfile = function () {
        var stageBtn = this.stageGroup?.querySelector('.option-btn.selected');
        var stageType = stageBtn?.dataset.stage || '';
        var stageLabel = stageBtn?.textContent.trim() || '';
        var majorBtn = this.majorGroup?.querySelector('.option-btn.selected');
        var interests = [];

        this.interestsContainer?.querySelectorAll('.option-btn.selected').forEach(function (btn) {
            interests.push(btn.textContent.trim());
        });

        return {
            title: this.titleInput?.value.trim() || '',
            profile: {
                name: this.nameInput?.value.trim() || '',
                careerStage: stageLabel,
                stageType: stageType,
                major: stageType === 'student' ? (majorBtn?.textContent.trim() || '') : '',
                interests: stageType === 'student' ? interests : [],
            },
        };
    };

    ProfileModal.prototype.open = function (options) {
        var initial = options?.initialProfile || {};
        var initialTitle = options?.initialTitle || '';
        this.titleInput && (this.titleInput.value = initialTitle);
        this.nameInput && (this.nameInput.value = initial.name || '');

        this.stageType = initial.stageType || '';

        this.stageType = initial.stageType || '';

        if (this.stageGroup) {
            var buttons = Array.from(this.stageGroup.querySelectorAll('.option-btn'));
            buttons.forEach(function (btn) {
                btn.classList.remove('selected');
            });
            var target = buttons.find(function (btn) {
                return btn.textContent.trim() === initial.careerStage;
            }) || null;
            if (target) {
                target.classList.add('selected');
                this.stageType = target.dataset.stage || this.stageType;
            }
        }

        if (this.majorGroup) {
            var majorButtons = Array.from(this.majorGroup.querySelectorAll('.option-btn'));
            majorButtons.forEach(function (btn) {
                btn.classList.remove('selected');
            });
            if (initial.stageType === 'student' && initial.major) {
                var majorTarget = majorButtons.find(function (btn) {
                    return btn.textContent.trim() === initial.major;
                });
                majorTarget?.classList.add('selected');
            }
        }

        if (this.interestsContainer) {
            var initialSet = (initial.stageType === 'student' && Array.isArray(initial.interests))
                ? new Set(initial.interests)
                : new Set();
            this.interestsContainer.querySelectorAll('.option-btn').forEach(function (btn) {
                var text = btn.textContent.trim();
                btn.classList.toggle('selected', initialSet.has(text));
            });
        }

        this._toggleStudentSections();

        this.callbacks = {
            onSubmit: options?.onSubmit,
            onUseExisting: options?.onUseExisting,
        };

        this.root.hidden = false;
        document.body.style.overflow = 'hidden';
    };

    ProfileModal.prototype.close = function () {
        this.root.hidden = true;
        document.body.style.overflow = '';
    };

    window.initProfileModal = function (selector) {
        var root = document.querySelector(selector);
        if (!root) return null;
        return new ProfileModal(root);
    };
})(window);
