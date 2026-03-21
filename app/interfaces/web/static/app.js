const state = {
    token: localStorage.getItem("syspragas_token") || "",
    user: null,
    customers: [],
    products: [],
    pests: [],
    technicians: [],
    workOrders: [],
    finance: [],
    cashLedger: [],
    financeDashboard: null,
    users: [],
    licenses: [],
    editing: {
        customer: null,
        product: null,
        pest: null,
        technician: null,
        finance: null,
        workOrder: null,
        user: null,
        license: null,
    },
    filters: {
        dashboardSearch: "",
        dashboardStatus: "todos",
        dashboardStock: "alerta",
        dashboardFinance: "pendente",
    },
};

const viewTitles = {
    dashboard: "Dashboard",
    clientes: "Clientes",
    produtos: "Produtos",
    pragas: "Pragas",
    tecnicos: "Tecnicos",
    ordens: "Ordens de servico",
    financeiro: "Financeiro",
    usuarios: "Usuarios",
    licencas: "Licencas",
};

const dashboardCharts = {
    status: null,
    finance: null,
};

const dataTableLanguage = {
    emptyTable: "Nenhum registro disponivel",
    info: "Mostrando _START_ ate _END_ de _TOTAL_ registros",
    infoEmpty: "Mostrando 0 ate 0 de 0 registros",
    infoFiltered: "(filtrado de _MAX_ registros)",
    lengthMenu: "Mostrar _MENU_ registros",
    loadingRecords: "Carregando...",
    processing: "Processando...",
    search: "Buscar:",
    zeroRecords: "Nenhum registro encontrado",
    paginate: {
        first: "Primeiro",
        last: "Ultimo",
        next: "Proximo",
        previous: "Anterior",
    },
};

document.addEventListener("DOMContentLoaded", () => {
    buildForms();
    bindNavigation();
    bindAuth();
    bindDashboardFilters();

    if (state.token) {
        bootstrapApp().catch(() => showLogin());
    } else {
        showLogin();
    }
});

function bindNavigation() {
    document.querySelectorAll(".nav-link[data-view]").forEach((button) => {
        button.addEventListener("click", (event) => {
            event.preventDefault();
            switchView(button.dataset.view);
        });
    });
}

function bindAuth() {
    document.getElementById("logout-button").addEventListener("click", logout);
    document.getElementById("login-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const form = new FormData(event.currentTarget);
        setSyncStatus("Autenticando...");
        try {
            const result = await apiFetch(
                "/api/v1/auth/login",
                {
                    method: "POST",
                    body: JSON.stringify({
                        username: form.get("username"),
                        password: form.get("password"),
                    }),
                },
                false,
            );
            state.token = result.access_token;
            localStorage.setItem("syspragas_token", state.token);
            await bootstrapApp();
            event.currentTarget.reset();
        } catch (error) {
            const errorNode = document.getElementById("login-error");
            errorNode.textContent = error.message;
            errorNode.classList.remove("hidden");
            setSyncStatus("Falha no login");
        }
    });
}

function bindDashboardFilters() {
    document.getElementById("dashboard-search").addEventListener("input", (event) => {
        state.filters.dashboardSearch = event.target.value.trim().toLowerCase();
        renderDashboard();
    });
    document.getElementById("dashboard-status-filter").addEventListener("change", (event) => {
        state.filters.dashboardStatus = event.target.value;
        renderDashboard();
    });
    document.getElementById("dashboard-stock-filter").addEventListener("change", (event) => {
        state.filters.dashboardStock = event.target.value;
        renderDashboard();
    });
    document.getElementById("dashboard-finance-filter").addEventListener("change", (event) => {
        state.filters.dashboardFinance = event.target.value;
        renderDashboard();
    });
}

async function bootstrapApp() {
    document.getElementById("login-error").classList.add("hidden");
    state.user = await apiFetch("/api/v1/auth/me");
    await loadAllData();
    document.getElementById("current-user-name").textContent = `${state.user.nome} - ${state.user.role}`;
    toggleMasterSections();
    document.getElementById("login-screen").classList.add("hidden");
    document.getElementById("app-shell").classList.remove("hidden");
    switchView("dashboard");
}

function showLogin() {
    document.getElementById("app-shell").classList.add("hidden");
    document.getElementById("login-screen").classList.remove("hidden");
    setSyncStatus("Sessao local");
}

function logout() {
    state.token = "";
    state.user = null;
    localStorage.removeItem("syspragas_token");
    showLogin();
}

async function loadAllData() {
    setSyncStatus("Sincronizando...");
    const basePromises = [
        apiFetch("/api/v1/clientes"),
        apiFetch("/api/v1/produtos"),
        apiFetch("/api/v1/pragas"),
        apiFetch("/api/v1/tecnicos"),
        apiFetch("/api/v1/os"),
    ];
    const canAccessFinance = state.user?.role === "master" || state.user?.role === "admin";
    if (canAccessFinance) {
        basePromises.push(apiFetch("/api/v1/financeiro"));
        basePromises.push(apiFetch("/api/v1/financeiro/caixa"));
        basePromises.push(apiFetch("/api/v1/financeiro/dashboard"));
    }
    const results = await Promise.all(basePromises);
    const [customers, products, pests, technicians, workOrders] = results;
    const finance = canAccessFinance ? results[5] : [];
    const cashLedger = canAccessFinance ? results[6] : [];
    const financeDashboard = canAccessFinance ? results[7] : null;

    state.customers = customers;
    state.products = products;
    state.pests = pests;
    state.technicians = technicians;
    state.workOrders = workOrders;
    state.finance = finance;
    state.cashLedger = cashLedger;
    state.financeDashboard = financeDashboard;

    if (state.user?.role === "master") {
        const [users, licenses] = await Promise.all([
            apiFetch("/api/v1/usuarios"),
            apiFetch("/api/v1/licencas"),
        ]);
        state.users = users;
        state.licenses = licenses;
    } else {
        state.users = [];
        state.licenses = [];
    }

    hydrateDynamicControls();
    syncEditingModes();
    renderAll();
    setSyncStatus("Sincronizado");
}

async function apiFetch(url, options = {}, withAuth = true) {
    const headers = { ...(options.headers || {}) };
    if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
        headers["Content-Type"] = "application/json";
    }
    if (withAuth && state.token) {
        headers.Authorization = `Bearer ${state.token}`;
    }

    const response = await fetch(url, { ...options, headers });
    if (!response.ok) {
        const text = await response.text();
        let detail = "Nao foi possivel concluir a operacao.";
        try {
            detail = JSON.parse(text).detail || detail;
        } catch {
            detail = text || detail;
        }
        if (response.status === 401) {
            logout();
        }
        throw new Error(detail);
    }

    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
        return response.json();
    }
    return response.blob();
}

function switchView(view) {
    document.querySelectorAll(".nav-link[data-view]").forEach((button) => {
        button.classList.toggle("active", button.dataset.view === view);
    });
    document.querySelectorAll(".view").forEach((section) => {
        section.classList.toggle("active", section.id === `view-${view}`);
    });
    document.getElementById("view-title").textContent = viewTitles[view] || viewTitles.dashboard;
}

function renderAll() {
    renderDashboard();
    renderCustomers();
    renderProducts();
    renderPests();
    renderTechnicians();
    renderWorkOrders();
    renderFinance();
    renderUsers();
    renderLicenses();
}

function toggleMasterSections() {
    const isMaster = state.user?.role === "master";
    document.querySelectorAll(".master-only").forEach((node) => {
        node.classList.toggle("hidden", !isMaster);
    });
    const canAccessFinance = state.user?.role === "master" || state.user?.role === "admin";
    document.querySelectorAll(".finance-only").forEach((node) => {
        node.classList.toggle("hidden", !canAccessFinance);
    });
}

function formActionHtml(kind, saveLabel, cancelLabel) {
    return `
        <div class="inline-actions">
            <button type="submit" class="btn btn-success" data-save-button="${kind}">${saveLabel}</button>
            <button type="button" class="btn btn-default ghost-button hidden" data-cancel-button="${kind}">${cancelLabel}</button>
        </div>
        <p class="origin-note hidden" data-mode-note="${kind}"></p>
        <p class="form-error hidden"></p>
    `;
}

function buildForms() {
    document.getElementById("customer-form").innerHTML = `
        <div class="form-grid">
            <label><span>Razao social</span><input name="razao_social" required></label>
            <label><span>CPF/CNPJ</span><input name="cpf_cnpj" required></label>
            <label class="full-width"><span>Endereco</span><input name="endereco" required></label>
            <label><span>Cidade</span><input name="cidade" required></label>
            <label><span>Estado</span><input name="estado" maxlength="2" required></label>
            <label><span>Telefone</span><input name="telefone" required></label>
            <label class="full-width"><span>Contato</span><input name="contato" required></label>
        </div>
        ${formActionHtml("customer", "Salvar cliente", "Cancelar edicao")}
    `;

    document.getElementById("product-form").innerHTML = `
        <div class="form-grid">
            <label><span>Nome</span><input name="nome" required></label>
            <label><span>Principio ativo</span><input name="principio_ativo" required></label>
            <label><span>Grupo quimico</span><input name="grupo_quimico" required></label>
            <label><span>Toxicidade</span><input name="toxicidade" required></label>
            <label><span>Concentracao</span><input name="concentracao" required></label>
            <label><span>Registro MS</span><input name="registro_ms" required></label>
            <label><span>Estoque atual</span><input name="estoque_atual" type="number" min="0" step="0.01" value="0"></label>
            <label><span>Estoque minimo</span><input name="estoque_minimo" type="number" min="0" step="0.01" value="0"></label>
        </div>
        <div class="section-heading">
            <h3>Importacoes de estoque</h3>
            <p>Use XML da NF-e ou CSV para dar entrada em produtos e registrar a despesa no financeiro.</p>
        </div>
        <div class="form-grid">
            <label class="full-width">
                <span>Modelos de importacao</span>
                <div class="inline-actions">
                    <a class="btn btn-default ghost-button" href="/static/import_templates/modelo_importacao_produtos_v3_1.csv" target="_blank" rel="noreferrer">Baixar CSV modelo</a>
                    <a class="btn btn-default ghost-button" href="/static/import_templates/modelo_importacao_produtos_v3_1.xlsx" target="_blank" rel="noreferrer">Baixar planilha modelo</a>
                </div>
            </label>
            <label class="full-width"><span>Arquivo XML</span><input id="product-xml-file" type="file" accept=".xml,application/xml"></label>
            <label><span>Registrar no financeiro</span>
                <select id="product-xml-finance">
                    <option value="true">Sim</option>
                    <option value="false">Nao</option>
                </select>
            </label>
            <div class="inline-actions">
                <button type="button" class="btn btn-default ghost-button" id="product-xml-import-button">Importar XML</button>
            </div>
            <label class="full-width"><span>Arquivo CSV</span><input id="product-csv-file" type="file" accept=".csv,text/csv"></label>
            <label><span>Registrar no financeiro</span>
                <select id="product-csv-finance">
                    <option value="true">Sim</option>
                    <option value="false">Nao</option>
                </select>
            </label>
            <div class="inline-actions">
                <button type="button" class="btn btn-default ghost-button" id="product-csv-import-button">Importar CSV</button>
            </div>
        </div>
        ${formActionHtml("product", "Salvar produto", "Cancelar edicao")}
    `;

    document.getElementById("pest-form").innerHTML = `
        <div class="form-grid">
            <label><span>Nome comum</span><input name="nome_comum" required></label>
            <label><span>Nome cientifico</span><input name="nome_cientifico" required></label>
            <label class="full-width"><span>Descricao</span><textarea name="descricao" required></textarea></label>
        </div>
        ${formActionHtml("pest", "Salvar praga", "Cancelar edicao")}
    `;

    document.getElementById("technician-form").innerHTML = `
        <div class="form-grid">
            <label><span>Nome</span><input name="nome" required></label>
            <label><span>Registro</span><input name="registro" required></label>
            <label><span>Telefone</span><input name="telefone" required></label>
            <label><span>Status</span>
                <select name="ativo">
                    <option value="true">Ativo</option>
                    <option value="false">Inativo</option>
                </select>
            </label>
        </div>
        ${formActionHtml("technician", "Salvar tecnico", "Cancelar edicao")}
    `;

    document.getElementById("finance-form").innerHTML = `
        <div class="form-grid">
            <label><span>Tipo</span>
                <select name="tipo">
                    <option value="receita">Receita</option>
                    <option value="despesa">Despesa</option>
                </select>
            </label>
            <label><span>Valor</span><input name="valor" type="number" step="0.01" min="0.01" required></label>
            <label class="full-width"><span>Descricao</span><input name="descricao" required></label>
            <label><span>Vencimento</span><input name="vencimento" type="date" required></label>
            <label><span>Status</span>
                <select name="status">
                    <option value="pendente">Pendente</option>
                    <option value="pago">Pago</option>
                    <option value="atrasado">Atrasado</option>
                </select>
            </label>
            <label><span>Categoria</span><input name="categoria" placeholder="Ex.: Operacional"></label>
            <label><span>Fornecedor</span><input name="fornecedor_nome" placeholder="Opcional"></label>
            <label><span>Parcelas</span><input name="total_parcelas" type="number" min="1" value="1" required></label>
            <label><span>Referencia</span><input name="referencia" placeholder="NF, contrato, OS"></label>
            <label class="full-width"><span>Cliente vinculado</span><select name="cliente_id"><option value="">Sem cliente</option></select></label>
            <label class="full-width"><span>Observacoes</span><textarea name="observacoes"></textarea></label>
        </div>
        ${formActionHtml("finance", "Salvar lancamento", "Cancelar edicao")}
    `;

    document.getElementById("work-order-form").innerHTML = `
        <div class="form-grid">
            <label><span>Numero</span><input name="numero" required></label>
            <label><span>Cliente</span><select name="cliente_id" required></select></label>
            <label><span>Tecnico</span><select name="tecnico_id" required></select></label>
            <label><span>Local de execucao</span><input name="local_execucao" required></label>
            <label><span>Data de execucao</span><input name="data_execucao" type="date" required></label>
            <label><span>Garantia ate</span><input name="garantia_ate" type="date" required></label>
            <label><span>Hora inicio</span><input name="hora_inicio" type="time" required></label>
            <label><span>Hora fim</span><input name="hora_fim" type="time"></label>
            <label><span>Status</span>
                <select name="status">
                    <option value="aberta">Aberta</option>
                    <option value="em_execucao">Em execucao</option>
                    <option value="concluida">Concluida</option>
                    <option value="cancelada">Cancelada</option>
                </select>
            </label>
            <label><span>Valor do servico</span><input name="valor_servico" type="number" step="0.01" min="0" value="0"></label>
            <label class="full-width"><span>Observacoes</span><textarea name="observacoes"></textarea></label>
        </div>
        <div class="section-heading">
            <h3>Produtos aplicados</h3>
            <p class="hint">Cada item reduz o estoque automaticamente.</p>
        </div>
        <div id="products-list"></div>
        <div class="inline-actions">
            <button type="button" id="add-product-row">Adicionar produto</button>
        </div>
        <div class="section-heading">
            <h3>Pragas relacionadas</h3>
            <p class="hint">Selecione as pragas vinculadas a esta execucao.</p>
        </div>
        <div id="pests-selector" class="selector-grid"></div>
        <label><span>Gerar financeiro automatico</span>
            <select name="gerar_financeiro">
                <option value="true">Sim</option>
                <option value="false">Nao</option>
            </select>
        </label>
        ${formActionHtml("workOrder", "Salvar ordem de servico", "Cancelar edicao")}
    `;

    document.getElementById("user-form").innerHTML = `
        <div class="form-grid">
            <label><span>Nome</span><input name="nome" required></label>
            <label><span>Usuario</span><input name="username" required></label>
            <label><span>Senha</span><input name="password" type="password" required></label>
            <label><span>Perfil</span>
                <select name="role">
                    <option value="operador">OPERADOR / TECNICO</option>
                    <option value="admin">ADMIN</option>
                    <option value="master">MASTER</option>
                </select>
            </label>
            <label><span>Status</span>
                <select name="is_active">
                    <option value="true">Ativo</option>
                    <option value="false">Inativo</option>
                </select>
            </label>
        </div>
        ${formActionHtml("user", "Salvar usuario", "Cancelar edicao")}
    `;

    document.getElementById("license-form").innerHTML = `
        <div class="form-grid">
            <label class="full-width"><span>Descricao</span><input name="descricao" required></label>
            <label><span>Inicio</span><input name="start_date" type="date" required></label>
            <label><span>Fim</span><input name="end_date" type="date" required></label>
            <label><span>Maximo de usuarios</span><input name="max_users" type="number" min="1" value="10" required></label>
            <label><span>Status</span>
                <select name="status">
                    <option value="ativa">Ativa</option>
                    <option value="suspensa">Suspensa</option>
                    <option value="expirada">Expirada</option>
                </select>
            </label>
            <label class="full-width"><span>Observacoes</span><textarea name="notes"></textarea></label>
        </div>
        ${formActionHtml("license", "Salvar licenca", "Cancelar edicao")}
    `;

    bindCrudForms();
    bindProductXmlImport();
    bindProductCsvImport();
    document.getElementById("add-product-row").addEventListener("click", () => addProductRow());
    addProductRow();
}

function bindProductXmlImport() {
    const button = document.getElementById("product-xml-import-button");
    if (!button) {
        return;
    }
    button.addEventListener("click", async () => {
        const fileInput = document.getElementById("product-xml-file");
        const financeSelect = document.getElementById("product-xml-finance");
        const file = fileInput?.files?.[0];
        if (!file) {
            toast("Selecione um arquivo XML da nota para importar.");
            return;
        }

        const formData = new FormData();
        formData.append("xml_file", file);

        button.disabled = true;
        setSyncStatus("Importando XML...");
        try {
            const result = await apiFetch(
                `/api/v1/produtos/importar-xml?registrar_financeiro=${financeSelect.value}`,
                {
                    method: "POST",
                    body: formData,
                },
            );
            fileInput.value = "";
            await loadAllData();
            toast(
                `XML importado: ${result.produtos_processados} item(ns), ${result.produtos_criados} criado(s) e ${result.produtos_atualizados} atualizado(s).`,
            );
        } catch (error) {
            toast(error.message);
            setSyncStatus("Falha na importacao");
        } finally {
            button.disabled = false;
            setSyncStatus("Sincronizado");
        }
    });
}

function bindProductCsvImport() {
    const button = document.getElementById("product-csv-import-button");
    if (!button) {
        return;
    }
    button.addEventListener("click", async () => {
        const fileInput = document.getElementById("product-csv-file");
        const financeSelect = document.getElementById("product-csv-finance");
        const file = fileInput?.files?.[0];
        if (!file) {
            toast("Selecione um arquivo CSV para importar.");
            return;
        }

        const formData = new FormData();
        formData.append("csv_file", file);

        button.disabled = true;
        setSyncStatus("Importando CSV...");
        try {
            const result = await apiFetch(
                `/api/v1/produtos/importar-csv?registrar_financeiro=${financeSelect.value}`,
                {
                    method: "POST",
                    body: formData,
                },
            );
            fileInput.value = "";
            await loadAllData();
            toast(
                `CSV importado: ${result.produtos_processados} item(ns), ${result.produtos_criados} criado(s) e ${result.produtos_atualizados} atualizado(s).`,
            );
        } catch (error) {
            toast(error.message);
            setSyncStatus("Falha na importacao");
        } finally {
            button.disabled = false;
            setSyncStatus("Sincronizado");
        }
    });
}

function bindCrudForms() {
    bindForm("customer-form", "customer", async (form) => {
        await submitCrud("customer", "/api/v1/clientes", objectFromForm(form));
    });

    bindForm("product-form", "product", async (form) => {
        await submitCrud("product", "/api/v1/produtos", objectFromForm(form));
    });

    bindForm("pest-form", "pest", async (form) => {
        await submitCrud("pest", "/api/v1/pragas", objectFromForm(form));
    });

    bindForm("technician-form", "technician", async (form) => {
        const payload = objectFromForm(form);
        payload.ativo = payload.ativo === "true";
        await submitCrud("technician", "/api/v1/tecnicos", payload);
    });

    bindForm("finance-form", "finance", async (form) => {
        const payload = objectFromForm(form);
        payload.cliente_id = payload.cliente_id ? Number(payload.cliente_id) : null;
        payload.os_id = null;
        payload.total_parcelas = Number(payload.total_parcelas || 1);
        payload.parcela_atual = 1;
        payload.categoria = payload.categoria || null;
        payload.fornecedor_nome = payload.fornecedor_nome || null;
        payload.referencia = payload.referencia || null;
        payload.observacoes = payload.observacoes || null;
        payload.origem = "manual";
        await submitCrud("finance", "/api/v1/financeiro", payload);
    });

    bindForm("work-order-form", "workOrder", async (form) => {
        await submitCrud("workOrder", "/api/v1/os", getWorkOrderPayload(form));
        clearWorkOrderForm();
    });

    bindForm("user-form", "user", async (form) => {
        const payload = objectFromForm(form);
        payload.is_active = payload.is_active === "true";
        if (state.editing.user && !payload.password) {
            delete payload.password;
        }
        await submitCrud("user", "/api/v1/usuarios", payload);
    });

    bindForm("license-form", "license", async (form) => {
        const payload = objectFromForm(form);
        payload.max_users = Number(payload.max_users);
        payload.notes = payload.notes || null;
        await submitCrud("license", "/api/v1/licencas", payload);
    });
}

function bindForm(formId, kind, handler) {
    const form = document.getElementById(formId);
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const errorBox = form.querySelector(".form-error");
        errorBox.classList.add("hidden");
        try {
            await handler(form);
        } catch (error) {
            errorBox.textContent = error.message;
            errorBox.classList.remove("hidden");
        }
    });

    form.querySelector(`[data-cancel-button="${kind}"]`).addEventListener("click", () => {
        resetFormMode(kind);
    });
}

async function submitCrud(kind, baseUrl, payload) {
    const id = state.editing[kind];
    if (id) {
        await apiFetch(`${baseUrl}/${id}`, { method: "PUT", body: JSON.stringify(payload) });
    } else {
        await apiFetch(baseUrl, { method: "POST", body: JSON.stringify(payload) });
    }
    resetFormMode(kind);
    await afterMutation(id ? "Registro atualizado com sucesso." : "Registro salvo com sucesso.");
}

async function afterMutation(message) {
    await loadAllData();
    toast(message);
}

function objectFromForm(form) {
    return Object.fromEntries(new FormData(form).entries());
}

function hydrateDynamicControls() {
    setSelectOptions(document.querySelector('#finance-form [name="cliente_id"]'), state.customers, "id", "razao_social");
    setSelectOptions(document.querySelector('#work-order-form [name="cliente_id"]'), state.customers, "id", "razao_social");
    setSelectOptions(
        document.querySelector('#work-order-form [name="tecnico_id"]'),
        state.technicians.filter((item) => item.ativo),
        "id",
        "nome",
    );

    document.querySelectorAll(".product-select").forEach((select) => {
        setSelectOptions(select, state.products, "id", "nome");
    });

    const pestsSelector = document.getElementById("pests-selector");
    pestsSelector.innerHTML = state.pests.length
        ? state.pests
            .map(
                (pest) => `
            <label class="checkbox-chip">
                <input type="checkbox" name="pragas_ids" value="${pest.id}">
                <span>${escapeHtml(pest.nome_comum)}</span>
            </label>
        `,
            )
            .join("")
        : `<div class="empty-state">Cadastre pragas para vincular na OS.</div>`;
}

function setSelectOptions(select, items, valueKey, labelKey) {
    if (!select) {
        return;
    }
    const current = select.value;
    const blank = select.querySelector('option[value=""]');
    const blankOption = blank ? `<option value="">${escapeHtml(blank.textContent)}</option>` : "";
    select.innerHTML =
        blankOption +
        items
            .map((item) => `<option value="${item[valueKey]}">${escapeHtml(item[labelKey])}</option>`)
            .join("");
    if (current && select.querySelector(`option[value="${current}"]`)) {
        select.value = current;
    }
}

function addProductRow(values = {}) {
    const list = document.getElementById("products-list");
    const row = document.createElement("div");
    row.className = "product-item-row";
    row.innerHTML = `
        <select class="product-select" required></select>
        <input type="number" class="product-quantity" min="0.01" step="0.01" placeholder="Quantidade" required>
        <input type="text" class="product-dilution" placeholder="Diluicao" required>
        <button type="button" class="btn btn-default ghost-button remove-product">Remover</button>
    `;
    row.querySelector(".remove-product").addEventListener("click", () => row.remove());
    list.appendChild(row);
    setSelectOptions(row.querySelector(".product-select"), state.products, "id", "nome");
    if (values.produto_id) {
        row.querySelector(".product-select").value = String(values.produto_id);
    }
    if (values.quantidade) {
        row.querySelector(".product-quantity").value = values.quantidade;
    }
    if (values.diluicao) {
        row.querySelector(".product-dilution").value = values.diluicao;
    }
}

function clearWorkOrderForm() {
    const form = document.getElementById("work-order-form");
    form.reset();
    document.getElementById("products-list").innerHTML = "";
    addProductRow();
    form.querySelectorAll('input[name="pragas_ids"]').forEach((checkbox) => {
        checkbox.checked = false;
    });
}

function getWorkOrderPayload(form) {
    const raw = objectFromForm(form);
    const produtos = Array.from(form.querySelectorAll(".product-item-row"))
        .map((row) => ({
            produto_id: Number(row.querySelector(".product-select").value),
            quantidade: row.querySelector(".product-quantity").value,
            diluicao: row.querySelector(".product-dilution").value,
        }))
        .filter((item) => item.produto_id);

    return {
        numero: raw.numero,
        cliente_id: Number(raw.cliente_id),
        tecnico_id: Number(raw.tecnico_id),
        data_execucao: raw.data_execucao,
        hora_inicio: raw.hora_inicio ? `${raw.hora_inicio}:00` : null,
        hora_fim: raw.hora_fim ? `${raw.hora_fim}:00` : null,
        local_execucao: raw.local_execucao,
        observacoes: raw.observacoes || null,
        garantia_ate: raw.garantia_ate,
        status: raw.status,
        valor_servico: raw.valor_servico || "0",
        produtos,
        pragas_ids: Array.from(form.querySelectorAll('input[name="pragas_ids"]:checked')).map((item) => Number(item.value)),
        gerar_financeiro: raw.gerar_financeiro === "true",
    };
}

function renderDashboard() {
    const filteredOrders = getFilteredWorkOrders();
    const filteredStock = getFilteredProductsForDashboard();
    const filteredFinance = getFilteredFinance();

    document.getElementById("metrics-grid").innerHTML = [
        metric("Clientes", state.customers.length, "Base operacional ativa"),
        metric("Produtos", filteredStock.length, "Produtos visiveis no filtro"),
        metric("Ordens", filteredOrders.length, "Ordens encontradas"),
        metric("Financeiro", filteredFinance.length, "Lancamentos no radar"),
    ].join("");

    setTableContent(
        "dashboard-os-table",
        ["Numero", "Cliente", "Tecnico", "Data", "Valor"],
        filteredOrders.slice(0, 8).map((item) => [
            item.numero,
            item.cliente.razao_social,
            item.tecnico.nome,
            formatDate(item.data_execucao),
            formatCurrency(item.valor_servico),
        ]),
        "Nenhuma ordem encontrada para os filtros atuais.",
        { pageLength: 4 },
    );

    document.getElementById("stock-alerts").innerHTML = filteredStock.length
        ? `<div class="alert-list">${filteredStock
            .slice(0, 8)
            .map(
                (item) => `
            <div class="alert-item">
                <div>
                    <strong>${escapeHtml(item.nome)}</strong>
                    <span class="origin-note">Minimo ${escapeHtml(String(item.estoque_minimo))}</span>
                </div>
                <span class="badge ${Number(item.estoque_atual) === 0 ? "danger" : "warn"}">${escapeHtml(String(item.estoque_atual))} em estoque</span>
            </div>
        `,
            )
            .join("")}</div>`
        : `<div class="empty-state">Nenhum produto corresponde ao filtro selecionado.</div>`;

    setTableContent(
        "dashboard-finance-table",
        ["Tipo", "Descricao", "Saldo", "Vencimento", "Status"],
        filteredFinance.slice(0, 8).map((item) => [
            badge(item.tipo, item.tipo === "despesa" ? "warn" : ""),
            item.descricao,
            formatCurrency(item.saldo_aberto ?? item.valor),
            formatDate(item.vencimento),
            badge(item.status, item.status === "atrasado" ? "danger" : item.status === "pago" ? "" : "warn"),
        ]),
        "Nenhum lancamento financeiro encontrado para os filtros atuais.",
        { pageLength: 4 },
    );

    renderDashboardWidgets(filteredOrders, filteredStock, filteredFinance);
    renderDashboardCharts(filteredOrders, filteredFinance);
}

function getFilteredWorkOrders() {
    return state.workOrders.filter((item) => {
        const matchesSearch = !state.filters.dashboardSearch || [
            item.numero,
            item.cliente.razao_social,
            item.tecnico.nome,
            item.local_execucao,
            item.observacoes || "",
        ]
            .join(" ")
            .toLowerCase()
            .includes(state.filters.dashboardSearch);
        const matchesStatus = state.filters.dashboardStatus === "todos" || item.status === state.filters.dashboardStatus;
        return matchesSearch && matchesStatus;
    });
}

function getFilteredProductsForDashboard() {
    return state.products.filter((item) => {
        const matchesSearch = !state.filters.dashboardSearch || [
            item.nome,
            item.principio_ativo,
            item.grupo_quimico,
        ]
            .join(" ")
            .toLowerCase()
            .includes(state.filters.dashboardSearch);
        if (!matchesSearch) {
            return false;
        }
        if (state.filters.dashboardStock === "todos") {
            return true;
        }
        if (state.filters.dashboardStock === "zerado") {
            return Number(item.estoque_atual) === 0;
        }
        return Number(item.estoque_atual) <= Number(item.estoque_minimo);
    });
}

function getFilteredFinance() {
    return state.finance.filter((item) => {
        const customerName = state.customers.find((customer) => customer.id === item.cliente_id)?.razao_social || "";
        const matchesSearch = !state.filters.dashboardSearch || [
            item.descricao,
            item.tipo,
            customerName,
            item.categoria || "",
            item.fornecedor_nome || "",
            item.referencia || "",
        ]
            .join(" ")
            .toLowerCase()
            .includes(state.filters.dashboardSearch);
        const matchesStatus = state.filters.dashboardFinance === "todos" || item.status === state.filters.dashboardFinance;
        return matchesSearch && matchesStatus;
    });
}

function renderCustomers() {
    setTableContent(
        "customers-table",
        ["Razao social", "Documento", "Cidade", "Contato", "Telefone", "Acoes"],
        state.customers.map((item) => [
            item.razao_social,
            item.cpf_cnpj,
            `${item.cidade}/${item.estado}`,
            item.contato,
            item.telefone,
            actionButtons("customer", item.id),
        ]),
        "Nenhum cliente cadastrado.",
        { nonSortableTargets: [5] },
    );
    bindEntityActions("customer");
}

function renderProducts() {
    setTableContent(
        "products-table",
        ["Produto", "Principio ativo", "Estoque", "Minimo", "Registro", "Acoes"],
        state.products.map((item) => [
            item.nome,
            item.principio_ativo,
            `${item.estoque_atual}`,
            `${item.estoque_minimo}`,
            item.registro_ms,
            actionButtons("product", item.id),
        ]),
        "Nenhum produto cadastrado.",
        { nonSortableTargets: [5] },
    );
    bindEntityActions("product");
}

function renderPests() {
    setTableContent(
        "pests-table",
        ["Nome comum", "Nome cientifico", "Descricao", "Acoes"],
        state.pests.map((item) => [item.nome_comum, item.nome_cientifico, item.descricao, actionButtons("pest", item.id)]),
        "Nenhuma praga cadastrada.",
        { nonSortableTargets: [3] },
    );
    bindEntityActions("pest");
}

function renderTechnicians() {
    setTableContent(
        "technicians-table",
        ["Tecnico", "Registro", "Telefone", "Status", "Acoes"],
        state.technicians.map((item) => [
            item.nome,
            item.registro,
            item.telefone,
            badge(item.ativo ? "Ativo" : "Inativo", item.ativo ? "" : "warn"),
            actionButtons("technician", item.id),
        ]),
        "Nenhum tecnico cadastrado.",
        { nonSortableTargets: [4] },
    );
    bindEntityActions("technician");
}

function renderWorkOrders() {
    setTableContent(
        "work-orders-table",
        ["Numero", "Cliente", "Tecnico", "Data", "Aplicacao", "Valor", "Acoes"],
        state.workOrders.map((item) => {
            const linkedFinance = state.finance.find((entry) => entry.os_id === item.id) || null;
            const quickActions = [];
            if (item.status !== "concluida" && item.status !== "cancelada") {
                quickActions.push(actionButton("complete-work-order", "Efetuar", `data-id="${item.id}"`));
            }
            if (userCanAccessFinance() && linkedFinance && linkedFinance.status !== "pago") {
                quickActions.push(actionButton("settle-work-order", "Dar baixa", `data-id="${item.id}"`));
            }
            return [
                item.numero,
                item.cliente.razao_social,
                item.tecnico.nome,
                formatDate(item.data_execucao),
                `${item.produtos.length} produto(s)`,
                formatCurrency(item.valor_servico),
                `<div class="toolbar">
                    ${badge(item.status.replaceAll("_", " "), "")}
                    <a href="#" class="subtle-link pdf-link" data-doc="os" data-id="${item.id}">OS PDF</a>
                    <a href="#" class="subtle-link pdf-link" data-doc="relatorio" data-id="${item.id}">Relatorio tecnico</a>
                    <a href="#" class="subtle-link pdf-link" data-doc="certificado" data-id="${item.id}">Certificado sanitario</a>
                    <a href="#" class="subtle-link pdf-link" data-doc="moldura" data-id="${item.id}">Certificado moldura</a>
                    ${quickActions.join("")}
                    <button type="button" class="ghost-button action-button secondary edit-entity" data-kind="workOrder" data-id="${item.id}">Editar</button>
                    <button type="button" class="ghost-button action-button danger delete-entity" data-kind="workOrder" data-id="${item.id}">Excluir</button>
                </div>`,
            ];
        }),
        "Nenhuma ordem de servico cadastrada.",
        { nonSortableTargets: [6], pageLength: 6 },
    );

    document.querySelectorAll(".pdf-link").forEach((link) => {
        link.addEventListener("click", async (event) => {
            event.preventDefault();
            try {
                const { id, doc } = event.currentTarget.dataset;
                const docUrlMap = {
                    os: `/api/v1/os/${id}/pdf`,
                    relatorio: `/api/v1/os/${id}/relatorio-tecnico.pdf`,
                    certificado: `/api/v1/os/${id}/certificado-sanitario.pdf`,
                    moldura: `/api/v1/os/${id}/certificado-moldura.pdf`,
                };
                const blob = await apiFetch(docUrlMap[doc]);
                const fileUrl = URL.createObjectURL(blob);
                window.open(fileUrl, "_blank", "noopener");
            } catch (error) {
                toast(error.message);
            }
        });
    });
    bindEntityActions("workOrder");
}

function renderFinance() {
    renderFinanceSummary();
    setTableContent(
        "finance-table",
        ["Tipo", "Descricao", "Categoria", "Valor", "Pago", "Saldo", "Vencimento", "Status", "Acoes"],
        state.finance.map((item) => {
            const payButton = item.status !== "pago" && Number(item.saldo_aberto ?? item.valor) > 0
                ? actionButton(
                    "pay-finance",
                    item.tipo === "receita" ? "Receber" : "Pagar",
                    `data-id="${item.id}" data-open-balance="${item.saldo_aberto ?? item.valor}"`,
                )
                : "";
            const parcelText = Number(item.total_parcelas || 1) > 1 ? `${item.parcela_atual}/${item.total_parcelas}` : "";
            const actions = item.os_id
                ? `<div class="toolbar"><span class="origin-note">Gerado pela OS ${item.os_id}</span>${parcelText ? `<span class="badge">${escapeHtml(parcelText)}</span>` : ""}${payButton}</div>`
                : actionButtons("finance", item.id, payButton);
            return [
                badge(item.tipo, item.tipo === "despesa" ? "warn" : ""),
                `${escapeHtml(item.descricao)}${parcelText ? `<div class="origin-note">Parcela ${escapeHtml(parcelText)}</div>` : ""}`,
                item.categoria || item.fornecedor_nome || "-",
                formatCurrency(item.valor),
                formatCurrency(item.valor_pago || 0),
                formatCurrency(item.saldo_aberto ?? item.valor),
                formatDate(item.vencimento),
                badge(item.status, item.status === "atrasado" ? "danger" : item.status === "pago" ? "" : "warn"),
                actions,
            ];
        }),
        "Nenhum lancamento financeiro cadastrado.",
        { nonSortableTargets: [8], pageLength: 6 },
    );
    renderCashLedger();
    bindEntityActions("finance");
    bindQuickActions();
}

function renderFinanceSummary() {
    const dashboard = state.financeDashboard || {
        total_a_receber: 0,
        total_a_pagar: 0,
        saldo_atual: 0,
        inadimplencia_quantidade: 0,
        inadimplencia_valor: 0,
    };
    setText("finance-total-receber", formatCurrency(dashboard.total_a_receber || 0));
    setText("finance-total-pagar", formatCurrency(dashboard.total_a_pagar || 0));
    setText("finance-saldo-atual", formatCurrency(dashboard.saldo_atual || 0));
    setText(
        "finance-inadimplencia",
        `${dashboard.inadimplencia_quantidade || 0} | ${formatCurrency(dashboard.inadimplencia_valor || 0)}`,
    );
}

function renderCashLedger() {
    setTableContent(
        "cash-ledger-table",
        ["Data", "Tipo", "Origem", "Valor", "Referencia"],
        state.cashLedger.map((item) => [
            formatDate(item.data_movimento),
            badge(item.tipo, item.tipo === "saida" ? "warn" : ""),
            item.origem,
            formatCurrency(item.valor),
            item.referencia || "-",
        ]),
        "Nenhuma movimentacao registrada no fluxo de caixa.",
        { pageLength: 6 },
    );
}

function renderUsers() {
    const target = document.getElementById("users-table");
    if (!target) {
        return;
    }
    if (state.user?.role !== "master") {
        target.innerHTML = `<div class="empty-state">Disponivel apenas para o perfil MASTER.</div>`;
        return;
    }
    setTableContent(
        "users-table",
        ["Nome", "Usuario", "Perfil", "Status", "Acoes"],
        state.users.map((item) => [
            item.nome,
            item.username,
            item.role,
            badge(item.is_active ? "Ativo" : "Inativo", item.is_active ? "" : "warn"),
            actionButtons("user", item.id),
        ]),
        "Nenhum usuario cadastrado.",
        { nonSortableTargets: [4] },
    );
    bindEntityActions("user");
}

function renderLicenses() {
    const target = document.getElementById("licenses-table");
    if (!target) {
        return;
    }
    if (state.user?.role !== "master") {
        target.innerHTML = `<div class="empty-state">Disponivel apenas para o perfil MASTER.</div>`;
        return;
    }
    setTableContent(
        "licenses-table",
        ["Descricao", "Inicio", "Fim", "Max usuarios", "Status", "Acoes"],
        state.licenses.map((item) => [
            item.descricao,
            formatDate(item.start_date),
            formatDate(item.end_date),
            String(item.max_users),
            badge(item.status, item.status === "ativa" ? "" : item.status === "suspensa" ? "warn" : "danger"),
            actionButtons("license", item.id),
        ]),
        "Nenhuma licenca cadastrada.",
        { nonSortableTargets: [5] },
    );
    bindEntityActions("license");
}

function setTableContent(targetId, headers, rows, emptyMessage, options = {}) {
    const target = document.getElementById(targetId);
    if (!target) {
        return;
    }
    destroyDataTable(target);
    target.innerHTML = renderTableHtml(headers, rows, emptyMessage);
    initDataTable(target, rows.length, options);
}

function destroyDataTable(target) {
    if (!target || !window.jQuery || !jQuery.fn.DataTable) {
        return;
    }
    target.querySelectorAll("table").forEach((table) => {
        if (jQuery.fn.DataTable.isDataTable(table)) {
            jQuery(table).DataTable().destroy();
        }
    });
}

function initDataTable(target, rowCount, options = {}) {
    if (!target || !window.jQuery || !jQuery.fn.DataTable) {
        return;
    }
    const table = target.querySelector("table");
    if (!table) {
        return;
    }
    const pageLength = options.pageLength || 5;
    jQuery(table).DataTable({
        language: dataTableLanguage,
        pageLength,
        lengthChange: false,
        searching: rowCount > pageLength,
        ordering: options.ordering ?? true,
        info: rowCount > 0,
        paging: rowCount > pageLength,
        autoWidth: false,
        order: [],
        columnDefs: (options.nonSortableTargets || []).map((targetIndex) => ({ targets: targetIndex, orderable: false })),
    });
}

function renderTableHtml(headers, rows, emptyMessage) {
    if (!rows.length) {
        return `<div class="empty-state">${escapeHtml(emptyMessage)}</div>`;
    }
    return `
        <div class="data-table-wrap">
            <table class="data-table table table-hover">
                <thead>
                    <tr>${headers.map((header) => `<th>${escapeHtml(header)}</th>`).join("")}</tr>
                </thead>
                <tbody>
                    ${rows.map((row) => `<tr>${row.map((cell) => `<td>${renderCell(cell)}</td>`).join("")}</tr>`).join("")}
                </tbody>
            </table>
        </div>
    `;
}

function renderCell(value) {
    if (typeof value !== "string") {
        return escapeHtml(String(value));
    }
    if (value.trimStart().startsWith("<")) {
        return value;
    }
    return escapeHtml(value);
}

function metric(label, value, caption) {
    const config = {
        Clientes: { tone: "bg-info", icon: "fas fa-building" },
        Produtos: { tone: "bg-warning", icon: "fas fa-flask" },
        Ordens: { tone: "bg-success", icon: "fas fa-clipboard-list" },
        Financeiro: { tone: "bg-primary", icon: "fas fa-wallet" },
    }[label] || { tone: "bg-secondary", icon: "fas fa-chart-bar" };

    return `
        <div class="col-lg-3 col-sm-6 metric-card">
            <article class="small-box metric-box ${config.tone}">
                <div class="inner">
                    <p class="eyebrow">${escapeHtml(label)}</p>
                    <h3>${escapeHtml(String(value))}</h3>
                    <span class="metric-caption">${escapeHtml(caption)}</span>
                </div>
                <div class="icon">
                    <i class="${config.icon}"></i>
                </div>
            </article>
        </div>
    `;
}

function badge(label, tone) {
    return `<span class="badge ${tone}">${escapeHtml(label)}</span>`;
}

function renderDashboardWidgets(filteredOrders, filteredStock, filteredFinance) {
    const openOrders = filteredOrders.filter((item) => item.status === "aberta" || item.status === "em_execucao").length;
    const completedOrders = filteredOrders.filter((item) => item.status === "concluida").length;
    const pendingFinance = state.financeDashboard
        ? Number(state.financeDashboard.total_a_receber || 0)
        : filteredFinance
            .filter((item) => item.status === "pendente" || item.status === "atrasado")
            .reduce((total, item) => total + Number(item.saldo_aberto ?? item.valor), 0);
    const criticalStock = filteredStock.filter((item) => Number(item.estoque_atual) <= Number(item.estoque_minimo)).length;

    setText("widget-open-orders", String(openOrders));
    setText("widget-completed-orders", String(completedOrders));
    setText("widget-pending-finance", formatCurrency(pendingFinance));
    setText("widget-critical-stock", String(criticalStock));
}

function renderDashboardCharts(filteredOrders, filteredFinance) {
    if (!window.Chart) {
        return;
    }

    Chart.defaults.font.family = '"Segoe UI", "Trebuchet MS", sans-serif';
    Chart.defaults.color = "#516055";

    destroyChart("status");
    destroyChart("finance");

    const statusCanvas = document.getElementById("dashboard-status-chart");
    if (statusCanvas) {
        const statusCounts = ["aberta", "em_execucao", "concluida", "cancelada"].map(
            (status) => filteredOrders.filter((item) => item.status === status).length,
        );

        dashboardCharts.status = new Chart(statusCanvas, {
            type: "doughnut",
            data: {
                labels: ["Aberta", "Em execucao", "Concluida", "Cancelada"],
                datasets: [
                    {
                        data: statusCounts,
                        backgroundColor: ["#3b82f6", "#f59e0b", "#2d6a4f", "#b14534"],
                        borderWidth: 0,
                    },
                ],
            },
            options: {
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom",
                    },
                },
            },
        });
    }

    const financeCanvas = document.getElementById("dashboard-finance-chart");
    if (financeCanvas) {
        const financeTotals = ["pendente", "pago", "atrasado"].map((status) => filteredFinance
            .filter((item) => item.status === status)
            .reduce((total, item) => total + Number(item.saldo_aberto ?? item.valor), 0));

        dashboardCharts.finance = new Chart(financeCanvas, {
            type: "bar",
            data: {
                labels: ["Pendente", "Pago", "Atrasado"],
                datasets: [
                    {
                        label: "Valor total",
                        data: financeTotals,
                        backgroundColor: ["#d2b453", "#2d6a4f", "#b14534"],
                        borderRadius: 8,
                    },
                ],
            },
            options: {
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                    },
                },
                plugins: {
                    legend: {
                        display: false,
                    },
                },
            },
        });
    }
}

function destroyChart(key) {
    if (dashboardCharts[key]) {
        dashboardCharts[key].destroy();
        dashboardCharts[key] = null;
    }
}

function setText(id, value) {
    const node = document.getElementById(id);
    if (node) {
        node.textContent = value;
    }
}

function userCanAccessFinance() {
    return state.user?.role === "master" || state.user?.role === "admin";
}

function actionButton(className, label, dataAttributes = "") {
    return `<button type="button" class="btn btn-sm ghost-button action-button ${className}" ${dataAttributes}>${escapeHtml(label)}</button>`;
}

function actionButtons(kind, id, extraHtml = "") {
    return `
        <div class="toolbar">
            ${extraHtml}
            <button type="button" class="btn btn-sm ghost-button action-button secondary edit-entity" data-kind="${kind}" data-id="${id}">Editar</button>
            <button type="button" class="btn btn-sm ghost-button action-button danger delete-entity" data-kind="${kind}" data-id="${id}">Excluir</button>
        </div>
    `;
}

function bindEntityActions(kind) {
    document.querySelectorAll(`.edit-entity[data-kind="${kind}"]`).forEach((button) => {
        button.addEventListener("click", () => startEditing(kind, Number(button.dataset.id)));
    });
    document.querySelectorAll(`.delete-entity[data-kind="${kind}"]`).forEach((button) => {
        button.addEventListener("click", async () => {
            if (!window.confirm("Deseja realmente excluir este registro?")) {
                return;
            }
            try {
                await deleteEntity(kind, Number(button.dataset.id));
                toast("Registro excluido com sucesso.");
            } catch (error) {
                toast(error.message);
            }
        });
    });
}

function bindQuickActions() {
    document.querySelectorAll(".pay-finance").forEach((button) => {
        button.addEventListener("click", async () => {
            try {
                const openBalance = Number(button.dataset.openBalance || 0);
                const typedValue = window.prompt(
                    `Informe o valor da baixa. Deixe em branco para quitar tudo.\nSaldo aberto: ${formatCurrency(openBalance)}`,
                    "",
                );
                if (typedValue === null) {
                    return;
                }
                const payload = typedValue && typedValue.trim()
                    ? { valor: typedValue.replace(",", ".") }
                    : {};
                await apiFetch(`/api/v1/financeiro/${button.dataset.id}/pagar`, {
                    method: "POST",
                    body: JSON.stringify(payload),
                });
                await afterMutation("Baixa financeira registrada com sucesso.");
            } catch (error) {
                toast(error.message);
            }
        });
    });

    document.querySelectorAll(".complete-work-order").forEach((button) => {
        button.addEventListener("click", async () => {
            try {
                await apiFetch(`/api/v1/os/${button.dataset.id}/efetuar`, { method: "POST" });
                await afterMutation("Ordem de servico marcada como efetuada.");
            } catch (error) {
                toast(error.message);
            }
        });
    });

    document.querySelectorAll(".settle-work-order").forEach((button) => {
        button.addEventListener("click", async () => {
            try {
                await apiFetch(`/api/v1/os/${button.dataset.id}/baixar`, { method: "POST" });
                await afterMutation("Ordem de servico baixada com sucesso.");
            } catch (error) {
                toast(error.message);
            }
        });
    });
}

function getEntityByKind(kind, id) {
    const sourceMap = {
        customer: state.customers,
        product: state.products,
        pest: state.pests,
        technician: state.technicians,
        finance: state.finance,
        workOrder: state.workOrders,
        user: state.users,
        license: state.licenses,
    };
    return sourceMap[kind].find((item) => item.id === id) || null;
}

function syncEditingModes() {
    Object.keys(state.editing).forEach((kind) => {
        const id = state.editing[kind];
        if (id && !getEntityByKind(kind, id)) {
            resetFormMode(kind);
        }
    });
}

function startEditing(kind, id) {
    const item = getEntityByKind(kind, id);
    if (!item) {
        return;
    }
    state.editing[kind] = id;
    const form = document.getElementById(formIdForKind(kind));
    form.querySelector(".form-error").classList.add("hidden");
    form.querySelector(`[data-cancel-button="${kind}"]`).classList.remove("hidden");
    form.querySelector(`[data-save-button="${kind}"]`).textContent = "Salvar alteracoes";
    const note = form.querySelector(`[data-mode-note="${kind}"]`);
    note.classList.remove("hidden");
    note.textContent = `Editando registro #${id}.`;

    if (kind === "technician") {
        fillForm(form, { ...item, ativo: String(item.ativo) });
        return;
    }
    if (kind === "finance") {
        fillForm(form, {
            ...item,
            cliente_id: item.cliente_id || "",
            categoria: item.categoria || "",
            fornecedor_nome: item.fornecedor_nome || "",
            referencia: item.referencia || "",
            observacoes: item.observacoes || "",
            total_parcelas: item.total_parcelas || 1,
        });
        return;
    }
    if (kind === "user") {
        fillForm(form, { ...item, is_active: String(item.is_active), password: "" });
        form.querySelector('[name="password"]').required = false;
        return;
    }
    if (kind === "license") {
        fillForm(form, item);
        return;
    }
    if (kind === "workOrder") {
        fillWorkOrderForm(item);
        return;
    }
    fillForm(form, item);
}

function resetFormMode(kind) {
    state.editing[kind] = null;
    const form = document.getElementById(formIdForKind(kind));
    form.reset();
    form.querySelector(".form-error").classList.add("hidden");
    form.querySelector(`[data-cancel-button="${kind}"]`).classList.add("hidden");
    form.querySelector(`[data-save-button="${kind}"]`).textContent = saveLabelForKind(kind);
    const note = form.querySelector(`[data-mode-note="${kind}"]`);
    note.classList.add("hidden");
    note.textContent = "";
    if (kind === "workOrder") {
        clearWorkOrderForm();
    }
    if (kind === "user") {
        form.querySelector('[name="password"]').required = true;
    }
}

function formIdForKind(kind) {
    return {
        customer: "customer-form",
        product: "product-form",
        pest: "pest-form",
        technician: "technician-form",
        finance: "finance-form",
        workOrder: "work-order-form",
        user: "user-form",
        license: "license-form",
    }[kind];
}

function saveLabelForKind(kind) {
    return {
        customer: "Salvar cliente",
        product: "Salvar produto",
        pest: "Salvar praga",
        technician: "Salvar tecnico",
        finance: "Salvar lancamento",
        workOrder: "Salvar ordem de servico",
        user: "Salvar usuario",
        license: "Salvar licenca",
    }[kind];
}

function fillForm(form, data) {
    Object.entries(data).forEach(([key, value]) => {
        const field = form.querySelector(`[name="${key}"]`);
        if (field) {
            field.value = value ?? "";
        }
    });
}

function fillWorkOrderForm(item) {
    const form = document.getElementById("work-order-form");
    fillForm(form, {
        numero: item.numero,
        cliente_id: String(item.cliente_id),
        tecnico_id: String(item.tecnico_id),
        local_execucao: item.local_execucao,
        data_execucao: item.data_execucao,
        garantia_ate: item.garantia_ate,
        hora_inicio: item.hora_inicio.slice(0, 5),
        hora_fim: item.hora_fim ? item.hora_fim.slice(0, 5) : "",
        status: item.status,
        valor_servico: item.valor_servico,
        observacoes: item.observacoes || "",
        gerar_financeiro: state.finance.some((entry) => entry.os_id === item.id) ? "true" : "false",
    });
    document.getElementById("products-list").innerHTML = "";
    item.produtos.forEach((product) => {
        addProductRow({
            produto_id: product.produto_id,
            quantidade: product.quantidade,
            diluicao: product.diluicao,
        });
    });
    form.querySelectorAll('input[name="pragas_ids"]').forEach((checkbox) => {
        checkbox.checked = item.pragas.some((pest) => pest.praga.id === Number(checkbox.value));
    });
}

async function deleteEntity(kind, id) {
    const endpointMap = {
        customer: "/api/v1/clientes",
        product: "/api/v1/produtos",
        pest: "/api/v1/pragas",
        technician: "/api/v1/tecnicos",
        finance: "/api/v1/financeiro",
        workOrder: "/api/v1/os",
        user: "/api/v1/usuarios",
        license: "/api/v1/licencas",
    };
    await apiFetch(`${endpointMap[kind]}/${id}`, { method: "DELETE" });
    if (state.editing[kind] === id) {
        resetFormMode(kind);
    }
    await loadAllData();
}

function formatDate(value) {
    return new Date(`${value}T00:00:00`).toLocaleDateString("pt-BR");
}

function formatCurrency(value) {
    return Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function setSyncStatus(text) {
    const target = document.getElementById("sync-status");
    if (target) {
        target.textContent = text;
    }
}

function toast(message) {
    const node = document.getElementById("toast");
    node.textContent = message;
    node.classList.remove("hidden");
    clearTimeout(node._timer);
    node._timer = setTimeout(() => node.classList.add("hidden"), 2600);
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
