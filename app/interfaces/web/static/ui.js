(function () {
    const TEXT_SELECTOR = 'input:not([type="hidden"]):not([type="checkbox"]):not([type="radio"]), select, textarea';

    function enhanceAllForms(root = document) {
        root.querySelectorAll("form").forEach(enhanceForm);
        root.querySelectorAll(".inline-actions").forEach((node) => node.classList.add("ui-form-actions"));
        root.querySelectorAll(".form-grid, .settings-field-grid, .dashboard-filter-grid, .finance-filter-grid, .appointments-filter-grid, .orders-filter-grid, .selector-grid").forEach((node) => {
            node.classList.add("ui-field-grid");
        });
    }

    function enhanceForm(form) {
        if (!(form instanceof HTMLFormElement)) {
            return;
        }
        form.classList.add("ui-form");
        form.querySelectorAll("label").forEach(enhanceFieldWrapper);
        form.querySelectorAll(TEXT_SELECTOR).forEach((field) => {
            field.classList.add("ui-control");
            field.dataset.uiBound = field.dataset.uiBound || "true";
        });
    }

    function enhanceFieldWrapper(label) {
        if (!(label instanceof HTMLElement)) {
            return;
        }
        const control = label.querySelector(TEXT_SELECTOR);
        if (!control) {
            return;
        }
        label.classList.add("ui-field");
        const heading = label.querySelector(":scope > span");
        if (heading) {
            heading.classList.add("ui-field-label");
            control.dataset.label = control.dataset.label || heading.textContent.trim();
        }
        control.classList.add("ui-control");
    }

    function clearValidation(form) {
        if (!(form instanceof HTMLElement)) {
            return;
        }
        form.querySelectorAll(`${TEXT_SELECTOR}, .field-invalid`).forEach((field) => {
            clearFieldState(field);
        });
        form.querySelectorAll(".form-error").forEach((node) => node.classList.add("hidden"));
    }

    function validateForm(form) {
        if (!(form instanceof HTMLFormElement)) {
            return true;
        }
        let firstInvalid = null;
        form.querySelectorAll(TEXT_SELECTOR).forEach((field) => {
            if (!(field instanceof HTMLElement) || field.hasAttribute("disabled")) {
                return;
            }
            const isInvalid = "checkValidity" in field && !field.checkValidity();
            if (isInvalid) {
                const message = buildValidationMessage(field);
                markInvalid(field, message);
                if (!firstInvalid) {
                    firstInvalid = field;
                }
                return;
            }
            clearFieldState(field);
        });
        if (firstInvalid) {
            firstInvalid.focus();
            return false;
        }
        return true;
    }

    function markInvalid(field, message) {
        if (!(field instanceof HTMLElement)) {
            return;
        }
        field.classList.add("field-invalid");
        field.classList.remove("field-success");
        const wrapper = findWrapper(field);
        wrapper?.classList.add("is-invalid");
        wrapper?.classList.remove("is-success");
        setFieldMessage(field, message, "error");
    }

    function markSuccess(field, message = "") {
        if (!(field instanceof HTMLElement)) {
            return;
        }
        field.classList.remove("field-invalid");
        field.classList.add("field-success");
        const wrapper = findWrapper(field);
        wrapper?.classList.remove("is-invalid");
        wrapper?.classList.add("is-success");
        setFieldMessage(field, message, "success");
    }

    function clearFieldState(field) {
        if (!(field instanceof HTMLElement)) {
            return;
        }
        field.classList.remove("field-invalid", "field-success");
        const wrapper = findWrapper(field);
        wrapper?.classList.remove("is-invalid", "is-success");
        removeFieldMessage(field);
    }

    function setFieldMessage(field, message, tone) {
        const wrapper = findWrapper(field);
        if (!wrapper) {
            return;
        }
        let node = wrapper.querySelector(".ui-field-message");
        if (!message) {
            node?.remove();
            return;
        }
        if (!node) {
            node = document.createElement("small");
            node.className = "ui-field-message";
            wrapper.appendChild(node);
        }
        node.textContent = message;
        node.dataset.tone = tone || "error";
    }

    function removeFieldMessage(field) {
        const wrapper = findWrapper(field);
        wrapper?.querySelector(".ui-field-message")?.remove();
    }

    function findWrapper(field) {
        return field.closest("label, .ui-field, .inline-field");
    }

    function buildValidationMessage(field) {
        const label = field.dataset.label || field.getAttribute("aria-label") || "Campo";
        const validity = field.validity || {};
        if (validity.valueMissing) {
            return `${label} e obrigatorio.`;
        }
        if (validity.typeMismatch) {
            return `${label} precisa ter um formato valido.`;
        }
        if (validity.patternMismatch) {
            return `${label} esta fora do formato esperado.`;
        }
        if (validity.rangeOverflow || validity.rangeUnderflow) {
            return `${label} esta fora do intervalo permitido.`;
        }
        if (validity.tooShort || validity.tooLong) {
            return `${label} precisa respeitar o tamanho permitido.`;
        }
        return `${label} precisa ser revisado.`;
    }

    window.SysPragasUI = {
        enhanceAllForms,
        enhanceForm,
        validateForm,
        clearValidation,
        markInvalid,
        markSuccess,
        clearFieldState,
        setFieldMessage,
    };
})();
