const state = {
    token: localStorage.getItem("syspragas_token") || "",
    user: null,
    customers: [],
    contracts: [],
    contractDashboard: null,
    contractReport: null,
    products: [],
    stockPositions: [],
    stockMovements: [],
    stockImportLogs: [],
    stockCompanies: [],
    stockWarehouses: [],
    stockLocations: [],
    stockInventories: [],
    nfeInvoices: [],
    simplesConfigs: [],
    pests: [],
    technicians: [],
    workOrders: [],
    appointments: [],
    appointmentDashboard: null,
    settings: null,
    integrations: {
        whatsapp: null,
        whatsappConfig: null,
        whatsappQr: null,
        google: null,
    },
    stockWorkflow: {
        lastLookup: null,
        activeInventoryId: null,
        scannerTarget: null,
    },
    finance: [],
    cashLedger: [],
    financeDashboard: null,
    receipts: [],
    cashFlowSummary: null,
    simplesSummary: null,
    sefazReadiness: null,
    users: [],
    licenses: [],
    providerCompanies: [],
    providerCompanyTab: "dados",
    contractWorkspace: {
        customerId: null,
    },
    workOrderScreen: "new",
    financeScreen: "lancamentos",
    stockScreen: "operations",
    nfeTab: "issue",
    appointmentScreen: "operational",
    appointmentCalendarView: "month",
    workOrderWorkflow: {
        lastSavedOrderId: null,
        certificateReady: false,
    },
    nfeWorkflow: {
        lastIssuedInvoiceId: null,
    },
    receiptPreview: null,
    workOrderPicker: {
        productSearch: "",
        pestSearch: "",
        productTab: "catalogo",
        stagedProductIds: [],
        stagedPestIds: [],
        selectedPestIds: [],
    },
    editing: {
        customer: null,
        contract: null,
        product: null,
        pest: null,
        technician: null,
        finance: null,
        receipt: null,
        nfe: null,
        workOrder: null,
        appointment: null,
        providerCompany: null,
        user: null,
        license: null,
    },
    filters: {
        dashboardSearch: "",
        dashboardStatus: "todos",
        dashboardStock: "alerta",
        dashboardFinance: "pendente",
        stockSearch: "",
        stockCompany: "",
        stockCategory: "",
        stockStatus: "todos",
        workOrderNumber: "",
        workOrderCustomer: "",
        workOrderDate: "",
        workOrderStartDate: "",
        workOrderEndDate: "",
        workOrderStatus: "todos",
        workOrderLane: "pending",
        appointmentSearch: "",
        appointmentStatus: "todos",
        appointmentTechnician: "",
        appointmentCustomer: "",
        appointmentDate: "",
        appointmentStartDate: "",
        appointmentEndDate: "",
        appointmentLane: "pending",
        financeSearch: "",
        financeStatus: "todos",
        financeCustomer: "",
        financeStartDate: "",
        financeEndDate: "",
        receiptSearch: "",
        receiptCustomer: "",
        nfeSearch: "",
        nfeStatus: "todos",
        nfeCustomer: "",
        contractReportCustomer: "",
        contractReportStatus: "todos",
        contractReportStartDate: "",
        contractReportEndDate: "",
        contractReportDueStartDate: "",
        contractReportDueEndDate: "",
        contractReportBillingActive: "todos",
        simplesReferenceMonth: new Date().toISOString().slice(0, 7),
    },
};

const permissionCatalog = {
    clientes: [
        ["customers.view", "Ver clientes"],
        ["customers.edit", "Criar e editar clientes"],
    ],
    contratos: [
        ["contracts.view", "Ver contratos"],
        ["contracts.manage", "Criar e editar contratos"],
    ],
    estoque: [
        ["stock.view", "Ver estoque"],
        ["stock.manage", "Cadastrar produtos"],
        ["stock.move", "Movimentar estoque"],
    ],
    financeiro: [
        ["finance.view", "Ver financeiro"],
        ["finance.manage", "Lancar e editar financeiro"],
    ],
    operacao: [
        ["work_orders.view", "Ver ordens de servico"],
        ["work_orders.manage", "Gerenciar ordens de servico"],
        ["appointments.view", "Ver agenda"],
        ["appointments.manage", "Gerenciar agenda"],
    ],
    sistema: [
        ["settings.view", "Ver configuracoes"],
        ["settings.manage", "Alterar configuracoes"],
        ["users.manage", "Gerenciar usuarios"],
        ["records.delete", "Excluir registros"],
        ["provider_companies.manage", "Gerenciar empresas prestadoras"],
        ["licenses.manage", "Gerenciar licencas"],
        ["fiscal.view", "Ver fiscal e NF-e"],
        ["fiscal.manage", "Emitir e gerenciar NF-e"],
        ["integrations.manage", "Gerenciar integracoes"],
    ],
};

const defaultPermissionsByRole = {
    master: Object.fromEntries(Object.values(permissionCatalog).flat().map(([key]) => [key, true])),
    admin: {
        "customers.view": true,
        "customers.edit": true,
        "contracts.view": true,
        "contracts.manage": true,
        "stock.view": true,
        "stock.manage": true,
        "stock.move": true,
        "finance.view": true,
        "finance.manage": true,
        "work_orders.view": true,
        "work_orders.manage": true,
        "appointments.view": true,
        "appointments.manage": true,
        "settings.view": true,
        "settings.manage": true,
        "users.manage": true,
        "records.delete": true,
        "provider_companies.manage": false,
        "licenses.manage": false,
        "fiscal.view": true,
        "fiscal.manage": true,
        "integrations.manage": true,
    },
    operador: {
        "customers.view": true,
        "customers.edit": false,
        "contracts.view": true,
        "contracts.manage": false,
        "stock.view": true,
        "stock.manage": false,
        "stock.move": false,
        "finance.view": false,
        "finance.manage": false,
        "work_orders.view": true,
        "work_orders.manage": true,
        "appointments.view": true,
        "appointments.manage": true,
        "settings.view": false,
        "settings.manage": false,
        "users.manage": false,
        "records.delete": false,
        "provider_companies.manage": false,
        "licenses.manage": false,
        "fiscal.view": true,
        "fiscal.manage": false,
        "integrations.manage": false,
    },
};

const viewTitles = {
    dashboard: "Dashboard",
    clientes: "Clientes",
    produtos: "Produtos",
    estoque: "Estoque",
    "estoque-balanco": "Balanco de estoque",
    "estoque-transferencias": "Transferencias de estoque",
    pragas: "Pragas",
    tecnicos: "Tecnicos",
    ordens: "Ordens de servico",
    "ordens-nova": "Nova ordem de servico",
    "ordens-cadastradas": "Ordens de servico cadastradas",
    agenda: "Agenda",
    "agenda-novo": "Novo agendamento",
    "agenda-operacional": "Agenda operacional",
    financeiro: "Financeiro",
    "financeiro-lancamentos": "Lancamentos financeiros",
    "financeiro-recibos": "Recibos",
    "financeiro-nfe": "NF-e",
    "financeiro-caixa": "Fluxo de caixa",
    "financeiro-relatorios": "Relatorios financeiros",
    configuracoes: "Configuracoes do sistema",
    empresas: "Cadastrar empresas",
    usuarios: "Usuarios",
    licencas: "Licencas",
};

const dashboardCharts = {
    status: null,
    finance: null,
};

const activeAppointmentStatuses = new Set([
    "pendente",
    "confirmado",
    "em_deslocamento",
    "em_atendimento",
    "reagendado",
]);

const finishedAppointmentStatuses = new Set([
    "concluido",
    "cancelado",
    "nao_realizado",
]);

const finishedWorkOrderStatuses = new Set([
    "concluida",
    "cancelada",
]);

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
    renderSettingsLoadingState();
    buildForms();
    window.SysPragasUI?.enhanceAllForms();
    bindNavigation();
    bindWorkOrderModuleNavigation();
    bindFinanceModuleNavigation();
    bindNfeTabNavigation();
    bindGoogleCalendarOAuth();
    bindSettingsActions();
    bindAuth();
    bindDashboardFilters();
    bindStockFilters();
    bindStockViewButtons();

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

function bindGoogleCalendarOAuth() {
    window.addEventListener("message", async (event) => {
        if (event.origin !== window.location.origin) {
            return;
        }
        const payload = event.data || {};
        if (payload.type !== "syspragas-google-calendar-oauth") {
            return;
        }
        if (payload.status === "success") {
            await loadAllData();
            openAppointmentView("operational");
            toast(payload.message || "Conta Google conectada com sucesso.");
            return;
        }
        toast(payload.message || "Nao foi possivel concluir a autenticacao Google.");
    });
}

function bindSettingsActions() {
  const root = document.getElementById("settings-root");
  if (!root) {
    return;
  }

    root.addEventListener("submit", async (event) => {
        const form = event.target;
        if (!(form instanceof HTMLFormElement) || form.id !== "system-settings-form") {
            return;
        }
        event.preventDefault();
        const errorBox = form.querySelector(".form-error");
        const saveButton = form.querySelector('[data-save-button="settings"]');
        errorBox?.classList.add("hidden");
        if (saveButton) {
            saveButton.disabled = true;
            saveButton.dataset.originalLabel = saveButton.dataset.originalLabel || saveButton.textContent;
            saveButton.textContent = "Salvando...";
        }
        try {
            if (!window.SysPragasUI?.validateForm(form)) {
                throw new Error("Revise os campos destacados antes de salvar as configuracoes.");
            }
            const payload = getSystemSettingsPayload(form);
            state.settings = await apiFetch("/api/v1/settings", {
                method: "PUT",
                body: JSON.stringify(payload),
            });
            await loadAllData();
            toast("Configuracoes atualizadas com sucesso.");
        } catch (error) {
            if (errorBox) {
                errorBox.textContent = error.message;
                errorBox.classList.remove("hidden");
            }
            toast(error.message || "Nao foi possivel salvar as configuracoes.");
        } finally {
            if (saveButton) {
                saveButton.disabled = false;
                saveButton.textContent = saveButton.dataset.originalLabel || "Salvar configuracoes";
            }
        }
    });

  root.addEventListener("change", async (event) => {
    const target = event.target;
    if (target instanceof HTMLInputElement && target.dataset.technicalUploadInput) {
      const file = target.files && target.files[0];
      if (!file) {
        return;
      }
      try {
        await uploadTechnicalAsset(target.dataset.technicalUploadInput, file);
      } catch (error) {
        toast(error.message || "Nao foi possivel enviar o arquivo tecnico.");
      } finally {
        target.value = "";
      }
      return;
    }
    if (!(target instanceof HTMLInputElement) || target.id !== "database-restore-input") {
      return;
    }
    const file = target.files && target.files[0];
    if (!file) {
      return;
    }
    try {
      await restoreDatabaseFromFile(file);
    } catch (error) {
      toast(error.message || "Erro ao restaurar o banco de dados.");
    } finally {
      target.value = "";
    }
  });

  root.addEventListener("click", (event) => {
    if (!(event.target instanceof Element)) {
      return;
    }
    const trigger = event.target.closest("[data-technical-upload-trigger]");
    if (!trigger) {
      return;
    }
    const kind = trigger.dataset.technicalUploadTrigger;
    root.querySelector(`[data-technical-upload-input="${kind}"]`)?.click();
  });

  root.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-settings-action], [data-settings-shortcut]");
    if (!button) {
      return;
    }

        const shortcut = button.dataset.settingsShortcut;
        if (shortcut) {
            switchView(shortcut);
            return;
        }

        const action = button.dataset.settingsAction;
        try {
            if (action === "google-login") {
                await loginGoogle();
                return;
            }
            if (action === "google-logout") {
                await logoutGoogle();
                return;
            }
            if (action === "refresh-integrations") {
                await refreshAppointmentIntegrationStatus();
                await loadAllData();
                toast("Status das integracoes atualizado.");
                return;
            }
            if (action === "whatsapp-connect-qr") {
                await connectWhatsAppQr();
                return;
            }
      if (action === "whatsapp-logout") {
        await logoutWhatsApp();
        return;
      }
      if (action === "database-backup") {
        await downloadDatabaseBackup();
        return;
      }
      if (action === "database-restore") {
        await openDatabaseRestorePicker();
        return;
      }
      if (action === "database-cleanup") {
        await cleanupDatabaseOperationalData();
      }
    } catch (error) {
      toast(error.message || "Nao foi possivel concluir a acao.");
    }
  });
}

function bindWorkOrderModuleNavigation() {
    const buttons = Array.from(document.querySelectorAll("[data-work-order-screen-trigger]"));
    if (!buttons.length) {
        return;
    }

    buttons.forEach((button, index) => {
        button.addEventListener("click", () => setWorkOrderWorkspaceView(button.dataset.workOrderScreenTrigger));
        button.addEventListener("keydown", (event) => {
            const currentIndex = buttons.indexOf(button);
            if (event.key === "ArrowRight") {
                event.preventDefault();
                buttons[(currentIndex + 1) % buttons.length].focus();
            } else if (event.key === "ArrowLeft") {
                event.preventDefault();
                buttons[(currentIndex - 1 + buttons.length) % buttons.length].focus();
            } else if (event.key === "Home") {
                event.preventDefault();
                buttons[0].focus();
            } else if (event.key === "End") {
                event.preventDefault();
                buttons[buttons.length - 1].focus();
            } else if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                setWorkOrderWorkspaceView(button.dataset.workOrderScreenTrigger);
            }
        });
        button.setAttribute("tabindex", index === 0 ? "0" : "-1");
    });

    setWorkOrderWorkspaceView(state.workOrderScreen || "new");
}

function bindFinanceModuleNavigation() {
    const buttons = Array.from(document.querySelectorAll("[data-finance-screen-trigger]"));
    if (!buttons.length) {
        return;
    }

    buttons.forEach((button, index) => {
        button.addEventListener("click", () => setFinanceWorkspaceView(button.dataset.financeScreenTrigger));
        button.addEventListener("keydown", (event) => {
            const currentIndex = buttons.indexOf(button);
            if (event.key === "ArrowRight") {
                event.preventDefault();
                buttons[(currentIndex + 1) % buttons.length].focus();
            } else if (event.key === "ArrowLeft") {
                event.preventDefault();
                buttons[(currentIndex - 1 + buttons.length) % buttons.length].focus();
            } else if (event.key === "Home") {
                event.preventDefault();
                buttons[0].focus();
            } else if (event.key === "End") {
                event.preventDefault();
                buttons[buttons.length - 1].focus();
            } else if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                setFinanceWorkspaceView(button.dataset.financeScreenTrigger);
            }
        });
        button.setAttribute("tabindex", index === 0 ? "0" : "-1");
    });

    setFinanceWorkspaceView(state.financeScreen || "lancamentos");
}

function bindNfeTabNavigation() {
    const buttons = Array.from(document.querySelectorAll("[data-nfe-tab-trigger]"));
    if (!buttons.length) {
        return;
    }
    buttons.forEach((button, index) => {
        button.addEventListener("click", () => setNfeTabView(button.dataset.nfeTabTrigger));
        button.addEventListener("keydown", (event) => {
            const currentIndex = buttons.indexOf(button);
            if (event.key === "ArrowRight") {
                event.preventDefault();
                buttons[(currentIndex + 1) % buttons.length].focus();
            } else if (event.key === "ArrowLeft") {
                event.preventDefault();
                buttons[(currentIndex - 1 + buttons.length) % buttons.length].focus();
            } else if (event.key === "Home") {
                event.preventDefault();
                buttons[0].focus();
            } else if (event.key === "End") {
                event.preventDefault();
                buttons[buttons.length - 1].focus();
            } else if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                setNfeTabView(button.dataset.nfeTabTrigger);
            }
        });
        button.setAttribute("tabindex", index === 0 ? "0" : "-1");
    });
    setNfeTabView(state.nfeTab || "issue");
}

function resolveAppView(view) {
    const rawView = String(view || "");
    if (rawView.startsWith("financeiro-")) {
        return "financeiro";
    }
    if (rawView.startsWith("estoque-")) {
        return "estoque";
    }
    if (rawView.startsWith("ordens-")) {
        return "ordens";
    }
    if (rawView.startsWith("agenda-")) {
        return "agenda";
    }
    return view;
}

function resolveFinanceScreenFromView(view) {
    const rawView = String(view || "");
    if (!rawView.startsWith("financeiro-")) {
        return rawView === "financeiro" ? state.financeScreen || "lancamentos" : null;
    }
    return rawView.replace("financeiro-", "") || "lancamentos";
}

function openFinanceView(screen = "lancamentos") {
    switchView(`financeiro-${screen}`);
}

function buildContractReportUrl(basePath = "/api/v1/contratos/relatorios") {
    const params = new URLSearchParams();
    if (state.filters.contractReportCustomer) {
        params.set("cliente_id", state.filters.contractReportCustomer);
    }
    if (state.filters.contractReportStatus && state.filters.contractReportStatus !== "todos") {
        params.set("status", state.filters.contractReportStatus);
    }
    if (state.filters.contractReportStartDate) {
        params.set("data_inicio_de", state.filters.contractReportStartDate);
    }
    if (state.filters.contractReportEndDate) {
        params.set("data_inicio_ate", state.filters.contractReportEndDate);
    }
    if (state.filters.contractReportDueStartDate) {
        params.set("data_vencimento_de", state.filters.contractReportDueStartDate);
    }
    if (state.filters.contractReportDueEndDate) {
        params.set("data_vencimento_ate", state.filters.contractReportDueEndDate);
    }
    if (state.filters.contractReportBillingActive === "true" || state.filters.contractReportBillingActive === "false") {
        params.set("cobranca_ativa", state.filters.contractReportBillingActive);
    }
    const query = params.toString();
    return query ? `${basePath}?${query}` : basePath;
}

function resolveAppointmentScreenFromView(view) {
    const rawView = String(view || "");
    if (!rawView.startsWith("agenda-")) {
        return rawView === "agenda" ? state.appointmentScreen || "operational" : null;
    }
    return rawView === "agenda-novo" ? "new" : "operational";
}

function openAppointmentView(screen = "operational") {
    switchView(screen === "new" ? "agenda-novo" : "agenda-operacional");
}

function resolveWorkOrderScreenFromView(view) {
    const rawView = String(view || "");
    if (!rawView.startsWith("ordens-")) {
        return rawView === "ordens" ? state.workOrderScreen || "new" : null;
    }
    return rawView === "ordens-cadastradas" ? "registered" : "new";
}

function openWorkOrderView(screen = "new") {
    switchView(screen === "registered" ? "ordens-cadastradas" : "ordens-nova");
}

function bindAuth() {
    document.getElementById("logout-button").addEventListener("click", logout);
    document.getElementById("sidebar-logout-button").addEventListener("click", logout);
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
    const loginForm = document.getElementById("login-form");
    const loginError = document.getElementById("login-error");
    document.getElementById("app-shell").classList.add("hidden");
    document.getElementById("login-screen").classList.remove("hidden");
    loginError.classList.add("hidden");
    loginError.textContent = "";
    if (loginForm) {
        loginForm.querySelector('[name="password"]').value = "";
        loginForm.querySelector('[name="username"]')?.focus();
    }
    setSyncStatus("Sessao local");
}

function logout() {
    state.token = "";
    state.user = null;
    state.receiptPreview = null;
    localStorage.removeItem("syspragas_token");
    showLogin();
}

async function loadAllData() {
    setSyncStatus("Sincronizando...");
    const stockManagerOnly = state.user?.role === "gestor_estoque";
    const basePromises = [
        stockManagerOnly ? Promise.resolve([]) : apiFetch("/api/v1/clientes"),
        stockManagerOnly ? Promise.resolve([]) : apiFetch("/api/v1/contratos"),
        stockManagerOnly ? Promise.resolve(null) : apiFetch("/api/v1/contratos/dashboard"),
        apiFetch("/api/v1/produtos"),
        apiFetch("/api/v1/produtos/estoque"),
        apiFetch("/api/v1/produtos/estoque/movimentacoes"),
        apiFetch("/api/v1/produtos/estoque/importacoes"),
        apiFetch("/api/v1/produtos/estoque/empresas"),
        apiFetch("/api/v1/produtos/estoque/armazens"),
        apiFetch("/api/v1/produtos/estoque/locais"),
        apiFetch("/api/v1/produtos/estoque/inventarios"),
        stockManagerOnly ? Promise.resolve([]) : apiFetch("/api/v1/pragas"),
        stockManagerOnly ? Promise.resolve([]) : apiFetch("/api/v1/tecnicos"),
        stockManagerOnly ? Promise.resolve([]) : apiFetch("/api/v1/os"),
        stockManagerOnly ? Promise.resolve([]) : apiFetch("/api/v1/agendamentos"),
        stockManagerOnly ? Promise.resolve(null) : apiFetch("/api/v1/agendamentos/dashboard"),
        stockManagerOnly ? Promise.resolve({
            status: "desconectado",
            provider: "custom",
            instance_name: null,
            error_message: null,
            configured: false,
        }) : apiFetch("/api/v1/whatsapp/status").catch(() => ({
            status: "erro",
            provider: "custom",
            instance_name: null,
            error_message: "Falha ao consultar o status do WhatsApp.",
            configured: false,
        })),
        stockManagerOnly ? Promise.resolve({
            status: "desconectado",
            message: null,
            company_id: 0,
            company_name: "Nao identificado",
            account_email: null,
            calendar_id: null,
        }) : apiFetch("/api/v1/google-calendar/status").catch(() => ({
            status: "erro",
            message: "Falha ao consultar a conexao com Google Agenda.",
            company_id: 0,
            company_name: "Nao identificado",
            account_email: null,
            calendar_id: null,
        })),
    ];
    const canAccessFinance = hasPermission("finance.view");
    const canAccessSettings = hasPermission("settings.view");
    if (canAccessFinance) {
        basePromises.push(apiFetch("/api/v1/financeiro"));
        basePromises.push(apiFetch("/api/v1/financeiro/caixa"));
        basePromises.push(apiFetch("/api/v1/financeiro/dashboard"));
        basePromises.push(apiFetch(buildContractReportUrl()));
        basePromises.push(apiFetch("/api/v1/recibos"));
        basePromises.push(apiFetch("/api/v1/nfe"));
        basePromises.push(apiFetch("/api/v1/nfe/sefaz/readiness"));
        basePromises.push(apiFetch("/api/v1/fiscal/simples"));
        basePromises.push(apiFetch("/api/v1/fiscal/fluxo-caixa/resumo?period=monthly"));
        basePromises.push(apiFetch(`/api/v1/fiscal/simples/resumo/${getSelectedSimplesReference().year}/${getSelectedSimplesReference().month}`));
    }
    if (canAccessSettings) {
        basePromises.push(apiFetch("/api/v1/settings"));
        basePromises.push(apiFetch("/api/v1/whatsapp/configuracao"));
    }
    const results = await Promise.all(basePromises);
    const [customers, contracts, contractDashboard, products, stockPositions, stockMovements, stockImportLogs, stockCompanies, stockWarehouses, stockLocations, stockInventories, pests, technicians, workOrders, appointments, appointmentDashboard, whatsappStatus, googleStatus] = results;
    const financeOffset = 18;
    const finance = canAccessFinance ? results[financeOffset] : [];
    const cashLedger = canAccessFinance ? results[financeOffset + 1] : [];
    const financeDashboard = canAccessFinance ? results[financeOffset + 2] : null;
    const contractReport = canAccessFinance ? results[financeOffset + 3] : null;
    const receipts = canAccessFinance ? results[financeOffset + 4] : [];
    const nfeInvoices = canAccessFinance ? results[financeOffset + 5] : [];
    const sefazReadiness = canAccessFinance ? results[financeOffset + 6] : null;
    const simplesConfigs = canAccessFinance ? results[financeOffset + 7] : [];
    const cashFlowSummary = canAccessFinance ? results[financeOffset + 8] : null;
    const simplesSummary = canAccessFinance ? results[financeOffset + 9] : null;
    const settingsState = canAccessSettings ? results[financeOffset + 10] : null;
    const whatsappConfig = canAccessSettings ? results[financeOffset + 11] : null;

    state.customers = customers;
    state.contracts = contracts;
    state.contractDashboard = contractDashboard;
    state.products = products;
    state.stockPositions = stockPositions;
    state.stockMovements = stockMovements;
    state.stockImportLogs = stockImportLogs;
    state.stockCompanies = stockCompanies;
    state.stockWarehouses = stockWarehouses;
    state.stockLocations = stockLocations;
    state.stockInventories = stockInventories;
    state.pests = pests;
    state.technicians = technicians;
    state.workOrders = workOrders;
    state.appointments = appointments;
    state.appointmentDashboard = appointmentDashboard;
    state.integrations.whatsapp = whatsappStatus;
    state.integrations.google = googleStatus;
    state.finance = finance;
    state.cashLedger = cashLedger;
    state.financeDashboard = financeDashboard;
    state.contractReport = contractReport;
    state.receipts = receipts;
    state.nfeInvoices = nfeInvoices;
    state.sefazReadiness = sefazReadiness;
    state.simplesConfigs = simplesConfigs;
    state.cashFlowSummary = cashFlowSummary;
    state.simplesSummary = simplesSummary;
    state.settings = settingsState;
    state.integrations.whatsappConfig = whatsappConfig;

    if (hasPermission("users.manage")) {
        const [users, licenses, providerCompanies] = await Promise.all([
            apiFetch("/api/v1/usuarios"),
            hasPermission("licenses.manage") ? apiFetch("/api/v1/licencas") : Promise.resolve([]),
            hasPermission("provider_companies.manage") ? apiFetch("/api/v1/empresas-prestadoras") : Promise.resolve([]),
        ]);
        state.users = users;
        state.licenses = licenses;
        state.providerCompanies = hasPermission("provider_companies.manage")
            ? providerCompanies
            : (state.user?.empresa_prestadora_id
                ? [{
                    id: state.user.empresa_prestadora_id,
                    razao_social: state.user.empresa_prestadora_nome || "Minha empresa",
                    nome_fantasia: state.user.empresa_prestadora_nome || "Minha empresa",
                }]
                : []);
    } else {
        state.users = [];
        state.licenses = [];
        state.providerCompanies = [];
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

async function apiFetchResponse(url, options = {}, withAuth = true) {
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
  return response;
}

async function downloadDatabaseBackup() {
  const response = await apiFetchResponse("/api/v1/settings/database/backup", { method: "GET" });
  const blob = await response.blob();
  const fileName = extractDownloadFileName(response.headers.get("content-disposition")) || `backup_${todayIso().replaceAll("-", "")}.db`;

  if (window.showDirectoryPicker) {
    try {
      const directoryHandle = await window.showDirectoryPicker();
      const fileHandle = await directoryHandle.getFileHandle(fileName, { create: true });
      const writable = await fileHandle.createWritable();
      await writable.write(blob);
      await writable.close();
      toast("Backup realizado com sucesso.");
      return;
    } catch (error) {
      if (error?.name === "AbortError") {
        toast("Operacao cancelada.");
        return;
      }
      console.warn("directory_picker_backup_failed", error);
    }
  }

  triggerBlobDownload(blob, fileName);
  toast("Backup realizado com sucesso.");
}

async function openDatabaseRestorePicker() {
  if (window.showOpenFilePicker) {
    try {
      const [fileHandle] = await window.showOpenFilePicker({
        multiple: false,
        excludeAcceptAllOption: true,
        types: [
          {
            description: "Backup SQLite",
            accept: {
              "application/octet-stream": [".db", ".sqlite", ".sqlite3"],
            },
          },
        ],
      });
      const file = await fileHandle.getFile();
      await restoreDatabaseFromFile(file);
      return;
    } catch (error) {
      if (error?.name === "AbortError") {
        toast("Operacao cancelada.");
        return;
      }
      console.warn("open_file_picker_restore_failed", error);
    }
  }

  const input = document.getElementById("database-restore-input");
  input?.click();
}

async function restoreDatabaseFromFile(file) {
  const confirmed = window.confirm("A restauracao do banco substituira os dados atuais. Um backup de seguranca sera gerado antes de prosseguir. Deseja continuar?");
  if (!confirmed) {
    toast("Operacao cancelada.");
    return;
  }
  const confirmation = window.prompt('Digite RESTAURAR para confirmar a restauracao do banco.', "");
  if ((confirmation || "").trim().toUpperCase() !== "RESTAURAR") {
    toast("Operacao cancelada.");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);
  formData.append("confirmation", confirmation);

  const payload = await apiFetch("/api/v1/settings/database/restore", {
    method: "POST",
    body: formData,
  });
  await loadAllData();
  toast(payload.message || "Restauracao concluida.");
}

async function cleanupDatabaseOperationalData() {
  const includeFinance = Boolean(document.querySelector('[name="database_reset_include_finance"]')?.checked);
  const confirmed = window.confirm(
    includeFinance
      ? "Esta limpeza removera ordens de servico, agendamentos, historicos, logs e dados financeiros. Deseja continuar?"
      : "Esta limpeza removera ordens de servico, agendamentos, historicos e logs. Os registros financeiros serao preservados. Deseja continuar?"
  );
  if (!confirmed) {
    toast("Operacao cancelada.");
    return;
  }
  const confirmation = window.prompt('Digite CONFIRMAR para limpar as movimentacoes operacionais.', "");
  if ((confirmation || "").trim().toUpperCase() !== "CONFIRMAR") {
    toast("Operacao cancelada.");
    return;
  }

  const payload = await apiFetch("/api/v1/settings/database/cleanup", {
    method: "POST",
    body: JSON.stringify({
      confirmation,
      include_finance: includeFinance,
    }),
  });
  await loadAllData();
  toast(payload.message || "Limpeza concluida.");
}

function extractDownloadFileName(contentDisposition) {
  if (!contentDisposition) {
    return null;
  }
  const match = /filename=\"?([^\";]+)\"?/i.exec(contentDisposition);
  return match ? match[1] : null;
}

function triggerBlobDownload(blob, fileName) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function switchView(view) {
    const appView = resolveAppView(view);
    const financeScreen = resolveFinanceScreenFromView(view);
    const stockScreen = resolveStockScreenFromView(view);
    const workOrderScreen = resolveWorkOrderScreenFromView(view);
    const appointmentScreen = resolveAppointmentScreenFromView(view);
    document.querySelectorAll(".nav-link[data-view]").forEach((button) => {
        const isActive = button.dataset.view === view;
        button.classList.toggle("active", isActive);
        button.setAttribute("aria-current", isActive ? "page" : "false");
    });
    document.querySelectorAll(".view").forEach((section) => {
        const isActive = section.id === `view-${appView}`;
        section.classList.toggle("active", isActive);
        section.hidden = !isActive;
        section.setAttribute("aria-hidden", isActive ? "false" : "true");
    });
    if (appView === "ordens") {
        setWorkOrderWorkspaceView(workOrderScreen || "new");
    }
    if (appView === "financeiro") {
        setFinanceWorkspaceView(financeScreen || "lancamentos");
    }
    if (appView === "estoque") {
        setStockWorkspaceView(stockScreen || "operations");
    }
    if (appView === "agenda") {
        setAppointmentWorkspaceView(appointmentScreen || "operational");
    }
    document.getElementById("view-title").textContent = viewTitles[view] || viewTitles[appView] || viewTitles.dashboard;
    window.scrollTo({ top: 0, behavior: "smooth" });
}

function setWorkOrderWorkspaceView(view) {
    state.workOrderScreen = view === "registered" ? "registered" : "new";
    document.querySelectorAll("[data-work-order-screen-trigger]").forEach((button) => {
        const isActive = button.dataset.workOrderScreenTrigger === state.workOrderScreen;
        button.classList.toggle("tab-active", isActive);
        button.setAttribute("aria-selected", isActive ? "true" : "false");
        button.setAttribute("tabindex", isActive ? "0" : "-1");
    });
    document.querySelectorAll("[data-work-order-screen-panel]").forEach((panel) => {
        const isActive = panel.dataset.workOrderScreenPanel === state.workOrderScreen;
        panel.classList.toggle("is-active", isActive);
        panel.hidden = !isActive;
    });
}

function setFinanceWorkspaceView(view) {
    const allowedViews = new Set(["lancamentos", "recibos", "nfe", "caixa", "relatorios"]);
    state.financeScreen = allowedViews.has(view) ? view : "lancamentos";
    document.querySelectorAll("[data-finance-screen-trigger]").forEach((button) => {
        const isActive = button.dataset.financeScreenTrigger === state.financeScreen;
        button.classList.toggle("tab-active", isActive);
        button.setAttribute("aria-selected", isActive ? "true" : "false");
        button.setAttribute("tabindex", isActive ? "0" : "-1");
    });
    document.querySelectorAll("[data-finance-screen-panel]").forEach((panel) => {
        const isActive = panel.dataset.financeScreenPanel === state.financeScreen;
        panel.classList.toggle("is-active", isActive);
        panel.hidden = !isActive;
    });
    if (state.financeScreen === "nfe") {
        setNfeTabView(state.nfeTab || "issue");
    }
}

function setNfeTabView(view) {
    state.nfeTab = view === "issued" ? "issued" : "issue";
    document.querySelectorAll("[data-nfe-tab-trigger]").forEach((button) => {
        const isActive = button.dataset.nfeTabTrigger === state.nfeTab;
        button.classList.toggle("tab-active", isActive);
        button.setAttribute("aria-selected", isActive ? "true" : "false");
        button.setAttribute("tabindex", isActive ? "0" : "-1");
    });
    document.querySelectorAll("[data-nfe-tab-panel]").forEach((panel) => {
        const isActive = panel.dataset.nfeTabPanel === state.nfeTab;
        panel.classList.toggle("tab-content-active", isActive);
        panel.hidden = !isActive;
    });
}

function setAppointmentWorkspaceView(view) {
    state.appointmentScreen = view === "new" ? "new" : "operational";
    document.querySelectorAll("[data-appointment-screen-panel]").forEach((panel) => {
        const isActive = panel.dataset.appointmentScreenPanel === state.appointmentScreen;
        panel.classList.toggle("is-active", isActive);
        panel.hidden = !isActive;
    });
}

function renderSettingsLoadingState() {
    const summary = document.getElementById("settings-summary-grid");
    const form = document.getElementById("system-settings-form");
    const integrations = document.getElementById("settings-integrations-panel");
    const admin = document.getElementById("settings-admin-panel");
    const environment = document.getElementById("settings-environment-panel");
    if (summary) {
        summary.innerHTML = `<div class="empty-state">As configuracoes carregam apos o login com perfil administrativo.</div>`;
    }
    if (form) {
        form.innerHTML = `<div class="empty-state">Entre com um usuario admin ou master para editar as configuracoes do sistema.</div>`;
    }
    if (integrations) {
        integrations.innerHTML = "";
    }
    if (admin) {
        admin.innerHTML = "";
    }
    if (environment) {
        environment.innerHTML = "";
    }
}

function renderSettings() {
    const summary = document.getElementById("settings-summary-grid");
    const form = document.getElementById("system-settings-form");
    const integrations = document.getElementById("settings-integrations-panel");
    const admin = document.getElementById("settings-admin-panel");
    const environment = document.getElementById("settings-environment-panel");
    if (!summary || !form || !integrations || !admin || !environment) {
        return;
    }

    const canAccessSettings = hasPermission("settings.view");
    if (!canAccessSettings || !state.settings) {
        renderSettingsLoadingState();
        return;
    }

    const settingsState = state.settings;
    const google = state.integrations.google || {};
    const whatsapp = state.integrations.whatsapp || {};
    const whatsappConfig = state.integrations.whatsappConfig || {};
    const whatsappQr = state.integrations.whatsappQr || {};
    const isMaster = state.user?.role === "master";
    const multiempresaBadge = settingsState.system.multiempresa_enabled ? "Ativo" : "Unificado";
    const operationModeLabel = settingsState.system.operation_mode === "rede" ? "Rede interna" : "Local";
    const notificationsLabel = settingsState.system.notifications_enabled ? "Ativas" : "Desativadas";
    const contractNotificationsLabel = settingsState.contracts.email_enabled ? "Email ativo" : "Email desativado";
    const smtpSummaryLabel = settingsState.email.smtp_host
        ? `${escapeHtml(settingsState.email.smtp_host)}:${escapeHtml(String(settingsState.email.smtp_port))}`
        : "SMTP nao configurado";
    const companyComplianceLabel = settingsState.company.technical_responsible_name && settingsState.company.sanitary_license_number
        ? "Documentacao informada"
        : "Documentacao pendente";
    const databaseSummaryLabel = settingsState.database.database_file_name
        ? `${escapeHtml(settingsState.database.engine)} | ${escapeHtml(settingsState.database.database_file_name)}`
        : escapeHtml(settingsState.database.engine);
    const googleLabel = formatIntegrationStatus(google.status || "desconectado");
    const whatsappLabel = formatIntegrationStatus(whatsapp.status || "desconectado");
    const whatsappEnabledInSettings = Boolean(settingsState.integrations.whatsapp_enabled);
    const googleMeta = google.account_email || google.message || "Conta nao conectada";
    const whatsappMeta = whatsapp.instance_name || whatsapp.error_message || "Nenhum numero vinculado detectado";

    summary.innerHTML = `
        <div class="settings-summary-grid">
            ${settingsSummaryCard("Modo de operacao", operationModeLabel, "Define o perfil de acesso local ou em rede do servidor atual.")}
            ${settingsSummaryCard("Multiempresa", multiempresaBadge, settingsState.system.multiempresa_enabled ? "Os dados ficam isolados por empresa prestadora." : "Os dados operam sem escopo por empresa." )}
            ${settingsSummaryCard("Google Agenda", googleLabel, googleMeta)}
            ${settingsSummaryCard("WhatsApp", whatsappLabel, whatsappMeta)}
            ${settingsSummaryCard("Notificacoes", notificationsLabel, settingsState.system.notifications_enabled ? "Avisos operacionais seguem habilitados." : "Avisos operacionais desabilitados." )}
            ${settingsSummaryCard("Contratos", contractNotificationsLabel, `${settingsState.contracts.alert_days} dias de antecedencia e armazenamento em ${settingsState.contracts.storage_dir}.`)}
            ${settingsSummaryCard("SMTP", smtpSummaryLabel, settingsState.email.smtp_password_configured ? "Credenciais salvas para envio automatico de e-mail." : "Defina host, porta e remetente para habilitar notificacoes por e-mail.")}
            ${settingsSummaryCard("Documentacao regulatoria", companyComplianceLabel, `${escapeHtml(settingsState.company.technical_responsible_name)} | CIT ${escapeHtml(settingsState.company.toxicology_center_phone || "-")}`)}
            ${settingsSummaryCard("Banco de dados", databaseSummaryLabel, `Backups operacionais em ${escapeHtml(settingsState.database.backup_dir)}.`)}
            ${settingsSummaryCard("Usuarios ativos", String(state.users.length || 0), isMaster ? "Leitura da administracao global disponivel neste perfil." : "Use a area de usuarios com perfil master para governanca completa.")}
        </div>
    `;

    form.innerHTML = `
        <section class="settings-form-section">
            <div class="section-heading compact">
                <p class="eyebrow">Integracoes</p>
                <h4>Regras operacionais das integracoes</h4>
                <p>Controle quando Google Agenda e WhatsApp participam do fluxo diario do time.</p>
            </div>
            <div class="settings-field-grid">
                ${toggleField("google_calendar_enabled", "Google Agenda ativa", "Permite sincronizacao manual e automatica com a conta conectada.", settingsState.integrations.google_calendar_enabled)}
                ${toggleField("whatsapp_enabled", "WhatsApp ativo", "Libera envio manual e automatico de mensagens do agendamento.", settingsState.integrations.whatsapp_enabled)}
                ${toggleField("whatsapp_auto_send", "Envio automatico de WhatsApp", "Dispara mensagem automaticamente ao criar ou atualizar compromissos elegiveis.", settingsState.integrations.whatsapp_auto_send)}
                ${toggleField("appointment_default_google_sync", "Google ativo por padrao nos novos agendamentos", "Preenche o padrao inicial dos formularios com sincronizacao ligada.", settingsState.system.appointment_default_google_sync)}
            </div>
            <label class="settings-textarea">
                <span>Mensagem padrao do WhatsApp</span>
                <textarea name="whatsapp_default_message" rows="4" placeholder="Mensagem automatica de agendamento">${escapeHtml(settingsState.integrations.whatsapp_default_message || "")}</textarea>
            </label>
        </section>
        <section class="settings-form-section">
            <div class="section-heading compact">
                <p class="eyebrow">Contratos</p>
                <h4>Vigencia, alertas e armazenamento</h4>
                <p>Defina a antecedencia do alerta, o envio de e-mail e o diretorio de arquivos dos contratos.</p>
            </div>
            <div class="settings-field-grid two-columns">
                ${toggleField("contract_email_enabled", "Enviar e-mail automaticamente", "Dispara notificacoes para clientes com contrato a vencer ou vencido.", settingsState.contracts.email_enabled)}
                <label>
                    <span>Dias de antecedencia</span>
                    <input name="contract_alert_days" type="number" min="1" max="365" value="${escapeHtml(String(settingsState.contracts.alert_days || 15))}">
                </label>
                <label class="full-width">
                    <span>Diretorio de armazenamento</span>
                    <input name="contract_storage_dir" value="${escapeHtml(settingsState.contracts.storage_dir || "uploads/contratos")}">
                </label>
            </div>
        </section>
        <section class="settings-form-section">
            <div class="section-heading compact">
                <p class="eyebrow">Documentos tecnicos</p>
                <h4>Dados regulatorios da empresa</h4>
                <p>Esses campos alimentam automaticamente a Ordem de Servico, o Relatorio Tecnico e os certificados com moldura. Sem eles a emissao fica bloqueada.</p>
            </div>
            <section class="technical-guidance-card full-width">
                <div class="section-heading compact">
                    <h4>CIT e preenchimento manual</h4>
                    <p>O CIT nao e um arquivo separado para upload. Ele deve ser informado manualmente nos campos abaixo, a menos que venha escrito dentro do PDF da licenca.</p>
                </div>
                <div class="settings-side-list">
                    ${settingsInfoRow("Upload disponivel", "Licenca sanitaria, licenca ambiental e assinatura")}
                    ${settingsInfoRow("Preenchimento manual", "Centro de Informacao Toxicologica e telefone CIT")}
                </div>
                <p class="origin-note">Se o PDF nao tiver o texto do CIT, o sistema nao consegue preencher esse dado sozinho.</p>
            </section>
            <div class="settings-field-grid two-columns">
                <label>
                    <span>Razao social</span>
                    <input name="company_legal_name" value="${escapeHtml(settingsState.company.legal_name || "")}" required>
                </label>
                <label>
                    <span>Nome fantasia</span>
                    <input name="company_trade_name" value="${escapeHtml(settingsState.company.trade_name || "")}" required>
                </label>
                <label>
                    <span>CNPJ</span>
                    <input name="company_cnpj" value="${escapeHtml(settingsState.company.cnpj || "")}" placeholder="00.000.000/0000-00">
                </label>
                <label>
                    <span>Telefone da empresa</span>
                    <input name="company_phone" value="${escapeHtml(settingsState.company.phone || "")}" placeholder="(11) 3333-4444">
                </label>
                <label class="full-width">
                    <span>Endereco completo da empresa</span>
                    <input name="company_address" value="${escapeHtml(settingsState.company.address || "")}" required>
                </label>
                <label>
                    <span>Responsavel tecnico</span>
                    <input name="technical_responsible_name" value="${escapeHtml(settingsState.company.technical_responsible_name || "")}" required>
                </label>
                <label>
                    <span>Conselho profissional</span>
                    <input name="technical_registry_type" value="${escapeHtml(settingsState.company.technical_registry_type || "")}" placeholder="CRBio, CREA, CRQ..." required>
                </label>
                <label>
                    <span>Numero do registro</span>
                    <input name="technical_registry_number" value="${escapeHtml(settingsState.company.technical_registry_number || "")}" placeholder="123456" required>
                </label>
                <label>
                    <span>UF do registro</span>
                    <input name="technical_registry_state" value="${escapeHtml(settingsState.company.technical_registry_state || "")}" maxlength="2" placeholder="SP" required>
                </label>
                <label>
                    <span>Licenca sanitaria</span>
                    <input name="sanitary_license_number" value="${escapeHtml(settingsState.company.sanitary_license_number || "")}" required>
                </label>
                <label>
                    <span>Validade licenca sanitaria</span>
                    <input name="sanitary_license_expiry" value="${escapeHtml(settingsState.company.sanitary_license_expiry || "")}" placeholder="31/12/2026">
                </label>
                <label>
                    <span>Licenca ambiental</span>
                    <input name="environmental_license_number" value="${escapeHtml(settingsState.company.environmental_license_number || "")}" required>
                </label>
                <label>
                    <span>Validade licenca ambiental</span>
                    <input name="environmental_license_expiry" value="${escapeHtml(settingsState.company.environmental_license_expiry || "")}" placeholder="31/12/2026">
                </label>
                <label>
                    <span>Centro de Informacao Toxicologica</span>
                    <input name="toxicology_center_name" value="${escapeHtml(settingsState.company.toxicology_center_name || "Centro de Informacao Toxicologica")}" required placeholder="Ex.: CEATOX / Centro de Informacao Toxicologica">
                </label>
                <label class="cit-field-highlight">
                    <span>CIT</span>
                    <input name="toxicology_center_phone" value="${escapeHtml(settingsState.company.toxicology_center_phone || "")}" required placeholder="0800 722 6001">
                    <small>Esse campo e manual quando a licenca nao traz o telefone do CIT no proprio PDF.</small>
                </label>
            </div>
            <div class="settings-field-grid two-columns technical-assets-grid">
                ${renderTechnicalAssetPanel("sanitary_license", "Licenca sanitaria digitalizada", settingsState.company.sanitary_license_file, ".pdf,.png,.jpg,.jpeg", "Enviar licenca sanitaria")}
                ${renderTechnicalAssetPanel("environmental_license", "Licenca ambiental digitalizada", settingsState.company.environmental_license_file, ".pdf,.png,.jpg,.jpeg", "Enviar licenca ambiental")}
                ${renderTechnicalAssetPanel("signature", "Assinatura do responsavel tecnico", settingsState.company.technical_signature, ".png,.jpg,.jpeg", "Enviar assinatura")}
                <section class="technical-signature-drawing full-width">
                    <div class="section-heading compact">
                        <h4>Assinatura digital desenhada</h4>
                        <p>Desenhe a assinatura no quadro abaixo e salve para aplicar nos documentos tecnicos desta empresa.</p>
                    </div>
                    <canvas id="technical-signature-canvas" width="760" height="220" aria-label="Area para desenhar assinatura"></canvas>
                    <div class="inline-actions ui-form-actions">
                        <button type="button" class="btn btn-default ghost-button" data-signature-clear>Limpar</button>
                        <button type="button" class="btn btn-primary" data-signature-save>Salvar assinatura desenhada</button>
                    </div>
                </section>
            </div>
        </section>
        <section class="settings-form-section">
            <div class="section-heading compact">
                <p class="eyebrow">SMTP</p>
                <h4>Servidor de e-mail</h4>
                <p>Configure o SMTP usado nas notificacoes automaticas dos contratos. Deixe a senha em branco para manter a atual.</p>
            </div>
            <div class="settings-field-grid two-columns">
                <label>
                    <span>Servidor SMTP</span>
                    <input name="smtp_host" value="${escapeHtml(settingsState.email.smtp_host || "")}" placeholder="smtp.empresa.com">
                </label>
                <label>
                    <span>Porta SMTP</span>
                    <input name="smtp_port" type="number" min="1" max="65535" value="${escapeHtml(String(settingsState.email.smtp_port || 587))}">
                </label>
                <label>
                    <span>Usuario SMTP</span>
                    <input name="smtp_username" value="${escapeHtml(settingsState.email.smtp_username || "")}" placeholder="usuario@empresa.com">
                </label>
                <label>
                    <span>Senha SMTP</span>
                    <input name="smtp_password" type="password" placeholder="${settingsState.email.smtp_password_configured ? "Senha ja configurada" : "Informe a senha"}">
                </label>
                ${toggleField("smtp_use_tls", "Usar STARTTLS", "Ative para conexoes SMTP com negociacao TLS.", settingsState.email.smtp_use_tls)}
                ${toggleField("smtp_use_ssl", "Usar SSL direto", "Ative para conexoes SMTPS, normalmente na porta 465.", settingsState.email.smtp_use_ssl)}
                <label>
                    <span>E-mail remetente</span>
                    <input name="smtp_sender_email" value="${escapeHtml(settingsState.email.smtp_sender_email || "")}" placeholder="naoresponda@empresa.com">
                </label>
                <label>
                    <span>Nome do remetente</span>
                    <input name="smtp_sender_name" value="${escapeHtml(settingsState.email.smtp_sender_name || "")}" placeholder="SysPragas">
                </label>
            </div>
        </section>
        <section class="settings-form-section">
            <div class="section-heading compact">
                <p class="eyebrow">Banco de dados</p>
                <h4>Backup, restauracao e limpeza operacional</h4>
                <p>Use este painel para exportar o banco, restaurar backups SQLite e limpar movimentacoes sem afetar os cadastros principais.</p>
            </div>
            <div class="settings-field-grid two-columns">
                <label class="full-width">
                    <span>Diretorio padrao para backups de seguranca</span>
                    <input name="database_backup_dir" value="${escapeHtml(settingsState.database.backup_dir || "backups/database")}">
                </label>
                ${toggleField("database_reset_include_finance", "Limpar financeiro junto", "Quando ativo, a limpeza remove tambem financeiro, recibos, fluxo de caixa e NF-e.", false)}
            </div>
            <div class="inline-actions">
                <button type="button" class="btn btn-primary" data-settings-action="database-backup">Fazer Backup</button>
                <button type="button" class="btn btn-default" data-settings-action="database-restore">Restaurar Backup</button>
                <button type="button" class="btn btn-danger" data-settings-action="database-cleanup">Limpar Movimentacoes</button>
            </div>
            <input id="database-restore-input" type="file" accept=".db,.sqlite,.sqlite3" class="hidden">
            <p class="origin-note">No navegador compativel, o backup pode ser salvo diretamente em uma pasta escolhida. Caso contrario, o arquivo sera baixado normalmente.</p>
        </section>
        <section class="settings-form-section">
            <div class="section-heading compact">
                <p class="eyebrow">Sistema</p>
                <h4>Contexto de operacao e seguranca</h4>
                <p>Ajuste o comportamento global do sistema e a organizacao por empresa.</p>
            </div>
            <div class="settings-field-grid two-columns">
                ${toggleField("multiempresa_enabled", "Multiempresa ativo", "Quando desativado, o sistema opera sem escopo por empresa.", settingsState.system.multiempresa_enabled)}
                ${toggleField("notifications_enabled", "Notificacoes operacionais", "Mantem avisos e estados auxiliares exibidos na interface.", settingsState.system.notifications_enabled)}
                <label>
                    <span>Modo de operacao</span>
                    <select name="operation_mode">
                        <option value="local" ${settingsState.system.operation_mode === "local" ? "selected" : ""}>Local</option>
                        <option value="rede" ${settingsState.system.operation_mode === "rede" ? "selected" : ""}>Rede</option>
                    </select>
                </label>
            </div>
        </section>
        <div class="inline-actions">
            <button type="submit" class="btn btn-success" data-save-button="settings">Salvar configuracoes</button>
            <button type="button" class="btn btn-default ghost-button" data-settings-action="refresh-integrations">Atualizar status das integracoes</button>
        </div>
        <p class="origin-note">As configuracoes persistem no banco e passam a valer para novos fluxos operacionais.</p>
        <p class="form-error hidden"></p>
    `;

    const shouldShowWhatsAppQrPanel = Boolean(
        whatsapp.supports_qr && (
            whatsappQr.qr_image_data_url
            || whatsappQr.qr_code
            || whatsappQr.message
            || whatsappQr.status
            || ["aguardando_conexao", "erro"].includes(whatsapp.status)
        )
    );
    const whatsappQrMessage = whatsappQr.message
        || (whatsapp.status === "aguardando_conexao"
            ? "A sessao esta sendo preparada. Se o QR nao aparecer em alguns segundos, clique novamente em Conectar via QR."
            : "Leia o QR Code abaixo com o WhatsApp para conectar a sessao.");

    integrations.innerHTML = `
        <section class="settings-side-section">
            <div class="section-heading compact">
                <p class="eyebrow">Google Agenda</p>
                <h4>Conexao e troca de conta</h4>
                <p>Use a conta correta por empresa e acompanhe o calendario vinculado.</p>
            </div>
            <div class="settings-side-list">
                ${settingsInfoRow("Status", googleLabel)}
                ${settingsInfoRow("Conta", google.account_email || "Nenhuma conta conectada")}
                ${settingsInfoRow("Calendario", google.calendar_id || "primary")}
                ${settingsInfoRow("Empresa", google.company_name || "Nao identificado")}
            </div>
            <div class="inline-actions">
                <button type="button" class="btn btn-success" data-settings-action="google-login">Login ou troca de conta</button>
                <button type="button" class="btn btn-default ghost-button" data-settings-action="google-logout" ${google.account_email ? "" : "disabled"}>Logout</button>
            </div>
        </section>
        <section class="settings-side-section">
            <div class="section-heading compact">
                <p class="eyebrow">WhatsApp</p>
                <h4>Conexao e automacao de mensagens</h4>
                <p>Monitore a instancia atual e o estado tecnico da integracao configurada.</p>
            </div>
            <div class="settings-side-list">
                ${settingsInfoRow("Status", whatsappLabel)}
                ${settingsInfoRow("Numero ou instancia", whatsapp.instance_name || "Nao identificado")}
                ${settingsInfoRow("Provedor", whatsapp.provider || whatsappConfig.provider || "custom")}
                ${settingsInfoRow("Configuracao tecnica", whatsappConfig.configured ? "Pronta" : "Incompleta")}
                ${settingsInfoRow("QR Code", whatsapp.supports_qr ? "Disponivel" : "Nao suportado")}
                ${settingsInfoRow("Numero conectado", whatsapp.connected_phone || "-")}
            </div>
            <p class="origin-note">${escapeHtml(whatsapp.error_message || "Use esta area para validar a integracao antes de disparos automaticos.")}</p>
            <div class="inline-actions">
                <button type="button" class="btn btn-success" data-settings-action="whatsapp-connect-qr" ${whatsappEnabledInSettings ? "" : "disabled"}>Conectar via QR</button>
                <button type="button" class="btn btn-default ghost-button" data-settings-action="whatsapp-logout" ${whatsapp.supports_qr ? "" : "disabled"}>Desconectar sessao</button>
                <button type="button" class="btn btn-default ghost-button" data-integration-action="refresh-whatsapp">Atualizar status</button>
            </div>
            ${shouldShowWhatsAppQrPanel ? `
                <div class="whatsapp-qr-panel">
                    <div class="section-heading compact">
                        <h4>Autenticacao por QR Code</h4>
                        <p>${escapeHtml(whatsappQrMessage)}</p>
                    </div>
                    ${whatsappQr.qr_image_data_url ? `<img class="whatsapp-qr-image" src="${escapeHtml(whatsappQr.qr_image_data_url)}" alt="QR Code do WhatsApp">` : ""}
                    ${!whatsappQr.qr_image_data_url && whatsappQr.qr_code ? `<pre class="whatsapp-qr-text">${escapeHtml(whatsappQr.qr_code)}</pre>` : ""}
                    ${!whatsappQr.qr_image_data_url && !whatsappQr.qr_code ? `<div class="empty-state">QR Code ainda nao recebido. Aguarde alguns segundos ou clique novamente em Conectar via QR.</div>` : ""}
                    <div class="settings-side-list">
                        ${settingsInfoRow("Status da sessao", whatsappQr.status || "aguardando_conexao")}
                        ${settingsInfoRow("Instancia", whatsappQr.instance_name || whatsapp.instance_name || "Nao identificada")}
                        ${settingsInfoRow("Expira em", whatsappQr.expires_at || "-")}
                        ${settingsInfoRow("Codigo de pareamento", whatsappQr.pairing_code || "-")}
                    </div>
                    ${whatsappQr.error_message ? `<p class="origin-note">${escapeHtml(whatsappQr.error_message)}</p>` : ""}
                </div>
            ` : ""}
        </section>
    `;

    admin.innerHTML = `
        <section class="settings-side-section">
            <div class="section-heading compact">
                <p class="eyebrow">Usuarios e permissoes</p>
                <h4>Administracao e restricoes por empresa</h4>
                <p>Os cadastros administrativos seguem em modulos proprios, mas a governanca parte daqui.</p>
            </div>
            <div class="settings-side-list">
                ${settingsInfoRow("Perfil atual", state.user?.role || "-")}
                ${settingsInfoRow("Empresas cadastradas", String(state.providerCompanies.length || 0))}
                ${settingsInfoRow("Usuarios carregados", String(state.users.length || 0))}
                ${settingsInfoRow("Licencas carregadas", String(state.licenses.length || 0))}
            </div>
            <div class="inline-actions">
                <button type="button" class="btn btn-default ghost-button" data-settings-shortcut="usuarios">Usuarios</button>
                <button type="button" class="btn btn-default ghost-button" data-settings-shortcut="empresas" ${isMaster ? "" : "disabled"}>Empresas</button>
                <button type="button" class="btn btn-default ghost-button" data-settings-shortcut="licencas" ${isMaster ? "" : "disabled"}>Licencas</button>
            </div>
        </section>
    `;

    environment.innerHTML = `
        <section class="settings-side-section">
            <div class="section-heading compact">
                <p class="eyebrow">Banco e ambiente</p>
                <h4>Contexto tecnico da execucao</h4>
                <p>Referencia segura para suporte local, rede interna e empacotamento da release.</p>
            </div>
            <div class="settings-side-list">
                ${settingsInfoRow("Banco", settingsState.environment.database_url_masked)}
                ${settingsInfoRow("Host configurado", settingsState.environment.app_host)}
                ${settingsInfoRow("Porta", String(settingsState.environment.app_port))}
                ${settingsInfoRow("Acesso remoto", settingsState.environment.allow_remote_access ? "Permitido" : "Desativado")}
            </div>
            <p class="origin-note">Para alterar host, porta ou conexao de banco use os arquivos de ambiente e os scripts de execucao da release.</p>
        </section>
    `;
    window.SysPragasUI?.enhanceAllForms(document.getElementById("settings-root"));
    setupTechnicalSignatureCanvas(form);
    refreshTechnicalAssetPreviews(form);
}

function settingsSummaryCard(label, value, description) {
    return `
        <article class="settings-summary-card">
            <span>${escapeHtml(label)}</span>
            <strong>${escapeHtml(value)}</strong>
            <p>${escapeHtml(description)}</p>
        </article>
    `;
}

function settingsInfoRow(label, value) {
    return `
        <div class="settings-info-row">
            <span>${escapeHtml(label)}</span>
            <strong>${escapeHtml(value)}</strong>
        </div>
    `;
}

function toggleField(name, label, description, checked) {
    return `
        <label class="settings-toggle">
            <span class="settings-toggle-copy">
                <strong>${escapeHtml(label)}</strong>
                <small>${escapeHtml(description)}</small>
            </span>
            <span class="settings-switch">
                <input type="checkbox" name="${escapeHtml(name)}" ${checked ? "checked" : ""}>
                <span class="settings-switch-ui" aria-hidden="true"></span>
            </span>
        </label>
    `;
}

function renderTechnicalAssetPanel(kind, title, asset, accept, actionLabel) {
    const hasFile = Boolean(asset?.has_file);
    const uploadedLabel = asset?.uploaded_at ? formatIsoDateTime(asset.uploaded_at) : "Nao enviado";
    const meta = hasFile
        ? `${escapeHtml(asset.filename || "arquivo")} • ${formatBytes(asset.size_bytes || 0)}`
        : "Nenhum arquivo vinculado";
    return `
        <section class="technical-asset-card">
            <div class="section-heading compact">
                <h4>${escapeHtml(title)}</h4>
                <p>${hasFile ? "Arquivo institucional pronto para os documentos." : "Upload pendente para este ativo tecnico."}</p>
            </div>
            <div class="settings-side-list">
                ${settingsInfoRow("Arquivo", meta)}
                ${settingsInfoRow("Ultimo envio", uploadedLabel)}
                ${settingsInfoRow("Formato", asset?.content_type || "-")}
            </div>
            <div class="technical-asset-preview" data-technical-preview-container="${escapeHtml(kind)}">
                <div class="empty-state" data-technical-preview-empty="${escapeHtml(kind)}">${hasFile ? "Carregando preview..." : "Nenhum preview disponivel."}</div>
                <img class="technical-asset-image hidden" data-technical-preview-image="${escapeHtml(kind)}" alt="${escapeHtml(title)}">
                <a class="toolbar-link hidden" data-technical-preview-link="${escapeHtml(kind)}" target="_blank" rel="noopener">Abrir arquivo</a>
            </div>
            <div class="inline-actions ui-form-actions">
                <button type="button" class="btn btn-secondary" data-technical-upload-trigger="${escapeHtml(kind)}">${escapeHtml(actionLabel)}</button>
            </div>
            <input class="hidden" type="file" data-technical-upload-input="${escapeHtml(kind)}" accept="${escapeHtml(accept)}">
        </section>
    `;
}

function formatBytes(value) {
    const size = Number(value || 0);
    if (!size) {
        return "0 B";
    }
    if (size < 1024) {
        return `${size} B`;
    }
    if (size < 1024 * 1024) {
        return `${(size / 1024).toFixed(1)} KB`;
    }
    return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function formatIsoDateTime(value) {
    if (!value) {
        return "-";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return value;
    }
    return date.toLocaleString("pt-BR");
}

async function uploadTechnicalAsset(kind, file) {
    if (!file) {
        return;
    }
    const formData = new FormData();
    formData.append("file", file);
    state.settings = await apiFetch(`/api/v1/settings/technical-documents/assets/${kind}`, {
        method: "POST",
        body: formData,
    });
    await loadAllData();
    renderSettings();
    switchView("configuracoes");
    toast("Arquivo tecnico atualizado com sucesso.");
}

async function saveDrawnSignature(canvas) {
    const dataUrl = canvas.toDataURL("image/png");
    const formData = new FormData();
    formData.append("data_url", dataUrl);
    state.settings = await apiFetch("/api/v1/settings/technical-documents/signature/draw", {
        method: "POST",
        body: formData,
    });
    await loadAllData();
    renderSettings();
    switchView("configuracoes");
    toast("Assinatura desenhada salva com sucesso.");
}

function setupTechnicalSignatureCanvas(root) {
    const canvas = root.querySelector("#technical-signature-canvas");
    if (!(canvas instanceof HTMLCanvasElement)) {
        return;
    }
    const context = canvas.getContext("2d");
    if (!context) {
        return;
    }
    context.lineWidth = 2.2;
    context.lineCap = "round";
    context.strokeStyle = "#17392b";
    context.fillStyle = "#ffffff";
    context.fillRect(0, 0, canvas.width, canvas.height);

    let drawing = false;

    const pointFromEvent = (event) => {
        const rect = canvas.getBoundingClientRect();
        const source = event.touches ? event.touches[0] : event;
        return {
            x: ((source.clientX - rect.left) / rect.width) * canvas.width,
            y: ((source.clientY - rect.top) / rect.height) * canvas.height,
        };
    };

    const start = (event) => {
        drawing = true;
        const point = pointFromEvent(event);
        context.beginPath();
        context.moveTo(point.x, point.y);
        event.preventDefault();
    };
    const move = (event) => {
        if (!drawing) {
            return;
        }
        const point = pointFromEvent(event);
        context.lineTo(point.x, point.y);
        context.stroke();
        event.preventDefault();
    };
    const stop = () => {
        drawing = false;
    };

    canvas.addEventListener("pointerdown", start);
    canvas.addEventListener("pointermove", move);
    canvas.addEventListener("pointerup", stop);
    canvas.addEventListener("pointerleave", stop);

    root.querySelector("[data-signature-clear]")?.addEventListener("click", () => {
        context.clearRect(0, 0, canvas.width, canvas.height);
        context.fillStyle = "#ffffff";
        context.fillRect(0, 0, canvas.width, canvas.height);
    });
    root.querySelector("[data-signature-save]")?.addEventListener("click", async () => {
        try {
            await saveDrawnSignature(canvas);
        } catch (error) {
            toast(error.message || "Nao foi possivel salvar a assinatura desenhada.");
        }
    });
}

async function refreshTechnicalAssetPreviews(root) {
    const kinds = ["sanitary_license", "environmental_license", "signature"];
    for (const kind of kinds) {
        const asset = kind === "signature"
            ? state.settings?.company?.technical_signature
            : state.settings?.company?.[`${kind}_file`];
        if (!asset?.has_file) {
            continue;
        }
        const emptyState = root.querySelector(`[data-technical-preview-empty="${kind}"]`);
        const image = root.querySelector(`[data-technical-preview-image="${kind}"]`);
        const link = root.querySelector(`[data-technical-preview-link="${kind}"]`);
        try {
            const response = await apiFetchResponse(`/api/v1/settings/technical-documents/assets/${kind}`, { method: "GET" });
            const blob = await response.blob();
            const objectUrl = URL.createObjectURL(blob);
            if (blob.type.startsWith("image/") && image instanceof HTMLImageElement) {
                image.src = objectUrl;
                image.classList.remove("hidden");
            }
            if (link instanceof HTMLAnchorElement) {
                link.href = objectUrl;
                link.classList.remove("hidden");
                link.textContent = blob.type === "application/pdf" ? "Abrir PDF" : "Abrir arquivo";
            }
            emptyState?.classList.add("hidden");
        } catch (error) {
            if (emptyState) {
                emptyState.textContent = error.message || "Nao foi possivel carregar o preview.";
                emptyState.classList.remove("hidden");
            }
        }
    }
}

function getSystemSettingsPayload(form) {
    return {
        integrations: {
            google_calendar_enabled: form.querySelector('[name="google_calendar_enabled"]').checked,
            whatsapp_enabled: form.querySelector('[name="whatsapp_enabled"]').checked,
            whatsapp_auto_send: form.querySelector('[name="whatsapp_auto_send"]').checked,
            whatsapp_default_message: form.querySelector('[name="whatsapp_default_message"]').value.trim(),
        },
        contracts: {
            alert_days: Number(form.querySelector('[name="contract_alert_days"]').value || 15),
            email_enabled: form.querySelector('[name="contract_email_enabled"]').checked,
            storage_dir: form.querySelector('[name="contract_storage_dir"]').value.trim(),
        },
        email: {
            smtp_host: form.querySelector('[name="smtp_host"]').value.trim() || null,
            smtp_port: Number(form.querySelector('[name="smtp_port"]').value || 587),
            smtp_username: form.querySelector('[name="smtp_username"]').value.trim() || null,
            smtp_password: form.querySelector('[name="smtp_password"]').value,
            smtp_use_tls: form.querySelector('[name="smtp_use_tls"]').checked,
            smtp_use_ssl: form.querySelector('[name="smtp_use_ssl"]').checked,
            smtp_sender_email: form.querySelector('[name="smtp_sender_email"]').value.trim() || null,
            smtp_sender_name: form.querySelector('[name="smtp_sender_name"]').value.trim() || null,
        },
        database: {
            backup_dir: form.querySelector('[name="database_backup_dir"]').value.trim() || "backups/database",
        },
        company: {
            legal_name: form.querySelector('[name="company_legal_name"]').value.trim(),
            trade_name: form.querySelector('[name="company_trade_name"]').value.trim(),
            cnpj: form.querySelector('[name="company_cnpj"]').value.trim() || null,
            address: form.querySelector('[name="company_address"]').value.trim(),
            phone: form.querySelector('[name="company_phone"]').value.trim() || null,
            technical_responsible_name: form.querySelector('[name="technical_responsible_name"]').value.trim(),
            technical_registry_type: form.querySelector('[name="technical_registry_type"]').value.trim(),
            technical_registry_number: form.querySelector('[name="technical_registry_number"]').value.trim(),
            technical_registry_state: form.querySelector('[name="technical_registry_state"]').value.trim().toUpperCase(),
            sanitary_license_number: form.querySelector('[name="sanitary_license_number"]').value.trim(),
            sanitary_license_expiry: form.querySelector('[name="sanitary_license_expiry"]').value.trim() || null,
            environmental_license_number: form.querySelector('[name="environmental_license_number"]').value.trim(),
            environmental_license_expiry: form.querySelector('[name="environmental_license_expiry"]').value.trim() || null,
            toxicology_center_name: form.querySelector('[name="toxicology_center_name"]').value.trim(),
            toxicology_center_phone: form.querySelector('[name="toxicology_center_phone"]').value.trim(),
        },
        system: {
            multiempresa_enabled: form.querySelector('[name="multiempresa_enabled"]').checked,
            operation_mode: form.querySelector('[name="operation_mode"]').value,
            notifications_enabled: form.querySelector('[name="notifications_enabled"]').checked,
            appointment_default_google_sync: form.querySelector('[name="appointment_default_google_sync"]').checked,
        },
    };
}

function renderAll() {
    renderDashboard();
    renderCustomers();
    renderProducts();
    renderStockModule();
    renderPests();
    renderTechnicians();
    renderWorkOrders();
    renderAppointments();
    renderFinance();
    renderSettings();
    renderProviderCompanies();
    renderUsers();
    renderLicenses();
    renderWorkOrderFormHeader();
    renderAppointmentFormHeader();
    renderWorkOrderSaveFeedback();
    renderNfeEmissionWorkspace();
    renderNfeEmissionFeedback();
    setWorkOrderWorkspaceView(state.workOrderScreen || "new");
    setFinanceWorkspaceView(state.financeScreen || "lancamentos");
    setStockWorkspaceView(state.stockScreen || "operations");
    setNfeTabView(state.nfeTab || "issue");
    setAppointmentWorkspaceView(state.appointmentScreen || "operational");
    switchProviderCompanyTab(state.providerCompanyTab || "dados");
    renderProviderCompanyLicenseWorkspace();
}

function toggleMasterSections() {
    const isMaster = state.user?.role === "master";
    const canAccessAdminSettings = hasPermission("settings.view") || hasPermission("users.manage");
    document.querySelectorAll(".master-only").forEach((node) => {
        node.classList.toggle("hidden", !isMaster);
    });
    const canAccessFinance = hasPermission("finance.view");
    document.querySelectorAll(".finance-only").forEach((node) => {
        node.classList.toggle("hidden", !canAccessFinance);
    });
    const canAccessStock = hasPermission("stock.view") || hasPermission("stock.manage") || hasPermission("stock.move");
    document.querySelectorAll(".stock-only").forEach((node) => {
        node.classList.toggle("hidden", !canAccessStock);
    });
    document.querySelectorAll(".admin-only").forEach((node) => {
        node.classList.toggle("hidden", !canAccessAdminSettings);
    });
}

function getEffectivePermissions(role, permissions = null) {
    const defaults = { ...(defaultPermissionsByRole[role] || defaultPermissionsByRole.operador) };
    if (role === "master") {
        Object.keys(defaults).forEach((key) => {
            defaults[key] = true;
        });
        return defaults;
    }
    if (!permissions) {
        return defaults;
    }
    Object.entries(permissions).forEach(([key, value]) => {
        if (Object.prototype.hasOwnProperty.call(defaults, key)) {
            defaults[key] = Boolean(value);
        }
    });
    return defaults;
}

function hasPermission(permissionKey, user = state.user) {
    if (!user) {
        return false;
    }
    const permissions = getEffectivePermissions(user.role, user.permissions || {});
    return Boolean(permissions[permissionKey]);
}

function renderUserPermissionGroups() {
    return Object.entries(permissionCatalog)
        .map(([category, permissions]) => `
            <section class="permission-group">
                <div class="section-heading compact">
                    <h4>${escapeHtml(category.charAt(0).toUpperCase() + category.slice(1))}</h4>
                </div>
                <div class="permission-checklist">
                    ${permissions
                        .map(([key, label]) => `
                            <label class="checkbox-field">
                                <input type="checkbox" name="permission_${key}">
                                <span>${escapeHtml(label)}</span>
                            </label>
                        `)
                        .join("")}
                </div>
            </section>
        `)
        .join("");
}

function collectUserPermissions(form) {
    const permissions = {};
    Object.values(permissionCatalog).flat().forEach(([key]) => {
        permissions[key] = Boolean(form.querySelector(`[name="permission_${CSS.escape(key)}"]`)?.checked);
    });
    return permissions;
}

function applyUserRolePermissionPreset(role, form = document.getElementById("user-form")) {
    if (!form) {
        return;
    }
    const permissions = getEffectivePermissions(role);
    Object.entries(permissions).forEach(([key, value]) => {
        const field = form.querySelector(`[name="permission_${CSS.escape(key)}"]`);
        if (field) {
            field.checked = Boolean(value);
            field.disabled = role === "master";
        }
    });
}

function formActionHtml(kind, saveLabel, cancelLabel) {
    return `
        <div class="inline-actions">
            ${buildButtonHtml({ label: saveLabel, variant: "primary", type: "submit", dataAttributes: `data-save-button=\"${kind}\"` })}
            ${buildButtonHtml({ label: cancelLabel, variant: "secondary", type: "button", hidden: true, dataAttributes: `data-cancel-button=\"${kind}\"` })}
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
            <label><span>E-mail</span><input name="email" type="email" placeholder="cliente@empresa.com"></label>
            <div class="inline-actions compact-actions full-width">
                <button type="button" class="btn btn-default ghost-button" id="customer-cnpj-lookup">Buscar por CNPJ</button>
            </div>
            <label><span>CEP</span><input name="cep" maxlength="9" placeholder="00000-000"></label>
            <label><span>Numero do endereco</span><input name="numero" placeholder="Numero"></label>
            <div class="inline-actions compact-actions full-width">
                <button type="button" class="btn btn-default ghost-button" id="customer-cep-lookup">Buscar por CEP</button>
            </div>
            <label class="full-width"><span>Endereco</span><input name="endereco" required></label>
            <label><span>Complemento</span><input name="complemento"></label>
            <label><span>Bairro</span><input name="bairro"></label>
            <label><span>Cidade</span><input name="cidade" required></label>
            <label><span>Estado</span><input name="estado" maxlength="2" required></label>
            <label><span>Telefone</span><input name="telefone" required></label>
            <label class="full-width"><span>Contato</span><input name="contato" required></label>
        </div>
        ${formActionHtml("customer", "Salvar cliente", "Cancelar edicao")}
    `;

    document.getElementById("contract-form").innerHTML = `
        <div class="section-heading compact">
            <h3>Novo contrato</h3>
            <p>Cadastre descricao, periodo, cobranca recorrente, observacoes e o arquivo vinculado ao cliente selecionado.</p>
        </div>
        <div class="form-grid">
            <label class="full-width"><span>Cliente selecionado</span><input name="cliente_nome" readonly placeholder="Selecione um cliente na tabela acima"></label>
            <label class="full-width"><span>Nome ou descricao do contrato</span><input name="nome" required></label>
            <label><span>Data de inicio</span><input name="data_inicio" type="date" required></label>
            <label><span>Data de vencimento</span><input name="data_vencimento" type="date" required></label>
            <label><span>Valor mensal</span><input name="valor_mensal" type="number" min="0" step="0.01" value="0"></label>
            <label><span>Tipo de cobranca</span>
                <select name="tipo_cobranca">
                    <option value="mensal">Mensal</option>
                    <option value="anual">Anual</option>
                    <option value="personalizado">Personalizado</option>
                </select>
            </label>
            <label><span>Dia de vencimento</span><input name="dia_vencimento" type="number" min="1" max="31" placeholder="Ex: 10"></label>
            <label><span>Gerar cobranca automatica</span>
                <select name="gerar_cobranca_automatica">
                    <option value="false">Nao</option>
                    <option value="true">Sim</option>
                </select>
            </label>
            <label class="full-width"><span>Arquivo do contrato</span><input name="arquivo" type="file" accept=".pdf,.doc,.docx,.png,.jpg,.jpeg,.txt"></label>
            <label class="full-width"><span>Observacoes</span><textarea name="observacoes" rows="4" placeholder="Observacoes internas ou contexto da vigencia"></textarea></label>
        </div>
        <div class="contract-file-actions">
            <span class="origin-note" id="contract-file-note">Anexe PDF, DOC, DOCX, imagem ou TXT ate 10 MB.</span>
        </div>
        ${formActionHtml("contract", "Salvar contrato", "Cancelar edicao")}
    `;

    document.getElementById("product-form").innerHTML = `
        <div class="form-grid">
            <label><span>Nome</span><input name="nome" required></label>
            <label><span>Categoria</span><input name="categoria" placeholder="Inseticida, insumo, equipamento..."></label>
            <label><span>Unidade de medida</span>
                <select name="unidade_medida">
                    <option value="UN">UN</option>
                    <option value="ML">ML</option>
                    <option value="L">L</option>
                    <option value="G">G</option>
                    <option value="KG">KG</option>
                </select>
            </label>
            <label><span>Principio ativo</span><input name="principio_ativo" required></label>
            <label><span>Grupo quimico</span><input name="grupo_quimico" required></label>
            <label><span>Toxicidade</span><input name="toxicidade" required></label>
            <label><span>Concentracao</span><input name="concentracao" required></label>
            <label><span>Registro MS</span><input name="registro_ms" required></label>
            <label><span>Codigo de barras</span><input name="codigo_barras" placeholder="EAN, Code128 ou similar"></label>
            <label>
                <span>NCM</span>
                <input name="ncm" id="product-ncm-input" list="product-ncm-suggestions" placeholder="Digite codigo ou descricao">
                <datalist id="product-ncm-suggestions"></datalist>
                <div id="product-ncm-live-results" class="ncm-live-results hidden"></div>
            </label>
            <label class="product-inline-action">
                <span>Base fiscal</span>
                <button type="button" class="btn btn-default ghost-button" id="product-ncm-lookup-button">Buscar NCM</button>
            </label>
            <label class="full-width"><span>Descricao fiscal</span><input name="ncm_descricao" id="product-ncm-description" readonly></label>
            <label>
                <span>Override manual</span>
                <select name="override_tributacao" id="product-tax-override">
                    <option value="false">Usar base automatica</option>
                    <option value="true">Informar aliquotas manualmente</option>
                </select>
            </label>
            <label><span>Saldo inicial</span><input name="estoque_atual" type="number" min="0" step="0.01" value="0"></label>
            <label><span>Estoque minimo</span><input name="estoque_minimo" type="number" min="0" step="0.01" value="0"></label>
        </div>
        <section class="tax-profile-card">
            <div class="section-heading compact">
                <h4>Tributacao vinculada ao produto</h4>
                <p>O cadastro usa cache local de NCM e permite ajuste manual quando necessario.</p>
            </div>
            <div class="form-grid">
                <label><span>ICMS (%)</span><input name="aliquota_icms" type="number" min="0" step="0.0001" value="0"></label>
                <label><span>IPI (%)</span><input name="aliquota_ipi" type="number" min="0" step="0.0001" value="0"></label>
                <label><span>PIS (%)</span><input name="aliquota_pis" type="number" min="0" step="0.0001" value="0"></label>
                <label><span>COFINS (%)</span><input name="aliquota_cofins" type="number" min="0" step="0.0001" value="0"></label>
            </div>
            <div class="origin-note" id="product-tax-source-note">Sem NCM vinculado. Informe um NCM para preencher automaticamente as aliquotas.</div>
        </section>
        ${formActionHtml("product", "Salvar produto", "Cancelar edicao")}
    `;

    const stockActionsPanel = document.getElementById("stock-actions-panel");
    const stockBalancePanel = document.getElementById("stock-balance-panel");
    const stockTransferPanel = document.getElementById("stock-transfer-panel");
    if (stockActionsPanel) {
        stockActionsPanel.innerHTML = `
            <section class="stock-section-block" id="stock-section-import">
                <div class="section-heading">
                    <h3>Importacoes de estoque</h3>
                    <p>Use XML, CSV ou planilha para dar entrada em produtos e registrar despesa no financeiro quando necessario.</p>
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
                    <div class="inline-actions ui-form-actions">
                        <button type="button" class="btn btn-default ghost-button" id="product-xml-import-button">Importar XML</button>
                    </div>
                    <label class="full-width"><span>Arquivo CSV</span><input id="product-csv-file" type="file" accept=".csv,text/csv"></label>
                    <label><span>Registrar no financeiro</span>
                        <select id="product-csv-finance">
                            <option value="true">Sim</option>
                            <option value="false">Nao</option>
                        </select>
                    </label>
                    <div class="inline-actions ui-form-actions">
                        <button type="button" class="btn btn-default ghost-button" id="product-csv-import-button">Importar CSV</button>
                    </div>
                    <label class="full-width"><span>Arquivo XLSX</span><input id="product-xlsx-file" type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"></label>
                    <label><span>Registrar no financeiro</span>
                        <select id="product-xlsx-finance">
                            <option value="true">Sim</option>
                            <option value="false">Nao</option>
                        </select>
                    </label>
                    <div class="inline-actions ui-form-actions">
                        <button type="button" class="btn btn-default ghost-button" id="product-xlsx-import-button">Importar planilha</button>
                    </div>
                </div>
            </section>
            <section class="stock-section-block" id="stock-section-movement">
                <div class="section-heading">
                    <h3>Movimentacao manual</h3>
                    <p>Registre entradas e saidas com leitura rapida, armazem e local fisico sem misturar saldos entre empresas.</p>
                </div>
                <form id="stock-movement-form" class="form-grid data-form">
                    <label class="full-width"><span>Leitura rapida</span><div class="scanner-inline"><input name="codigo_lido" placeholder="Leia QR Code, codigo de barras ou digite o codigo interno"><button type="button" class="btn btn-default ghost-button" data-stock-scan="movement">Ler codigo</button></div></label>
                    <label><span>Produto</span><select name="produto_id" required><option value="">Selecione um produto</option></select></label>
                    <label><span>Armazem</span><select name="armazem_id"><option value="">Armazem padrao</option></select></label>
                    <label><span>Local fisico</span><select name="local_id"><option value="">Local padrao</option></select></label>
                    <label><span>Tipo</span>
                        <select name="tipo_movimento">
                            <option value="entrada">Entrada</option>
                            <option value="saida">Saida</option>
                        </select>
                    </label>
                    <label><span>Quantidade</span><input name="quantidade" type="number" min="0.01" step="0.01" required></label>
                    <label><span>Unidade</span>
                        <select name="unidade_medida">
                            <option value="UN">UN</option>
                            <option value="ML">ML</option>
                            <option value="L">L</option>
                            <option value="G">G</option>
                            <option value="KG">KG</option>
                        </select>
                    </label>
                    <label><span>Motivo</span><input name="motivo" required placeholder="Ex.: Compra, ajuste, consumo interno"></label>
                    <label><span>Referencia</span><input name="referencia" placeholder="NF, lote, OS, ajuste..."></label>
                    <label class="full-width"><span>Observacoes</span><textarea name="observacoes" rows="2"></textarea></label>
                    <div class="inline-actions ui-form-actions">
                        <button type="submit" class="btn btn-primary">Registrar movimentacao</button>
                    </div>
                </form>
            </section>
            <section class="stock-section-block" id="stock-section-structure">
                <div class="section-heading">
                    <h3>Armazens, locais e etiquetas</h3>
                    <p>Estruture o estoque por deposito, veiculo, equipe ou prateleira e gere etiquetas com QR e codigo de barras.</p>
                </div>
                <form id="stock-warehouse-form" class="form-grid data-form">
                    <label><span>Armazem</span><input name="nome" required placeholder="Ex.: Deposito central"></label>
                    <label><span>Codigo</span><input name="codigo" required placeholder="Ex.: DEP-CENTRAL"></label>
                    <label><span>Tipo</span><input name="tipo" value="armazem" placeholder="armazem, veiculo, equipe"></label>
                    <label><span>Ativo</span><select name="ativo"><option value="true">Sim</option><option value="false">Nao</option></select></label>
                    <label><span>Padrao</span><select name="padrao"><option value="false">Nao</option><option value="true">Sim</option></select></label>
                    <label class="full-width"><span>Descricao</span><input name="descricao" placeholder="Contexto do armazem"></label>
                    <div class="inline-actions ui-form-actions"><button type="submit" class="btn btn-default">Salvar armazem</button></div>
                </form>
                <form id="stock-location-form" class="form-grid data-form">
                    <label><span>Armazem</span><select name="armazem_id" required><option value="">Selecione</option></select></label>
                    <label><span>Local fisico</span><input name="nome" required placeholder="Ex.: Prateleira A1"></label>
                    <label><span>Codigo</span><input name="codigo" required placeholder="Ex.: A1"></label>
                    <label><span>Ativo</span><select name="ativo"><option value="true">Sim</option><option value="false">Nao</option></select></label>
                    <label><span>Padrao</span><select name="padrao"><option value="false">Nao</option><option value="true">Sim</option></select></label>
                    <label class="full-width"><span>Descricao</span><input name="descricao" placeholder="Contexto do local"></label>
                    <div class="inline-actions ui-form-actions"><button type="submit" class="btn btn-default">Salvar local</button></div>
                </form>
                <div class="inline-actions ui-form-actions">
                    <button type="button" class="btn btn-default ghost-button" id="stock-generate-labels-button">Gerar etiquetas PDF</button>
                </div>
                <div id="stock-structure-panel" class="inline-details-panel"></div>
            </section>
        `;
    }
    if (stockBalancePanel) {
        stockBalancePanel.innerHTML = `
            <section class="stock-section-block" id="stock-section-balance">
                <div class="section-heading">
                    <h3>Balanco e inventario</h3>
                    <p>Use esta tela somente para saldo contado, conferencias, leituras continuas e ajuste de inventario.</p>
                </div>
                <form id="stock-balance-form" class="form-grid data-form">
                    <label class="full-width"><span>Leitura rapida</span><div class="scanner-inline"><input name="codigo_lido" placeholder="Leia QR Code, codigo de barras ou digite o codigo interno"><button type="button" class="btn btn-default ghost-button" data-stock-scan="balance">Ler codigo</button></div></label>
                    <label><span>Produto</span><select name="produto_id" required><option value="">Selecione um produto</option></select></label>
                    <label><span>Armazem</span><select name="armazem_id"><option value="">Armazem padrao</option></select></label>
                    <label><span>Local fisico</span><select name="local_id"><option value="">Local padrao</option></select></label>
                    <label><span>Saldo contado</span><input name="saldo_contado" type="number" min="0" step="0.01" required></label>
                    <label><span>Unidade</span>
                        <select name="unidade_medida">
                            <option value="UN">UN</option>
                            <option value="ML">ML</option>
                            <option value="L">L</option>
                            <option value="G">G</option>
                            <option value="KG">KG</option>
                        </select>
                    </label>
                    <label><span>Justificativa</span><input name="motivo" required placeholder="Ex.: Inventario mensal"></label>
                    <label><span>Referencia</span><input name="referencia" placeholder="BAL-..."></label>
                    <label class="full-width"><span>Observacoes</span><textarea name="observacoes" rows="2"></textarea></label>
                    <div class="inline-actions ui-form-actions">
                        <button type="submit" class="btn btn-secondary">Registrar balanco</button>
                    </div>
                </form>
                <div id="stock-inventory-panel" class="inline-details-panel"></div>
            </section>
        `;
    }
    if (stockTransferPanel) {
        stockTransferPanel.innerHTML = `
            <section class="stock-section-block" id="stock-section-transfer">
                <div class="section-heading">
                    <h3>Transferencia entre unidades</h3>
                    <p>Use esta tela somente para transferencias entre matriz, filial, veiculo ou equipe, mantendo cada saldo separado.</p>
                </div>
                <form id="stock-transfer-form" class="form-grid data-form">
                    <label class="full-width"><span>Leitura rapida</span><div class="scanner-inline"><input name="codigo_lido" placeholder="Leia QR Code, codigo de barras ou digite o codigo interno"><button type="button" class="btn btn-default ghost-button" data-stock-scan="transfer">Ler codigo</button></div></label>
                    <label><span>Produto de origem</span><select name="produto_id" required><option value="">Selecione um produto</option></select></label>
                    <label><span>Empresa destino</span><select name="empresa_destino_id" required><option value="">Selecione a empresa destino</option></select></label>
                    <label><span>Armazem origem</span><select name="armazem_origem_id"><option value="">Armazem padrao</option></select></label>
                    <label><span>Local origem</span><select name="local_origem_id"><option value="">Local padrao</option></select></label>
                    <label><span>Armazem destino</span><select name="armazem_destino_id"><option value="">Armazem padrao</option></select></label>
                    <label><span>Local destino</span><select name="local_destino_id"><option value="">Local padrao</option></select></label>
                    <label><span>Quantidade</span><input name="quantidade" type="number" min="0.01" step="0.01" required></label>
                    <label><span>Unidade</span>
                        <select name="unidade_medida">
                            <option value="UN">UN</option>
                            <option value="ML">ML</option>
                            <option value="L">L</option>
                            <option value="G">G</option>
                            <option value="KG">KG</option>
                        </select>
                    </label>
                    <label><span>Motivo</span><input name="motivo" required placeholder="Ex.: Reposicao da filial"></label>
                    <label><span>Referencia</span><input name="referencia" placeholder="TRF-..."></label>
                    <label class="full-width"><span>Observacoes</span><textarea name="observacoes" rows="2"></textarea></label>
                    <div class="inline-actions ui-form-actions">
                        <button type="submit" class="btn btn-secondary">Transferir estoque</button>
                    </div>
                </form>
            </section>
        `;
    }

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

    const receiptForm = document.getElementById("receipt-form");
    if (receiptForm) {
        receiptForm.innerHTML = `
            <div class="form-grid">
                <label><span>Cliente</span><select name="cliente_id" required><option value="">Selecione o cliente</option></select></label>
                <label><span>OS vinculada</span><select name="os_id"><option value="">Sem vinculacao</option></select></label>
                <label><span>Data do recebimento</span><input name="data_recebimento" type="date" required></label>
                <label><span>Valor recebido</span><input name="valor" type="number" min="0.01" step="0.01" required></label>
                <label>
                    <span>Forma de pagamento</span>
                    <select name="forma_pagamento" required>
                        <option value="pix">PIX</option>
                        <option value="dinheiro">Dinheiro</option>
                        <option value="transferencia">Transferencia bancaria</option>
                        <option value="cartao_credito">Cartao de credito</option>
                        <option value="cartao_debito">Cartao de debito</option>
                        <option value="boleto">Boleto</option>
                        <option value="cheque">Cheque</option>
                        <option value="outros">Outros</option>
                    </select>
                </label>
                <label class="full-width"><span>Descricao</span><textarea name="descricao" required placeholder="Descreva claramente o motivo do recebimento."></textarea></label>
            </div>
            <div class="inline-actions compact-actions">
                <button type="button" class="btn btn-default ghost-button" id="receipt-preview-refresh">Atualizar preview</button>
                <span class="origin-note">O valor por extenso e o texto formal sao gerados automaticamente.</span>
            </div>
            <section class="receipt-preview-panel">
                <div class="section-heading compact">
                    <h4>Preview do recibo</h4>
                    <p>Revise o texto formal e os dados finais antes de salvar.</p>
                </div>
                <div id="receipt-preview-card" class="receipt-preview-card">
                    <div class="empty-state">Preencha os dados do recibo para visualizar o documento antes de salvar.</div>
                </div>
            </section>
            ${formActionHtml("receipt", "Salvar recibo", "Cancelar edicao")}
        `;
    }

    const nfeForm = document.getElementById("nfe-form");
    if (nfeForm) {
        nfeForm.innerHTML = `
            <div id="nfe-emission-workspace" class="nfe-emission-workspace"></div>
            <div class="form-grid">
                <label><span>Numero NF-e</span><input name="numero_nfe" required></label>
                <label><span>Cliente</span><select name="cliente_id" required><option value="">Selecione o cliente</option></select></label>
                <label><span>Valor total</span><input name="valor_total" type="number" min="0.01" step="0.01" required></label>
                <label><span>Data emissao</span><input name="data_emissao" type="date" required></label>
                <label><span>Data vencimento</span><input name="data_vencimento" type="date" required></label>
                <label><span>Natureza da operacao</span><input name="natureza_operacao" value="Venda" required></label>
                <label><span>Referencia externa</span><input name="referencia_externa" placeholder="Ex.: NFE-2026-001"></label>
                <label><span>Ambiente</span>
                    <select name="ambiente">
                        <option value="homologacao">Homologacao</option>
                        <option value="producao">Producao</option>
                    </select>
                </label>
                <label><span>Status</span>
                    <select name="status">
                        <option value="emitida">Emitida</option>
                        <option value="cancelada">Cancelada</option>
                    </select>
                </label>
                <label>
                    <span>Gerar financeiro</span>
                    <select name="gerar_financeiro">
                        <option value="true">Sim</option>
                        <option value="false">Nao</option>
                    </select>
                </label>
                <label class="full-width"><span>Observacoes</span><textarea name="observacoes"></textarea></label>
            </div>
            <section class="tax-profile-card">
                <div class="section-heading compact">
                    <h4>Itens fiscais da NF-e</h4>
                    <p>Informe ao menos um item com descricao, NCM, quantidade e valor unitario para emitir na SEFAZ.</p>
                </div>
                <div id="nfe-items-list" class="product-row-list"></div>
                <div class="inline-actions">
                    <button type="button" class="btn btn-default ghost-button" id="add-nfe-item-row">Adicionar item</button>
                </div>
                <p class="origin-note nfe-items-note">Ao selecionar um produto, o sistema preenche descricao, NCM e aliquotas automaticamente.</p>
            </section>
            ${formActionHtml("nfe", "Salvar NF-e", "Cancelar edicao")}
            <div id="nfe-save-feedback" class="nfe-save-feedback hidden"></div>
        `;
    }

    const simplesConfigForm = document.getElementById("simples-config-form");
    if (simplesConfigForm) {
        simplesConfigForm.innerHTML = `
            <div class="form-grid">
                <label><span>Faixa inicial</span><input name="faixa_faturamento_inicio" type="number" min="0" step="0.01" value="0" required></label>
                <label><span>Faixa final</span><input name="faixa_faturamento_fim" type="number" min="0" step="0.01" placeholder="Opcional"></label>
                <label><span>Aliquota (%)</span><input name="aliquota" type="number" min="0.0001" step="0.0001" required></label>
                <label><span>Anexo</span><input name="anexo" placeholder="III"></label>
                <label>
                    <span>Configuracao vigente</span>
                    <select name="vigente">
                        <option value="true">Sim</option>
                        <option value="false">Nao</option>
                    </select>
                </label>
                <label class="full-width"><span>Observacoes</span><textarea name="observacoes"></textarea></label>
            </div>
            <div class="inline-actions">
                <button type="submit" class="btn btn-success" data-save-button="simplesConfig">Salvar configuracao</button>
                <button type="button" class="btn btn-default ghost-button" id="simples-config-clear">Limpar formulario</button>
            </div>
            <p class="origin-note hidden" id="simples-config-mode-note"></p>
            <p class="form-error hidden"></p>
        `;
    }

    document.getElementById("work-order-form").innerHTML = `
        <div class="form-grid">
            <div class="work-order-number-banner full-width">
                <p class="eyebrow">Identificacao da OS</p>
                <strong id="work-order-number-display">Sera gerado automaticamente ao salvar</strong>
                <small>O sistema gera o numero definitivo em sequencia e ele nao pode ser editado manualmente.</small>
            </div>
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
            <label><span>Tipo da O.S.</span>
                <select name="tipo_os">
                    <option value="avulsa">Avulsa</option>
                    <option value="contrato">Contrato</option>
                </select>
            </label>
            <label><span>Valor do servico</span><input name="valor_servico" type="number" step="0.01" min="0" value="0"></label>
            <label class="full-width"><span>Observacoes</span><textarea name="observacoes"></textarea></label>
        </div>
        <div class="section-heading">
            <h3>Produtos aplicados</h3>
            <p class="hint">Pesquise no catalogo, selecione varios itens e adicione em lote na OS.</p>
        </div>
        <div class="tabbed-panel">
            <div class="tabs" role="tablist" aria-label="Produtos da ordem de servico">
                <button
                    type="button"
                    class="tab tab-active"
                    role="tab"
                    aria-selected="true"
                    aria-controls="products-tab-catalogo"
                    id="products-tab-trigger-catalogo"
                    data-products-tab-trigger="catalogo"
                >
                    Catalogo
                </button>
                <button
                    type="button"
                    class="tab"
                    role="tab"
                    aria-selected="false"
                    aria-controls="products-tab-ordem"
                    id="products-tab-trigger-ordem"
                    data-products-tab-trigger="ordem"
                >
                    Na ordem
                </button>
            </div>
            <section
                class="tab-content tab-content-active os-products-card"
                role="tabpanel"
                id="products-tab-catalogo"
                aria-labelledby="products-tab-trigger-catalogo"
                data-products-tab-panel="catalogo"
            >
                <div class="os-products-card-header section-heading compact">
                    <h4>Catalogo de produtos</h4>
                    <p>Busque no catalogo, marque varios itens e envie todos de uma vez para a lista da OS.</p>
                </div>
                <div class="os-products-card-content">
                    <label class="selection-search-field os-products-field">
                        <span>Buscar produto</span>
                        <input id="product-picker-search" type="search" placeholder="Nome, principio ativo ou registro">
                    </label>
                    <div class="selection-panel-toolbar">
                        <div class="selection-panel-summary">
                            <strong id="product-picker-selection-count">0 selecionados</strong>
                            <span id="product-picker-selection-hint">Marque os produtos desejados no catalogo.</span>
                        </div>
                        <div class="selection-panel-batch os-products-batch-grid">
                            <label class="os-products-field">
                                <span>Qtd. padrao</span>
                                <input id="product-picker-default-quantity" type="number" min="0.01" step="0.01" value="1">
                            </label>
                            <label class="os-products-field">
                                <span>Diluicao padrao</span>
                                <input id="product-picker-default-dilution" type="text" placeholder="Ex.: 1:20">
                            </label>
                        </div>
                    </div>
                    <div id="product-picker-options" class="selection-option-list os-products-option-list"></div>
                </div>
                <div class="os-products-actions">
                    <button type="button" class="btn btn-default ghost-button" id="product-picker-select-visible">Selecionar visiveis</button>
                    <button type="button" class="btn btn-success" id="product-picker-add-selected">Adicionar selecionados</button>
                    <button type="button" class="btn btn-default ghost-button" id="product-picker-clear-selection">Limpar selecao</button>
                </div>
            </section>
            <section
                class="tab-content os-products-card"
                role="tabpanel"
                id="products-tab-ordem"
                aria-labelledby="products-tab-trigger-ordem"
                data-products-tab-panel="ordem"
                hidden
            >
                <div class="os-products-card-header section-heading compact">
                    <h4>Produtos na ordem</h4>
                    <p>Defina quantidade e diluicao dos itens escolhidos para esta execucao.</p>
                </div>
                <div class="os-products-card-content">
                    <div class="selection-panel-summary selection-panel-summary-inline">
                        <strong id="product-picker-added-count">0 produtos na OS</strong>
                        <span>Revise quantidade e diluicao antes de salvar a ordem de servico.</span>
                    </div>
                    <div id="products-list" class="product-row-list"></div>
                    <div id="products-empty-state" class="empty-state">Nenhum produto adicionado na ordem ainda.</div>
                </div>
                <div class="os-products-actions">
                    <button type="button" class="btn btn-default ghost-button" id="add-product-row">Adicionar linha manual</button>
                </div>
            </section>
        </div>
        <div class="section-heading">
            <h3>Pragas relacionadas</h3>
            <p class="hint">Pesquise, marque varias pragas e mova para a selecao da OS.</p>
        </div>
        <div class="selection-board">
            <section class="selection-panel">
                <div class="section-heading compact">
                    <h4>Catalogo de pragas</h4>
                    <p>Use a busca para localizar mais rapido a praga atendida na ordem.</p>
                </div>
                <label class="selection-search-field">
                    <span>Buscar praga</span>
                    <input id="pest-picker-search" type="search" placeholder="Nome comum, cientifico ou descricao">
                </label>
                <div id="pest-picker-options" class="selection-option-list"></div>
                <div class="inline-actions">
                    <button type="button" id="pest-picker-add-selected">Adicionar selecionadas</button>
                    <button type="button" class="btn btn-default ghost-button" id="pest-picker-clear-selection">Limpar selecao</button>
                </div>
            </section>
            <section class="selection-panel">
                <div class="section-heading compact">
                    <h4>Pragas na ordem</h4>
                    <p>As pragas escolhidas entram na OS e nos documentos emitidos.</p>
                </div>
                <div id="selected-pests-list" class="selected-chip-list"></div>
            </section>
        </div>
        <div class="section-heading">
            <h3>Fotos da ordem</h3>
            <p id="work-order-photo-hint" class="hint">Salve a ordem e entre em modo de edicao para anexar fotos do atendimento.</p>
        </div>
        <div class="work-order-photos-panel">
            <div class="work-order-photos-toolbar">
                <label class="selection-search-field">
                    <span>Selecionar fotos</span>
                    <input id="work-order-photo-input" type="file" accept="image/png,image/jpeg,image/webp" multiple>
                </label>
                <div class="inline-actions action-strip">
                    <button type="button" class="btn btn-success" id="work-order-photo-upload">Enviar fotos</button>
                </div>
            </div>
            <div id="work-order-photo-list" class="work-order-photo-list"></div>
        </div>
        <div class="section-heading">
            <h3>Agendamento vinculado</h3>
            <p class="hint">Use a OS para criar ou atualizar automaticamente o compromisso na agenda operacional.</p>
        </div>
        <div class="form-grid appointment-link-grid">
            <label><span>Gerar agendamento</span>
                <select name="gerar_agendamento">
                    <option value="true">Sim</option>
                    <option value="false">Nao</option>
                </select>
            </label>
            <label><span>Tipo de servico na agenda</span><input name="tipo_servico_agendamento" placeholder="Ex.: Controle de pragas"></label>
            <label><span>Duracao prevista (min)</span><input name="duracao_prevista_minutos" type="number" min="15" max="480" value="60"></label>
            <label><span>Sincronizar Google Agenda</span>
                <select name="sincronizar_google_agenda">
                    <option value="false">Nao</option>
                    <option value="true">Sim</option>
                </select>
            </label>
            <label class="full-width"><span>Observacoes internas do agendamento</span><textarea name="observacoes_internas_agendamento"></textarea></label>
            <label class="full-width"><span>Instrucoes tecnicas</span><textarea name="instrucoes_tecnicas_agendamento"></textarea></label>
            <label class="full-width"><span>Retorno ou revisita</span><textarea name="retorno_revisita_agendamento"></textarea></label>
        </div>
        <label><span>Gerar financeiro automatico</span>
            <select name="gerar_financeiro">
                <option value="true">Sim</option>
                <option value="false">Nao</option>
            </select>
        </label>
        <p id="work-order-contract-warning" class="origin-note hidden">Esta O.S. nao gerara cobranca automatica.</p>
        ${formActionHtml("workOrder", "Salvar ordem de servico", "Cancelar edicao")}
        <div id="work-order-save-feedback" class="work-order-save-feedback hidden"></div>
    `;

    document.getElementById("appointment-form").innerHTML = `
        <div class="form-grid">
            <label><span>Cliente</span><select name="cliente_id" required><option value="">Selecione um cliente</option></select></label>
            <label><span>Ordem de servico vinculada</span><select name="os_id"><option value="">Sem vinculacao</option></select></label>
            <label><span>Tecnico responsavel</span><select name="tecnico_id"><option value="">Sem tecnico definido</option></select></label>
            <label><span>Tipo de servico</span><input name="tipo_servico" required placeholder="Ex.: Dedetizacao preventiva"></label>
            <label><span>Data do agendamento</span><input name="data_agendamento" type="date" required></label>
            <label><span>Hora do agendamento</span><input name="hora_agendamento" type="time" required></label>
            <label><span>Duracao prevista (min)</span><input name="duracao_prevista_minutos" type="number" min="15" max="480" value="60" required></label>
            <label><span>Status</span>
                <select name="status">
                    <option value="pendente">Pendente</option>
                    <option value="confirmado">Confirmado</option>
                    <option value="em_deslocamento">Em deslocamento</option>
                    <option value="em_atendimento">Em atendimento</option>
                    <option value="concluido">Concluido</option>
                    <option value="reagendado">Reagendado</option>
                    <option value="cancelado">Cancelado</option>
                    <option value="nao_realizado">Nao realizado</option>
                </select>
            </label>
            <label><span>Origem</span>
                <select name="origem">
                    <option value="manual">Manual</option>
                    <option value="ordem_servico">Ordem de servico</option>
                </select>
            </label>
            <label><span>Sincronizar Google Agenda</span>
                <select name="sincronizar_google">
                    <option value="false">Nao</option>
                    <option value="true">Sim</option>
                </select>
            </label>
            <label class="checkbox-field">
                <input name="enviar_whatsapp" type="checkbox" checked>
                <span>Enviar WhatsApp ao salvar este agendamento</span>
            </label>
            <label class="full-width"><span>Observacoes externas</span><textarea name="observacoes" placeholder="Orientacoes visiveis para a operacao"></textarea></label>
            <label class="full-width"><span>Observacoes internas</span><textarea name="observacoes_internas"></textarea></label>
            <label class="full-width"><span>Instrucoes tecnicas</span><textarea name="instrucoes_tecnicas"></textarea></label>
            <label class="full-width"><span>Retorno ou revisita</span><textarea name="retorno_revisita"></textarea></label>
        </div>
        <div id="appointment-customer-summary" class="appointment-customer-summary"></div>
        <div class="inline-actions action-strip appointment-form-shortcuts">
            <button type="button" class="btn btn-default ghost-button" id="appointment-open-linked-work-order">Abrir OS vinculada</button>
            <button type="button" class="btn btn-default ghost-button" id="appointment-duplicate-follow-up">Criar revisita</button>
        </div>
        ${formActionHtml("appointment", "Salvar agendamento", "Cancelar edicao")}
    `;

    document.getElementById("provider-company-form").innerHTML = `
        <div class="tab-strip company-tab-strip">
            <button type="button" class="tab-pill is-active" data-company-tab="dados">Dados da empresa</button>
            <button type="button" class="tab-pill" data-company-tab="usuarios">Usuarios vinculados</button>
            <button type="button" class="tab-pill" data-company-tab="licencas">Licencas</button>
        </div>
        <section class="company-tab-panel is-active" data-company-tab-panel="dados">
            <div class="form-grid">
                <label><span>Razao social</span><input name="razao_social" required></label>
                <label><span>Nome fantasia</span><input name="nome_fantasia"></label>
                <label><span>CNPJ</span><input name="cnpj" required></label>
                <div class="inline-actions compact-actions full-width">
                    <button type="button" class="btn btn-default ghost-button" id="provider-company-cnpj-lookup">Buscar por CNPJ</button>
                </div>
                <label><span>E-mail</span><input name="email"></label>
                <label><span>Telefone</span><input name="telefone"></label>
                <label><span>CEP</span><input name="cep"></label>
                <label class="full-width"><span>Endereco</span><input name="endereco"></label>
                <label><span>Bairro</span><input name="bairro"></label>
                <label><span>Cidade</span><input name="cidade"></label>
                <label><span>Estado</span><input name="estado" maxlength="2"></label>
                <label><span>Status</span>
                    <select name="is_active">
                        <option value="true">Ativa</option>
                        <option value="false">Inativa</option>
                    </select>
                </label>
                <label><span>Tipo</span>
                    <select name="is_provider">
                        <option value="true">Empresa prestadora</option>
                        <option value="false">Apenas unidade de apoio</option>
                    </select>
                </label>
                <label><span>Empresa matriz</span><select name="empresa_pai_id"><option value="">Sem matriz</option></select></label>
                <label><span>Compartilhar visao de estoque</span>
                    <select name="compartilha_visualizacao_estoque">
                        <option value="false">Nao</option>
                        <option value="true">Sim</option>
                    </select>
                </label>
            </div>
        </section>
        <section class="company-tab-panel" data-company-tab-panel="usuarios">
            <div class="section-heading compact">
                <h4>Usuarios vinculados</h4>
                <p>Selecione os usuarios que pertencem a esta empresa prestadora.</p>
            </div>
            <label class="full-width"><span>Usuarios do sistema</span>
                <select name="usuarios_vinculados_ids" id="provider-company-users-select" multiple size="8"></select>
            </label>
        </section>
        <section class="company-tab-panel" data-company-tab-panel="licencas">
            <div class="section-heading compact">
                <h4>Licencas da empresa</h4>
                <p>Cadastre e acompanhe as licencas da prestadora sem sair desta tela.</p>
            </div>
            <div id="provider-company-license-state" class="empty-state"></div>
            <div id="provider-company-licenses-list"></div>
            <div class="section-heading compact">
                <h4>Nova licenca</h4>
                <p>Salve a empresa primeiro para liberar o cadastro de licencas vinculadas.</p>
            </div>
            <div class="form-grid company-license-grid">
                <label class="full-width"><span>Descricao</span><input id="provider-license-descricao"></label>
                <label><span>Inicio</span><input id="provider-license-start-date" type="date"></label>
                <label><span>Fim</span><input id="provider-license-end-date" type="date"></label>
                <label><span>Maximo de usuarios</span><input id="provider-license-max-users" type="number" min="1" value="10"></label>
                <label><span>Status</span>
                    <select id="provider-license-status">
                        <option value="ativa">Ativa</option>
                        <option value="suspensa">Suspensa</option>
                        <option value="expirada">Expirada</option>
                    </select>
                </label>
                <label class="full-width"><span>Observacoes</span><textarea id="provider-license-notes"></textarea></label>
            </div>
            <div class="inline-actions">
                <button type="button" id="provider-license-save-button">Salvar licenca da empresa</button>
            </div>
        </section>
        ${formActionHtml("providerCompany", "Salvar empresa", "Cancelar edicao")}
    `;

    document.getElementById("user-form").innerHTML = `
        <div class="form-grid">
            <label><span>Nome</span><input name="nome" required></label>
            <label><span>Usuario</span><input name="username" required></label>
            <label><span>Senha</span><input name="password" type="password" required></label>
            <label><span>Perfil</span>
                <select name="role">
                    <option value="operador">OPERADOR / TECNICO</option>
                    <option value="gestor_estoque">GESTOR DE ESTOQUE</option>
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
            <label class="full-width"><span>Empresa prestadora</span><select name="empresa_prestadora_id" required><option value="">Selecione uma empresa</option></select></label>
        </div>
        <div class="section-heading">
            <h3>Permissoes do usuario</h3>
            <p>O nivel define o padrão inicial. Ajuste os acessos finos abaixo.</p>
        </div>
        <div id="user-permissions-panel">${renderUserPermissionGroups()}</div>
        ${formActionHtml("user", "Salvar usuario", "Cancelar edicao")}
    `;

    document.getElementById("license-form").innerHTML = `
        <div class="form-grid">
            <label class="full-width"><span>Descricao</span><input name="descricao" required></label>
            <label><span>Inicio</span><input name="start_date" type="date" required></label>
            <label><span>Fim</span><input name="end_date" type="date" required></label>
            <label><span>Maximo de usuarios</span><input name="max_users" type="number" min="1" value="10" required></label>
            <label class="full-width"><span>Empresa prestadora</span><select name="empresa_prestadora_id"><option value="">Licenca global / legado</option></select></label>
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
    bindProductXlsxImport();
    bindStockMovementForm();
    bindStockBalanceForm();
    bindStockTransferForm();
    bindStockStructureForms();
    bindStockCodeHelpers();
    bindStockViewButtons();
    bindCustomerAutoLookup();
    bindNfeFormHelpers();
    bindProductFiscalControls();
    bindProviderCompanyWorkspace();
    bindWorkOrderSelectors();
    bindAppointmentWorkspace();
    bindFinancialModuleWorkspace();
    bindStockFilters();
    clearWorkOrderForm();
    clearAppointmentForm();
    clearReceiptForm();
    window.SysPragasUI?.enhanceAllForms();
}

function bindProductFiscalControls() {
    const ncmInput = document.getElementById("product-ncm-input");
    const lookupButton = document.getElementById("product-ncm-lookup-button");
    const overrideSelect = document.getElementById("product-tax-override");
    const resultsPanel = document.getElementById("product-ncm-live-results");
    if (!ncmInput || !lookupButton || !overrideSelect || !resultsPanel) {
        return;
    }

    let searchTimer = null;
    ncmInput.addEventListener("input", () => {
        window.clearTimeout(searchTimer);
        searchTimer = window.setTimeout(() => {
            loadNcmSuggestions(ncmInput.value);
        }, 220);
    });
    ncmInput.addEventListener("focus", () => {
        if (String(ncmInput.value || "").trim().length >= 2) {
            loadNcmSuggestions(ncmInput.value);
        }
    });
    ncmInput.addEventListener("change", async () => {
        await applyNcmProfileToProductForm(ncmInput.value, false);
    });
    ncmInput.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            hideNcmLiveResults();
        }
    });
    lookupButton.addEventListener("click", async () => {
        await applyNcmProfileToProductForm(ncmInput.value, true);
    });
    overrideSelect.addEventListener("change", () => {
        syncProductTaxFields();
    });
    if (document.body.dataset.ncmOutsideBound !== "true") {
        document.body.dataset.ncmOutsideBound = "true";
        document.addEventListener("click", (event) => {
            const target = event.target;
            if (
                target instanceof HTMLElement
                && !target.closest("#product-ncm-input")
                && !target.closest("#product-ncm-live-results")
                && !target.closest("#product-ncm-lookup-button")
            ) {
                hideNcmLiveResults();
            }
        });
    }
    syncProductTaxFields();
}

function bindFinancialModuleWorkspace() {
    bindFinanceFilters();
    bindReceiptFilters();
    bindNfeFilters();
    bindSimplesSummaryRefresh();
    bindReceiptWorkspace();
}

function bindStockFilters() {
    const bindings = [
        ["stock-search-filter", "stockSearch", "input"],
        ["stock-company-filter", "stockCompany", "change"],
        ["stock-category-filter", "stockCategory", "change"],
        ["stock-status-filter", "stockStatus", "change"],
    ];
    bindings.forEach(([id, key, eventName]) => {
        const field = document.getElementById(id);
        if (!field || field.dataset.bound === "true") {
            return;
        }
        field.dataset.bound = "true";
        field.addEventListener(eventName, () => {
            state.filters[key] = field.value;
            renderStockModule();
        });
    });

    const clearButton = document.getElementById("stock-clear-filters");
    if (clearButton && clearButton.dataset.bound !== "true") {
        clearButton.dataset.bound = "true";
        clearButton.addEventListener("click", () => {
            state.filters.stockSearch = "";
            state.filters.stockCompany = "";
            state.filters.stockCategory = "";
            state.filters.stockStatus = "todos";
            const searchField = document.getElementById("stock-search-filter");
            const companyField = document.getElementById("stock-company-filter");
            const categoryField = document.getElementById("stock-category-filter");
            const statusField = document.getElementById("stock-status-filter");
            if (searchField) searchField.value = "";
            if (companyField) companyField.value = "";
            if (categoryField) categoryField.value = "";
            if (statusField) statusField.value = "todos";
            renderStockModule();
        });
    }
}

function bindFinanceFilters() {
    const bindings = [
        ["finance-search-filter", "financeSearch", "input"],
        ["finance-status-filter", "financeStatus", "change"],
        ["finance-customer-filter", "financeCustomer", "change"],
        ["finance-start-date-filter", "financeStartDate", "change"],
        ["finance-end-date-filter", "financeEndDate", "change"],
    ];
    bindings.forEach(([id, key, eventName]) => {
        const field = document.getElementById(id);
        if (!field || field.dataset.bound === "true") {
            return;
        }
        field.dataset.bound = "true";
        field.addEventListener(eventName, () => {
            state.filters[key] = field.value;
            renderFinance();
        });
    });

    const clearButton = document.getElementById("finance-clear-filters");
    if (clearButton && clearButton.dataset.bound !== "true") {
        clearButton.dataset.bound = "true";
        clearButton.addEventListener("click", () => {
            state.filters.financeSearch = "";
            state.filters.financeStatus = "todos";
            state.filters.financeCustomer = "";
            state.filters.financeStartDate = "";
            state.filters.financeEndDate = "";
            renderFinance();
        });
    }
}

function bindReceiptFilters() {
    const bindings = [
        ["receipt-search-filter", "receiptSearch", "input"],
        ["receipt-customer-filter", "receiptCustomer", "change"],
    ];
    bindings.forEach(([id, key, eventName]) => {
        const field = document.getElementById(id);
        if (!field || field.dataset.bound === "true") {
            return;
        }
        field.dataset.bound = "true";
        field.addEventListener(eventName, () => {
            state.filters[key] = field.value;
            renderFinance();
        });
    });

    const clearButton = document.getElementById("receipt-clear-filters");
    if (clearButton && clearButton.dataset.bound !== "true") {
        clearButton.dataset.bound = "true";
        clearButton.addEventListener("click", () => {
            state.filters.receiptSearch = "";
            state.filters.receiptCustomer = "";
            renderFinance();
        });
    }
}

function bindReceiptWorkspace() {
    const form = document.getElementById("receipt-form");
    const previewButton = document.getElementById("receipt-preview-refresh");
    if (!form || !previewButton) {
        return;
    }

    if (previewButton.dataset.bound !== "true") {
        previewButton.dataset.bound = "true";
        previewButton.addEventListener("click", async () => {
            await refreshReceiptPreview(false);
        });
    }

    if (form.dataset.previewBound !== "true") {
        form.dataset.previewBound = "true";
        const schedulePreview = () => {
            window.clearTimeout(form._receiptPreviewTimer);
            form._receiptPreviewTimer = window.setTimeout(() => {
                refreshReceiptPreview(true);
            }, 220);
        };
        form.addEventListener("input", schedulePreview);
        form.addEventListener("change", (event) => {
            if (event.target?.name === "cliente_id") {
                syncReceiptWorkOrderOptions();
                applySelectedReceiptWorkOrderDefaults();
            }
            if (event.target?.name === "os_id") {
                applySelectedReceiptWorkOrderDefaults();
            }
            schedulePreview();
        });
    }
}

function bindNfeFilters() {
    const bindings = [
        ["nfe-search-filter", "nfeSearch", "input"],
        ["nfe-status-filter", "nfeStatus", "change"],
        ["nfe-customer-filter", "nfeCustomer", "change"],
    ];
    bindings.forEach(([id, key, eventName]) => {
        const field = document.getElementById(id);
        if (!field || field.dataset.bound === "true") {
            return;
        }
        field.dataset.bound = "true";
        field.addEventListener(eventName, () => {
            state.filters[key] = field.value;
            renderFinance();
        });
    });

    const clearButton = document.getElementById("nfe-clear-filters");
    if (clearButton && clearButton.dataset.bound !== "true") {
        clearButton.dataset.bound = "true";
        clearButton.addEventListener("click", () => {
            state.filters.nfeSearch = "";
            state.filters.nfeStatus = "todos";
            state.filters.nfeCustomer = "";
            renderFinance();
        });
    }
}

function bindSimplesSummaryRefresh() {
    const refreshButton = document.getElementById("simples-summary-refresh");
    if (refreshButton && refreshButton.dataset.bound !== "true") {
        refreshButton.dataset.bound = "true";
        refreshButton.addEventListener("click", async () => {
            try {
                setSyncStatus("Atualizando resumo fiscal...");
                state.simplesSummary = await apiFetch(
                    `/api/v1/fiscal/simples/resumo/${getSelectedSimplesReference().year}/${getSelectedSimplesReference().month}`,
                );
                renderFinance();
                setSyncStatus("Sincronizado");
            } catch (error) {
                setSyncStatus("Falha na consulta");
                toast(error.message);
            }
        });
    }

    const monthField = document.getElementById("simples-reference-month");
    if (monthField && monthField.dataset.bound !== "true") {
        monthField.dataset.bound = "true";
        monthField.addEventListener("change", async () => {
            state.filters.simplesReferenceMonth = monthField.value || state.filters.simplesReferenceMonth;
            try {
                state.simplesSummary = await apiFetch(
                    `/api/v1/fiscal/simples/resumo/${getSelectedSimplesReference().year}/${getSelectedSimplesReference().month}`,
                );
                renderFinance();
            } catch (error) {
                toast(error.message);
            }
        });
    }
}

function bindSimplesConfigActions() {
    const clearButton = document.getElementById("simples-config-clear");
    if (clearButton && clearButton.dataset.bound !== "true") {
        clearButton.dataset.bound = "true";
        clearButton.addEventListener("click", () => clearSimplesConfigForm());
    }
}

function syncFinancialReferenceMonth() {
    const monthField = document.getElementById("simples-reference-month");
    if (monthField) {
        monthField.value = state.filters.simplesReferenceMonth || new Date().toISOString().slice(0, 7);
    }
}

function getSelectedSimplesReference() {
    const rawValue = state.filters.simplesReferenceMonth || new Date().toISOString().slice(0, 7);
    const [yearText, monthText] = rawValue.split("-");
    const year = Number(yearText) || new Date().getFullYear();
    const month = Number(monthText) || new Date().getMonth() + 1;
    return { year, month };
}

async function loadNcmSuggestions(query) {
    const datalist = document.getElementById("product-ncm-suggestions");
    const resultsPanel = document.getElementById("product-ncm-live-results");
    if (!datalist || !resultsPanel) {
        return;
    }
    const normalizedQuery = String(query || "").trim();
    if (normalizedQuery.length < 2) {
        datalist.innerHTML = "";
        hideNcmLiveResults();
        return;
    }
    try {
        const results = await apiFetch(`/api/v1/fiscal/ncm?query=${encodeURIComponent(normalizedQuery)}&limit=8`);
        datalist.innerHTML = results
            .map((item) => `<option value="${escapeHtml(item.codigo)}">${escapeHtml(`${item.codigo} - ${item.descricao}`)}</option>`)
            .join("");
        renderNcmLiveResults(results, normalizedQuery);
        const exactCode = digitsOnly(normalizedQuery).slice(0, 8);
        if (exactCode.length === 8 && results.some((item) => item.codigo === exactCode)) {
            await applyNcmProfileToProductForm(exactCode, false);
            hideNcmLiveResults();
        }
    } catch {
        datalist.innerHTML = "";
        hideNcmLiveResults();
    }
}

function renderNcmLiveResults(results, query) {
    const resultsPanel = document.getElementById("product-ncm-live-results");
    const ncmInput = document.getElementById("product-ncm-input");
    if (!resultsPanel || !ncmInput) {
        return;
    }
    if (!results.length) {
        resultsPanel.innerHTML = `<div class="ncm-live-empty">Nenhum NCM encontrado para "${escapeHtml(query)}".</div>`;
        resultsPanel.classList.remove("hidden");
        return;
    }

    resultsPanel.innerHTML = `
        <div class="ncm-live-header">Resultados da pre-busca</div>
        <div class="ncm-live-list">
            ${results.map((item) => `
                <button type="button" class="ncm-live-option" data-code="${escapeHtml(item.codigo)}">
                    <strong>${escapeHtml(item.codigo)}</strong>
                    <span>${escapeHtml(item.descricao)}</span>
                    <small>ICMS ${escapeHtml(String(item.aliquota_icms || 0))}% | PIS ${escapeHtml(String(item.aliquota_pis || 0))}% | COFINS ${escapeHtml(String(item.aliquota_cofins || 0))}%</small>
                </button>
            `).join("")}
        </div>
    `;
    resultsPanel.classList.remove("hidden");

    resultsPanel.querySelectorAll(".ncm-live-option").forEach((button) => {
        button.addEventListener("click", async () => {
            ncmInput.value = button.dataset.code || "";
            hideNcmLiveResults();
            await applyNcmProfileToProductForm(ncmInput.value, true);
        });
    });
}

function hideNcmLiveResults() {
    const resultsPanel = document.getElementById("product-ncm-live-results");
    if (!resultsPanel) {
        return;
    }
    resultsPanel.classList.add("hidden");
}

async function applyNcmProfileToProductForm(ncmValue, warnOnEmpty = false) {
    const normalized = digitsOnly(ncmValue || "").slice(0, 8);
    if (!normalized) {
        if (warnOnEmpty) {
            toast("Informe um NCM para consultar a tributacao.");
        }
        syncProductTaxFields();
        return;
    }
    try {
        const profile = await apiFetch(`/api/v1/fiscal/ncm/${normalized}`);
        const form = document.getElementById("product-form");
        fillForm(form, {
            ncm: profile.codigo,
            ncm_descricao: profile.descricao,
            aliquota_icms: profile.aliquota_icms,
            aliquota_ipi: profile.aliquota_ipi,
            aliquota_pis: profile.aliquota_pis,
            aliquota_cofins: profile.aliquota_cofins,
        });
        syncProductTaxFields();
        updateProductTaxSourceNote(`Base fiscal carregada de ${profile.fonte_dados}.`);
    } catch (error) {
        syncProductTaxFields();
        updateProductTaxSourceNote("Nao foi possivel localizar o NCM informado na base fiscal.");
        if (warnOnEmpty) {
            toast(error.message);
        }
    }
}

function syncProductTaxFields() {
    const form = document.getElementById("product-form");
    if (!form) {
        return;
    }
    const manualOverride = form.querySelector('[name="override_tributacao"]')?.value === "true";
    ["aliquota_icms", "aliquota_ipi", "aliquota_pis", "aliquota_cofins", "ncm_descricao"].forEach((fieldName) => {
        const field = form.querySelector(`[name="${fieldName}"]`);
        if (!field) {
            return;
        }
        const isDescription = fieldName === "ncm_descricao";
        field.readOnly = !manualOverride || isDescription;
        field.classList.toggle("readonly-field", !manualOverride || isDescription);
    });
    updateProductTaxSourceNote(
        manualOverride
            ? "Modo manual ativo. As aliquotas informadas serao preservadas no produto."
            : "Modo automatico ativo. O sistema usa a base local de NCM para preencher as aliquotas.",
    );
}

function updateProductTaxSourceNote(message) {
    const note = document.getElementById("product-tax-source-note");
    if (note && message) {
        note.textContent = message;
    }
}

function clearSimplesConfigForm() {
    const form = document.getElementById("simples-config-form");
    if (!form) {
        return;
    }
    form.reset();
    form.dataset.editingId = "";
    form.querySelector(".form-error").classList.add("hidden");
    const note = document.getElementById("simples-config-mode-note");
    if (note) {
        note.classList.add("hidden");
        note.textContent = "";
    }
    syncFinancialReferenceMonth();
}

function clearReceiptForm() {
    const form = document.getElementById("receipt-form");
    if (!form) {
        return;
    }
    form.reset();
    form.querySelector(".form-error").classList.add("hidden");
    form.querySelector('[name="data_recebimento"]').value = todayIso();
    form.querySelector('[name="forma_pagamento"]').value = "pix";
    state.receiptPreview = null;
    syncReceiptWorkOrderOptions();
    renderReceiptPreview(null);
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

function bindProductXlsxImport() {
    const button = document.getElementById("product-xlsx-import-button");
    if (!button) {
        return;
    }
    button.addEventListener("click", async () => {
        const fileInput = document.getElementById("product-xlsx-file");
        const financeSelect = document.getElementById("product-xlsx-finance");
        const file = fileInput?.files?.[0];
        if (!file) {
            toast("Selecione uma planilha XLSX para importar.");
            return;
        }

        const formData = new FormData();
        formData.append("xlsx_file", file);

        button.disabled = true;
        setSyncStatus("Importando planilha...");
        try {
            const result = await apiFetch(
                `/api/v1/produtos/importar-xlsx?registrar_financeiro=${financeSelect.value}`,
                {
                    method: "POST",
                    body: formData,
                },
            );
            fileInput.value = "";
            await loadAllData();
            toast(
                `Planilha importada: ${result.produtos_processados} item(ns), ${result.produtos_criados} criado(s) e ${result.produtos_atualizados} atualizado(s).`,
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

function bindCustomerAutoLookup() {
    const customerForm = document.getElementById("customer-form");
    const cnpjButton = document.getElementById("customer-cnpj-lookup");
    const cepButton = document.getElementById("customer-cep-lookup");
    const cnpjField = customerForm?.querySelector('[name="cpf_cnpj"]');
    const cepField = customerForm?.querySelector('[name="cep"]');
    if (!customerForm || !cnpjButton || !cepButton || !cnpjField || !cepField) {
        return;
    }

    cnpjButton.addEventListener("click", () => lookupCustomerByCnpj());
    cepButton.addEventListener("click", () => lookupCustomerByCep());
    cnpjField.addEventListener("blur", () => {
        if (digitsOnly(cnpjField.value).length === 14) {
            lookupCustomerByCnpj();
        }
    });
    cepField.addEventListener("blur", () => {
        if (digitsOnly(cepField.value).length === 8) {
            lookupCustomerByCep();
        }
    });
}

function bindProviderCompanyWorkspace() {
    document.querySelectorAll("[data-company-tab]").forEach((button) => {
        button.addEventListener("click", () => switchProviderCompanyTab(button.dataset.companyTab));
    });

    const cnpjButton = document.getElementById("provider-company-cnpj-lookup");
    const cnpjField = document.querySelector('#provider-company-form [name="cnpj"]');
    if (cnpjButton) {
        cnpjButton.addEventListener("click", lookupProviderCompanyByCnpj);
    }
    if (cnpjField) {
        cnpjField.addEventListener("blur", () => {
            if (digitsOnly(cnpjField.value).length === 14) {
                lookupProviderCompanyByCnpj();
            }
        });
    }

    const saveLicenseButton = document.getElementById("provider-license-save-button");
    if (saveLicenseButton) {
        saveLicenseButton.addEventListener("click", saveProviderCompanyLicense);
    }
}

function switchProviderCompanyTab(tab) {
    state.providerCompanyTab = tab || "dados";
    document.querySelectorAll("[data-company-tab]").forEach((button) => {
        button.classList.toggle("is-active", button.dataset.companyTab === state.providerCompanyTab);
    });
    document.querySelectorAll("[data-company-tab-panel]").forEach((panel) => {
        panel.classList.toggle("is-active", panel.dataset.companyTabPanel === state.providerCompanyTab);
    });
}

async function lookupProviderCompanyByCnpj() {
    const form = document.getElementById("provider-company-form");
    const cnpj = form.querySelector('[name="cnpj"]').value;
    if (digitsOnly(cnpj).length !== 14) {
        toast("Informe um CNPJ valido para consulta da empresa.");
        return;
    }
    try {
        setSyncStatus("Consultando CNPJ...");
        const result = await apiFetch(`/api/v1/empresas-prestadoras/consultar-cnpj/${digitsOnly(cnpj)}`);
        fillForm(form, {
            razao_social: result.razao_social || "",
            nome_fantasia: result.nome_fantasia || "",
            email: result.email || "",
            telefone: result.telefone || "",
            cep: formatCep(result.cep || ""),
            endereco: result.endereco || "",
            bairro: result.bairro || "",
            cidade: result.cidade || "",
            estado: result.estado || "",
        });
        setSyncStatus("Sincronizado");
        toast("Dados da empresa preenchidos pelo CNPJ.");
    } catch (error) {
        setSyncStatus("Falha na consulta");
        toast(error.message);
    }
}

function getCurrentProviderCompany() {
    return state.providerCompanies.find((item) => item.id === state.editing.providerCompany) || null;
}

function getCurrentProviderCompanyLicenses() {
    const company = getCurrentProviderCompany();
    if (!company) {
        return [];
    }
    return state.licenses.filter((item) => item.empresa_prestadora_id === company.id);
}

function renderProviderCompanyLicenseWorkspace() {
    const stateNode = document.getElementById("provider-company-license-state");
    const listNode = document.getElementById("provider-company-licenses-list");
    const saveButton = document.getElementById("provider-license-save-button");
    if (!stateNode || !listNode || !saveButton) {
        return;
    }
    const company = getCurrentProviderCompany();
    if (!company) {
        stateNode.textContent = "Salve ou edite uma empresa para visualizar e cadastrar licencas vinculadas.";
        listNode.innerHTML = "";
        saveButton.disabled = true;
        clearProviderCompanyLicenseForm();
        return;
    }

    const licenses = getCurrentProviderCompanyLicenses();
    stateNode.textContent = `Licencas vinculadas a ${company.nome_fantasia || company.razao_social}.`;
    listNode.innerHTML = licenses.length
        ? `<div class="alert-list">${licenses
            .map(
                (item) => `
                    <div class="alert-item">
                        <div>
                            <strong>${escapeHtml(item.descricao)}</strong>
                            <span class="origin-note">${formatDate(item.start_date)} ate ${formatDate(item.end_date)} | max ${escapeHtml(String(item.max_users))} usuario(s)</span>
                        </div>
                        <span>${badge(item.status, item.status === "ativa" ? "" : item.status === "suspensa" ? "warn" : "danger")}</span>
                    </div>
                `,
            )
            .join("")}</div>`
        : `<div class="empty-state">Nenhuma licenca cadastrada para esta empresa.</div>`;
    saveButton.disabled = false;
}

async function saveProviderCompanyLicense() {
    const company = getCurrentProviderCompany();
    if (!company) {
        toast("Salve a empresa primeiro para cadastrar a licenca.");
        return;
    }
    const payload = {
        descricao: document.getElementById("provider-license-descricao").value.trim(),
        start_date: document.getElementById("provider-license-start-date").value,
        end_date: document.getElementById("provider-license-end-date").value,
        max_users: Number(document.getElementById("provider-license-max-users").value || 0),
        status: document.getElementById("provider-license-status").value,
        notes: document.getElementById("provider-license-notes").value.trim() || null,
        empresa_prestadora_id: company.id,
    };
    if (!payload.descricao || !payload.start_date || !payload.end_date) {
        toast("Preencha descricao, inicio e fim da licenca da empresa.");
        return;
    }
    try {
        const result = await apiFetch("/api/v1/licencas", { method: "POST", body: JSON.stringify(payload) });
        clearProviderCompanyLicenseForm();
        await afterMutation("Licenca da empresa salva com sucesso.", { kind: "license", entity: result });
        renderProviderCompanyLicenseWorkspace();
    } catch (error) {
        toast(error.message);
    }
}

function clearProviderCompanyLicenseForm() {
    const descricao = document.getElementById("provider-license-descricao");
    const startDate = document.getElementById("provider-license-start-date");
    const endDate = document.getElementById("provider-license-end-date");
    const maxUsers = document.getElementById("provider-license-max-users");
    const status = document.getElementById("provider-license-status");
    const notes = document.getElementById("provider-license-notes");
    if (!descricao || !startDate || !endDate || !maxUsers || !status || !notes) {
        return;
    }
    descricao.value = "";
    startDate.value = "";
    endDate.value = "";
    maxUsers.value = "10";
    status.value = "ativa";
    notes.value = "";
}

async function lookupCustomerByCnpj() {
    const form = document.getElementById("customer-form");
    const cnpj = form.querySelector('[name="cpf_cnpj"]').value;
    if (digitsOnly(cnpj).length !== 14) {
        toast("Informe um CNPJ valido para consulta.");
        return;
    }
    try {
        setSyncStatus("Consultando CNPJ...");
        const result = await apiFetch(`/api/v1/clientes/consultar-cnpj/${digitsOnly(cnpj)}`);
        fillForm(form, {
            razao_social: result.razao_social || "",
            contato: result.nome_fantasia || result.razao_social || "",
            email: result.email || "",
            telefone: result.telefone || "",
            cep: formatCep(result.cep || ""),
            endereco: result.endereco || "",
            numero: result.numero || "",
            complemento: result.complemento || "",
            bairro: result.bairro || "",
            cidade: result.cidade || "",
            estado: result.estado || "",
        });
        setSyncStatus("Sincronizado");
        toast("Dados do CNPJ preenchidos automaticamente.");
    } catch (error) {
        setSyncStatus("Falha na consulta");
        toast(error.message);
    }
}

async function lookupCustomerByCep() {
    const form = document.getElementById("customer-form");
    const cep = form.querySelector('[name="cep"]').value;
    if (digitsOnly(cep).length !== 8) {
        toast("Informe um CEP valido para consulta.");
        return;
    }
    try {
        setSyncStatus("Consultando CEP...");
        const result = await apiFetch(`/api/v1/clientes/consultar-cep/${digitsOnly(cep)}`);
        fillForm(form, {
            cep: formatCep(result.cep || ""),
            endereco: result.endereco || "",
            bairro: result.bairro || "",
            cidade: result.cidade || "",
            estado: result.estado || "",
        });
        setSyncStatus("Sincronizado");
        toast("Endereco preenchido automaticamente pelo CEP.");
    } catch (error) {
        setSyncStatus("Falha na consulta");
        toast(error.message);
    }
}

function bindCrudForms() {
    bindForm("customer-form", "customer", async (form) => {
        const payload = objectFromForm(form);
        payload.cep = digitsOnly(payload.cep || "") || null;
        payload.email = payload.email || null;
        payload.numero = payload.numero || null;
        payload.complemento = payload.complemento || null;
        payload.bairro = payload.bairro || null;
        await submitCrud("customer", "/api/v1/clientes", payload);
    });

    bindForm("contract-form", "contract", async (form) => {
        const customerId = Number(state.contractWorkspace.customerId || 0);
        if (!customerId) {
            throw new Error("Selecione um cliente antes de salvar um contrato.");
        }
        const formData = new FormData();
        formData.append("nome", form.querySelector('[name="nome"]').value);
        formData.append("data_inicio", form.querySelector('[name="data_inicio"]').value);
        formData.append("data_vencimento", form.querySelector('[name="data_vencimento"]').value);
        formData.append("valor_mensal", form.querySelector('[name="valor_mensal"]').value || "0");
        formData.append("tipo_cobranca", form.querySelector('[name="tipo_cobranca"]').value || "mensal");
        formData.append("dia_vencimento", form.querySelector('[name="dia_vencimento"]').value || "");
        formData.append("gerar_cobranca_automatica", form.querySelector('[name="gerar_cobranca_automatica"]').value || "false");
        formData.append("observacoes", form.querySelector('[name="observacoes"]').value || "");
        const fileField = form.querySelector('[name="arquivo"]');
        if (fileField?.files?.[0]) {
            formData.append("arquivo", fileField.files[0]);
        }

        const id = state.editing.contract;
        const endpoint = id ? `/api/v1/contratos/${id}` : `/api/v1/clientes/${customerId}/contratos`;
        const method = id ? "PUT" : "POST";
        const result = await apiFetch(endpoint, { method, body: formData });
        resetFormMode("contract");
        await afterMutation(id ? "Contrato atualizado com sucesso." : "Contrato salvo com sucesso.", {
            kind: "contract",
            entity: result,
        });
    });

    bindForm("product-form", "product", async (form) => {
        const payload = objectFromForm(form);
        payload.override_tributacao = payload.override_tributacao === "true";
        payload.ncm = digitsOnly(payload.ncm || "").slice(0, 8) || null;
        payload.ncm_descricao = payload.ncm_descricao || null;
        await submitCrud("product", "/api/v1/produtos", payload);
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
        payload.nfe_id = null;
        payload.total_parcelas = Number(payload.total_parcelas || 1);
        payload.parcela_atual = 1;
        payload.categoria = payload.categoria || null;
        payload.fornecedor_nome = payload.fornecedor_nome || null;
        payload.referencia = payload.referencia || null;
        payload.observacoes = payload.observacoes || null;
        payload.origem = "manual";
        await submitCrud("finance", "/api/v1/financeiro", payload);
    });

    if (document.getElementById("receipt-form")) {
        bindForm("receipt-form", "receipt", async (form) => {
            const payload = buildReceiptPayload(form);
            const result = await submitCrud("receipt", "/api/v1/recibos", payload);
            state.receiptPreview = result;
            renderReceiptPreview(result);
            openFinanceView("recibos");
        });
    }

    if (document.getElementById("nfe-form")) {
        bindForm("nfe-form", "nfe", async (form) => {
            clearNfeEmissionFeedback();
            const payload = buildNfePayloadFromForm(form);
            const result = await submitCrud("nfe", "/api/v1/nfe", payload);
            state.nfeWorkflow.lastIssuedInvoiceId = result.id;
            state.nfeTab = "issue";
            renderNfeEmissionWorkspace();
            renderNfeEmissionFeedback();
            openFinanceView("nfe");
        });
    }

    bindForm("work-order-form", "workOrder", async (form) => {
        await save_order(form);
    });

    bindForm("appointment-form", "appointment", async (form) => {
        await saveAppointment(form);
    });

    bindForm("provider-company-form", "providerCompany", async (form) => {
        const payload = objectFromForm(form);
        payload.is_active = payload.is_active === "true";
        payload.is_provider = payload.is_provider === "true";
        payload.compartilha_visualizacao_estoque = payload.compartilha_visualizacao_estoque === "true";
        payload.empresa_pai_id = payload.empresa_pai_id ? Number(payload.empresa_pai_id) : null;
        payload.usuarios_vinculados_ids = Array.from(form.querySelector('[name="usuarios_vinculados_ids"]').selectedOptions)
            .map((option) => Number(option.value));
        const id = state.editing.providerCompany;
        const result = await apiFetch(
            id ? `/api/v1/empresas-prestadoras/${id}` : "/api/v1/empresas-prestadoras",
            {
                method: id ? "PUT" : "POST",
                body: JSON.stringify(payload),
            },
        );
        state.editing.providerCompany = result.id;
        form.querySelector(".form-error").classList.add("hidden");
        form.querySelector('[data-cancel-button="providerCompany"]').classList.remove("hidden");
        form.querySelector('[data-save-button="providerCompany"]').textContent = "Salvar alteracoes";
        const note = form.querySelector('[data-mode-note="providerCompany"]');
        note.classList.remove("hidden");
        note.textContent = `Editando registro #${result.id}.`;
        await afterMutation(id ? "Empresa atualizada com sucesso." : "Empresa salva com sucesso.", {
            kind: "providerCompany",
            entity: result,
        });
        if (!id) {
            switchProviderCompanyTab("licencas");
        }
        renderProviderCompanyLicenseWorkspace();
    });

    bindForm("user-form", "user", async (form) => {
        const payload = objectFromForm(form);
        payload.is_active = payload.is_active === "true";
        payload.empresa_prestadora_id = payload.empresa_prestadora_id ? Number(payload.empresa_prestadora_id) : null;
        payload.permissions = collectUserPermissions(form);
        if (!payload.empresa_prestadora_id) {
            toast("Selecione a empresa prestadora antes de salvar o usuario.");
            return;
        }
        if (state.editing.user && !payload.password) {
            delete payload.password;
        }
        await submitCrud("user", "/api/v1/usuarios", payload);
    });

    const userRoleField = document.querySelector('#user-form [name="role"]');
    if (userRoleField) {
        userRoleField.addEventListener("change", (event) => {
            applyUserRolePermissionPreset(event.currentTarget.value);
        });
        applyUserRolePermissionPreset(userRoleField.value);
    }

    bindForm("license-form", "license", async (form) => {
        const payload = objectFromForm(form);
        payload.max_users = Number(payload.max_users);
        payload.notes = payload.notes || null;
        payload.empresa_prestadora_id = payload.empresa_prestadora_id ? Number(payload.empresa_prestadora_id) : null;
        await submitCrud("license", "/api/v1/licencas", payload);
    });

    const simplesConfigForm = document.getElementById("simples-config-form");
    if (simplesConfigForm) {
        simplesConfigForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const form = event.currentTarget;
            const errorBox = form.querySelector(".form-error");
            const saveButton = form.querySelector('[data-save-button="simplesConfig"]');
            errorBox.classList.add("hidden");
            if (!window.SysPragasUI?.validateForm(form)) {
                throw new Error("Revise os campos destacados antes de salvar a configuracao.");
            }
            saveButton.disabled = true;
            saveButton.dataset.originalLabel = saveButton.dataset.originalLabel || saveButton.textContent;
            saveButton.textContent = "Salvando...";
            try {
                const payload = objectFromForm(form);
                payload.faixa_faturamento_fim = payload.faixa_faturamento_fim || null;
                payload.anexo = payload.anexo || null;
                payload.observacoes = payload.observacoes || null;
                payload.vigente = payload.vigente === "true";
                const editingId = Number(form.dataset.editingId || 0) || null;
                const result = await apiFetch(editingId ? `/api/v1/fiscal/simples/${editingId}` : "/api/v1/fiscal/simples", {
                    method: editingId ? "PUT" : "POST",
                    body: JSON.stringify(payload),
                });
                clearSimplesConfigForm();
                await afterMutation(editingId ? "Configuracao do Simples atualizada com sucesso." : "Configuracao do Simples salva com sucesso.", {
                    kind: "simplesConfig",
                    entity: result,
                });
            } catch (error) {
                errorBox.textContent = error.message;
                errorBox.classList.remove("hidden");
                errorBox.scrollIntoView({ behavior: "smooth", block: "center" });
                toast(error.message || "Nao foi possivel salvar a configuracao.");
            } finally {
                saveButton.disabled = false;
                saveButton.textContent = saveButton.dataset.originalLabel || "Salvar configuracao";
            }
        });
    }
}

function bindForm(formId, kind, handler) {
    const form = document.getElementById(formId);
    form.noValidate = true;
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const errorBox = form.querySelector(".form-error");
        const saveButton = form.querySelector(`[data-save-button="${kind}"]`);
        errorBox.classList.add("hidden");
        if (!window.SysPragasUI?.validateForm(form)) {
            errorBox.textContent = "Revise os campos destacados antes de continuar.";
            errorBox.classList.remove("hidden");
            return;
        }
        if (saveButton) {
            saveButton.disabled = true;
            saveButton.dataset.originalLabel = saveButton.dataset.originalLabel || saveButton.textContent;
            saveButton.textContent = kind === "workOrder" ? "Salvando..." : "Salvando...";
        }
        try {
            await handler(form);
        } catch (error) {
            errorBox.textContent = error.message;
            errorBox.classList.remove("hidden");
            errorBox.scrollIntoView({ behavior: "smooth", block: "center" });
            toast(error.message || "Nao foi possivel concluir a operacao.");
        } finally {
            if (saveButton) {
                saveButton.disabled = false;
                saveButton.textContent = saveButton.dataset.originalLabel || saveLabelForKind(kind);
            }
        }
    });

    form.querySelector(`[data-cancel-button="${kind}"]`).addEventListener("click", () => {
        resetFormMode(kind);
    });
}

async function submitCrud(kind, baseUrl, payload) {
    const id = state.editing[kind];
    let result;
    if (id) {
        result = await apiFetch(`${baseUrl}/${id}`, { method: "PUT", body: JSON.stringify(payload) });
    } else {
        result = await apiFetch(baseUrl, { method: "POST", body: JSON.stringify(payload) });
    }
    resetFormMode(kind);
    await afterMutation(id ? "Registro atualizado com sucesso." : "Registro salvo com sucesso.", { kind, entity: result });
    return result;
}

function getEntityCollectionByKind(kind) {
    const sourceMap = {
        customer: state.customers,
        contract: state.contracts,
        product: state.products,
        pest: state.pests,
        technician: state.technicians,
        finance: state.finance,
        receipt: state.receipts,
        nfe: state.nfeInvoices,
        workOrder: state.workOrders,
        appointment: state.appointments,
        providerCompany: state.providerCompanies,
        user: state.users,
        license: state.licenses,
        simplesConfig: state.simplesConfigs,
    };
    return sourceMap[kind] || null;
}

function applyLocalMutation(kind, entity) {
    const collection = getEntityCollectionByKind(kind);
    if (!collection || !entity || entity.id == null) {
        return;
    }
    const index = collection.findIndex((item) => item.id === entity.id);
    if (index >= 0) {
        collection[index] = entity;
        return;
    }
    collection.unshift(entity);
}

function refreshUiFromLocalState() {
    hydrateDynamicControls();
    syncEditingModes();
    renderAll();
}

async function afterMutation(message, options = {}) {
    const { kind = null, entity = null } = options;
    if (kind && entity) {
        applyLocalMutation(kind, entity);
    }
    try {
        await loadAllData();
        toast(message);
    } catch (error) {
        refreshUiFromLocalState();
        setSyncStatus("Atualizacao parcial");
        toast(`${message} Nao foi possivel atualizar a tela agora: ${error.message}`);
    }
}

function objectFromForm(form) {
    return Object.fromEntries(new FormData(form).entries());
}

function buildReceiptPayload(form) {
    const raw = objectFromForm(form);
    const payload = {
        cliente_id: Number(raw.cliente_id || 0),
        os_id: raw.os_id ? Number(raw.os_id) : null,
        valor: raw.valor,
        forma_pagamento: raw.forma_pagamento,
        descricao: String(raw.descricao || "").trim(),
        data_recebimento: raw.data_recebimento,
    };

    const errors = [];
    if (!payload.cliente_id) {
        errors.push("Selecione o cliente do recibo.");
    }
    if (!payload.data_recebimento) {
        errors.push("Informe a data do recebimento.");
    }
    if (!(Number(payload.valor) > 0)) {
        errors.push("Informe um valor maior que zero para o recibo.");
    }
    if (!payload.forma_pagamento) {
        errors.push("Selecione a forma de pagamento.");
    }
    if (!payload.descricao || payload.descricao.length < 5) {
        errors.push("Descreva o recebimento com pelo menos 5 caracteres.");
    }
    if (payload.os_id) {
        const workOrder = getEntityByKind("workOrder", payload.os_id);
        if (!workOrder) {
            errors.push("A ordem de servico selecionada nao foi encontrada.");
        } else if (workOrder.cliente_id !== payload.cliente_id) {
            errors.push("A OS vinculada deve pertencer ao mesmo cliente informado.");
        }
    }

    if (errors.length) {
        throw new Error([...new Set(errors)].join(" "));
    }
    return payload;
}

function getFilteredReceipts() {
    const search = (state.filters.receiptSearch || "").trim().toLowerCase();
    const customerId = state.filters.receiptCustomer || "";
    return state.receipts.filter((item) => {
        const customerMatches = !customerId || String(item.cliente_id) === String(customerId);
        const searchMatches = !search || [
            item.numero,
            item.cliente?.razao_social,
            item.descricao,
            item.forma_pagamento,
            item.os_numero,
        ]
            .filter(Boolean)
            .join(" ")
            .toLowerCase()
            .includes(search);
        return customerMatches && searchMatches;
    });
}

function syncReceiptWorkOrderOptions() {
    const form = document.getElementById("receipt-form");
    const select = form?.querySelector('[name="os_id"]');
    if (!select) {
        return;
    }
    const currentValue = select.value;
    const customerId = Number(form.querySelector('[name="cliente_id"]')?.value || 0);
    const items = state.workOrders
        .filter((item) => !customerId || item.cliente_id === customerId)
        .sort((a, b) => `${b.data_execucao}${b.hora_inicio}`.localeCompare(`${a.data_execucao}${a.hora_inicio}`));
    select.innerHTML = `
        <option value="">Sem vinculacao</option>
        ${items.map((item) => `
            <option value="${item.id}">
                ${escapeHtml(`OS ${item.numero} | ${item.cliente?.razao_social || "Cliente"} | ${formatDate(item.data_execucao)}`)}
            </option>
        `).join("")}
    `;
    if (currentValue && select.querySelector(`option[value="${currentValue}"]`)) {
        select.value = currentValue;
    }
}

function applySelectedReceiptWorkOrderDefaults() {
    const form = document.getElementById("receipt-form");
    if (!form) {
        return;
    }
    const workOrder = getEntityByKind("workOrder", Number(form.querySelector('[name="os_id"]').value || 0));
    if (!workOrder) {
        return;
    }
    if (!form.querySelector('[name="valor"]').value) {
        form.querySelector('[name="valor"]').value = workOrder.valor_servico || "";
    }
    if (!String(form.querySelector('[name="descricao"]').value || "").trim()) {
        form.querySelector('[name="descricao"]').value = `Recebimento referente a OS ${workOrder.numero}`;
    }
}

async function refreshReceiptPreview(silent = true) {
    const form = document.getElementById("receipt-form");
    if (!form) {
        return null;
    }
    let payload;
    try {
        payload = buildReceiptPayload(form);
    } catch (error) {
        if (!silent) {
            toast(error.message);
        }
        if (!silent || !String(form.querySelector('[name="descricao"]').value || "").trim()) {
            state.receiptPreview = null;
            renderReceiptPreview(null);
        }
        return null;
    }

    try {
        const preview = await apiFetch("/api/v1/recibos/preview", {
            method: "POST",
            body: JSON.stringify(payload),
        });
        state.receiptPreview = preview;
        renderReceiptPreview(preview);
        return preview;
    } catch (error) {
        state.receiptPreview = null;
        renderReceiptPreview(null, error.message);
        if (!silent) {
            toast(error.message);
        }
        return null;
    }
}

function renderReceiptPreview(preview, errorMessage = "") {
    const target = document.getElementById("receipt-preview-card");
    if (!target) {
        return;
    }
    if (!preview) {
        target.innerHTML = errorMessage
            ? `<div class="empty-state">${escapeHtml(errorMessage)}</div>`
            : `<div class="empty-state">Preencha os dados do recibo para visualizar o documento antes de salvar.</div>`;
        return;
    }
    const customerName = preview.cliente_nome || preview.cliente?.razao_social || "Cliente";
    const customerDocument = preview.cliente_documento || preview.cliente?.cpf_cnpj || "-";
    const formattedAmount = preview.valor_formatado || formatCurrency(preview.valor || 0);
    const amountInWords = preview.valor_por_extenso || "-";
    const paymentLabel = preview.forma_pagamento_label || String(preview.forma_pagamento || "").replaceAll("_", " ");
    const formattedDate = preview.data_recebimento_formatada || formatDate(preview.data_recebimento);
    target.innerHTML = `
        <div class="receipt-preview-grid">
            <article class="receipt-preview-metric">
                <span>Cliente</span>
                <strong>${escapeHtml(customerName)}</strong>
                <small>${escapeHtml(customerDocument)}</small>
            </article>
            <article class="receipt-preview-metric">
                <span>Valor</span>
                <strong>${escapeHtml(formattedAmount)}</strong>
                <small>${escapeHtml(amountInWords)}</small>
            </article>
            <article class="receipt-preview-metric">
                <span>Pagamento</span>
                <strong>${escapeHtml(paymentLabel)}</strong>
                <small>${escapeHtml(formattedDate)}</small>
            </article>
            <article class="receipt-preview-metric">
                <span>OS</span>
                <strong>${escapeHtml(preview.os_numero || "Sem vinculacao")}</strong>
                <small>Numero definitivo sera gerado ao salvar.</small>
            </article>
        </div>
        <div class="receipt-preview-text">
            <strong>Texto formal</strong>
            <p>${escapeHtml(preview.texto_formal)}</p>
        </div>
    `;
}

function focusReceiptPreview() {
    const previewCard = document.getElementById("receipt-preview-card");
    if (!previewCard) {
        return;
    }
    previewCard.scrollIntoView({ behavior: "smooth", block: "center" });
}

function showReceiptPreview(receiptId) {
    const receipt = getEntityByKind("receipt", Number(receiptId));
    if (!receipt) {
        toast("Recibo nao encontrado para visualizacao.");
        return;
    }
    state.receiptPreview = receipt;
    renderReceiptPreview(receipt);
    openFinanceView("recibos");
    window.setTimeout(() => focusReceiptPreview(), 80);
}

function bindNfeFormHelpers() {
    const form = document.getElementById("nfe-form");
    if (!form) {
        return;
    }
    const addButton = document.getElementById("add-nfe-item-row");
    if (addButton) {
        addButton.addEventListener("click", () => addNfeItemRow());
    }
    form.addEventListener("input", () => {
        if (state.nfeWorkflow.lastIssuedInvoiceId) {
            clearNfeEmissionFeedback();
        }
        renderNfeEmissionWorkspace();
    });
    form.addEventListener("change", (event) => {
        if (event.target?.name === "ambiente") {
            renderNfeEmissionWorkspace();
        }
    });
    ensureNfeItemRows();
}

function buildNfePayloadFromForm(form) {
    const raw = objectFromForm(form);
    const items = getNfeItemsFromForm(form);
    if (!items.length) {
        throw new Error("Adicione ao menos um item fiscal para emitir a NF-e.");
    }

    const totalFromItems = items.reduce(
        (sum, item) => sum + (Number(item.quantidade || 0) * Number(item.valor_unitario || 0)),
        0,
    );

    return {
        numero_nfe: raw.numero_nfe,
        cliente_id: Number(raw.cliente_id),
        valor_total: raw.valor_total || totalFromItems.toFixed(2),
        data_emissao: raw.data_emissao,
        data_vencimento: raw.data_vencimento,
        status: raw.status,
        gerar_financeiro: raw.gerar_financeiro === "true",
        observacoes: raw.observacoes || null,
        natureza_operacao: raw.natureza_operacao || "Venda",
        ambiente: raw.ambiente || "homologacao",
        referencia_externa: raw.referencia_externa || null,
        itens: items,
    };
}

function ensureNfeItemRows() {
    const list = document.getElementById("nfe-items-list");
    if (!list || list.children.length) {
        hydrateNfeItemProductOptions();
        return;
    }
    addNfeItemRow();
}

function addNfeItemRow(item = {}) {
    const list = document.getElementById("nfe-items-list");
    if (!list) {
        return;
    }
    const row = document.createElement("div");
    row.className = "product-item-row nfe-item-row";
    row.innerHTML = `
        <label class="product-row-field product-row-product">
            <span class="product-row-label">Produto</span>
            <select class="nfe-item-product">
                <option value="">Produto avulso</option>
            </select>
        </label>
        <label class="product-row-field">
            <span class="product-row-label">Descricao</span>
            <input class="nfe-item-description" value="${escapeHtml(item.descricao || "")}" required>
        </label>
        <label class="product-row-field">
            <span class="product-row-label">NCM</span>
            <input class="nfe-item-ncm" value="${escapeHtml(digitsOnly(item.ncm || "").slice(0, 8))}" maxlength="8" required>
        </label>
        <label class="product-row-field">
            <span class="product-row-label">Quantidade</span>
            <input class="nfe-item-quantity" type="number" min="0.0001" step="0.0001" value="${escapeHtml(String(item.quantidade || "1"))}" required>
        </label>
        <label class="product-row-field">
            <span class="product-row-label">Valor unitario</span>
            <input class="nfe-item-unit-price" type="number" min="0.01" step="0.01" value="${escapeHtml(String(item.valor_unitario || ""))}" required>
        </label>
        <label class="product-row-field">
            <span class="product-row-label">CFOP</span>
            <input class="nfe-item-cfop" value="${escapeHtml(item.cfop || "5102")}">
        </label>
        <div class="product-row-actions">
            <button type="button" class="btn btn-default ghost-button nfe-item-remove">Remover item</button>
        </div>
    `;
    list.appendChild(row);
    hydrateNfeItemProductOptions(row.querySelector(".nfe-item-product"), item.produto_id || "");
    bindNfeItemRow(row);
    if (item.produto_id) {
        applyProductToNfeItemRow(row, Number(item.produto_id), { preserveProvidedValues: true, item });
    }
    recalculateNfeFormTotal();
}

function bindNfeItemRow(row) {
    const productSelect = row.querySelector(".nfe-item-product");
    const removeButton = row.querySelector(".nfe-item-remove");
    const ncmInput = row.querySelector(".nfe-item-ncm");
    const valueInputs = row.querySelectorAll(".nfe-item-quantity, .nfe-item-unit-price");

    productSelect?.addEventListener("change", () => {
        applyProductToNfeItemRow(row, Number(productSelect.value || 0));
    });
    removeButton?.addEventListener("click", () => {
        const list = document.getElementById("nfe-items-list");
        row.remove();
        if (list && !list.children.length) {
            addNfeItemRow();
        }
        recalculateNfeFormTotal();
    });
    ncmInput?.addEventListener("input", () => {
        ncmInput.value = digitsOnly(ncmInput.value).slice(0, 8);
    });
    valueInputs.forEach((input) => {
        input.addEventListener("input", () => recalculateNfeFormTotal());
    });
}

function hydrateNfeItemProductOptions(selectNode = null, selectedValue = "") {
    const selects = selectNode ? [selectNode] : Array.from(document.querySelectorAll(".nfe-item-product"));
    selects.forEach((select) => {
        if (!select) {
            return;
        }
        const currentValue = String(selectedValue || select.value || "");
        select.innerHTML = `<option value="">Produto avulso</option>${state.products
            .map((product) => `<option value="${product.id}">${escapeHtml(product.nome)}</option>`)
            .join("")}`;
        if (currentValue) {
            select.value = currentValue;
        }
    });
}

function applyProductToNfeItemRow(row, productId, options = {}) {
    const product = state.products.find((item) => item.id === productId);
    if (!product) {
        recalculateNfeFormTotal();
        return;
    }
    const descriptionInput = row.querySelector(".nfe-item-description");
    const ncmInput = row.querySelector(".nfe-item-ncm");
    const unitPriceInput = row.querySelector(".nfe-item-unit-price");
    const item = options.item || {};

    descriptionInput.value = options.preserveProvidedValues
        ? (item.descricao || product.nome || "")
        : (product.nome || "");
    ncmInput.value = options.preserveProvidedValues
        ? digitsOnly(item.ncm || product.ncm || "").slice(0, 8)
        : digitsOnly(product.ncm || "").slice(0, 8);
    if (!options.preserveProvidedValues && !unitPriceInput.value) {
        unitPriceInput.value = Number(product.preco_unitario || 0).toFixed(2);
    }
    recalculateNfeFormTotal();
}

function recalculateNfeFormTotal() {
    const totalInput = document.querySelector('#nfe-form [name="valor_total"]');
    if (!totalInput) {
        return;
    }
    const currentValue = Number(totalInput.value || 0);
    if (currentValue > 0 && document.activeElement === totalInput) {
        return;
    }
    const total = Array.from(document.querySelectorAll("#nfe-items-list .nfe-item-row")).reduce((sum, row) => {
        const quantity = Number(row.querySelector(".nfe-item-quantity")?.value || 0);
        const unitPrice = Number(row.querySelector(".nfe-item-unit-price")?.value || 0);
        return sum + (quantity * unitPrice);
    }, 0);
    totalInput.value = total > 0 ? total.toFixed(2) : "";
}

function getNfeItemsFromForm(form) {
    return Array.from(form.querySelectorAll(".nfe-item-row"))
        .map((row) => ({
            produto_id: row.querySelector(".nfe-item-product").value ? Number(row.querySelector(".nfe-item-product").value) : null,
            descricao: row.querySelector(".nfe-item-description").value.trim(),
            ncm: digitsOnly(row.querySelector(".nfe-item-ncm").value || "").slice(0, 8),
            quantidade: row.querySelector(".nfe-item-quantity").value,
            valor_unitario: row.querySelector(".nfe-item-unit-price").value,
            cfop: row.querySelector(".nfe-item-cfop").value.trim() || "5102",
        }))
        .filter((item) => item.descricao && item.ncm && item.quantidade && item.valor_unitario);
}

function renderNfeEmissionWorkspace() {
    const target = document.getElementById("nfe-emission-workspace");
    const form = document.getElementById("nfe-form");
    if (!target || !form) {
        return;
    }
    const readiness = state.sefazReadiness;
    const currentEnvironment = form.querySelector('[name="ambiente"]')?.value || readiness?.environment || "homologacao";
    const provider = readiness?.provider || "focus_nfe";
    const directProvider = provider === "sefaz_direct";
    const canEmit = directProvider && (currentEnvironment !== "producao" || Boolean(readiness?.xsd_dir));
    const statusTone = readiness?.ready ? "is-ready" : "is-warning";
    const notes = Array.isArray(readiness?.notes) ? readiness.notes.slice(0, 3) : [];
    const currentInvoice = state.editing.nfe ? getEntityByKind("nfe", state.editing.nfe) : null;
    const saveButton = form.querySelector('[data-save-button="nfe"]');

    if (saveButton) {
        saveButton.textContent = currentInvoice
            ? "Salvar alteracoes"
            : (canEmit ? "Emitir NF-e" : "Salvar NF-e");
        saveButton.dataset.originalLabel = saveButton.textContent;
    }

    target.innerHTML = `
        <section class="nfe-emission-card ${statusTone}">
            <div class="section-heading compact">
                <h4>${directProvider ? "Emissao fiscal pronta" : "Emissao em modo integrado"}</h4>
                <p>${directProvider
                    ? `Provider ativo: ${escapeHtml(provider)} em ${escapeHtml(currentEnvironment)}.`
                    : "A tela continua funcional, mas a emissao direta pela SEFAZ nao esta ativa."}</p>
            </div>
            <div class="nfe-emission-meta">
                <span class="orders-stat is-active">${escapeHtml(provider)}</span>
                <span class="orders-stat">${escapeHtml(currentEnvironment)}</span>
                <span class="orders-stat">${readiness?.ready ? "Prontidao validada" : "Configuracao parcial"}</span>
            </div>
            ${notes.length ? `<div class="nfe-emission-notes">${notes.map((note) => `<p>${escapeHtml(note)}</p>`).join("")}</div>` : ""}
            ${currentInvoice ? '<p class="origin-note">Edicao local aberta. Os itens fiscais serao reusados do payload salvo quando disponivel.</p>' : ""}
        </section>
    `;
}

function clearNfeEmissionFeedback() {
    state.nfeWorkflow.lastIssuedInvoiceId = null;
    renderNfeEmissionFeedback();
}

function renderNfeEmissionFeedback() {
    const target = document.getElementById("nfe-save-feedback");
    if (!target) {
        return;
    }
    const invoice = state.nfeWorkflow.lastIssuedInvoiceId
        ? getEntityByKind("nfe", state.nfeWorkflow.lastIssuedInvoiceId)
        : null;
    if (!invoice) {
        target.innerHTML = "";
        target.classList.add("hidden");
        return;
    }
    target.innerHTML = `
        <section class="work-order-save-card">
            <div class="section-heading compact">
                <h4>NF-e emitida com sucesso</h4>
                <p>Nota ${escapeHtml(invoice.numero_nfe)} vinculada a ${escapeHtml(invoice.cliente?.razao_social || "cliente")}.</p>
            </div>
            <div class="work-order-save-meta">
                <span class="orders-stat is-active">${escapeHtml(invoice.provedor || "nfe")}</span>
                <span class="orders-stat">${escapeHtml(badgeLabel(invoice.status_processamento || invoice.status))}</span>
                <span class="orders-stat">${escapeHtml(invoice.finance_entry_id ? `Lancamento #${invoice.finance_entry_id}` : "Sem financeiro")}</span>
            </div>
            <div class="work-order-save-actions">
                <button type="button" class="btn btn-success nfe-sync-status" data-id="${invoice.id}">Consultar status</button>
                <button type="button" class="btn btn-default ghost-button nfe-download-xml" data-id="${invoice.id}">Baixar XML</button>
                <button type="button" class="btn btn-default ghost-button nfe-open-pdf" data-id="${invoice.id}">Abrir DANFE</button>
            </div>
        </section>
    `;
    target.classList.remove("hidden");
    bindNfeActions();
}

function badgeLabel(value) {
    return String(value || "-").replaceAll("_", " ");
}

function extractPrefixedFields(form, prefix) {
    const entries = Array.from(new FormData(form).entries())
        .filter(([key]) => key.startsWith(prefix))
        .map(([key, value]) => [key.replace(prefix, ""), typeof value === "string" ? value.trim() : value]);
    if (!entries.length) {
        return null;
    }
    const payload = Object.fromEntries(entries);
    const hasValue = Object.values(payload).some((value) => String(value || "").trim() !== "");
    return hasValue ? payload : null;
}

function clearPrefixedFields(form, prefix) {
    form.querySelectorAll(`[name^="${prefix}"]`).forEach((field) => {
        if (field.tagName === "SELECT") {
            field.selectedIndex = 0;
        } else {
            field.value = "";
        }
    });
}

function hydrateDynamicControls() {
    setSelectOptions(document.querySelector('#finance-form [name="cliente_id"]'), state.customers, "id", "razao_social");
    setSelectOptions(document.querySelector('#receipt-form [name="cliente_id"]'), state.customers, "id", "razao_social");
    setSelectOptions(document.querySelector('#nfe-form [name="cliente_id"]'), state.customers, "id", "razao_social");
    setSelectOptions(document.getElementById("finance-customer-filter"), state.customers, "id", "razao_social");
    setSelectOptions(document.getElementById("receipt-customer-filter"), state.customers, "id", "razao_social");
    setSelectOptions(document.getElementById("nfe-customer-filter"), state.customers, "id", "razao_social");
    setSelectOptions(document.querySelector('#work-order-form [name="cliente_id"]'), state.customers, "id", "razao_social");
    setSelectOptions(
        document.querySelector('#work-order-form [name="tecnico_id"]'),
        state.technicians.filter((item) => item.ativo),
        "id",
        "nome",
    );
    setSelectOptions(document.querySelector('#appointment-form [name="cliente_id"]'), state.customers, "id", "razao_social");
    setSelectOptions(
        document.querySelector('#appointment-form [name="tecnico_id"]'),
        state.technicians.filter((item) => item.ativo),
        "id",
        "nome",
    );
    hydrateNfeItemProductOptions();
    recalculateNfeFormTotal();
    syncReceiptWorkOrderOptions();
    syncAppointmentWorkOrderOptions();
    syncFinancialReferenceMonth();

    document.querySelectorAll(".product-select").forEach((select) => {
        setSelectOptions(select, state.products, "id", "nome");
    });
    setSelectOptions(
        document.querySelector('#user-form [name="empresa_prestadora_id"]'),
        state.providerCompanies.map((item) => ({ ...item, display_name: item.nome_fantasia || item.razao_social })),
        "id",
        "display_name",
    );
    setSelectOptions(
        document.querySelector('#license-form [name="empresa_prestadora_id"]'),
        state.providerCompanies.map((item) => ({ ...item, display_name: item.nome_fantasia || item.razao_social })),
        "id",
        "display_name",
    );
    setSelectOptions(
        document.querySelector('#provider-company-form [name="empresa_pai_id"]'),
        state.providerCompanies.map((item) => ({ ...item, display_name: item.nome_fantasia || item.razao_social })),
        "id",
        "display_name",
    );
    setSelectOptions(
        document.querySelector('#stock-movement-form [name="produto_id"]'),
        state.products.map((item) => ({
            ...item,
            display_name: `${item.nome} | ${item.empresa_prestadora_nome || "Sem empresa"} | saldo ${item.estoque_atual} ${item.unidade_medida || "UN"}`,
        })),
        "id",
        "display_name",
    );
    const warehouseOptions = state.stockWarehouses.map((item) => ({
        ...item,
        display_name: `${item.nome} | ${item.empresa_prestadora_nome || "Sem empresa"}`,
    }));
    [
        document.querySelector('#stock-movement-form [name="armazem_id"]'),
        document.querySelector('#stock-balance-form [name="armazem_id"]'),
        document.querySelector('#stock-transfer-form [name="armazem_origem_id"]'),
        document.querySelector('#stock-transfer-form [name="armazem_destino_id"]'),
        document.querySelector('#stock-location-form [name="armazem_id"]'),
    ].forEach((select) => setSelectOptions(select, warehouseOptions, "id", "display_name"));
    const locationOptions = state.stockLocations.map((item) => ({
        ...item,
        display_name: `${item.nome} | ${item.armazem_nome || "Sem armazem"}`,
    }));
    [
        document.querySelector('#stock-movement-form [name="local_id"]'),
        document.querySelector('#stock-balance-form [name="local_id"]'),
        document.querySelector('#stock-transfer-form [name="local_origem_id"]'),
        document.querySelector('#stock-transfer-form [name="local_destino_id"]'),
    ].forEach((select) => setSelectOptions(select, locationOptions, "id", "display_name"));
    setSelectOptions(
        document.getElementById("stock-company-filter"),
        state.stockCompanies.map((item) => ({ ...item, display_name: item.nome_fantasia || item.razao_social })),
        "id",
        "display_name",
    );
    const stockCategories = Array.from(new Set(state.stockPositions.map((item) => item.categoria).filter(Boolean)))
        .sort((a, b) => String(a).localeCompare(String(b), "pt-BR"))
        .map((item) => ({ value: item, label: item }));
    setSelectOptions(
        document.getElementById("stock-category-filter"),
        stockCategories.map((item) => ({ id: item.value, display_name: item.label })),
        "id",
        "display_name",
    );
    setSelectOptions(
        document.querySelector('#stock-balance-form [name="produto_id"]'),
        state.products.map((item) => ({
            ...item,
            display_name: `${item.nome} | saldo ${item.estoque_atual} ${item.unidade_medida || "UN"}` ,
        })),
        "id",
        "display_name",
    );
    setSelectOptions(
        document.querySelector('#stock-transfer-form [name="produto_id"]'),
        state.products.map((item) => ({
            ...item,
            display_name: `${item.nome} | origem ${item.empresa_prestadora_nome || "Sem empresa"} | saldo ${item.estoque_atual} ${item.unidade_medida || "UN"}`,
        })),
        "id",
        "display_name",
    );
    const currentCompanyId = String(state.user?.empresa_prestadora_id || "");
    setSelectOptions(
        document.querySelector('#stock-transfer-form [name="empresa_destino_id"]'),
        state.stockCompanies
            .filter((item) => String(item.id) !== currentCompanyId)
            .map((item) => ({
                ...item,
                display_name: item.nome_fantasia || item.razao_social,
            })),
        "id",
        "display_name",
    );
    setMultiSelectOptions(
        document.querySelector('#provider-company-form [name="usuarios_vinculados_ids"]'),
        state.users.map((item) => ({ ...item, display_name: `${item.nome} | ${item.username} | ${item.role}` })),
        "id",
        "display_name",
    );
    if (!state.editing.workOrder) {
        const workOrderGoogleField = document.querySelector('#work-order-form [name="sincronizar_google_agenda"]');
        if (workOrderGoogleField) {
            workOrderGoogleField.value = state.settings?.system?.appointment_default_google_sync ? "true" : "false";
        }
    }
    if (!state.editing.appointment) {
        const appointmentGoogleField = document.querySelector('#appointment-form [name="sincronizar_google"]');
        if (appointmentGoogleField) {
            appointmentGoogleField.value = state.settings?.system?.appointment_default_google_sync ? "true" : "false";
        }
    }
    syncWorkOrderPickerState();
    renderWorkOrderSelectors();
    syncProductTaxFields();
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

function setMultiSelectOptions(select, items, valueKey, labelKey) {
    if (!select) {
        return;
    }
    const selectedValues = Array.from(select.selectedOptions).map((option) => option.value);
    select.innerHTML = items
        .map((item) => `<option value="${item[valueKey]}">${escapeHtml(item[labelKey])}</option>`)
        .join("");
    selectedValues.forEach((value) => {
        const option = select.querySelector(`option[value="${value}"]`);
        if (option) {
            option.selected = true;
        }
    });
}

function addProductRow(values = {}) {
    const list = document.getElementById("products-list");
    const row = document.createElement("div");
    row.className = "product-item-row";
    row.innerHTML = `
        <label class="product-row-field product-row-product">
            <span class="product-row-label">Produto</span>
            <select class="product-select" required></select>
        </label>
        <label class="product-row-field">
            <span class="product-row-label">Quantidade</span>
            <input type="number" class="product-quantity" min="0.01" step="0.01" placeholder="Quantidade" required>
        </label>
        <label class="product-row-field">
            <span class="product-row-label">Diluicao</span>
            <input type="text" class="product-dilution" placeholder="Diluicao" required>
        </label>
        <div class="product-row-actions">
            <button type="button" class="btn btn-default ghost-button remove-product">Remover</button>
        </div>
    `;
    const productSelect = row.querySelector(".product-select");
    productSelect.addEventListener("change", () => renderWorkOrderProductPicker());
    row.querySelector(".remove-product").addEventListener("click", () => {
        row.remove();
        renderWorkOrderProductPicker();
    });
    list.appendChild(row);
    setSelectOptions(productSelect, state.products, "id", "nome");
    if (values.produto_id) {
        productSelect.value = String(values.produto_id);
    }
    if (values.quantidade) {
        row.querySelector(".product-quantity").value = values.quantidade;
    }
    if (values.diluicao) {
        row.querySelector(".product-dilution").value = values.diluicao;
    }
    renderWorkOrderProductPicker();
}

function clearWorkOrderForm() {
    const form = document.getElementById("work-order-form");
    form.reset();
    clearWorkOrderValidation(form);
    form.querySelector(".form-error").classList.add("hidden");
    document.getElementById("products-list").innerHTML = "";
    state.workOrderPicker.productSearch = "";
    state.workOrderPicker.pestSearch = "";
    state.workOrderPicker.productTab = "catalogo";
    state.workOrderPicker.stagedProductIds = [];
    state.workOrderPicker.stagedPestIds = [];
    state.workOrderPicker.selectedPestIds = [];
    document.getElementById("product-picker-search").value = "";
    document.getElementById("pest-picker-search").value = "";
    document.getElementById("product-picker-default-quantity").value = "1";
    document.getElementById("product-picker-default-dilution").value = "";
    document.getElementById("work-order-photo-input").value = "";
    form.querySelector('[name="tipo_os"]').value = "avulsa";
    form.querySelector('[name="gerar_agendamento"]').value = "true";
    form.querySelector('[name="gerar_financeiro"]').value = "true";
    form.querySelector('[name="duracao_prevista_minutos"]').value = "60";
    form.querySelector('[name="sincronizar_google_agenda"]').value = state.settings?.system?.appointment_default_google_sync ? "true" : "false";
    syncWorkOrderTypePresentation(form);
    renderWorkOrderSelectors();
    renderWorkOrderFormHeader();
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
        cliente_id: Number(raw.cliente_id),
        tecnico_id: Number(raw.tecnico_id),
        data_execucao: raw.data_execucao,
        hora_inicio: raw.hora_inicio ? `${raw.hora_inicio}:00` : null,
        hora_fim: raw.hora_fim ? `${raw.hora_fim}:00` : null,
        local_execucao: raw.local_execucao,
        observacoes: raw.observacoes || null,
        garantia_ate: raw.garantia_ate,
        status: raw.status,
        tipo_os: raw.tipo_os || "avulsa",
        valor_servico: raw.valor_servico || "0",
        produtos,
        pragas_ids: [...state.workOrderPicker.selectedPestIds],
        gerar_financeiro: (raw.tipo_os || "avulsa") === "contrato" ? false : raw.gerar_financeiro === "true",
        gerar_agendamento: raw.gerar_agendamento === "true",
        tipo_servico_agendamento: raw.tipo_servico_agendamento || null,
        duracao_prevista_minutos: Number(raw.duracao_prevista_minutos || 60),
        observacoes_internas_agendamento: raw.observacoes_internas_agendamento || null,
        instrucoes_tecnicas_agendamento: raw.instrucoes_tecnicas_agendamento || null,
        retorno_revisita_agendamento: raw.retorno_revisita_agendamento || null,
        sincronizar_google_agenda: raw.sincronizar_google_agenda === "true",
    };
}

function validate_work_order_form(form) {
    clearWorkOrderValidation(form);
    const payload = getWorkOrderPayload(form);
    const errors = [];
    const markFieldInvalid = (selector, message) => {
        const field = form.querySelector(selector);
        if (field) {
            window.SysPragasUI?.markInvalid(field, message);
        }
        errors.push(message);
    };
    const markNodeInvalid = (node, message) => {
        if (node) {
            window.SysPragasUI?.markInvalid(node, message);
        }
        errors.push(message);
    };

    if (!payload.cliente_id) {
        markFieldInvalid('[name="cliente_id"]', "Selecione um cliente para a ordem.");
    }
    if (!payload.tecnico_id) {
        markFieldInvalid('[name="tecnico_id"]', "Selecione um tecnico ativo para a ordem.");
    }
    if (!payload.data_execucao) {
        markFieldInvalid('[name="data_execucao"]', "Informe a data de execucao.");
    }
    if (!payload.garantia_ate) {
        markFieldInvalid('[name="garantia_ate"]', "Informe a data de validade da garantia.");
    }
    if (!payload.hora_inicio) {
        markFieldInvalid('[name="hora_inicio"]', "Informe a hora inicial do atendimento.");
    }
    if (!payload.local_execucao?.trim()) {
        markFieldInvalid('[name="local_execucao"]', "Informe o local de execucao da ordem.");
    }

    const rawStart = form.querySelector('[name="hora_inicio"]')?.value || "";
    const rawEnd = form.querySelector('[name="hora_fim"]')?.value || "";
    if (payload.data_execucao && payload.garantia_ate && payload.garantia_ate < payload.data_execucao) {
        markFieldInvalid('[name="garantia_ate"]', "A garantia deve ser igual ou posterior a data de execucao.");
    }
    if (rawStart && rawEnd && rawEnd <= rawStart) {
        markFieldInvalid('[name="hora_fim"]', "A hora final deve ser posterior a hora inicial.");
    }

    const selectedProductIds = new Set();
    const productRows = Array.from(form.querySelectorAll(".product-item-row"));
    if (!productRows.length && ["em_execucao", "concluida"].includes(payload.status)) {
        markNodeInvalid(
            document.getElementById("products-tab-ordem"),
            "Adicione pelo menos um produto antes de salvar a OS como em execucao ou concluida.",
        );
    }
    productRows.forEach((row, index) => {
        const productSelect = row.querySelector(".product-select");
        const quantityInput = row.querySelector(".product-quantity");
        const dilutionInput = row.querySelector(".product-dilution");
        const productId = Number(productSelect?.value || 0);
        const quantity = Number(quantityInput?.value || 0);
        const dilution = dilutionInput?.value?.trim() || "";
        if (!productId) {
            window.SysPragasUI?.markInvalid(productSelect, `Selecione o produto da linha ${index + 1}.`);
            errors.push(`Selecione o produto da linha ${index + 1}.`);
        } else if (selectedProductIds.has(productId)) {
            window.SysPragasUI?.markInvalid(productSelect, `O produto da linha ${index + 1} esta duplicado na OS.`);
            errors.push(`O produto da linha ${index + 1} esta duplicado na OS.`);
        } else {
            selectedProductIds.add(productId);
        }
        if (!(quantity > 0)) {
            window.SysPragasUI?.markInvalid(quantityInput, `Informe uma quantidade valida na linha ${index + 1}.`);
            errors.push(`Informe uma quantidade valida na linha ${index + 1}.`);
        }
        if (!dilution) {
            window.SysPragasUI?.markInvalid(dilutionInput, `Informe a diluicao do produto na linha ${index + 1}.`);
            errors.push(`Informe a diluicao do produto na linha ${index + 1}.`);
        }
    });

    if (errors.length) {
        throw new Error([...new Set(errors)].join(" "));
    }

    return payload;
}

async function save_order(form) {
    const payload = validate_work_order_form(form);
    clearWorkOrderSaveFeedback();
    const workOrderId = state.editing.workOrder;
    const result = await apiFetch(
        workOrderId ? `/api/v1/os/${workOrderId}` : "/api/v1/os",
        {
            method: workOrderId ? "PUT" : "POST",
            body: JSON.stringify(payload),
        },
    );
    resetFormMode("workOrder");
    await afterMutation(workOrderId ? "OS atualizada com sucesso." : "OS gravada com sucesso.", {
        kind: "workOrder",
        entity: result,
    });
    setWorkOrderWorkspaceView("new");
    state.workOrderWorkflow.lastSavedOrderId = result.id;
    state.workOrderWorkflow.certificateReady = false;
    try {
        await generate_certificate(result.id, { mode: "background", variant: "garantia" });
        state.workOrderWorkflow.certificateReady = true;
    } catch (error) {
        state.workOrderWorkflow.certificateReady = false;
        toast(`Ordem salva, mas houve falha ao preparar o certificado de garantia: ${error.message}`);
    }
    renderWorkOrderSaveFeedback();
    return result;
}

function clearWorkOrderValidation(form = document.getElementById("work-order-form")) {
    window.SysPragasUI?.clearValidation(form);
}

function clearWorkOrderSaveFeedback() {
    state.workOrderWorkflow.lastSavedOrderId = null;
    state.workOrderWorkflow.certificateReady = false;
    renderWorkOrderSaveFeedback();
}

function bindWorkOrderSelectors() {
    const workOrderForm = document.getElementById("work-order-form");
    document.getElementById("add-product-row").addEventListener("click", () => addProductRow());
    workOrderForm.addEventListener("input", () => {
        clearWorkOrderValidation(workOrderForm);
        const errorBox = workOrderForm.querySelector(".form-error");
        errorBox.classList.add("hidden");
        if (state.workOrderWorkflow.lastSavedOrderId) {
            clearWorkOrderSaveFeedback();
        }
    });
    workOrderForm.querySelector('[name="tipo_os"]').addEventListener("change", () => {
        syncWorkOrderTypePresentation(workOrderForm);
    });
    document.getElementById("product-picker-search").addEventListener("input", (event) => {
        state.workOrderPicker.productSearch = event.target.value.trim().toLowerCase();
        renderWorkOrderProductPicker();
    });
    document.getElementById("pest-picker-search").addEventListener("input", (event) => {
        state.workOrderPicker.pestSearch = event.target.value.trim().toLowerCase();
        renderWorkOrderPestPicker();
    });
    document.querySelectorAll("[data-products-tab-trigger]").forEach((button) => {
        button.addEventListener("click", () => {
            setWorkOrderProductTab(button.dataset.productsTabTrigger);
        });
        button.addEventListener("keydown", (event) => {
            const tabs = Array.from(document.querySelectorAll("[data-products-tab-trigger]"));
            const currentIndex = tabs.indexOf(button);
            if (event.key !== "ArrowRight" && event.key !== "ArrowLeft" && event.key !== "Home" && event.key !== "End") {
                return;
            }
            event.preventDefault();
            if (event.key === "Home") {
                tabs[0]?.focus();
                setWorkOrderProductTab(tabs[0]?.dataset.productsTabTrigger);
                return;
            }
            if (event.key === "End") {
                tabs[tabs.length - 1]?.focus();
                setWorkOrderProductTab(tabs[tabs.length - 1]?.dataset.productsTabTrigger);
                return;
            }
            const delta = event.key === "ArrowRight" ? 1 : -1;
            const nextIndex = (currentIndex + delta + tabs.length) % tabs.length;
            tabs[nextIndex]?.focus();
            setWorkOrderProductTab(tabs[nextIndex]?.dataset.productsTabTrigger);
        });
    });
    document.getElementById("product-picker-options").addEventListener("click", (event) => {
        const option = event.target.closest("[data-product-option]");
        if (!option || option.disabled) {
            return;
        }
        toggleStagedSelection("stagedProductIds", Number(option.dataset.id));
        renderWorkOrderProductPicker();
    });
    document.getElementById("pest-picker-options").addEventListener("click", (event) => {
        const option = event.target.closest("[data-pest-option]");
        if (!option || option.disabled) {
            return;
        }
        toggleStagedSelection("stagedPestIds", Number(option.dataset.id));
        renderWorkOrderPestPicker();
    });
    document.getElementById("product-picker-select-visible").addEventListener("click", selectVisibleProductsToWorkOrder);
    document.getElementById("product-picker-add-selected").addEventListener("click", addSelectedProductsToWorkOrder);
    document.getElementById("product-picker-clear-selection").addEventListener("click", () => {
        state.workOrderPicker.stagedProductIds = [];
        renderWorkOrderProductPicker();
    });
    document.getElementById("pest-picker-add-selected").addEventListener("click", addSelectedPestsToWorkOrder);
    document.getElementById("pest-picker-clear-selection").addEventListener("click", () => {
        state.workOrderPicker.stagedPestIds = [];
        renderWorkOrderPestPicker();
    });
    document.getElementById("selected-pests-list").addEventListener("click", (event) => {
        const button = event.target.closest("[data-remove-pest]");
        if (!button) {
            return;
        }
        state.workOrderPicker.selectedPestIds = state.workOrderPicker.selectedPestIds.filter(
            (id) => id !== Number(button.dataset.id),
        );
        renderWorkOrderPestPicker();
    });
    document.getElementById("work-order-photo-upload").addEventListener("click", uploadWorkOrderPhotos);
    document.getElementById("work-order-photo-list").addEventListener("click", async (event) => {
        const button = event.target.closest("[data-remove-photo]");
        if (!button) {
            return;
        }
        if (!window.confirm("Deseja remover esta foto da ordem de servico?")) {
            return;
        }
        try {
            const workOrderId = Number(button.dataset.workOrderId);
            const photoId = Number(button.dataset.photoId);
            await apiFetch(`/api/v1/os/${workOrderId}/fotos/${photoId}`, { method: "DELETE" });
            await loadAllData();
            if (state.editing.workOrder === workOrderId) {
                startEditing("workOrder", workOrderId);
            }
            toast("Foto removida com sucesso.");
        } catch (error) {
            toast(error.message);
        }
    });
    document.getElementById("work-order-save-feedback").addEventListener("click", async (event) => {
        const button = event.target.closest("[data-work-order-action][data-id]");
        if (!button) {
            return;
        }
        const workOrderId = Number(button.dataset.id);
        const action = button.dataset.workOrderAction;
        const previewActions = new Set(["preview-order", "print", "certificate-preview", "certificate-guarantee-preview", "certificate-moldura-preview"]);
        const previewTitleMap = {
            "preview-order": `Ordem de Servico ${workOrderId}`,
            print: `Ordem de Servico ${workOrderId}`,
            "certificate-preview": `Certificado ${workOrderId}`,
            "certificate-guarantee-preview": `Certificado de Garantia ${workOrderId}`,
            "certificate-moldura-preview": `Certificado Moldura ${workOrderId}`,
        };
        const previewWindow = previewActions.has(action)
            ? openDocumentPreviewShell(previewTitleMap[action] || `Documento ${workOrderId}`)
            : null;
        try {
            logClientEvent("work_order_save_action_click", { work_order_id: workOrderId, action });
            if (action === "preview-order") {
                await preview_work_order(workOrderId, { previewWindow });
                return;
            }
            if (action === "print") {
                await print_order(workOrderId, { previewWindow });
                return;
            }
            if (action === "certificate-preview") {
                await generate_certificate(workOrderId, { mode: "preview", previewWindow });
                return;
            }
            if (action === "certificate-guarantee-preview") {
                await generate_certificate(workOrderId, { mode: "preview", variant: "garantia", previewWindow });
                return;
            }
            if (action === "certificate-guarantee-download") {
                await generate_certificate(workOrderId, { mode: "download", variant: "garantia" });
                return;
            }
            if (action === "certificate-download") {
                await generate_certificate(workOrderId, { mode: "download" });
                return;
            }
            if (action === "certificate-moldura-preview") {
                await generate_certificate(workOrderId, { mode: "preview", variant: "moldura", previewWindow });
                return;
            }
            if (action === "certificate-moldura-download") {
                await generate_certificate(workOrderId, { mode: "download", variant: "moldura" });
            }
        } catch (error) {
            if (previewWindow) {
                renderDocumentPreviewError(previewWindow, previewTitleMap[action] || "Documento", error.message);
            }
            logClientEvent(
                "work_order_save_action_error",
                {
                    work_order_id: Number(button.dataset.id),
                    action: button.dataset.workOrderAction,
                    message: error.message,
                },
                "error"
            );
            toast(error.message);
        }
    });
}

function toggleStagedSelection(key, id) {
    const current = state.workOrderPicker[key];
    state.workOrderPicker[key] = current.includes(id)
        ? current.filter((item) => item !== id)
        : [...current, id];
}

function syncWorkOrderPickerState() {
    const productIds = new Set(state.products.map((item) => item.id));
    const pestIds = new Set(state.pests.map((item) => item.id));
    state.workOrderPicker.stagedProductIds = uniqueIds(state.workOrderPicker.stagedProductIds.filter((id) => productIds.has(id)));
    state.workOrderPicker.stagedPestIds = uniqueIds(state.workOrderPicker.stagedPestIds.filter((id) => pestIds.has(id)));
    state.workOrderPicker.selectedPestIds = uniqueIds(state.workOrderPicker.selectedPestIds.filter((id) => pestIds.has(id)));
}

function renderWorkOrderSelectors() {
    renderWorkOrderProductTabs();
    renderWorkOrderProductPicker();
    renderWorkOrderPestPicker();
    renderWorkOrderPhotoWorkspace();
    syncWorkOrderTypePresentation(document.getElementById("work-order-form"));
}

function syncWorkOrderTypePresentation(form) {
    if (!form) {
        return;
    }
    const typeField = form.querySelector('[name="tipo_os"]');
    const financeField = form.querySelector('[name="gerar_financeiro"]');
    const warning = document.getElementById("work-order-contract-warning");
    const isContract = typeField?.value === "contrato";
    if (financeField) {
        if (isContract) {
            if (!financeField.disabled) {
                financeField.dataset.previousValue = financeField.value || "true";
            }
            financeField.value = "false";
            financeField.disabled = true;
        } else {
            financeField.disabled = false;
            financeField.value = financeField.dataset.previousValue || financeField.value || "true";
        }
    }
    warning?.classList.toggle("hidden", !isContract);
}

function setWorkOrderProductTab(tab) {
    state.workOrderPicker.productTab = tab === "ordem" ? "ordem" : "catalogo";
    renderWorkOrderProductTabs();
}

function renderWorkOrderProductTabs() {
    document.querySelectorAll("[data-products-tab-trigger]").forEach((button) => {
        const isActive = button.dataset.productsTabTrigger === state.workOrderPicker.productTab;
        button.classList.toggle("tab-active", isActive);
        button.setAttribute("aria-selected", isActive ? "true" : "false");
        button.setAttribute("tabindex", isActive ? "0" : "-1");
    });
    document.querySelectorAll("[data-products-tab-panel]").forEach((panel) => {
        const isActive = panel.dataset.productsTabPanel === state.workOrderPicker.productTab;
        panel.classList.toggle("tab-content-active", isActive);
        panel.hidden = !isActive;
    });
}

function renderWorkOrderProductPicker() {
    const target = document.getElementById("product-picker-options");
    if (!target) {
        return;
    }
    const search = state.workOrderPicker.productSearch;
    const selectedProductIds = getSelectedProductIds();
    const filteredProducts = state.products.filter((item) => [item.nome, item.principio_ativo, item.registro_ms, item.grupo_quimico]
        .join(" ")
        .toLowerCase()
        .includes(search));
    const availableProducts = filteredProducts.filter((item) => !selectedProductIds.includes(item.id));

    target.innerHTML = filteredProducts.length
        ? filteredProducts
            .map((item) => {
                const alreadyAdded = selectedProductIds.includes(item.id);
                const staged = state.workOrderPicker.stagedProductIds.includes(item.id);
                return `
                    <button
                        type="button"
                        class="selection-option ${staged ? "is-staged" : ""} ${alreadyAdded ? "is-selected" : ""}"
                        data-product-option
                        data-id="${item.id}"
                        ${alreadyAdded ? "disabled" : ""}
                    >
                        <span class="selection-option-topline">
                            <span class="selection-option-title">${escapeHtml(item.nome)}</span>
                            <span class="selection-option-stock">${escapeHtml(String(item.estoque_atual))} em estoque</span>
                        </span>
                        <span class="selection-option-meta">
                            ${escapeHtml(item.principio_ativo)} | Grupo ${escapeHtml(item.grupo_quimico)} | Registro ${escapeHtml(item.registro_ms)}
                        </span>
                        <span class="selection-option-state">${alreadyAdded ? "Ja adicionado" : staged ? "Selecionado" : "Selecionar"}</span>
                    </button>
                `;
            })
            .join("")
        : `<div class="empty-state">Nenhum produto encontrado para a busca informada.</div>`;

    renderWorkOrderProductSummary(filteredProducts.length, availableProducts.length);
}

function renderWorkOrderPestPicker() {
    const optionsTarget = document.getElementById("pest-picker-options");
    const selectedTarget = document.getElementById("selected-pests-list");
    if (!optionsTarget || !selectedTarget) {
        return;
    }

    const search = state.workOrderPicker.pestSearch;
    const filteredPests = state.pests.filter((item) => [item.nome_comum, item.nome_cientifico, item.descricao]
        .join(" ")
        .toLowerCase()
        .includes(search));

    optionsTarget.innerHTML = filteredPests.length
        ? filteredPests
            .map((item) => {
                const alreadyAdded = state.workOrderPicker.selectedPestIds.includes(item.id);
                const staged = state.workOrderPicker.stagedPestIds.includes(item.id);
                return `
                    <button
                        type="button"
                        class="selection-option ${staged ? "is-staged" : ""} ${alreadyAdded ? "is-selected" : ""}"
                        data-pest-option
                        data-id="${item.id}"
                        ${alreadyAdded ? "disabled" : ""}
                    >
                        <span class="selection-option-title">${escapeHtml(item.nome_comum)}</span>
                        <span class="selection-option-meta">${escapeHtml(item.nome_cientifico)}</span>
                        <span class="selection-option-state">${alreadyAdded ? "Ja adicionada" : staged ? "Selecionada" : "Selecionar"}</span>
                    </button>
                `;
            })
            .join("")
        : `<div class="empty-state">Nenhuma praga encontrada para a busca informada.</div>`;

    selectedTarget.innerHTML = state.workOrderPicker.selectedPestIds.length
        ? state.workOrderPicker.selectedPestIds
            .map((id) => state.pests.find((item) => item.id === id))
            .filter(Boolean)
            .map(
                (item) => `
                    <div class="selected-chip">
                        <div>
                            <strong>${escapeHtml(item.nome_comum)}</strong>
                            <span>${escapeHtml(item.nome_cientifico)}</span>
                        </div>
                        <button type="button" class="btn btn-default ghost-button" data-remove-pest data-id="${item.id}">Remover</button>
                    </div>
                `,
            )
            .join("")
        : `<div class="empty-state">Nenhuma praga selecionada para esta ordem.</div>`;
}

function addSelectedProductsToWorkOrder() {
    const existingIds = getSelectedProductIds();
    const newIds = state.workOrderPicker.stagedProductIds.filter((id) => !existingIds.includes(id));
    if (!newIds.length) {
        toast("Selecione pelo menos um produto novo para adicionar.");
        return;
    }
    const defaultQuantity = document.getElementById("product-picker-default-quantity").value || "1";
    const defaultDilution = document.getElementById("product-picker-default-dilution").value.trim();
    newIds.forEach((id) => addProductRow({
        produto_id: id,
        quantidade: defaultQuantity,
        diluicao: defaultDilution,
    }));
    state.workOrderPicker.stagedProductIds = [];
    renderWorkOrderProductPicker();
}

function selectVisibleProductsToWorkOrder() {
    const search = state.workOrderPicker.productSearch;
    const selectedProductIds = getSelectedProductIds();
    const visibleIds = state.products
        .filter((item) => [item.nome, item.principio_ativo, item.registro_ms, item.grupo_quimico]
            .join(" ")
            .toLowerCase()
            .includes(search))
        .map((item) => item.id)
        .filter((id) => !selectedProductIds.includes(id));

    if (!visibleIds.length) {
        toast("Nenhum produto disponivel nesta busca para selecionar.");
        return;
    }

    state.workOrderPicker.stagedProductIds = uniqueIds([...state.workOrderPicker.stagedProductIds, ...visibleIds]);
    renderWorkOrderProductPicker();
}

function renderWorkOrderProductSummary(filteredCount, availableCount) {
    const stagedCount = state.workOrderPicker.stagedProductIds.length;
    const addedCount = getSelectedProductIds().length;
    const selectionCountLabel = document.getElementById("product-picker-selection-count");
    const selectionHintLabel = document.getElementById("product-picker-selection-hint");
    const addedCountLabel = document.getElementById("product-picker-added-count");
    const emptyState = document.getElementById("products-empty-state");
    const addButton = document.getElementById("product-picker-add-selected");
    const clearButton = document.getElementById("product-picker-clear-selection");
    const selectVisibleButton = document.getElementById("product-picker-select-visible");

    if (selectionCountLabel) {
        selectionCountLabel.textContent = `${stagedCount} selecionado(s)`;
    }
    if (selectionHintLabel) {
        if (stagedCount > 0) {
            selectionHintLabel.textContent = "Defina quantidade e diluicao padrao e adicione tudo em lote.";
        } else if (filteredCount > 0) {
            selectionHintLabel.textContent = "Clique nos cards do catalogo para montar o lote desta OS.";
        } else {
            selectionHintLabel.textContent = "Ajuste a busca para localizar produtos do catalogo.";
        }
    }
    if (addedCountLabel) {
        addedCountLabel.textContent = `${addedCount} produto(s) na OS`;
    }
    if (emptyState) {
        emptyState.classList.toggle("hidden", addedCount > 0);
    }
    if (addButton) {
        addButton.disabled = stagedCount === 0;
    }
    if (clearButton) {
        clearButton.disabled = stagedCount === 0;
    }
    if (selectVisibleButton) {
        selectVisibleButton.disabled = availableCount === 0;
    }
}

function renderWorkOrderPhotoCards(photos, options = {}) {
    const { removable = false, workOrderId = null, compact = false } = options;
    if (!photos.length) {
        return `<div class="empty-state">Nenhuma foto anexada nesta ordem de servico.</div>`;
    }

    const listClass = compact ? "work-order-photo-list work-order-photo-list-compact" : "work-order-photo-list";
    return `
        <div class="${listClass}">
            ${photos.map((photo) => `
                <article class="work-order-photo-card ${compact ? "work-order-photo-card-compact" : ""}">
                    <div class="work-order-photo-thumb" data-photo-thumb data-photo-url="${escapeHtml(photo.url)}">
                        <span>Carregando foto...</span>
                    </div>
                    <div class="work-order-photo-copy">
                        <strong>${escapeHtml(photo.filename)}</strong>
                        <span>${formatDateTime(photo.created_at)}</span>
                    </div>
                    ${removable
        ? `
                        <button
                            type="button"
                            class="btn btn-default ghost-button action-button danger"
                            data-remove-photo
                            data-work-order-id="${workOrderId}"
                            data-photo-id="${photo.id}"
                        >
                            Remover
                        </button>
                    `
        : `
                        <button
                            type="button"
                            class="btn btn-default ghost-button"
                            data-view-photo-url="${escapeHtml(photo.url)}"
                        >
                            Abrir foto
                        </button>
                    `}
                </article>
            `).join("")}
        </div>
    `;
}

function renderWorkOrderPhotoWorkspace() {
    const photoInput = document.getElementById("work-order-photo-input");
    const uploadButton = document.getElementById("work-order-photo-upload");
    const hint = document.getElementById("work-order-photo-hint");
    const list = document.getElementById("work-order-photo-list");
    if (!photoInput || !uploadButton || !hint || !list) {
        return;
    }

    const workOrderId = state.editing.workOrder;
    const workOrder = workOrderId ? getEntityByKind("workOrder", workOrderId) : null;
    const isEditable = Boolean(workOrder);

    photoInput.disabled = !isEditable;
    uploadButton.disabled = !isEditable;

    if (!isEditable) {
        hint.textContent = "Salve a ordem e clique em editar para anexar fotos do atendimento.";
        list.innerHTML = `<div class="empty-state">As fotos ficam disponiveis quando a OS ja existe e esta em edicao.</div>`;
        return;
    }

    hint.textContent = "Adicione fotos JPG, PNG ou WEBP para documentar a execucao deste atendimento.";
    list.innerHTML = renderWorkOrderPhotoCards(workOrder.fotos || [], { removable: true, workOrderId: workOrder.id });

    hydrateWorkOrderPhotoThumbs(list);
}

async function hydrateWorkOrderPhotoThumbs(root = document) {
    const nodes = Array.from(root.querySelectorAll("[data-photo-thumb][data-photo-url]"))
        .filter((node) => node.dataset.photoHydrated !== "true");
    await Promise.all(nodes.map(async (node) => {
        try {
            const blob = await apiFetch(node.dataset.photoUrl);
            const objectUrl = URL.createObjectURL(blob);
            node.innerHTML = `<img src="${objectUrl}" alt="Foto da ordem de servico">`;
            node.dataset.photoHydrated = "true";
        } catch {
            node.innerHTML = `<span>Nao foi possivel carregar a foto.</span>`;
        }
    }));
}

async function uploadWorkOrderPhotos() {
    const workOrderId = state.editing.workOrder;
    if (!workOrderId) {
        toast("Salve e edite a ordem de servico antes de anexar fotos.");
        return;
    }

    const input = document.getElementById("work-order-photo-input");
    const files = Array.from(input?.files || []);
    if (!files.length) {
        toast("Selecione pelo menos uma foto para enviar.");
        return;
    }

    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    try {
        await apiFetch(`/api/v1/os/${workOrderId}/fotos`, {
            method: "POST",
            body: formData,
        });
        if (input) {
            input.value = "";
        }
        await loadAllData();
        startEditing("workOrder", workOrderId);
        toast("Fotos anexadas com sucesso.");
    } catch (error) {
        toast(error.message);
    }
}

function formatDateTime(value) {
    return new Date(value).toLocaleString("pt-BR");
}

function addSelectedPestsToWorkOrder() {
    const newIds = state.workOrderPicker.stagedPestIds.filter((id) => !state.workOrderPicker.selectedPestIds.includes(id));
    if (!newIds.length) {
        toast("Selecione pelo menos uma praga nova para adicionar.");
        return;
    }
    state.workOrderPicker.selectedPestIds = uniqueIds([...state.workOrderPicker.selectedPestIds, ...newIds]);
    state.workOrderPicker.stagedPestIds = [];
    renderWorkOrderPestPicker();
}

function getSelectedProductIds() {
    return uniqueIds(
        Array.from(document.querySelectorAll("#products-list .product-select"))
            .map((select) => Number(select.value))
            .filter(Boolean),
    );
}

function uniqueIds(items) {
    return [...new Set(items.map((item) => Number(item)).filter(Boolean))];
}

function todayIso() {
    return new Date().toISOString().slice(0, 10);
}

function parseLocalDate(value) {
    return new Date(`${value || todayIso()}T00:00:00`);
}

function formatTime(value) {
    return value ? String(value).slice(0, 5) : "--:--";
}

function getAppointmentPayload(form) {
    const raw = objectFromForm(form);
    return {
        cliente_id: Number(raw.cliente_id),
        os_id: raw.os_id ? Number(raw.os_id) : null,
        tecnico_id: raw.tecnico_id ? Number(raw.tecnico_id) : null,
        tipo_servico: raw.tipo_servico,
        data_agendamento: raw.data_agendamento,
        hora_agendamento: raw.hora_agendamento ? `${raw.hora_agendamento}:00` : null,
        duracao_prevista_minutos: Number(raw.duracao_prevista_minutos || 60),
        observacoes: raw.observacoes || null,
        observacoes_internas: raw.observacoes_internas || null,
        instrucoes_tecnicas: raw.instrucoes_tecnicas || null,
        retorno_revisita: raw.retorno_revisita || null,
        status: raw.status,
        origem: raw.origem,
        sincronizar_google: raw.sincronizar_google === "true",
        enviar_whatsapp: form.querySelector('[name="enviar_whatsapp"]').checked,
    };
}

function parseTimeToMinutes(value) {
    if (!value) {
        return null;
    }
    const [hours, minutes] = String(value).split(":").map((part) => Number(part));
    if (!Number.isFinite(hours) || !Number.isFinite(minutes)) {
        return null;
    }
    return (hours * 60) + minutes;
}

function minutesToTimeLabel(totalMinutes) {
    if (!Number.isFinite(totalMinutes)) {
        return "--:--";
    }
    const normalized = ((totalMinutes % 1440) + 1440) % 1440;
    const hours = String(Math.floor(normalized / 60)).padStart(2, "0");
    const minutes = String(normalized % 60).padStart(2, "0");
    return `${hours}:${minutes}`;
}

function getAppointmentScheduleInsight(form) {
    const technicianId = Number(form.querySelector('[name="tecnico_id"]')?.value || 0);
    const appointmentDate = form.querySelector('[name="data_agendamento"]')?.value || "";
    const startTime = form.querySelector('[name="hora_agendamento"]')?.value || "";
    const durationMinutes = Number(form.querySelector('[name="duracao_prevista_minutos"]')?.value || 0);
    const startMinutes = parseTimeToMinutes(startTime);
    const editingId = Number(state.editing.appointment || 0);

    if (!technicianId || !appointmentDate || startMinutes === null || durationMinutes < 15) {
        return {
            canEvaluate: false,
            startLabel: startTime || "--:--",
            endLabel: "--:--",
            conflict: null,
        };
    }

    const endMinutes = startMinutes + durationMinutes;
    const conflict = state.appointments.find((item) => {
        if (item.id === editingId) {
            return false;
        }
        if (item.tecnico_id !== technicianId || item.data_agendamento !== appointmentDate) {
            return false;
        }
        if (!activeAppointmentStatuses.has(item.status)) {
            return false;
        }
        const otherStart = parseTimeToMinutes(formatTime(item.hora_agendamento));
        const otherEnd = otherStart === null ? null : otherStart + Number(item.duracao_prevista_minutos || 0);
        if (otherStart === null || otherEnd === null) {
            return false;
        }
        return startMinutes < otherEnd && endMinutes > otherStart;
    }) || null;

    return {
        canEvaluate: true,
        startLabel: minutesToTimeLabel(startMinutes),
        endLabel: minutesToTimeLabel(endMinutes),
        conflict,
    };
}

function buildAppointmentConflictMessage(insight, technicianName) {
    if (!insight?.conflict) {
        return null;
    }
    const conflictingStart = parseTimeToMinutes(formatTime(insight.conflict.hora_agendamento));
    const conflictingEnd = conflictingStart === null
        ? null
        : conflictingStart + Number(insight.conflict.duracao_prevista_minutos || 0);
    const conflictingInterval = `${minutesToTimeLabel(conflictingStart)} ate ${minutesToTimeLabel(conflictingEnd)}`;
    return `Conflito de horario para o tecnico '${technicianName || insight.conflict.tecnico_nome || "selecionado"}' com o agendamento #${insight.conflict.id} (${insight.conflict.cliente_nome}, ${conflictingInterval}). Horario solicitado: ${insight.startLabel} ate ${insight.endLabel}.`;
}

function validateAppointmentForm(form) {
    const payload = getAppointmentPayload(form);
    const errors = [];
    const markFieldInvalid = (selector, message) => {
        const field = form.querySelector(selector);
        if (field) {
            window.SysPragasUI?.markInvalid(field, message);
        }
        errors.push(message);
    };

    window.SysPragasUI?.clearValidation(form);
    if (!payload.cliente_id) {
        markFieldInvalid('[name="cliente_id"]', "Selecione o cliente do agendamento.");
    }
    if (!payload.tipo_servico?.trim()) {
        markFieldInvalid('[name="tipo_servico"]', "Informe o tipo de servico.");
    }
    if (!payload.data_agendamento) {
        markFieldInvalid('[name="data_agendamento"]', "Informe a data do agendamento.");
    }
    if (!payload.hora_agendamento) {
        markFieldInvalid('[name="hora_agendamento"]', "Informe a hora do agendamento.");
    }
    if (!(payload.duracao_prevista_minutos >= 15)) {
        markFieldInvalid('[name="duracao_prevista_minutos"]', "Defina uma duracao minima de 15 minutos.");
    }
    const scheduleInsight = getAppointmentScheduleInsight(form);
    if (scheduleInsight.conflict) {
        window.SysPragasUI?.markInvalid(form.querySelector('[name="tecnico_id"]'), "Existe conflito de agenda para o tecnico selecionado.");
        window.SysPragasUI?.markInvalid(form.querySelector('[name="data_agendamento"]'), "Existe conflito de agenda para a data informada.");
        window.SysPragasUI?.markInvalid(form.querySelector('[name="hora_agendamento"]'), "Existe conflito de agenda para o horario informado.");
        window.SysPragasUI?.markInvalid(form.querySelector('[name="duracao_prevista_minutos"]'), "A duracao informada conflita com outro agendamento.");
        errors.push(
            buildAppointmentConflictMessage(
                scheduleInsight,
                getEntityByKind("technician", payload.tecnico_id)?.nome || "selecionado",
            ),
        );
    }

    if (errors.length) {
        throw new Error([...new Set(errors)].join(" "));
    }
    return payload;
}

async function saveAppointment(form) {
    const payload = validateAppointmentForm(form);
    const appointmentId = state.editing.appointment;
    const result = await apiFetch(
        appointmentId ? `/api/v1/agendamentos/${appointmentId}` : "/api/v1/agendamentos",
        {
            method: appointmentId ? "PUT" : "POST",
            body: JSON.stringify(payload),
        },
    );
    resetFormMode("appointment");
    await afterMutation(buildAppointmentSaveMessage(result, Boolean(appointmentId)), {
        kind: "appointment",
        entity: result,
    });
    openAppointmentView("operational");
    return result;
}

function buildAppointmentSaveMessage(appointment, isEditing = false) {
    const baseMessage = isEditing ? "Agendamento atualizado com sucesso." : "Agendamento salvo com sucesso.";
    if (isEditing || !appointment) {
        return baseMessage;
    }
    if (appointment.whatsapp_status === "enviado") {
        return `${baseMessage} WhatsApp enviado ao cliente.`;
    }
    if (appointment.whatsapp_status === "falha") {
        return `${baseMessage} WhatsApp nao enviado: ${appointment.whatsapp_ultimo_erro || "consulte o log do agendamento."}`;
    }
    return baseMessage;
}

function bindAppointmentWorkspace() {
    const form = document.getElementById("appointment-form");
    if (!form) {
        return;
    }

    form.addEventListener("input", () => {
        form.querySelector(".form-error").classList.add("hidden");
        window.SysPragasUI?.clearValidation(form);
        renderAppointmentCustomerSummary();
    });

    form.querySelector('[name="cliente_id"]').addEventListener("change", () => {
        syncAppointmentWorkOrderOptions();
        renderAppointmentCustomerSummary();
    });
    form.querySelector('[name="os_id"]').addEventListener("change", (event) => {
        applyWorkOrderToAppointmentForm(Number(event.target.value || 0));
        renderAppointmentCustomerSummary();
    });
    form.querySelector('[name="tecnico_id"]').addEventListener("change", renderAppointmentCustomerSummary);
    form.querySelector('[name="sincronizar_google"]').addEventListener("change", renderAppointmentCustomerSummary);
    form.querySelector('[name="enviar_whatsapp"]').addEventListener("change", renderAppointmentCustomerSummary);
    form.querySelector('[name="data_agendamento"]').addEventListener("change", renderAppointmentCustomerSummary);
    form.querySelector('[name="hora_agendamento"]').addEventListener("change", renderAppointmentCustomerSummary);
    form.querySelector('[name="duracao_prevista_minutos"]').addEventListener("change", renderAppointmentCustomerSummary);

    document.getElementById("appointment-open-linked-work-order").addEventListener("click", () => {
        openLinkedWorkOrderFromAppointmentForm();
    });
    document.getElementById("appointment-duplicate-follow-up").addEventListener("click", () => {
        duplicateAppointmentAsFollowUp();
    });
}

function clearAppointmentForm() {
    const form = document.getElementById("appointment-form");
    if (!form) {
        return;
    }
    form.reset();
    form.querySelector(".form-error").classList.add("hidden");
    form.querySelector('[name="status"]').value = "pendente";
    form.querySelector('[name="origem"]').value = "manual";
    form.querySelector('[name="sincronizar_google"]').value = state.settings?.system?.appointment_default_google_sync ? "true" : "false";
    form.querySelector('[name="enviar_whatsapp"]').checked = Boolean(state.settings?.integrations?.whatsapp_auto_send);
    form.querySelector('[name="duracao_prevista_minutos"]').value = "60";
    form.querySelector('[name="data_agendamento"]').value = todayIso();
    syncAppointmentWorkOrderOptions();
    renderAppointmentCustomerSummary();
    renderAppointmentFormHeader();
}

function syncAppointmentWorkOrderOptions() {
    const form = document.getElementById("appointment-form");
    const select = form?.querySelector('[name="os_id"]');
    if (!select) {
        return;
    }
    const currentValue = select.value;
    const customerId = Number(form.querySelector('[name="cliente_id"]')?.value || 0);
    const items = state.workOrders
        .filter((item) => !customerId || item.cliente_id === customerId)
        .sort((a, b) => `${b.data_execucao}${b.hora_inicio}`.localeCompare(`${a.data_execucao}${a.hora_inicio}`));
    select.innerHTML = `
        <option value="">Sem vinculacao</option>
        ${items.map((item) => `
            <option value="${item.id}">
                ${escapeHtml(`OS ${item.numero} | ${item.cliente?.razao_social || "Cliente"} | ${formatDate(item.data_execucao)}`)}
            </option>
        `).join("")}
    `;
    if (currentValue && select.querySelector(`option[value="${currentValue}"]`)) {
        select.value = currentValue;
    }
}

function renderAppointmentCustomerSummary() {
    const form = document.getElementById("appointment-form");
    const target = document.getElementById("appointment-customer-summary");
    if (!form || !target) {
        return;
    }

    const customer = getEntityByKind("customer", Number(form.querySelector('[name="cliente_id"]').value || 0));
    const workOrder = getEntityByKind("workOrder", Number(form.querySelector('[name="os_id"]').value || 0));
    const technician = getEntityByKind("technician", Number(form.querySelector('[name="tecnico_id"]').value || 0));
    const scheduleInsight = getAppointmentScheduleInsight(form);
    const scheduleMessage = scheduleInsight.conflict
        ? buildAppointmentConflictMessage(scheduleInsight, technician?.nome)
        : (scheduleInsight.canEvaluate
            ? `Janela prevista: ${scheduleInsight.startLabel} ate ${scheduleInsight.endLabel}. Nenhum conflito encontrado para este tecnico.`
            : "Defina tecnico, data, horario e duracao para validar a disponibilidade.");

    target.innerHTML = `
        <div class="appointment-customer-card">
            <span class="order-summary-label">Cliente</span>
            <strong>${escapeHtml(customer?.razao_social || "Selecione um cliente")}</strong>
            <span>${escapeHtml(customer?.telefone || "Telefone sera preenchido automaticamente.")}</span>
        </div>
        <div class="appointment-customer-card">
            <span class="order-summary-label">Endereco</span>
            <strong>${escapeHtml(customer ? `${customer.endereco}, ${customer.numero || "s/n"} - ${customer.cidade}/${customer.estado}` : "Sem endereco selecionado")}</strong>
            <span>${escapeHtml(workOrder ? `OS vinculada: ${workOrder.numero}` : "Sem OS vinculada")}</span>
        </div>
        <div class="appointment-customer-card">
            <span class="order-summary-label">Responsavel</span>
            <strong>${escapeHtml(technician?.nome || "Tecnico ainda nao atribuido")}</strong>
            <span>${escapeHtml(form.querySelector('[name="sincronizar_google"]').value === "true" ? "Google Agenda habilitado" : "Google Agenda desabilitado")}</span>
        </div>
        <div class="appointment-customer-card">
            <span class="order-summary-label">WhatsApp</span>
            <strong>${escapeHtml(form.querySelector('[name="enviar_whatsapp"]').checked ? "Envio previsto" : "Nao enviar")}</strong>
            <span>${escapeHtml(form.querySelector('[name="enviar_whatsapp"]').checked ? "O cliente recebera mensagem ao salvar." : "Nenhuma mensagem automatica sera enviada neste salvamento.")}</span>
        </div>
        <div class="appointment-customer-card ${scheduleInsight.conflict ? "is-conflict" : "is-available"}">
            <span class="order-summary-label">Disponibilidade</span>
            <strong>${escapeHtml(scheduleInsight.canEvaluate ? `${scheduleInsight.startLabel} ate ${scheduleInsight.endLabel}` : "Analise pendente")}</strong>
            <span>${escapeHtml(scheduleMessage)}</span>
        </div>
    `;

    document.getElementById("appointment-open-linked-work-order").disabled = !workOrder;
    document.getElementById("appointment-duplicate-follow-up").disabled = !state.editing.appointment;
}

function applyWorkOrderToAppointmentForm(workOrderId) {
    if (!workOrderId) {
        return;
    }
    const form = document.getElementById("appointment-form");
    const workOrder = getEntityByKind("workOrder", workOrderId);
    if (!form || !workOrder) {
        return;
    }
    form.querySelector('[name="cliente_id"]').value = String(workOrder.cliente_id);
    syncAppointmentWorkOrderOptions();
    form.querySelector('[name="os_id"]').value = String(workOrder.id);
    form.querySelector('[name="tecnico_id"]').value = workOrder.tecnico_id ? String(workOrder.tecnico_id) : "";
    form.querySelector('[name="tipo_servico"]').value = form.querySelector('[name="tipo_servico"]').value || "Atendimento vinculado a OS";
    form.querySelector('[name="data_agendamento"]').value = workOrder.data_execucao;
    form.querySelector('[name="hora_agendamento"]').value = formatTime(workOrder.hora_inicio);
    form.querySelector('[name="observacoes"]').value = form.querySelector('[name="observacoes"]').value || workOrder.observacoes || "";
    form.querySelector('[name="origem"]').value = "ordem_servico";
}

function getAppointmentCounts(items) {
    const counts = {
        total: items.length,
        pendente: 0,
        confirmado: 0,
        em_deslocamento: 0,
        em_atendimento: 0,
        concluido: 0,
        reagendado: 0,
        cancelado: 0,
        nao_realizado: 0,
    };
    items.forEach((item) => {
        counts[item.status] = (counts[item.status] || 0) + 1;
    });
    return counts;
}

function getFilteredAppointments() {
    const search = (state.filters.appointmentSearch || "").trim().toLowerCase();
    const status = state.filters.appointmentStatus || "todos";
    const technician = state.filters.appointmentTechnician || "";
    const customer = state.filters.appointmentCustomer || "";
    const selectedDate = state.filters.appointmentDate || "";
    const startDate = state.filters.appointmentStartDate || "";
    const endDate = state.filters.appointmentEndDate || "";

    return state.appointments.filter((item) => {
        const searchMatch = !search || [
            item.id,
            item.cliente_nome,
            item.telefone,
            item.os_numero,
            item.tipo_servico,
            item.data_agendamento,
        ].some((value) => String(value || "").toLowerCase().includes(search));
        const statusMatch = status === "todos" || item.status === status;
        const technicianMatch = !technician || String(item.tecnico_id || "") === technician;
        const customerMatch = !customer || String(item.cliente_id) === customer;
        const dateMatch = !selectedDate || item.data_agendamento === selectedDate;
        const startMatch = !startDate || item.data_agendamento >= startDate;
        const endMatch = !endDate || item.data_agendamento <= endDate;
        return searchMatch && statusMatch && technicianMatch && customerMatch && dateMatch && startMatch && endMatch;
    });
}

function renderDashboard() {
    const filteredOrders = getFilteredWorkOrders();
    const filteredStock = getFilteredProductsForDashboard();
    const filteredFinance = getFilteredFinance();
    const contractDashboard = state.contractDashboard || { a_vencer: 0, vencidos: 0, a_vencer_alertas: [], vencidos_alertas: [] };

    document.getElementById("metrics-grid").innerHTML = [
        metric("Clientes", state.customers.length, "Base operacional ativa"),
        metric("Contratos", state.contracts.length, "Contratos monitorados por cliente"),
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

    const contractAlerts = [
        ...(contractDashboard.vencidos_alertas || []).map((item) => ({ ...item, visualStatus: "danger" })),
        ...(contractDashboard.a_vencer_alertas || []).map((item) => ({ ...item, visualStatus: "warn" })),
    ];
    document.getElementById("contract-alerts").innerHTML = contractAlerts.length
        ? `<div class="alert-list">${contractAlerts
            .slice(0, 8)
            .map(
                (item) => `
            <div class="alert-item">
                <div>
                    <strong>${escapeHtml(item.nome)}</strong>
                    <span class="origin-note">${escapeHtml(item.cliente_nome)} • vence em ${formatDate(item.data_vencimento)}</span>
                </div>
                <span class="badge ${item.visualStatus}">${item.status === "vencido" ? "Vencido" : `A vencer (${item.dias_para_vencimento}d)`}</span>
            </div>
        `,
            )
            .join("")}</div>`
        : `<div class="empty-state">Nenhum contrato em alerta no momento.</div>`;

    renderDashboardWidgets(filteredOrders, filteredStock, filteredFinance);
    renderDashboardCharts(filteredOrders, filteredFinance);
}

function renderAppointments() {
    const dashboardTarget = document.getElementById("appointments-dashboard");
    const calendarTarget = document.getElementById("appointments-calendar");
    const dayListTarget = document.getElementById("appointments-day-list");
    if (!dashboardTarget || !calendarTarget || !dayListTarget) {
        return;
    }

    const filteredAppointments = getFilteredAppointments();
    const counts = getAppointmentCounts(filteredAppointments);
    const pendingAppointments = getAppointmentsForLane(filteredAppointments, "pending");
    const finishedAppointments = getAppointmentsForLane(filteredAppointments, "finished");
    const selectedLane = state.filters.appointmentLane === "finished" ? "finished" : "pending";
    const laneAppointments = selectedLane === "finished" ? finishedAppointments : pendingAppointments;
    const referenceDate = parseLocalDate(state.filters.appointmentDate || todayIso());

    dashboardTarget.innerHTML = `
        <div class="appointments-toolbar">
            <div class="section-heading compact">
                <h3>Agenda operacional</h3>
                <p>Controle compromissos, retornos e o andamento da equipe em um unico painel.</p>
            </div>
            <div class="inline-actions">
                <button type="button" class="btn btn-success" id="appointment-new-button">Novo agendamento</button>
            </div>
        </div>
        ${renderAppointmentIntegrationCards()}
        <div class="appointments-summary-grid">
            <article class="summary-metric-card"><span>Total</span><strong>${counts.total}</strong></article>
            <article class="summary-metric-card is-pending"><span>Pendentes</span><strong>${counts.pendente}</strong></article>
            <article class="summary-metric-card is-confirmed"><span>Confirmados</span><strong>${counts.confirmado}</strong></article>
            <article class="summary-metric-card is-progress"><span>Em rota / atendimento</span><strong>${counts.em_deslocamento + counts.em_atendimento}</strong></article>
            <article class="summary-metric-card is-complete"><span>Concluidos</span><strong>${counts.concluido}</strong></article>
            <article class="summary-metric-card is-alert"><span>Cancelados / nao realizados</span><strong>${counts.cancelado + counts.nao_realizado}</strong></article>
        </div>
        <div class="tab-strip workspace-lane-tabs">
            <button type="button" class="tab-pill ${selectedLane === "pending" ? "is-active" : ""}" data-appointment-lane="pending">Pendentes <span>${pendingAppointments.length}</span></button>
            <button type="button" class="tab-pill ${selectedLane === "finished" ? "is-active" : ""}" data-appointment-lane="finished">Finalizados <span>${finishedAppointments.length}</span></button>
        </div>
        <div class="appointments-filter-grid">
            <label class="orders-search-field">
                <span>Busca geral</span>
                <input id="appointment-search" type="search" placeholder="Cliente, telefone, OS ou data" value="${escapeHtml(state.filters.appointmentSearch || "")}">
            </label>
            <label class="orders-search-field">
                <span>Cliente</span>
                <select id="appointment-customer-filter">
                    <option value="">Todos</option>
                    ${state.customers.map((item) => `<option value="${item.id}" ${String(item.id) === state.filters.appointmentCustomer ? "selected" : ""}>${escapeHtml(item.razao_social)}</option>`).join("")}
                </select>
            </label>
            <label class="orders-search-field">
                <span>Tecnico</span>
                <select id="appointment-technician-filter">
                    <option value="">Todos</option>
                    ${state.technicians.filter((item) => item.ativo).map((item) => `<option value="${item.id}" ${String(item.id) === state.filters.appointmentTechnician ? "selected" : ""}>${escapeHtml(item.nome)}</option>`).join("")}
                </select>
            </label>
            <label class="orders-search-field">
                <span>Status</span>
                <select id="appointment-status-filter">
                    <option value="todos" ${state.filters.appointmentStatus === "todos" ? "selected" : ""}>Todos</option>
                    <option value="pendente" ${state.filters.appointmentStatus === "pendente" ? "selected" : ""}>Pendente</option>
                    <option value="confirmado" ${state.filters.appointmentStatus === "confirmado" ? "selected" : ""}>Confirmado</option>
                    <option value="em_deslocamento" ${state.filters.appointmentStatus === "em_deslocamento" ? "selected" : ""}>Em deslocamento</option>
                    <option value="em_atendimento" ${state.filters.appointmentStatus === "em_atendimento" ? "selected" : ""}>Em atendimento</option>
                    <option value="concluido" ${state.filters.appointmentStatus === "concluido" ? "selected" : ""}>Concluido</option>
                    <option value="reagendado" ${state.filters.appointmentStatus === "reagendado" ? "selected" : ""}>Reagendado</option>
                    <option value="cancelado" ${state.filters.appointmentStatus === "cancelado" ? "selected" : ""}>Cancelado</option>
                    <option value="nao_realizado" ${state.filters.appointmentStatus === "nao_realizado" ? "selected" : ""}>Nao realizado</option>
                </select>
            </label>
            <label class="orders-search-field">
                <span>Referencia do calendario</span>
                <input id="appointment-date-filter" type="date" value="${escapeHtml(state.filters.appointmentDate || "")}">
            </label>
            <label class="orders-search-field">
                <span>Periodo inicial</span>
                <input id="appointment-start-date-filter" type="date" value="${escapeHtml(state.filters.appointmentStartDate || "")}">
            </label>
            <label class="orders-search-field">
                <span>Periodo final</span>
                <input id="appointment-end-date-filter" type="date" value="${escapeHtml(state.filters.appointmentEndDate || "")}">
            </label>
            <div class="orders-filter-actions">
                <button type="button" class="btn btn-default ghost-button" id="appointment-clear-filters">Limpar filtros</button>
            </div>
        </div>
        <div class="tabs appointments-view-tabs" role="tablist" aria-label="Visualizacao da agenda">
            <button type="button" class="tab ${state.appointmentCalendarView === "day" ? "tab-active" : ""}" data-appointment-view="day">Diario</button>
            <button type="button" class="tab ${state.appointmentCalendarView === "week" ? "tab-active" : ""}" data-appointment-view="week">Semanal</button>
            <button type="button" class="tab ${state.appointmentCalendarView === "month" ? "tab-active" : ""}" data-appointment-view="month">Mensal</button>
        </div>
    `;

    calendarTarget.innerHTML = renderAppointmentCalendar(laneAppointments, referenceDate);
    dayListTarget.innerHTML = renderAppointmentDayLists(laneAppointments, referenceDate, selectedLane);

    bindAppointmentFilters();
    bindAppointmentActions();
}

function renderAppointmentCalendar(appointments, referenceDate) {
    if (state.appointmentCalendarView === "day") {
        const dayItems = appointments
            .filter((item) => item.data_agendamento === referenceDate.toISOString().slice(0, 10))
            .sort((a, b) => `${a.data_agendamento}${a.hora_agendamento}`.localeCompare(`${b.data_agendamento}${b.hora_agendamento}`));
        return `
            <section class="appointments-calendar-panel">
                <div class="section-heading compact">
                    <h4>Agenda do dia ${formatDate(referenceDate.toISOString().slice(0, 10))}</h4>
                    <p>${dayItems.length} compromisso(s) no periodo selecionado.</p>
                </div>
                <div class="appointment-day-timeline">
                    ${dayItems.length ? dayItems.map((item) => renderAppointmentCalendarChip(item)).join("") : '<div class="empty-state">Nenhum compromisso para este dia.</div>'}
                </div>
            </section>
        `;
    }

    if (state.appointmentCalendarView === "week") {
        const weekStart = new Date(referenceDate);
        const mondayShift = (weekStart.getDay() + 6) % 7;
        weekStart.setDate(weekStart.getDate() - mondayShift);
        const columns = Array.from({ length: 7 }, (_, index) => {
            const current = new Date(weekStart);
            current.setDate(weekStart.getDate() + index);
            const currentIso = current.toISOString().slice(0, 10);
            const items = appointments.filter((item) => item.data_agendamento === currentIso);
            return `
                <article class="appointment-week-column ${currentIso === todayIso() ? "is-today" : ""}">
                    <header>
                        <strong>${current.toLocaleDateString("pt-BR", { weekday: "short" })}</strong>
                        <span>${formatDate(currentIso)}</span>
                    </header>
                    <div class="appointment-week-items">
                        ${items.length ? items.map((item) => renderAppointmentCalendarChip(item)).join("") : '<span class="empty-inline">Sem compromissos</span>'}
                    </div>
                </article>
            `;
        }).join("");
        return `
            <section class="appointments-calendar-panel">
                <div class="section-heading compact">
                    <h4>Visao semanal</h4>
                    <p>Distribuicao da equipe e dos atendimentos na semana selecionada.</p>
                </div>
                <div class="appointment-week-grid">${columns}</div>
            </section>
        `;
    }

    const year = referenceDate.getFullYear();
    const month = referenceDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const firstCell = new Date(firstDay);
    firstCell.setDate(1 - ((firstDay.getDay() + 6) % 7));
    const monthCells = Array.from({ length: 42 }, (_, index) => {
        const current = new Date(firstCell);
        current.setDate(firstCell.getDate() + index);
        const currentIso = current.toISOString().slice(0, 10);
        const items = appointments.filter((item) => item.data_agendamento === currentIso);
        return `
            <article class="appointment-month-cell ${current.getMonth() !== month ? "is-muted" : ""} ${currentIso === todayIso() ? "is-today" : ""}">
                <header>
                    <strong>${current.getDate()}</strong>
                    <span>${items.length} ag.</span>
                </header>
                <div class="appointment-month-items">
                    ${items.slice(0, 2).map((item) => renderAppointmentCalendarChip(item)).join("")}
                    ${items.length > 2 ? `<span class="empty-inline">+${items.length - 2} item(ns)</span>` : ""}
                </div>
            </article>
        `;
    }).join("");
    return `
        <section class="appointments-calendar-panel">
            <div class="section-heading compact">
                <h4>${referenceDate.toLocaleDateString("pt-BR", { month: "long", year: "numeric" })}</h4>
                <p>Mapa mensal para leitura rapida dos compromissos e alertas operacionais.</p>
            </div>
            <div class="appointment-month-grid">${monthCells}</div>
        </section>
    `;
}

function renderAppointmentCalendarChip(item) {
    return `
        <button type="button" class="appointment-calendar-chip" data-appointment-action="edit" data-id="${item.id}">
            <strong>${formatTime(item.hora_agendamento)}</strong>
            <span>${escapeHtml(item.cliente_nome)}</span>
        </button>
    `;
}

function renderAppointmentDayLists(appointments, referenceDate, lane = "pending") {
    const referenceIso = referenceDate.toISOString().slice(0, 10);
    const visibleAppointments = appointments.filter((item) => {
        if (state.appointmentCalendarView === "day") {
            return item.data_agendamento === referenceIso;
        }
        if (state.appointmentCalendarView === "week") {
            const monday = new Date(referenceDate);
            monday.setDate(referenceDate.getDate() - ((referenceDate.getDay() + 6) % 7));
            const sunday = new Date(monday);
            sunday.setDate(monday.getDate() + 6);
            return item.data_agendamento >= monday.toISOString().slice(0, 10) && item.data_agendamento <= sunday.toISOString().slice(0, 10);
        }
        return item.data_agendamento.slice(0, 7) === referenceIso.slice(0, 7);
    });
    const todayItems = appointments.filter((item) => item.data_agendamento === todayIso());
    const overdueItems = lane === "pending"
        ? appointments.filter((item) =>
            item.data_agendamento < todayIso()
            && ["pendente", "confirmado", "em_deslocamento", "em_atendimento", "reagendado"].includes(item.status))
        : [];
    const firstSectionTitle = lane === "finished" ? "Finalizados do dia" : "Pendentes do dia";
    const firstSectionDescription = lane === "finished"
        ? `${todayItems.length} compromisso(s) finalizados hoje.`
        : `${todayItems.length} compromisso(s) pendentes para hoje.`;
    const thirdSectionTitle = lane === "finished" ? "Historico finalizado" : "Compromissos atrasados";
    const thirdSectionDescription = lane === "finished"
        ? `${visibleAppointments.length} registro(s) finalizados no recorte atual.`
        : `${overdueItems.length} item(ns) exigem atencao operacional.`;

    return `
        <div class="appointments-day-board">
            <section class="appointments-day-section">
                <div class="section-heading compact">
                    <h4>${firstSectionTitle}</h4>
                    <p>${firstSectionDescription}</p>
                </div>
                <div class="appointment-card-list">
                    ${todayItems.length ? todayItems.map((item) => renderAppointmentCard(item)).join("") : '<div class="empty-state">Nenhum atendimento programado para hoje.</div>'}
                </div>
            </section>
            <section class="appointments-day-section">
                <div class="section-heading compact">
                    <h4>Compromissos em foco</h4>
                    <p>${visibleAppointments.length} registro(s) conforme filtros e visualizacao.</p>
                </div>
                <div class="appointment-card-list">
                    ${visibleAppointments.length ? visibleAppointments.map((item) => renderAppointmentCard(item)).join("") : '<div class="empty-state">Nenhum agendamento encontrado para esta visualizacao.</div>'}
                </div>
            </section>
            <section class="appointments-day-section ${lane === "pending" && overdueItems.length ? "is-alert" : ""}">
                <div class="section-heading compact">
                    <h4>${thirdSectionTitle}</h4>
                    <p>${thirdSectionDescription}</p>
                </div>
                <div class="appointment-card-list">
                    ${lane === "finished"
        ? (visibleAppointments.length
            ? visibleAppointments.map((item) => renderAppointmentCard(item, { compact: true })).join("")
            : '<div class="empty-state">Nenhum agendamento finalizado neste periodo.</div>')
        : (overdueItems.length
            ? overdueItems.map((item) => renderAppointmentCard(item, { compact: true })).join("")
            : '<div class="empty-state">Sem compromissos atrasados.</div>')}
                </div>
            </section>
        </div>
    `;
}

function formatIntegrationStatus(status) {
    const normalized = String(status || "").toLowerCase();
    if (normalized === "ativo") {
        return "🟢 Ativo";
    }
    if (normalized === "aguardando_conexao") {
        return "🟡 Aguardando conexao";
    }
    if (normalized === "erro") {
        return "⚠️ Erro";
    }
    return "🔴 Desconectado";
}

function renderAppointmentIntegrationCards() {
    const whatsapp = state.integrations.whatsapp || {};
    const google = state.integrations.google || {};
    const whatsappEnabledInSettings = Boolean(state.settings?.integrations?.whatsapp_enabled);
    const googleConnected = google.status === "ativo";
    const googleCanLogout = googleConnected && Number(google.company_id || 0) > 0;
    const whatsappConnected = whatsapp.status === "ativo";
    const whatsappCanConnect = whatsappEnabledInSettings;
    const googleEmail = google.account_email || "Nenhuma conta conectada";
    const googleCompany = google.company_name ? `Empresa: ${escapeHtml(google.company_name)}` : "Empresa nao identificada";
    const whatsappMeta = whatsapp.instance_name
        ? `Instancia: ${escapeHtml(whatsapp.instance_name)}`
        : `Provedor: ${escapeHtml(whatsapp.provider || "-")}`;

    return `
        <div class="appointments-summary-grid integrations-grid">
            <article class="summary-metric-card">
                <span>WhatsApp</span>
                <strong>${escapeHtml(formatIntegrationStatus(whatsapp.status))}</strong>
                <p>${whatsappMeta}</p>
                <p>${escapeHtml(whatsapp.error_message || "Status operacional da conexao usado pela agenda.")}</p>
                <div class="inline-actions">
                    <button type="button" class="btn btn-success" data-integration-action="whatsapp-connect-qr" ${whatsappCanConnect ? "" : "disabled"}>Conectar WhatsApp</button>
                    <button type="button" class="btn btn-default ghost-button" data-integration-action="whatsapp-logout" ${whatsappConnected ? "" : "disabled"}>Logout</button>
                    <button type="button" class="btn btn-default ghost-button" data-integration-action="refresh-whatsapp">Atualizar status</button>
                </div>
            </article>
            <article class="summary-metric-card">
                <span>Google Agenda</span>
                <strong>${escapeHtml(formatIntegrationStatus(google.status))}</strong>
                <p>${escapeHtml(googleEmail)}</p>
                <p>${googleConnected ? googleCompany : escapeHtml(google.message || "Conecte uma conta Google para sincronizar.")}</p>
                <div class="inline-actions">
                    <button type="button" class="btn btn-success" data-integration-action="google-login">Conectar nova conta</button>
                    <button type="button" class="btn btn-default ghost-button" data-integration-action="google-logout" ${googleCanLogout ? "" : "disabled"}>Logout</button>
                </div>
            </article>
        </div>
    `;
}


async function refreshAppointmentIntegrationStatus() {
    state.integrations.whatsapp = await apiFetch("/api/v1/whatsapp/status");
    state.integrations.google = await apiFetch("/api/v1/google-calendar/status");
    renderAppointments();
    renderSettings();
}


async function connectWhatsAppQr() {
    state.integrations.whatsappQr = await apiFetch("/api/v1/whatsapp/sessao/qr", {
        method: "POST",
    });
    renderSettings();
    renderAppointments();
    switchView("configuracoes");
    try {
        await refreshAppointmentIntegrationStatus();
    } catch (error) {
        console.warn("Falha ao atualizar status do WhatsApp apos solicitar QR.", error);
    }
    toast(state.integrations.whatsappQr.message || "Leia o QR Code do WhatsApp para conectar a sessao.");
}


async function logoutWhatsApp() {
    state.integrations.whatsapp = await apiFetch("/api/v1/whatsapp/sessao/logout", {
        method: "POST",
    });
    state.integrations.whatsappQr = null;
    renderSettings();
    renderAppointments();
    toast(state.integrations.whatsapp.error_message || "Sessao WhatsApp desconectada.");
}


async function loginGoogle() {
    const result = await apiFetch("/api/v1/google-calendar/login", { method: "POST" });
    const popup = window.open(
        result.authorization_url,
        "syspragas-google-calendar-oauth",
        "width=640,height=760,menubar=no,toolbar=no,location=yes,resizable=yes,scrollbars=yes,status=no",
    );
    if (!popup) {
        window.location.href = result.authorization_url;
        return;
    }
    popup.focus();
    toast(result.message || "Abra a autenticacao Google para conectar uma nova conta.");
}


async function logoutGoogle() {
    const result = await apiFetch("/api/v1/google-calendar/logout", { method: "POST" });
    state.integrations.google = result;
    await loadAllData();
    openAppointmentView("operational");
    toast(result.message || "Conta Google desconectada com sucesso.");
}

function renderAppointmentCard(item, options = {}) {
    const compact = options.compact || false;
    const linkedWorkOrder = item.os_id ? getEntityByKind("workOrder", item.os_id) : null;
    const isOverdue = item.data_agendamento < todayIso() && ["pendente", "confirmado", "em_deslocamento", "em_atendimento", "reagendado"].includes(item.status);
    const whatsappIntegration = state.integrations.whatsapp || {};
    const googleEnabled = Boolean(item.sincronizar_google);
    const whatsappLogs = Array.isArray(item.whatsapp_logs) ? item.whatsapp_logs : [];
    const finished = isAppointmentFinished(item.status);
    const hasPhone = Boolean(item.telefone);
    const whatsappIntegrationAvailable = whatsappIntegration.status === "ativo";
    const whatsappEnabled = hasPhone && whatsappIntegrationAvailable;
    const whatsappStatusLabel = item.whatsapp_status ? item.whatsapp_status.replaceAll("_", " ") : "sem envio";
    let whatsappButtonLabel = whatsappLogs.length ? "Reenviar WhatsApp" : "Enviar WhatsApp";
    let whatsappDisabledReason = "";
    if (!hasPhone) {
        whatsappButtonLabel = "WhatsApp indisponivel";
        whatsappDisabledReason = "Cliente sem telefone valido para envio.";
    } else if (!whatsappIntegrationAvailable) {
        whatsappButtonLabel = "WhatsApp indisponivel";
        whatsappDisabledReason = whatsappIntegration.error_message || "Integracao WhatsApp desabilitada ou incompleta.";
    }
    const googleStatusLabel = (item.google_sync_status || "desconectado").replaceAll("_", " ");
    let googleButtonLabel = "Google desativado";
    if (googleEnabled) {
        if (item.google_sync_status === "falha") {
            googleButtonLabel = "Tentar sincronizar no Google";
        } else if (item.google_calendar_event_id) {
            googleButtonLabel = "Sincronizar novamente";
        } else {
            googleButtonLabel = "Sincronizar no Google";
        }
    }
    const googleMessage = item.google_sync_message
        ? `<p class="origin-note">${escapeHtml(item.google_sync_message)}</p>`
        : "";
    const whatsappMessage = item.whatsapp_ultimo_erro
        ? `<p class="origin-note">WhatsApp: ${escapeHtml(item.whatsapp_ultimo_erro)}</p>`
        : (whatsappLogs[0]?.created_at
            ? `<p class="origin-note">WhatsApp ${escapeHtml(whatsappStatusLabel)} em ${escapeHtml(formatDateTime(whatsappLogs[0].created_at))}.</p>`
            : "");
    const whatsappAvailabilityMessage = whatsappDisabledReason
        ? `<p class="origin-note">WhatsApp indisponivel: ${escapeHtml(whatsappDisabledReason)}</p>`
        : "";
    const detailsHtml = linkedWorkOrder
        ? `
            <div class="appointment-linked-assets">
                <span class="order-summary-label">Fotos e itens da OS</span>
                ${renderWorkOrderPhotoCards(linkedWorkOrder.fotos || [], { compact: true })}
            </div>
        `
        : "";

    return `
        <article class="appointment-card ${compact ? "is-compact" : ""} ${isOverdue ? "is-overdue" : ""}">
            <div class="appointment-card-head">
                <div>
                    <p class="order-summary-number">AG ${item.id}${item.os_numero ? ` | OS ${escapeHtml(item.os_numero)}` : ""}</p>
                    <h4>${escapeHtml(item.cliente_nome)}</h4>
                    <p class="order-summary-meta">${escapeHtml(item.tipo_servico)} | ${formatDate(item.data_agendamento)} | ${formatTime(item.hora_agendamento)}</p>
                </div>
                ${renderAppointmentStatusBadge(item.status)}
            </div>
            <div class="appointment-card-grid">
                <div><span class="order-summary-label">Tecnico</span><strong>${escapeHtml(item.tecnico_nome || "Nao definido")}</strong></div>
                <div><span class="order-summary-label">Duracao</span><strong>${escapeHtml(String(item.duracao_prevista_minutos))} min</strong></div>
                <div><span class="order-summary-label">Telefone</span><strong>${escapeHtml(item.telefone || "-")}</strong></div>
                <div><span class="order-summary-label">Google</span><strong>${escapeHtml(googleStatusLabel)}</strong></div>
                <div><span class="order-summary-label">WhatsApp</span><strong>${escapeHtml(whatsappStatusLabel)}</strong></div>
            </div>
            <p class="appointment-card-note">${escapeHtml(item.observacoes || item.observacoes_internas || "Sem observacoes adicionais.")}</p>
            ${googleMessage}
            ${whatsappMessage}
            ${whatsappAvailabilityMessage}
            <div class="appointment-status-actions">
                ${renderAppointmentProgressActions(item)}
            </div>
            <div class="appointment-main-actions">
                <button type="button" class="btn btn-default ghost-button" data-appointment-action="edit" data-id="${item.id}">Editar / reagendar</button>
                <button type="button" class="btn btn-default ghost-button" data-appointment-action="print" data-id="${item.id}">${finished ? "Reimprimir" : "Imprimir resumo"}</button>
                <button type="button" class="btn btn-default ghost-button" data-appointment-action="reopen" data-id="${item.id}" ${finished ? "" : "disabled"}>Reabrir agendamento</button>
                <button type="button" class="btn btn-default ghost-button" data-appointment-action="send-whatsapp" data-id="${item.id}" ${whatsappEnabled ? "" : `disabled title="${escapeHtml(whatsappDisabledReason)}"`}>${whatsappButtonLabel}</button>
                <button type="button" class="btn btn-default ghost-button" data-appointment-action="sync-google" data-id="${item.id}" ${googleEnabled ? "" : "disabled"}>${googleButtonLabel}</button>
                <button type="button" class="btn btn-default ghost-button" data-appointment-action="open-work-order" data-os-id="${item.os_id || ""}" ${item.os_id ? "" : "disabled"}>Abrir OS</button>
            </div>
            <details class="appointment-details">
                <summary>Ver detalhes</summary>
                <div class="appointment-details-content">
                    <dl class="order-details-data">
                        <div><dt>Endereco</dt><dd>${escapeHtml(item.endereco_completo || "-")}</dd></div>
                        <div><dt>Observacoes internas</dt><dd>${escapeHtml(item.observacoes_internas || "-")}</dd></div>
                        <div><dt>Instrucoes tecnicas</dt><dd>${escapeHtml(item.instrucoes_tecnicas || "-")}</dd></div>
                        <div><dt>Retorno / revisita</dt><dd>${escapeHtml(item.retorno_revisita || "-")}</dd></div>
                    </dl>
                    ${detailsHtml}
                    <div class="appointment-history-list">
                        <div class="section-heading compact">
                            <h4>Logs de WhatsApp</h4>
                            <p>Historico de envios automaticos e manuais ao cliente.</p>
                        </div>
                        ${whatsappLogs.length
        ? whatsappLogs.slice().reverse().map((entry) => `
                            <article class="appointment-history-item">
                                <strong>${escapeHtml(entry.usuario_nome || (entry.automatico ? "Sistema" : "Usuario"))}</strong>
                                <span>${formatDateTime(entry.created_at)}</span>
                                <p>${escapeHtml(`WhatsApp ${entry.status} para ${entry.destino_telefone}${entry.erro ? ` | ${entry.erro}` : ""}`)}</p>
                            </article>
                        `).join("")
        : '<div class="empty-state">Nenhum envio de WhatsApp registrado.</div>'}
                    </div>
                    <div class="appointment-history-list">
                        ${(item.historico || []).length
        ? item.historico.slice().reverse().map((entry) => `
                            <article class="appointment-history-item">
                                <strong>${escapeHtml(entry.usuario_nome || "Sistema")}</strong>
                                <span>${formatDateTime(entry.created_at)}</span>
                                <p>${escapeHtml(entry.detalhes || entry.acao)}</p>
                            </article>
                        `).join("")
        : '<div class="empty-state">Sem historico de movimentacao.</div>'}
                    </div>
                </div>
            </details>
        </article>
    `;
}

function renderAppointmentStatusBadge(status) {
    const toneMap = {
        pendente: "warn",
        confirmado: "",
        em_deslocamento: "",
        em_atendimento: "",
        concluido: "",
        reagendado: "warn",
        cancelado: "danger",
        nao_realizado: "danger",
    };
    return badge(status.replaceAll("_", " "), toneMap[status] || "");
}

function renderAppointmentProgressActions(item) {
    const actions = [];
    if (isAppointmentFinished(item.status)) {
        return actions.join("");
    }
    if (item.status === "pendente" || item.status === "reagendado") {
        actions.push(`<button type="button" class="btn btn-success" data-appointment-action="status" data-id="${item.id}" data-status="confirmado">Confirmar</button>`);
    }
    if (item.status === "confirmado") {
        actions.push(`<button type="button" class="btn btn-default ghost-button" data-appointment-action="status" data-id="${item.id}" data-status="em_deslocamento">Em deslocamento</button>`);
    }
    if (item.status === "em_deslocamento") {
        actions.push(`<button type="button" class="btn btn-default ghost-button" data-appointment-action="status" data-id="${item.id}" data-status="em_atendimento">Em atendimento</button>`);
    }
    if (!["concluido", "cancelado", "nao_realizado"].includes(item.status)) {
        actions.push(`<button type="button" class="btn btn-success" data-appointment-action="status" data-id="${item.id}" data-status="concluido">Concluir</button>`);
        actions.push(`<button type="button" class="btn btn-default ghost-button" data-appointment-action="status" data-id="${item.id}" data-status="cancelado">Cancelar</button>`);
    }
    return actions.join("");
}

function bindAppointmentFilters() {
    document.getElementById("appointment-new-button")?.addEventListener("click", () => {
        resetFormMode("appointment");
        openAppointmentView("new");
    });
    document.getElementById("appointment-search")?.addEventListener("input", (event) => {
        state.filters.appointmentSearch = event.target.value;
        renderAppointments();
    });
    document.getElementById("appointment-customer-filter")?.addEventListener("change", (event) => {
        state.filters.appointmentCustomer = event.target.value;
        renderAppointments();
    });
    document.getElementById("appointment-technician-filter")?.addEventListener("change", (event) => {
        state.filters.appointmentTechnician = event.target.value;
        renderAppointments();
    });
    document.getElementById("appointment-status-filter")?.addEventListener("change", (event) => {
        state.filters.appointmentStatus = event.target.value;
        renderAppointments();
    });
    document.getElementById("appointment-date-filter")?.addEventListener("change", (event) => {
        state.filters.appointmentDate = event.target.value;
        renderAppointments();
    });
    document.getElementById("appointment-start-date-filter")?.addEventListener("change", (event) => {
        state.filters.appointmentStartDate = event.target.value;
        renderAppointments();
    });
    document.getElementById("appointment-end-date-filter")?.addEventListener("change", (event) => {
        state.filters.appointmentEndDate = event.target.value;
        renderAppointments();
    });
    document.querySelectorAll("[data-appointment-lane]").forEach((button) => {
        button.addEventListener("click", () => {
            state.filters.appointmentLane = button.dataset.appointmentLane === "finished" ? "finished" : "pending";
            renderAppointments();
        });
    });
    document.getElementById("appointment-clear-filters")?.addEventListener("click", () => {
        state.filters.appointmentSearch = "";
        state.filters.appointmentStatus = "todos";
        state.filters.appointmentTechnician = "";
        state.filters.appointmentCustomer = "";
        state.filters.appointmentDate = "";
        state.filters.appointmentStartDate = "";
        state.filters.appointmentEndDate = "";
        state.filters.appointmentLane = "pending";
        renderAppointments();
    });
    document.querySelectorAll("[data-appointment-view]").forEach((button) => {
        button.addEventListener("click", () => {
            state.appointmentCalendarView = button.dataset.appointmentView;
            renderAppointments();
        });
    });
    document.querySelectorAll("[data-integration-action]").forEach((button) => {
        if (button.dataset.bound === "true") {
            return;
        }
        button.dataset.bound = "true";
        button.addEventListener("click", async () => {
            try {
                if (button.dataset.integrationAction === "refresh-whatsapp") {
                    await refreshAppointmentIntegrationStatus();
                    toast("Status das integracoes atualizado.");
                    return;
                }
                if (button.dataset.integrationAction === "whatsapp-connect-qr") {
                    await connectWhatsAppQr();
                    return;
                }
                if (button.dataset.integrationAction === "whatsapp-logout") {
                    await logoutWhatsApp();
                    return;
                }
                if (button.dataset.integrationAction === "google-login") {
                    await loginGoogle();
                    return;
                }
                if (button.dataset.integrationAction === "google-logout") {
                    await logoutGoogle();
                }
            } catch (error) {
                toast(error.message);
            }
        });
    });
}

function bindAppointmentActions() {
    document.querySelectorAll("[data-appointment-action]").forEach((button) => {
        button.addEventListener("click", async () => {
            const action = button.dataset.appointmentAction;
            const appointmentId = Number(button.dataset.id || 0);
            const osId = Number(button.dataset.osId || 0);
            try {
                if (action === "edit") {
                    startEditing("appointment", appointmentId);
                    return;
                }
                if (action === "open-work-order" && osId) {
                    startEditing("workOrder", osId);
                    return;
                }
                if (action === "sync-google") {
                    await syncAppointmentWithGoogle(appointmentId);
                    return;
                }
                if (action === "print") {
                    printAppointmentSummary(appointmentId);
                    return;
                }
                if (action === "reopen") {
                    const reopened = await apiFetch(`/api/v1/agendamentos/${appointmentId}/reabrir`, {
                        method: "POST",
                    });
                    await afterMutation("Agendamento reaberto com sucesso.", {
                        kind: "appointment",
                        entity: reopened,
                    });
                    openAppointmentView("operational");
                    return;
                }
                if (action === "send-whatsapp") {
                    const result = await apiFetch(`/api/v1/whatsapp/agendamentos/${appointmentId}/enviar`, {
                        method: "POST",
                    });
                    await afterMutation("Mensagem de WhatsApp enviada com sucesso.", {
                        kind: "appointment",
                        entity: result,
                    });
                    openAppointmentView("operational");
                    return;
                }
                if (action === "status") {
                    const targetStatus = button.dataset.status;
                    await apiFetch(`/api/v1/agendamentos/${appointmentId}/status`, {
                        method: "POST",
                        body: JSON.stringify({
                            status: targetStatus,
                            detalhes: `Status ajustado para ${targetStatus.replaceAll("_", " ")} pela agenda.`,
                        }),
                    });
                    await afterMutation("Status do agendamento atualizado.");
                    openAppointmentView("operational");
                }
            } catch (error) {
                toast(error.message);
            }
        });
    });
    document.querySelectorAll(".appointment-details").forEach((node) => {
        node.addEventListener("toggle", () => {
            if (node.open) {
                hydrateWorkOrderPhotoThumbs(node);
                bindWorkOrderPhotoViewer();
            }
        });
    });
}

async function syncAppointmentWithGoogle(appointmentId) {
    const result = await apiFetch(`/api/v1/google-calendar/appointments/${appointmentId}/sync`, { method: "POST" });
    if (result.mode === "oauth_required" && result.authorization_url) {
        const popup = window.open(
            result.authorization_url,
            "syspragas-google-calendar-oauth",
            "width=640,height=760,menubar=no,toolbar=no,location=yes,resizable=yes,scrollbars=yes,status=no",
        );
        if (!popup) {
            window.location.href = result.authorization_url;
            return;
        }
        popup.focus();
        toast(result.message || "Conecte sua conta Google para concluir a sincronizacao.");
        return;
    }
    await afterMutation(result.message || "Agendamento sincronizado com Google Agenda.");
    openAppointmentView("operational");
}

function openLinkedWorkOrderFromAppointmentForm() {
    const osId = Number(document.querySelector('#appointment-form [name="os_id"]')?.value || 0);
    if (!osId) {
        toast("Selecione uma OS vinculada para abrir os detalhes.");
        return;
    }
    startEditing("workOrder", osId);
}

function duplicateAppointmentAsFollowUp() {
    const appointmentId = state.editing.appointment;
    const original = appointmentId ? getEntityByKind("appointment", appointmentId) : null;
    if (!original) {
        toast("Abra um agendamento existente para criar a revisita.");
        return;
    }
    resetFormMode("appointment");
    openAppointmentView("new");
    const form = document.getElementById("appointment-form");
    fillForm(form, {
        cliente_id: String(original.cliente_id),
        os_id: original.os_id ? String(original.os_id) : "",
        tecnico_id: original.tecnico_id ? String(original.tecnico_id) : "",
        tipo_servico: original.tipo_servico,
        data_agendamento: original.data_agendamento,
        hora_agendamento: formatTime(original.hora_agendamento),
        duracao_prevista_minutos: original.duracao_prevista_minutos,
        status: "pendente",
        origem: "manual",
        sincronizar_google: String(original.sincronizar_google),
        observacoes: original.observacoes || "",
        observacoes_internas: original.observacoes_internas || "",
        instrucoes_tecnicas: original.instrucoes_tecnicas || "",
        retorno_revisita: `Revisita vinculada ao agendamento #${original.id}`,
    });
    syncAppointmentWorkOrderOptions();
    renderAppointmentCustomerSummary();
    renderAppointmentFormHeader();
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
        ["Razao social", "Documento", "Cidade", "CEP", "Contato", "Telefone", "E-mail", "Acoes"],
        state.customers.map((item) => [
            item.razao_social,
            item.cpf_cnpj,
            `${item.cidade}/${item.estado}`,
            item.cep ? formatCep(item.cep) : "-",
            item.contato,
            item.telefone,
            item.email || "-",
            actionButtons(
                "customer",
                item.id,
                actionButton("secondary customer-contracts-button", "Contratos", `data-customer-id="${item.id}"`),
            ),
        ]),
        "Nenhum cliente cadastrado.",
        { nonSortableTargets: [7] },
    );
    bindEntityActions("customer");
    bindCustomerContractSelectors();
    renderCustomerContractsWorkspace();
}

function bindCustomerContractSelectors() {
    document.querySelectorAll(".customer-contracts-button").forEach((button) => {
        if (button.dataset.bound === "true") {
            return;
        }
        button.dataset.bound = "true";
        button.addEventListener("click", () => {
            state.contractWorkspace.customerId = Number(button.dataset.customerId);
            state.editing.contract = null;
            resetFormMode("contract");
            renderCustomerContractsWorkspace();
        });
    });
}

function bindStockMovementForm() {
    const form = document.getElementById("stock-movement-form");
    if (!form) {
        return;
    }
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const payload = objectFromForm(form);
        if (!payload.produto_id && !payload.codigo_lido) {
            toast("Selecione um produto ou leia um codigo para movimentar o estoque.");
            return;
        }
        payload.produto_id = Number(payload.produto_id || 0);
        payload.armazem_id = normalizeOptionalNumber(payload.armazem_id);
        payload.local_id = normalizeOptionalNumber(payload.local_id);
        payload.quantidade = String(payload.quantidade || "").trim();
        payload.codigo_lido = payload.codigo_lido || null;
        payload.referencia = payload.referencia || null;
        payload.observacoes = payload.observacoes || null;
        await apiFetch("/api/v1/produtos/estoque/movimentacoes", {
            method: "POST",
            body: JSON.stringify(payload),
        });
        form.reset();
        await afterMutation("Movimentacao de estoque registrada com sucesso.");
    });
}

function bindStockBalanceForm() {
    const form = document.getElementById("stock-balance-form");
    if (!form) {
        return;
    }
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const payload = objectFromForm(form);
        payload.produto_id = Number(payload.produto_id || 0);
        payload.armazem_id = normalizeOptionalNumber(payload.armazem_id);
        payload.local_id = normalizeOptionalNumber(payload.local_id);
        payload.saldo_contado = String(payload.saldo_contado || "").trim();
        payload.codigo_lido = payload.codigo_lido || null;
        payload.referencia = payload.referencia || null;
        payload.observacoes = payload.observacoes || null;
        if (!payload.produto_id && !payload.codigo_lido) {
            toast("Selecione um produto ou leia um codigo para o balanco.");
            return;
        }
        await apiFetch("/api/v1/produtos/estoque/balanco", {
            method: "POST",
            body: JSON.stringify(payload),
        });
        form.reset();
        await afterMutation("Balanco de estoque registrado com sucesso.");
    });
}

function bindStockTransferForm() {
    const form = document.getElementById("stock-transfer-form");
    if (!form) {
        return;
    }
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const payload = objectFromForm(form);
        payload.produto_id = Number(payload.produto_id || 0);
        payload.empresa_destino_id = Number(payload.empresa_destino_id || 0);
        payload.armazem_origem_id = normalizeOptionalNumber(payload.armazem_origem_id);
        payload.local_origem_id = normalizeOptionalNumber(payload.local_origem_id);
        payload.armazem_destino_id = normalizeOptionalNumber(payload.armazem_destino_id);
        payload.local_destino_id = normalizeOptionalNumber(payload.local_destino_id);
        payload.quantidade = String(payload.quantidade || "").trim();
        payload.codigo_lido = payload.codigo_lido || null;
        payload.referencia = payload.referencia || null;
        payload.observacoes = payload.observacoes || null;
        if ((!payload.produto_id && !payload.codigo_lido) || !payload.empresa_destino_id) {
            toast("Selecione o produto ou leia um codigo e informe a empresa destino.");
            return;
        }
        await apiFetch("/api/v1/produtos/estoque/transferencias", {
            method: "POST",
            body: JSON.stringify(payload),
        });
        form.reset();
        await afterMutation("Transferencia de estoque registrada com sucesso.");
    });
}

function setStockWorkspaceView(view) {
    const allowedViews = new Set(["operations", "balance", "transfer"]);
    state.stockScreen = allowedViews.has(view) ? view : "operations";
    document.querySelectorAll("[data-stock-view]").forEach((button) => {
        const mapped = button.dataset.stockView === "estoque-balanco"
            ? "balance"
            : button.dataset.stockView === "estoque-transferencias"
                ? "transfer"
                : "operations";
        const isActive = mapped === state.stockScreen;
        button.classList.toggle("is-active", isActive);
        button.setAttribute("aria-pressed", isActive ? "true" : "false");
    });
    document.querySelectorAll("[data-stock-screen-panel]").forEach((panel) => {
        const isActive = panel.dataset.stockScreenPanel === state.stockScreen;
        panel.classList.toggle("is-active", isActive);
        panel.hidden = !isActive;
    });
    const heading = document.getElementById("stock-view-heading");
    if (heading) {
        const copy = {
            operations: {
                title: "Operacao atual do estoque",
                description: "Visualize saldo atual, importacoes, estrutura e historico operacional.",
            },
            balance: {
                title: "Balanco e inventario",
                description: "Use esta tela apenas para contagem, conferencias e ajustes de inventario.",
            },
            transfer: {
                title: "Transferencias entre unidades",
                description: "Use esta tela apenas para movimentacoes entre matriz, filial, veiculo ou equipe.",
            },
        };
        heading.innerHTML = `<h3>${escapeHtml(copy[state.stockScreen].title)}</h3><p>${escapeHtml(copy[state.stockScreen].description)}</p>`;
    }
}

function resolveStockScreenFromView(view) {
    const rawView = String(view || "");
    if (!rawView.startsWith("estoque-")) {
        return rawView === "estoque" ? state.stockScreen || "operations" : null;
    }
    const mapped = rawView.replace("estoque-", "");
    if (mapped === "balanco") {
        return "balance";
    }
    if (mapped === "transferencias") {
        return "transfer";
    }
    return "operations";
}

function openStockView(screen = "operations") {
    const mapped = {
        operations: "estoque",
        balance: "estoque-balanco",
        transfer: "estoque-transferencias",
    };
    switchView(mapped[screen] || "estoque");
}

function normalizeOptionalNumber(value) {
    const raw = String(value || "").trim();
    return raw ? Number(raw) : null;
}

async function resolveStockCodeIntoForm(form, code) {
    const sanitizedCode = String(code || "").trim();
    if (!sanitizedCode) {
        return;
    }
    const data = await apiFetch(`/api/v1/produtos/estoque/buscar-por-codigo/${encodeURIComponent(sanitizedCode)}`);
    state.stockWorkflow.lastLookup = data;
    const productField = form.querySelector('[name="produto_id"]');
    if (productField) {
        productField.value = String(data.produto_id);
    }
    const warehouseField = form.querySelector('[name="armazem_id"], [name="armazem_origem_id"]');
    if (warehouseField && !warehouseField.value) {
        warehouseField.value = String(data.armazem_id || "");
    }
    const locationField = form.querySelector('[name="local_id"], [name="local_origem_id"]');
    if (locationField && !locationField.value) {
        locationField.value = String(data.local_id || "");
    }
    const quantityField = form.querySelector('[name="quantidade"], [name="saldo_contado"]');
    quantityField?.focus();
    toast(`Produto identificado: ${data.produto_nome}.`);
}

function bindStockCodeHelpers() {
    document.querySelectorAll("[data-stock-scan]").forEach((button) => {
        if (button.dataset.bound === "true") {
            return;
        }
        button.dataset.bound = "true";
        button.addEventListener("click", async () => {
            const target = button.dataset.stockScan;
            const formMap = {
                movement: "stock-movement-form",
                balance: "stock-balance-form",
                transfer: "stock-transfer-form",
            };
            const form = document.getElementById(formMap[target]);
            const input = form?.querySelector('[name="codigo_lido"]');
            if (!form || !input) {
                return;
            }
            state.stockWorkflow.scannerTarget = target;
            const scannedValue = window.prompt("Leia ou informe o QR Code / codigo de barras do produto:", input.value || "");
            if (!scannedValue) {
                return;
            }
            input.value = scannedValue;
            await resolveStockCodeIntoForm(form, scannedValue);
        });
    });

    document.querySelectorAll('#stock-movement-form [name="codigo_lido"], #stock-balance-form [name="codigo_lido"], #stock-transfer-form [name="codigo_lido"]').forEach((input) => {
        if (input.dataset.bound === "true") {
            return;
        }
        input.dataset.bound = "true";
        input.addEventListener("change", async (event) => {
            const form = event.target.closest("form");
            await resolveStockCodeIntoForm(form, event.target.value);
        });
    });
}

function bindStockStructureForms() {
    const warehouseForm = document.getElementById("stock-warehouse-form");
    if (warehouseForm && warehouseForm.dataset.bound !== "true") {
        warehouseForm.dataset.bound = "true";
        warehouseForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const payload = objectFromForm(warehouseForm);
            payload.ativo = payload.ativo === "true";
            payload.padrao = payload.padrao === "true";
            await apiFetch("/api/v1/produtos/estoque/armazens", {
                method: "POST",
                body: JSON.stringify(payload),
            });
            warehouseForm.reset();
            await afterMutation("Armazem salvo com sucesso.");
        });
    }

    const locationForm = document.getElementById("stock-location-form");
    if (locationForm && locationForm.dataset.bound !== "true") {
        locationForm.dataset.bound = "true";
        locationForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const payload = objectFromForm(locationForm);
            payload.armazem_id = Number(payload.armazem_id || 0);
            payload.ativo = payload.ativo === "true";
            payload.padrao = payload.padrao === "true";
            if (!payload.armazem_id) {
                toast("Selecione um armazem para cadastrar o local.");
                return;
            }
            await apiFetch("/api/v1/produtos/estoque/locais", {
                method: "POST",
                body: JSON.stringify(payload),
            });
            locationForm.reset();
            await afterMutation("Local fisico salvo com sucesso.");
        });
    }

    const labelsButton = document.getElementById("stock-generate-labels-button");
    if (labelsButton && labelsButton.dataset.bound !== "true") {
        labelsButton.dataset.bound = "true";
        labelsButton.addEventListener("click", async () => {
            const selectedIds = getFilteredStockPositions().map((item) => item.produto_id);
            if (!selectedIds.length) {
                toast("Nao ha produtos no filtro atual para gerar etiquetas.");
                return;
            }
            const response = await fetch("/api/v1/produtos/estoque/etiquetas/pdf", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${state.token}`,
                },
                body: JSON.stringify({ produto_ids: selectedIds }),
            });
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText || "Falha ao gerar etiquetas.");
            }
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            window.open(url, "_blank", "noopener");
            setTimeout(() => URL.revokeObjectURL(url), 10_000);
        });
    }
}

function bindStockInventoryForms(activeInventory) {
    const inventoryForm = document.getElementById("stock-inventory-form");
    if (inventoryForm && inventoryForm.dataset.bound !== "true") {
        inventoryForm.dataset.bound = "true";
        inventoryForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const payload = objectFromForm(inventoryForm);
            payload.armazem_id = Number(payload.armazem_id || 0);
            payload.local_id = Number(payload.local_id || 0);
            if (!payload.armazem_id || !payload.local_id) {
                toast("Selecione armazem e local para abrir o inventario.");
                return;
            }
            await apiFetch("/api/v1/produtos/estoque/inventarios", {
                method: "POST",
                body: JSON.stringify(payload),
            });
            await afterMutation("Inventario aberto com sucesso.");
        });
    }

    const countForm = document.getElementById("stock-inventory-count-form");
    if (countForm && activeInventory && countForm.dataset.bound !== "true") {
        countForm.dataset.bound = "true";
        countForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const payload = objectFromForm(countForm);
            payload.quantidade = String(payload.quantidade || "").trim();
            payload.codigo = payload.codigo || null;
            if (!payload.codigo) {
                toast("Leia ou informe um codigo para registrar a contagem.");
                return;
            }
            await apiFetch(`/api/v1/produtos/estoque/inventarios/${activeInventory.id}/contagens`, {
                method: "POST",
                body: JSON.stringify(payload),
            });
            await afterMutation("Leitura do inventario registrada com sucesso.");
        });
    }

    const finalizeButton = document.getElementById("stock-inventory-finalize-button");
    if (finalizeButton && activeInventory && finalizeButton.dataset.bound !== "true") {
        finalizeButton.dataset.bound = "true";
        finalizeButton.addEventListener("click", async () => {
            await apiFetch(`/api/v1/produtos/estoque/inventarios/${activeInventory.id}/finalizar`, {
                method: "POST",
                body: JSON.stringify({
                    aplicar_ajustes: true,
                    motivo_ajuste: `Ajuste do inventario ${activeInventory.id}`,
                }),
            });
            await afterMutation("Inventario finalizado com ajuste aplicado.");
        });
    }

    const inventoryScanButton = document.querySelector('[data-stock-scan="inventory"]');
    if (inventoryScanButton && inventoryScanButton.dataset.bound !== "true") {
        inventoryScanButton.dataset.bound = "true";
        inventoryScanButton.addEventListener("click", () => {
            const input = document.querySelector('#stock-inventory-count-form [name="codigo"]');
            const scannedValue = window.prompt("Leia ou informe o QR Code / codigo de barras do produto:", input?.value || "");
            if (!scannedValue || !input) {
                return;
            }
            input.value = scannedValue;
            input.dispatchEvent(new Event("change", { bubbles: true }));
        });
    }
}

function currentContractCustomer() {
    return getEntityByKind("customer", Number(state.contractWorkspace.customerId || 0));
}

function currentCustomerContracts() {
    const customerId = Number(state.contractWorkspace.customerId || 0);
    return state.contracts.filter((item) => item.cliente_id === customerId);
}

function contractStatusBadge(status) {
    if (status === "vencido") {
        return badge("Vencido", "danger");
    }
    if (status === "a_vencer") {
        return badge("A vencer", "warn");
    }
    return badge("Ativo", "");
}

function renderCustomerContractsWorkspace() {
    const summary = document.getElementById("customer-contracts-summary");
    const table = document.getElementById("customer-contracts-table");
    const form = document.getElementById("contract-form");
    const headingCopy = document.getElementById("customer-contracts-heading-copy");
    if (!summary || !table || !form || !headingCopy) {
        return;
    }

    const customer = currentContractCustomer();
    if (!customer) {
        summary.innerHTML = `<div class="empty-state">Selecione um cliente na tabela para liberar a gestao de contratos.</div>`;
        table.innerHTML = `<div class="empty-state">Nenhum cliente selecionado.</div>`;
        fillForm(form, { cliente_nome: "" });
        headingCopy.textContent = "Selecione um cliente na tabela para cadastrar, consultar e acompanhar contratos vinculados.";
        return;
    }

    const items = currentCustomerContracts();
    const overdueCount = items.filter((item) => item.status === "vencido").length;
    const dueSoonCount = items.filter((item) => item.status === "a_vencer").length;
    const activeCount = items.filter((item) => item.status === "ativo").length;
    const autoBillingCount = items.filter((item) => item.gerar_cobranca_automatica).length;
    headingCopy.textContent = `Cliente selecionado: ${customer.razao_social}. Cadastre novos contratos ou acompanhe os existentes abaixo.`;
    fillForm(form, { cliente_nome: customer.razao_social });

    summary.innerHTML = `
        <div class="contract-summary-grid">
            <article class="contract-summary-card">
                <span>Total</span>
                <strong>${items.length}</strong>
                <p class="origin-note">${escapeHtml(customer.email || "Cliente sem e-mail cadastrado")}</p>
            </article>
            <article class="contract-summary-card">
                <span>Ativos</span>
                <strong>${activeCount}</strong>
                <p class="origin-note">Contratos vigentes fora da janela de alerta.</p>
            </article>
            <article class="contract-summary-card is-warn">
                <span>A vencer</span>
                <strong>${dueSoonCount}</strong>
                <p class="origin-note">Dentro da janela configurada para notificacao.</p>
            </article>
            <article class="contract-summary-card is-danger">
                <span>Vencidos</span>
                <strong>${overdueCount}</strong>
                <p class="origin-note">Exigem renovacao ou regularizacao.</p>
            </article>
            <article class="contract-summary-card">
                <span>Cobranca automatica</span>
                <strong>${autoBillingCount}</strong>
                <p class="origin-note">Contratos com integracao recorrente no financeiro.</p>
            </article>
        </div>
    `;

    setTableContent(
        "customer-contracts-table",
        ["Contrato", "Inicio", "Vencimento", "Cobranca", "Status", "Financeiro", "Arquivo", "Acoes"],
        items.map((item) => [
            `<div>${escapeHtml(item.nome)}<div class="origin-note">${escapeHtml(item.observacoes || "")}</div></div>`,
            formatDate(item.data_inicio),
            formatDate(item.data_vencimento),
            `<div>${escapeHtml(item.tipo_cobranca.replaceAll("_", " "))}<div class="origin-note">${item.gerar_cobranca_automatica ? `${formatCurrency(item.valor_mensal || 0)} | dia ${item.dia_vencimento || "-"}` : "Sem cobranca automatica"}</div></div>`,
            `<div>${contractStatusBadge(item.status)}<div class="origin-note">${item.quantidade_cobrancas || 0} cobranca(s) | ${item.quantidade_cobrancas_vencidas || 0} vencida(s)</div></div>`,
            contractStatusBadge(item.status),
            item.arquivo_nome_original ? escapeHtml(item.arquivo_nome_original) : "-",
            actionButtons(
                "contract",
                item.id,
                [
                    actionButton("secondary view-contract-file", "Visualizar", `data-id="${item.id}" ${item.arquivo_disponivel ? "" : "disabled"}`),
                    actionButton("secondary download-contract-file", "Baixar", `data-id="${item.id}" ${item.arquivo_disponivel ? "" : "disabled"}`),
                ].join(""),
            ),
        ]),
        "Nenhum contrato cadastrado para este cliente.",
        { nonSortableTargets: [7] },
    );
    bindEntityActions("contract");
    bindContractFileActions();
}

function bindContractFileActions() {
    document.querySelectorAll(".view-contract-file").forEach((button) => {
        if (button.dataset.bound === "true") {
            return;
        }
        button.dataset.bound = "true";
        button.addEventListener("click", async () => {
            try {
                const blob = await apiFetch(`/api/v1/contratos/${button.dataset.id}/arquivo`);
                const contract = getEntityByKind("contract", Number(button.dataset.id));
                openBlobPreview(blob, contract?.arquivo_nome_original || `contrato-${button.dataset.id}`);
            } catch (error) {
                toast(error.message);
            }
        });
    });

    document.querySelectorAll(".download-contract-file").forEach((button) => {
        if (button.dataset.bound === "true") {
            return;
        }
        button.dataset.bound = "true";
        button.addEventListener("click", async () => {
            try {
                const blob = await apiFetch(`/api/v1/contratos/${button.dataset.id}/arquivo?download=true`);
                const contract = getEntityByKind("contract", Number(button.dataset.id));
                downloadBlob(blob, contract?.arquivo_nome_original || `contrato-${button.dataset.id}`);
            } catch (error) {
                toast(error.message);
            }
        });
    });
}

function renderProducts() {
    setTableContent(
        "products-table",
        ["Produto", "Categoria", "Unidade", "Registro", "Base fiscal", "Saldo inicial", "Minimo", "Acoes"],
        state.products.map((item) => [
            `<div>${escapeHtml(item.nome)}<div class="origin-note">${escapeHtml(item.principio_ativo || "-")}</div></div>`,
            escapeHtml(item.categoria || "-"),
            escapeHtml(item.unidade_medida || "UN"),
            escapeHtml(item.registro_ms || "-"),
            item.ncm ? `<div>${escapeHtml(item.ncm)}<div class="origin-note">${escapeHtml(item.ncm_descricao || "")}</div></div>` : "-",
            `${escapeHtml(String(item.estoque_atual))} ${escapeHtml(item.unidade_medida || "UN")}`,
            `${escapeHtml(String(item.estoque_minimo))} ${escapeHtml(item.unidade_medida || "UN")}`,
            actionButtons("product", item.id),
        ]),
        "Nenhum produto cadastrado.",
        { nonSortableTargets: [7] },
    );
    bindEntityActions("product");
}

function getFilteredStockPositions() {
    const search = String(state.filters.stockSearch || "").trim().toLowerCase();
    const companyFilter = String(state.filters.stockCompany || "");
    const categoryFilter = String(state.filters.stockCategory || "").trim().toLowerCase();
    const statusFilter = String(state.filters.stockStatus || "todos");
    return state.stockPositions.filter((item) => {
        if (companyFilter && String(item.empresa_prestadora_id) !== companyFilter) {
            return false;
        }
        if (categoryFilter && String(item.categoria || "").trim().toLowerCase() !== categoryFilter) {
            return false;
        }
        if (search) {
            const haystack = [
                item.produto_nome,
                item.empresa_prestadora_nome,
                item.categoria,
                item.registro_ms,
                item.codigo_barras,
                item.qr_code_value,
                item.armazem_nome,
                item.local_nome,
            ].join(" ").toLowerCase();
            if (!haystack.includes(search)) {
                return false;
            }
        }
        const currentStock = Number(item.estoque_atual || 0);
        if (statusFilter === "baixo" && !item.estoque_baixo) {
            return false;
        }
        if (statusFilter === "normal" && (item.estoque_baixo || currentStock === 0)) {
            return false;
        }
        if (statusFilter === "zerado" && currentStock !== 0) {
            return false;
        }
        return true;
    });
}

function stockStatusBadge(item) {
    const currentStock = Number(item.estoque_atual || 0);
    if (currentStock === 0) {
        return badge("Zerado", "danger");
    }
    if (item.estoque_baixo) {
        return badge("Baixo", "warn");
    }
    return badge("Normal", "success");
}

function renderStockModule() {
    const ownProductIds = new Set(state.products.map((item) => item.id));
    setTableContent(
        "stock-positions-table",
        ["Produto", "Empresa", "Armazem / local", "Categoria", "Saldo", "Minimo", "Status", "Acoes"],
        getFilteredStockPositions().map((item) => {
            const actions = ownProductIds.has(item.produto_id)
                ? `
                    <div class="inline-actions compact-actions">
                        <button type="button" class="btn btn-xs btn-primary" data-stock-action="entrada" data-product-id="${item.produto_id}">Entrada</button>
                        <button type="button" class="btn btn-xs btn-secondary" data-stock-action="saida" data-product-id="${item.produto_id}">Saida</button>
                        <button type="button" class="btn btn-xs btn-default ghost-button" data-stock-action="balanco" data-product-id="${item.produto_id}">Balanco</button>
                    </div>
                `
                : '<span class="origin-note">Visualizacao compartilhada</span>';
            return [
                `<div>${escapeHtml(item.produto_nome)}<div class="origin-note">Registro ${escapeHtml(item.registro_ms || "-")} | ${escapeHtml(item.unidade_medida || "UN")} | ${escapeHtml(item.codigo_barras || item.qr_code_value || "-")}</div></div>`,
                escapeHtml(item.empresa_prestadora_nome || "-"),
                `${escapeHtml(item.armazem_nome || "Armazem padrao")}<div class="origin-note">${escapeHtml(item.local_nome || "Local padrao")}</div>`,
                escapeHtml(item.categoria || "-"),
                `${escapeHtml(String(item.estoque_atual))} ${escapeHtml(item.unidade_medida || "UN")}`,
                `${escapeHtml(String(item.estoque_minimo))} ${escapeHtml(item.unidade_medida || "UN")}`,
                stockStatusBadge(item),
                actions,
            ];
        }),
        "Nenhuma posicao de estoque encontrada para os filtros aplicados.",
        { nonSortableTargets: [7], pageLength: 8 },
    );
    renderStockMovementHistory();
    renderStockImportHistory();
    renderStockStructureSummary();
    renderStockInventoryPanel();
    bindStockActionButtons();
}

function bindStockActionButtons() {
    document.querySelectorAll("[data-stock-action]").forEach((button) => {
        if (button.dataset.bound === "true") {
            return;
        }
        button.dataset.bound = "true";
        button.addEventListener("click", () => {
            openStockAction(button.dataset.stockAction, Number(button.dataset.productId || 0));
        });
    });
}

function openStockAction(action, productId = 0) {
    if (action === "balanco") {
        switchView("estoque-balanco");
    } else {
        switchView("estoque");
    }
    const product = state.products.find((item) => item.id === productId) || state.stockPositions.find((item) => item.produto_id === productId) || null;
    if (action === "entrada" || action === "saida") {
        const form = document.getElementById("stock-movement-form");
        if (form) {
            form.querySelector('[name="produto_id"]').value = productId ? String(productId) : "";
            form.querySelector('[name="tipo_movimento"]').value = action === "saida" ? "saida" : "entrada";
            form.querySelector('[name="unidade_medida"]').value = product?.unidade_medida || "UN";
            const warehouseField = form.querySelector('[name="armazem_id"]');
            const locationField = form.querySelector('[name="local_id"]');
            if (warehouseField) {
                warehouseField.value = product?.armazem_id ? String(product.armazem_id) : "";
            }
            if (locationField) {
                locationField.value = product?.local_id ? String(product.local_id) : "";
            }
            form.querySelector('[name="quantidade"]').focus();
        }
        document.getElementById("stock-section-movement")?.scrollIntoView({ behavior: "smooth", block: "start" });
        return;
    }
    if (action === "balanco") {
        const form = document.getElementById("stock-balance-form");
        if (form) {
            form.querySelector('[name="produto_id"]').value = productId ? String(productId) : "";
            form.querySelector('[name="unidade_medida"]').value = product?.unidade_medida || "UN";
            const warehouseField = form.querySelector('[name="armazem_id"]');
            const locationField = form.querySelector('[name="local_id"]');
            if (warehouseField) {
                warehouseField.value = product?.armazem_id ? String(product.armazem_id) : "";
            }
            if (locationField) {
                locationField.value = product?.local_id ? String(product.local_id) : "";
            }
            form.querySelector('[name="saldo_contado"]').focus();
        }
        document.getElementById("stock-section-balance")?.scrollIntoView({ behavior: "smooth", block: "start" });
        return;
    }
}

function bindStockViewButtons() {
    document.querySelectorAll("[data-stock-view]").forEach((button) => {
        if (button.dataset.bound === "true") {
            return;
        }
        button.dataset.bound = "true";
        button.addEventListener("click", () => {
            switchView(button.dataset.stockView || "estoque");
        });
    });
}

function renderStockMovementHistory() {
    const target = document.getElementById("stock-movement-history");
    if (!target) {
        return;
    }
    const filteredMovements = state.stockScreen === "balance"
        ? state.stockMovements.filter((item) => item.origem === "inventario_balanco" || item.origem === "inventario_leitura")
        : state.stockScreen === "transfer"
            ? state.stockMovements.filter((item) => item.origem === "transferencia")
            : state.stockMovements;
    const recentItems = filteredMovements.slice(0, 12);
    if (!recentItems.length) {
        const emptyCopy = state.stockScreen === "balance"
            ? "Nenhum balanco ou inventario registrado ainda."
            : state.stockScreen === "transfer"
                ? "Nenhuma transferencia registrada ainda."
                : "Nenhuma movimentacao de estoque registrada ainda.";
        target.innerHTML = `<div class="empty-state">${emptyCopy}</div>`;
        return;
    }
    const title = state.stockScreen === "balance"
        ? "Historico de balancos e inventarios"
        : state.stockScreen === "transfer"
            ? "Historico de transferencias"
            : "Historico recente de estoque";
    const description = state.stockScreen === "balance"
        ? "Conferencias, leituras e ajustes aplicados no inventario."
        : state.stockScreen === "transfer"
            ? "Saidas e entradas entre matriz, filial, veiculo ou equipe."
            : "Entradas, saidas, ajustes, balancos e transferencias por empresa/unidade.";
    target.innerHTML = `
        <div class="section-heading compact">
            <h4>${escapeHtml(title)}</h4>
            <p>${escapeHtml(description)}</p>
        </div>
        <div class="stack-list">
            ${recentItems
                .map((item) => {
                    const relatedCompany = item.empresa_relacionada_nome ? ` | relacao: ${escapeHtml(item.empresa_relacionada_nome)}` : "";
                    const reference = item.referencia ? ` | ref. ${escapeHtml(item.referencia)}` : "";
                    const structure = item.armazem_nome || item.local_nome
                        ? ` | ${escapeHtml(item.armazem_nome || "Armazem padrao")} > ${escapeHtml(item.local_nome || "Local padrao")}`
                        : "";
                    const scannedCode = item.codigo_lido ? ` | leitura ${escapeHtml(item.codigo_lido)}` : "";
                    const notes = item.observacoes ? `<div class="origin-note">${escapeHtml(item.observacoes)}</div>` : "";
                    return `
                    <article class="list-card">
                        <strong>${escapeHtml(item.produto_nome)}</strong>
                        <div class="origin-note">${escapeHtml(item.empresa_prestadora_nome || "-")} | ${escapeHtml(item.tipo_movimento)} ${escapeHtml(String(item.quantidade))} ${escapeHtml(item.unidade_medida || "UN")}${relatedCompany}${reference}</div>
                        <div>${escapeHtml(item.motivo)}</div>
                        <div class="origin-note">Origem ${escapeHtml(item.origem)}${structure}${scannedCode} | saldo ${escapeHtml(String(item.saldo_anterior))} -> ${escapeHtml(String(item.saldo_posterior))} | ${escapeHtml(formatDateTime(item.created_at))}</div>
                        ${notes}
                    </article>`;
                })
                .join("")}
        </div>
    `;
}

function renderStockImportHistory() {
    const target = document.getElementById("stock-import-history");
    if (!target) {
        return;
    }
    if (state.stockScreen !== "operations") {
        target.innerHTML = "";
        target.hidden = true;
        return;
    }
    target.hidden = false;
    const recentItems = state.stockImportLogs.slice(0, 8);
    if (!recentItems.length) {
        target.innerHTML = `<div class="empty-state">Nenhuma importacao registrada ainda.</div>`;
        return;
    }
    target.innerHTML = `
        <div class="section-heading compact">
            <h4>Historico de importacoes</h4>
            <p>Rastreabilidade completa para XML, CSV e planilhas com log por empresa.</p>
        </div>
        <div class="stack-list">
            ${recentItems
                .map((item) => {
                    const errors = Array.isArray(item.errors) && item.errors.length
                        ? `<div class="origin-note">Pendencias: ${escapeHtml(item.errors.join(" | "))}</div>`
                        : "";
                    const fileInfo = item.nome_arquivo ? `Arquivo ${escapeHtml(item.nome_arquivo)} | ` : "";
                    return `
                        <article class="list-card">
                            <strong>${escapeHtml(String(item.tipo_arquivo).toUpperCase())} | ${escapeHtml(item.referencia)}</strong>
                            <div class="origin-note">${escapeHtml(item.empresa_prestadora_nome || "-")} | ${fileInfo}${escapeHtml(formatDateTime(item.created_at))}</div>
                            <div>${escapeHtml(String(item.produtos_processados))} item(ns), ${escapeHtml(String(item.produtos_criados))} criado(s), ${escapeHtml(String(item.produtos_atualizados))} atualizado(s), total ${escapeHtml(String(item.total_movimentado))}.</div>
                            ${errors}
                        </article>`;
                })
                .join("")}
        </div>
    `;
}

function renderStockStructureSummary() {
    const target = document.getElementById("stock-structure-panel");
    if (!target) {
        return;
    }
    target.hidden = state.stockScreen !== "operations";
    if (state.stockScreen !== "operations") {
        target.innerHTML = "";
        return;
    }
    target.innerHTML = `
        <div class="section-heading compact">
            <h4>Estrutura operacional do estoque</h4>
            <p>${escapeHtml(String(state.stockWarehouses.length))} armazem(ns), ${escapeHtml(String(state.stockLocations.length))} local(is) e etiquetas PDF prontas para impressao.</p>
        </div>
        <div class="stack-list">
            ${state.stockWarehouses.slice(0, 6).map((item) => `
                <article class="list-card">
                    <strong>${escapeHtml(item.nome)}</strong>
                    <div class="origin-note">${escapeHtml(item.codigo)} | ${escapeHtml(item.empresa_prestadora_nome || "-")} | ${escapeHtml(item.tipo || "armazem")}</div>
                </article>
            `).join("") || '<div class="empty-state">Nenhum armazem cadastrado ainda.</div>'}
        </div>
    `;
}

function renderStockInventoryPanel() {
    const target = document.getElementById("stock-inventory-panel");
    if (!target) {
        return;
    }
    const activeInventory = state.stockInventories.find((item) => item.status === "aberto") || null;
    target.innerHTML = `
        <div class="section-heading compact">
            <h4>Inventarios por leitura</h4>
            <p>Abra um inventario no armazem/local, some leituras automaticamente e finalize com ou sem ajuste.</p>
        </div>
        <form id="stock-inventory-form" class="form-grid data-form">
            <label><span>Armazem</span><select name="armazem_id" required><option value="">Selecione</option>${state.stockWarehouses.map((item) => `<option value="${item.id}">${escapeHtml(item.nome)}</option>`).join("")}</select></label>
            <label><span>Local fisico</span><select name="local_id" required><option value="">Selecione</option>${state.stockLocations.map((item) => `<option value="${item.id}">${escapeHtml(item.nome)} | ${escapeHtml(item.armazem_nome || "-")}</option>`).join("")}</select></label>
            <label class="full-width"><span>Observacoes</span><input name="observacoes" placeholder="Contexto do inventario"></label>
            <div class="inline-actions ui-form-actions"><button type="submit" class="btn btn-default">Abrir inventario</button></div>
        </form>
        ${activeInventory ? `
            <form id="stock-inventory-count-form" class="form-grid data-form">
                <label class="full-width"><span>Leitura continua</span><div class="scanner-inline"><input name="codigo" placeholder="Leia QR Code, codigo de barras ou codigo interno"><button type="button" class="btn btn-default ghost-button" data-stock-scan="inventory">Ler codigo</button></div></label>
                <label><span>Quantidade lida</span><input name="quantidade" type="number" min="0.01" step="0.01" value="1" required></label>
                <label><span>Unidade</span><select name="unidade_medida"><option value="UN">UN</option><option value="ML">ML</option><option value="L">L</option><option value="G">G</option><option value="KG">KG</option></select></label>
                <div class="inline-actions ui-form-actions"><button type="submit" class="btn btn-primary">Registrar leitura</button><button type="button" class="btn btn-secondary" id="stock-inventory-finalize-button">Finalizar com ajuste</button></div>
            </form>
            <div class="stack-list">
                ${activeInventory.itens.map((item) => `
                    <article class="list-card">
                        <strong>${escapeHtml(item.produto_nome)}</strong>
                        <div class="origin-note">Sistema ${escapeHtml(String(item.quantidade_sistema))} | Contado ${escapeHtml(String(item.quantidade_contada))} | Divergencia ${escapeHtml(String(item.divergencia))}</div>
                    </article>
                `).join("") || '<div class="empty-state">Nenhuma leitura registrada neste inventario.</div>'}
            </div>
        ` : '<div class="empty-state">Nenhum inventario aberto. Abra um inventario para usar leitura continua.</div>'}
    `;
    bindStockInventoryForms(activeInventory);
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
    const target = document.getElementById("work-orders-table");
    if (!target) {
        return;
    }

    const filteredOrders = getFilteredWorkOrdersForWorkspace();
    const activeOrders = getWorkOrdersForLane(filteredOrders, "pending");
    const archivedOrders = getWorkOrdersForLane(filteredOrders, "finished");
    const selectedLane = state.filters.workOrderLane === "finished" ? "finished" : "pending";
    const laneOrders = selectedLane === "finished" ? archivedOrders : activeOrders;
    const laneTitle = selectedLane === "finished" ? "Ordens finalizadas" : "Ordens pendentes";
    const laneDescription = selectedLane === "finished"
        ? "Historico operacional com acesso rapido para reimpressao e reabertura."
        : "Ordens em acompanhamento com foco nas proximas execucoes e ajustes operacionais.";

    target.innerHTML = `
        <div class="orders-workspace">
            <div class="orders-toolbar">
                <div class="orders-filter-grid">
                    <label class="orders-search-field">
                        <span>Numero / ID</span>
                        <input id="work-orders-number-search" type="search" placeholder="OS 1024 ou ID interno" value="${escapeHtml(state.filters.workOrderNumber || "")}">
                    </label>
                    <label class="orders-search-field">
                        <span>Cliente</span>
                        <input id="work-orders-customer-search" type="search" placeholder="Razao social" value="${escapeHtml(state.filters.workOrderCustomer || "")}">
                    </label>
                    <label class="orders-search-field">
                        <span>Data exata</span>
                        <input id="work-orders-date-filter" type="date" value="${escapeHtml(state.filters.workOrderDate || "")}">
                    </label>
                    <label class="orders-search-field">
                        <span>Periodo inicial</span>
                        <input id="work-orders-start-date-filter" type="date" value="${escapeHtml(state.filters.workOrderStartDate || "")}">
                    </label>
                    <label class="orders-search-field">
                        <span>Periodo final</span>
                        <input id="work-orders-end-date-filter" type="date" value="${escapeHtml(state.filters.workOrderEndDate || "")}">
                    </label>
                    <label class="orders-search-field">
                        <span>Status</span>
                        <select id="work-orders-status-filter">
                            <option value="todos" ${state.filters.workOrderStatus === "todos" ? "selected" : ""}>Todos</option>
                            <option value="aberta" ${state.filters.workOrderStatus === "aberta" ? "selected" : ""}>Aberta</option>
                            <option value="em_execucao" ${state.filters.workOrderStatus === "em_execucao" ? "selected" : ""}>Em execucao</option>
                            <option value="concluida" ${state.filters.workOrderStatus === "concluida" ? "selected" : ""}>Concluida</option>
                            <option value="cancelada" ${state.filters.workOrderStatus === "cancelada" ? "selected" : ""}>Cancelada</option>
                        </select>
                    </label>
                    <div class="orders-filter-actions">
                        <button type="button" class="btn btn-default ghost-button" id="work-orders-clear-filters">Limpar filtros</button>
                    </div>
                </div>
                <div class="orders-toolbar-stats">
                    <span class="orders-stat">${filteredOrders.length} resultado(s)</span>
                    <span class="orders-stat is-active">${activeOrders.length} ativas</span>
                    <span class="orders-stat">${archivedOrders.length} finalizadas / historico</span>
                </div>
            </div>
            <div class="tab-strip workspace-lane-tabs">
                <button type="button" class="tab-pill ${selectedLane === "pending" ? "is-active" : ""}" data-work-order-lane="pending">Pendentes <span>${activeOrders.length}</span></button>
                <button type="button" class="tab-pill ${selectedLane === "finished" ? "is-active" : ""}" data-work-order-lane="finished">Finalizados <span>${archivedOrders.length}</span></button>
            </div>
            ${renderWorkOrderLane(
                laneTitle,
                laneDescription,
                laneOrders,
                selectedLane === "finished",
            )}
        </div>
    `;

    bindWorkOrderWorkspaceFilters();

    bindWorkOrderDocumentLinks();
    bindEntityActions("workOrder");
    bindQuickActions();
    bindWorkOrderDetails();
    bindWorkOrderPhotoViewer();
}

function getFilteredWorkOrdersForWorkspace() {
    const numberSearch = (state.filters.workOrderNumber || "").trim().toLowerCase();
    const customerSearch = (state.filters.workOrderCustomer || "").trim().toLowerCase();
    const selectedDate = state.filters.workOrderDate || "";
    const startDate = state.filters.workOrderStartDate || "";
    const endDate = state.filters.workOrderEndDate || "";
    const selectedStatus = state.filters.workOrderStatus || "todos";

    return state.workOrders.filter((item) => {
        const numberMatch = !numberSearch || [item.numero, item.id]
            .map((value) => String(value || "").toLowerCase())
            .some((value) => value.includes(numberSearch));
        const customerMatch = !customerSearch || (item.cliente?.razao_social || "")
            .toLowerCase()
            .includes(customerSearch);
        const dateMatch = !selectedDate || item.data_execucao === selectedDate;
        const startMatch = !startDate || item.data_execucao >= startDate;
        const endMatch = !endDate || item.data_execucao <= endDate;
        const statusMatch = selectedStatus === "todos" || item.status === selectedStatus;
        return numberMatch && customerMatch && dateMatch && startMatch && endMatch && statusMatch;
    });
}

function isAppointmentFinished(status) {
    return finishedAppointmentStatuses.has(String(status || "").toLowerCase());
}

function isWorkOrderFinished(status) {
    return finishedWorkOrderStatuses.has(String(status || "").toLowerCase());
}

function getAppointmentsForLane(items, lane = state.filters.appointmentLane || "pending") {
    return items.filter((item) => lane === "finished" ? isAppointmentFinished(item.status) : !isAppointmentFinished(item.status));
}

function getWorkOrdersForLane(items, lane = state.filters.workOrderLane || "pending") {
    return items.filter((item) => lane === "finished" ? isWorkOrderFinished(item.status) : !isWorkOrderFinished(item.status));
}

function bindWorkOrderWorkspaceFilters() {
    const numberSearch = document.getElementById("work-orders-number-search");
    const customerSearch = document.getElementById("work-orders-customer-search");
    const dateFilter = document.getElementById("work-orders-date-filter");
    const startDateFilter = document.getElementById("work-orders-start-date-filter");
    const endDateFilter = document.getElementById("work-orders-end-date-filter");
    const statusFilter = document.getElementById("work-orders-status-filter");
    const clearButton = document.getElementById("work-orders-clear-filters");

    numberSearch?.addEventListener("input", (event) => {
        state.filters.workOrderNumber = event.target.value;
        renderWorkOrders();
    });
    customerSearch?.addEventListener("input", (event) => {
        state.filters.workOrderCustomer = event.target.value;
        renderWorkOrders();
    });
    dateFilter?.addEventListener("change", (event) => {
        state.filters.workOrderDate = event.target.value;
        renderWorkOrders();
    });
    startDateFilter?.addEventListener("change", (event) => {
        state.filters.workOrderStartDate = event.target.value;
        renderWorkOrders();
    });
    endDateFilter?.addEventListener("change", (event) => {
        state.filters.workOrderEndDate = event.target.value;
        renderWorkOrders();
    });
    statusFilter?.addEventListener("change", (event) => {
        state.filters.workOrderStatus = event.target.value;
        renderWorkOrders();
    });
    document.querySelectorAll("[data-work-order-lane]").forEach((button) => {
        button.addEventListener("click", () => {
            state.filters.workOrderLane = button.dataset.workOrderLane === "finished" ? "finished" : "pending";
            renderWorkOrders();
        });
    });
    clearButton?.addEventListener("click", () => {
        state.filters.workOrderNumber = "";
        state.filters.workOrderCustomer = "";
        state.filters.workOrderDate = "";
        state.filters.workOrderStartDate = "";
        state.filters.workOrderEndDate = "";
        state.filters.workOrderStatus = "todos";
        state.filters.workOrderLane = "pending";
        renderWorkOrders();
    });
}

function renderWorkOrderLane(title, description, orders, archived) {
    return `
        <section class="orders-lane ${archived ? "orders-lane-archived" : ""}">
            <div class="section-heading compact">
                <h3>${escapeHtml(title)}</h3>
                <p>${escapeHtml(description)}</p>
            </div>
            <div class="orders-card-grid">
                ${orders.length
        ? orders.map((item) => renderWorkOrderCard(item, archived)).join("")
        : `<div class="empty-state">${archived
            ? "Nenhuma ordem finalizada encontrada para esta busca."
            : "Nenhuma ordem ativa encontrada para esta busca."}</div>`}
            </div>
        </section>
    `;
}

function renderWorkOrderCard(item, archived) {
    const productPreview = item.produtos?.length
        ? item.produtos
            .slice(0, 3)
            .map((product) => `
                <li>
                    <strong>${escapeHtml(product.produto.nome)}</strong>
                    <span>${escapeHtml(String(product.quantidade))} | ${escapeHtml(product.diluicao)}</span>
                </li>
            `)
            .join("")
        : `<li><strong>Sem produtos aplicados</strong><span>Cadastre itens para detalhar esta execucao.</span></li>`;

    const detailsPanel = renderWorkOrderDetails(item);

    return `
        <article class="order-summary-card ${archived ? "is-archived" : ""}">
            <div class="order-summary-head">
                <div>
                    <p class="order-summary-number">OS ${escapeHtml(item.numero)}</p>
                    <h4>${escapeHtml(item.cliente.razao_social)}</h4>
                    <p class="order-summary-meta">${escapeHtml(item.tecnico.nome)} | ${formatDate(item.data_execucao)} | ${escapeHtml(item.local_execucao)}</p>
                </div>
                ${badge(item.status.replaceAll("_", " "), archived ? "warn" : "")}
            </div>
            <div class="order-summary-grid">
                <div>
                    <span class="order-summary-label">Aplicacao</span>
                    <strong>${item.produtos.length} item(ns)</strong>
                </div>
                <div>
                    <span class="order-summary-label">Valor</span>
                    <strong>${formatCurrency(item.valor_servico)}</strong>
                </div>
                <div>
                    <span class="order-summary-label">Fotos</span>
                    <strong>${item.fotos?.length || 0} anexo(s)</strong>
                </div>
                <div>
                    <span class="order-summary-label">Garantia</span>
                    <strong>${formatDate(item.garantia_ate)}</strong>
                </div>
            </div>
            <div class="order-summary-products">
                <span class="order-summary-label">Itens adicionados</span>
                <ul>${productPreview}</ul>
            </div>
            ${renderWorkOrderActionPanel(item)}
            ${detailsPanel}
        </article>
    `;
}

function renderWorkOrderActionPanel(item) {
    const linkedFinance = state.finance.find((entry) => entry.os_id === item.id) || null;
    const quickActions = [];
    if (!isWorkOrderFinished(item.status)) {
        quickActions.push(`
            <button type="button" class="btn btn-sm ghost-button action-button complete-work-order" data-id="${item.id}">
                <i class="fas fa-check-circle"></i>
                <span>Concluir ordem</span>
            </button>
        `);
    } else {
        quickActions.push(`
            <button type="button" class="btn btn-sm ghost-button action-button reopen-work-order" data-id="${item.id}">
                <i class="fas fa-rotate-left"></i>
                <span>Reabrir OS</span>
            </button>
        `);
    }
    if (userCanAccessFinance() && linkedFinance && linkedFinance.status !== "pago") {
        quickActions.push(`
            <button type="button" class="btn btn-sm ghost-button action-button settle-work-order" data-id="${item.id}">
                <i class="fas fa-wallet"></i>
                <span>Dar baixa</span>
            </button>
        `);
    }
    quickActions.push(`
        <button type="button" class="btn btn-sm ghost-button action-button reprint-work-order" data-id="${item.id}">
            <i class="fas fa-print"></i>
            <span>Reimprimir OS</span>
        </button>
    `);

    const primaryActions = quickActions.length
        ? `<div class="order-primary-actions">${quickActions.join("")}</div>`
        : `<div class="order-primary-actions order-primary-actions-empty"><span class="origin-note">Sem acoes rapidas disponiveis.</span></div>`;

    return `
        <div class="order-action-panel">
            <div class="order-action-header">
                <span class="order-action-counter">${item.produtos.length} item(ns) aplicados</span>
                <span class="order-action-counter">${item.fotos?.length || 0} foto(s)</span>
            </div>
            ${primaryActions}
            <div class="order-secondary-actions">
                <details class="action-menu order-details-toggle" data-order-details="${item.id}">
                    <summary class="action-menu-trigger">
                        <i class="fas fa-eye"></i>
                        <span>Ver detalhes</span>
                    </summary>
                </details>
                <details class="action-menu">
                    <summary class="action-menu-trigger">
                        <i class="fas fa-file-alt"></i>
                        <span>Documentos</span>
                    </summary>
                    <div class="action-menu-panel">
                        <a href="#" class="subtle-link toolbar-link pdf-link" data-doc="os" data-id="${item.id}">
                            <i class="fas fa-file-pdf"></i>
                            <span>OS PDF</span>
                        </a>
                        <a href="#" class="subtle-link toolbar-link pdf-link" data-doc="relatorio" data-id="${item.id}">
                            <i class="fas fa-clipboard"></i>
                            <span>Relatorio</span>
                        </a>
                        <a href="#" class="subtle-link toolbar-link pdf-link" data-doc="certificado" data-id="${item.id}">
                            <i class="fas fa-shield-alt"></i>
                            <span>Sanitario padrao</span>
                        </a>
                        <a href="#" class="subtle-link toolbar-link pdf-link is-featured" data-doc="garantia" data-id="${item.id}">
                            <i class="fas fa-award"></i>
                            <span>Certificado garantia</span>
                        </a>
                        <a href="#" class="subtle-link toolbar-link pdf-link is-featured" data-doc="moldura" data-id="${item.id}">
                            <i class="fas fa-certificate"></i>
                            <span>Moldura recomendada</span>
                        </a>
                    </div>
                </details>
                <details class="action-menu">
                    <summary class="action-menu-trigger">
                        <i class="fas fa-ellipsis-h"></i>
                        <span>Mais acoes</span>
                    </summary>
                    <div class="action-menu-panel">
                        <button type="button" class="btn btn-sm ghost-button action-button secondary edit-entity" data-kind="workOrder" data-id="${item.id}">
                            <i class="fas fa-pen"></i>
                            <span>Editar ordem</span>
                        </button>
                        <button type="button" class="btn btn-sm ghost-button action-button danger delete-entity" data-kind="workOrder" data-id="${item.id}">
                            <i class="fas fa-trash-alt"></i>
                            <span>Excluir ordem</span>
                        </button>
                    </div>
                </details>
            </div>
        </div>
    `;
}

function renderWorkOrderDetails(item) {
    const pestList = item.pragas?.length
        ? item.pragas
            .map((pest) => `<li>${escapeHtml(pest.praga.nome_comum)} <span>${escapeHtml(pest.praga.nome_cientifico)}</span></li>`)
            .join("")
        : `<li>Sem pragas vinculadas.</li>`;
    const productList = item.produtos?.length
        ? item.produtos
            .map((product) => `
                <li>
                    <strong>${escapeHtml(product.produto.nome)}</strong>
                    <span>${escapeHtml(String(product.quantidade))} | ${escapeHtml(product.diluicao)}</span>
                </li>
            `)
            .join("")
        : `<li>Sem produtos aplicados.</li>`;

    return `
        <div class="order-details-panel hidden" id="order-details-panel-${item.id}">
            <div class="order-details-grid">
                <section class="order-details-block">
                    <span class="order-summary-label">Resumo operacional</span>
                    <dl class="order-details-data">
                        <div><dt>Cliente</dt><dd>${escapeHtml(item.cliente?.razao_social || "-")}</dd></div>
                        <div><dt>Tecnico</dt><dd>${escapeHtml(item.tecnico?.nome || "-")}</dd></div>
                        <div><dt>Execucao</dt><dd>${formatDate(item.data_execucao)} | ${escapeHtml(item.hora_inicio?.slice(0, 5) || "-")}</dd></div>
                        <div><dt>Garantia</dt><dd>${formatDate(item.garantia_ate)}</dd></div>
                    </dl>
                </section>
                <section class="order-details-block">
                    <span class="order-summary-label">Pragas relacionadas</span>
                    <ul class="order-details-list">${pestList}</ul>
                </section>
                <section class="order-details-block">
                    <span class="order-summary-label">Produtos da ordem</span>
                    <ul class="order-details-list">${productList}</ul>
                </section>
                <section class="order-details-block">
                    <span class="order-summary-label">Observacoes</span>
                    <p class="order-details-note">${escapeHtml(item.observacoes || "Sem observacoes registradas para esta ordem.")}</p>
                </section>
            </div>
            <section class="order-details-block">
                <span class="order-summary-label">Fotos anexadas</span>
                ${renderWorkOrderPhotoCards(item.fotos || [], {
        workOrderId: item.id,
        compact: true,
    })}
            </section>
        </div>
    `;
}

function bindWorkOrderDetails() {
    document.querySelectorAll(".order-details-toggle").forEach((toggle) => {
        toggle.addEventListener("toggle", async () => {
            const panel = document.getElementById(`order-details-panel-${toggle.dataset.orderDetails}`);
            if (!panel) {
                return;
            }
            const isOpen = toggle.open;
            panel.classList.toggle("hidden", !isOpen);
            if (isOpen) {
                await hydrateWorkOrderPhotoThumbs(panel);
            }
        });
    });
}

function bindWorkOrderDocumentLinks() {
    document.querySelectorAll(".pdf-link").forEach((link) => {
        link.addEventListener("click", async (event) => {
            event.preventDefault();
            const { id, doc } = event.currentTarget.dataset;
            const docUrlMap = {
                os: `/api/v1/os/${id}/pdf`,
                relatorio: `/api/v1/os/${id}/relatorio-tecnico.pdf`,
                certificado: `/api/v1/os/${id}/certificado-sanitario.pdf`,
                garantia: `/api/v1/os/${id}/certificado-garantia.pdf`,
                moldura: `/api/v1/os/${id}/certificado-moldura.pdf`,
            };
            const docTitleMap = {
                os: `Ordem de Servico ${id}`,
                relatorio: `Relatorio tecnico ${id}`,
                certificado: `Certificado sanitario ${id}`,
                garantia: `Certificado de garantia ${id}`,
                moldura: `Certificado moldura ${id}`,
            };
            const previewWindow = openDocumentPreviewShell(
                docTitleMap[doc] || `Documento ${id}`,
                "Preparando documento..."
            );
            try {
                logClientEvent("work_order_document_open", { work_order_id: Number(id), document: doc });
                const blob = await apiFetch(docUrlMap[doc]);
                openBlobPreview(blob, docTitleMap[doc] || `Documento ${id}`, { previewWindow });
            } catch (error) {
                renderDocumentPreviewError(
                    previewWindow,
                    docTitleMap[doc] || `Documento ${id}`,
                    error.message || "Nao foi possivel abrir o documento."
                );
                logClientEvent(
                    "work_order_document_error",
                    { work_order_id: Number(id), document: doc, message: error.message },
                    "error"
                );
                toast(error.message);
            }
        });
    });
}

function bindWorkOrderPhotoViewer() {
    document.querySelectorAll("[data-view-photo-url]").forEach((button) => {
        button.addEventListener("click", async () => {
            try {
                const blob = await apiFetch(button.dataset.viewPhotoUrl);
                const fileUrl = URL.createObjectURL(blob);
                window.open(fileUrl, "_blank", "noopener");
            } catch (error) {
                toast(error.message);
            }
        });
    });
}

function renderWorkOrderSaveFeedback() {
    const target = document.getElementById("work-order-save-feedback");
    if (!target) {
        return;
    }

    const workOrder = state.workOrderWorkflow.lastSavedOrderId
        ? getEntityByKind("workOrder", state.workOrderWorkflow.lastSavedOrderId)
        : null;
    if (!workOrder) {
        target.innerHTML = "";
        target.classList.add("hidden");
        return;
    }

    target.innerHTML = `
        <section class="work-order-save-card">
            <div class="section-heading compact">
                <h4>Ordem salva com sucesso</h4>
                <p>OS ${escapeHtml(workOrder.numero)} pronta para visualizacao, impressao e emissao dos documentos. O certificado de garantia foi preparado automaticamente e pode ser aberto abaixo.</p>
            </div>
            <div class="work-order-save-meta">
                <span class="orders-stat is-active">${escapeHtml(workOrder.cliente?.razao_social || "Cliente")}</span>
                <span class="orders-stat">${formatDate(workOrder.data_execucao)}</span>
                <span class="orders-stat">${state.workOrderWorkflow.certificateReady ? "Garantia pronta" : "Garantia sob demanda"}</span>
            </div>
            <div class="work-order-save-actions">
                <button type="button" class="btn btn-success" data-work-order-action="preview-order" data-id="${workOrder.id}">Visualizar OS</button>
                <button type="button" class="btn btn-default ghost-button" data-work-order-action="print" data-id="${workOrder.id}">Imprimir OS</button>
                <button type="button" class="btn btn-primary" data-work-order-action="certificate-guarantee-preview" data-id="${workOrder.id}">Abrir garantia</button>
                <button type="button" class="btn btn-default ghost-button" data-work-order-action="certificate-guarantee-download" data-id="${workOrder.id}">Baixar garantia</button>
                <button type="button" class="btn btn-warning" data-work-order-action="certificate-moldura-preview" data-id="${workOrder.id}">Abrir moldura</button>
                <button type="button" class="btn btn-default ghost-button" data-work-order-action="certificate-moldura-download" data-id="${workOrder.id}">Baixar moldura</button>
            </div>
        </section>
    `;
    target.classList.remove("hidden");
}

async function preview_work_order(workOrderId, options = {}) {
    const blob = await apiFetch(`/api/v1/os/${workOrderId}/pdf`);
    const workOrder = getEntityByKind("workOrder", workOrderId);
    openBlobPreview(blob, `Ordem de Servico ${workOrder?.numero || workOrderId}`, {
        previewWindow: options.previewWindow,
    });
}

async function print_order(workOrderId, options = {}) {
    const blob = await apiFetch(`/api/v1/os/${workOrderId}/pdf`);
    const workOrder = getEntityByKind("workOrder", workOrderId);
    openBlobPreview(blob, `Ordem de Servico ${workOrder?.numero || workOrderId}`, {
        printOnLoad: true,
        previewWindow: options.previewWindow,
    });
}

function printAppointmentSummary(appointmentId) {
    const appointment = getEntityByKind("appointment", Number(appointmentId));
    if (!appointment) {
        toast("Agendamento nao encontrado para impressao.");
        return;
    }
    const printWindow = window.open("", "_blank", "noopener");
    if (!printWindow) {
        toast("Nao foi possivel abrir a janela de impressao.");
        return;
    }
    printWindow.document.write(`
        <!doctype html>
        <html lang="pt-BR">
            <head>
                <meta charset="utf-8">
                <title>Agendamento ${appointment.id}</title>
                <style>
                    body { font-family: "Trebuchet MS", "Segoe UI", sans-serif; margin: 0; color: #1c2922; background: #eff3ec; }
                    .print-shell { display: grid; gap: 20px; padding: 24px; }
                    .print-header { padding: 22px 24px; border: 1px solid rgba(28, 67, 51, 0.08); border-radius: 22px; background: linear-gradient(135deg, rgba(220, 239, 215, 0.72), rgba(255, 255, 255, 0.96)); }
                    .eyebrow { margin: 0 0 8px; color: #617065; font-size: 12px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
                    h1 { margin: 0 0 6px; font-family: Georgia, "Times New Roman", serif; }
                    .meta { color: #617065; margin: 0; line-height: 1.5; }
                    .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px 18px; }
                    .card { border: 1px solid #d7dfd3; border-radius: 18px; padding: 14px 16px; background: rgba(255, 255, 255, 0.96); }
                    .card span { display: block; color: #617065; font-size: 12px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; margin-bottom: 6px; }
                    .note { display: grid; gap: 10px; padding: 18px 20px; border: 1px solid #d7dfd3; border-radius: 18px; background: rgba(255, 255, 255, 0.96); white-space: pre-wrap; }
                    .note strong { font-family: Georgia, "Times New Roman", serif; }
                    .note p { margin: 0; line-height: 1.65; }
                    @media (max-width: 640px) { .print-shell { padding: 16px; } .grid { grid-template-columns: 1fr; } }
                    @media print { body { background: #fff; } .print-shell { padding: 0; } }
                </style>
            </head>
            <body>
                <div class="print-shell">
                    <section class="print-header">
                        <p class="eyebrow">Resumo de agendamento</p>
                        <h1>Agendamento #${appointment.id}</h1>
                        <p class="meta">${escapeHtml(appointment.cliente_nome)} | ${escapeHtml(appointment.tipo_servico)}</p>
                    </section>
                    <div class="grid">
                        <div class="card"><span>Data</span><strong>${escapeHtml(formatDate(appointment.data_agendamento))}</strong></div>
                        <div class="card"><span>Hora</span><strong>${escapeHtml(formatTime(appointment.hora_agendamento))}</strong></div>
                        <div class="card"><span>Tecnico</span><strong>${escapeHtml(appointment.tecnico_nome || "Nao definido")}</strong></div>
                        <div class="card"><span>Status</span><strong>${escapeHtml(appointment.status.replaceAll("_", " "))}</strong></div>
                        <div class="card"><span>Telefone</span><strong>${escapeHtml(appointment.telefone || "-")}</strong></div>
                        <div class="card"><span>OS vinculada</span><strong>${escapeHtml(appointment.os_numero || "Sem vinculacao")}</strong></div>
                        <div class="card" style="grid-column: 1 / -1;"><span>Endereco</span><strong>${escapeHtml(appointment.endereco_completo || "-")}</strong></div>
                    </div>
                    <div class="note">
                        <strong>Observacoes</strong>
                        <p>${escapeHtml(appointment.observacoes || appointment.observacoes_internas || "Sem observacoes adicionais.")}</p>
                    </div>
                </div>
                <script>
                    window.addEventListener("load", () => {
                        setTimeout(() => {
                            window.focus();
                            window.print();
                        }, 250);
                    });
                </script>
            </body>
        </html>
    `);
    printWindow.document.close();
}

async function generate_certificate(workOrderId, options = {}) {
    const mode = options.mode || "preview";
    const variant = options.variant || "standard";
    const endpointMap = {
        standard: `/api/v1/os/${workOrderId}/certificado-sanitario.pdf`,
        garantia: `/api/v1/os/${workOrderId}/certificado-garantia.pdf`,
        moldura: `/api/v1/os/${workOrderId}/certificado-moldura.pdf`,
    };
    const endpoint = endpointMap[variant] || endpointMap.standard;
    const blob = await apiFetch(endpoint);
    const workOrder = getEntityByKind("workOrder", workOrderId);
    if (mode === "background") {
        return blob;
    }
    if (mode === "download") {
        downloadBlob(blob, buildCertificateFilename(workOrder, variant));
        return blob;
    }
    const titlePrefix = variant === "moldura"
        ? "Certificado Moldura"
        : variant === "garantia"
            ? "Certificado de Garantia"
            : "Certificado";
    openBlobPreview(blob, `${titlePrefix} ${workOrder?.numero || workOrderId}`, {
        previewWindow: options.previewWindow,
    });
    return blob;
}

function buildCertificateFilename(workOrder, variant = "standard") {
    const customer = sanitizeFilenamePart(workOrder?.cliente?.razao_social || "cliente");
    const suffix = variant === "moldura" ? "moldura" : variant === "garantia" ? "garantia" : "padrao";
    return `cert_${suffix}_${workOrder?.id || "os"}_${customer}.pdf`;
}

function buildReceiptPdfFilename(receipt) {
    const receiptNumber = sanitizeFilenamePart(receipt?.numero || receipt?.id || "recibo");
    const customer = sanitizeFilenamePart(receipt?.cliente?.razao_social || "cliente");
    return `recibo_${receiptNumber}_${customer}.pdf`;
}

function sanitizeFilenamePart(value) {
    return String(value || "arquivo")
        .normalize("NFD")
        .replaceAll(/[\u0300-\u036f]/g, "")
        .replaceAll(/[^a-zA-Z0-9_-]+/g, "_")
        .replaceAll(/^_+|_+$/g, "")
        .toLowerCase() || "arquivo";
}

function logClientEvent(eventName, payload = {}, level = "info") {
    const logger = level === "error"
        ? console.error
        : level === "warn"
            ? console.warn
            : console.info;
    logger(`[SysPragas] ${eventName}`, payload);
}

function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    logClientEvent("document_download", { filename, size_bytes: blob.size || null });
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function openDocumentPreviewShell(title, message = "Preparando documento...") {
    const previewWindow = window.open("", "_blank");
    if (!previewWindow) {
        return null;
    }
    renderPreviewWindowState(previewWindow, title, {
        bodyHtml: `<div class="preview-state preview-state-loading">${escapeHtml(message)}</div>`,
    });
    return previewWindow;
}

function renderDocumentPreviewError(previewWindow, title, message) {
    if (!previewWindow || previewWindow.closed) {
        return;
    }
    renderPreviewWindowState(previewWindow, title, {
        bodyHtml: `<div class="preview-state preview-state-error">${escapeHtml(message)}</div>`,
    });
}

function renderPreviewWindowState(previewWindow, title, options = {}) {
    previewWindow.document.open();
    previewWindow.document.write(`
        <!doctype html>
        <html lang="pt-BR">
            <head>
                <meta charset="utf-8">
                <title>${escapeHtml(title)}</title>
                <style>
                    body { margin: 0; font-family: 'Trebuchet MS', 'Segoe UI', sans-serif; background: #eff3ec; color: #1c2922; }
                    .preview-shell { display: grid; gap: 14px; min-height: 100vh; padding: 18px; background: radial-gradient(circle at top left, rgba(41, 95, 73, 0.08), transparent 26%), linear-gradient(180deg, #f7f9f4 0%, #eff3ec 100%); }
                    .preview-note { padding: 14px 16px; border: 1px solid #d7dfd3; background: linear-gradient(135deg, rgba(220, 239, 215, 0.72), rgba(255,255,255,0.96)); border-radius: 18px; color: #1c4333; font-weight: 700; }
                    .preview-state { display: grid; place-items: center; min-height: calc(100vh - 128px); padding: 28px; text-align: center; border-radius: 20px; background: rgba(255, 255, 255, 0.95); border: 1px solid #d7dfd3; box-shadow: 0 18px 50px rgba(20, 36, 24, 0.08); }
                    .preview-state-loading { color: #2d6a4f; font-weight: 700; }
                    .preview-state-error { color: #b14534; font-weight: 700; }
                    iframe { width: 100%; height: calc(100vh - 94px); border: 0; background: #fff; border-radius: 20px; box-shadow: 0 18px 50px rgba(20, 36, 24, 0.08); }
                    @media (max-width: 640px) { .preview-shell { padding: 12px; } .preview-note { border-radius: 16px; } .preview-state, iframe { border-radius: 16px; } }
                </style>
            </head>
            <body>
                <div class="preview-shell">
                    <div class="preview-note">${escapeHtml(options.note || "Documento pronto para visualizacao e impressao.")}</div>
                    ${options.bodyHtml || ""}
                </div>
            </body>
        </html>
    `);
    previewWindow.document.close();
}

function openBlobPreview(blob, title, options = {}) {
    const previewUrl = URL.createObjectURL(blob);
    const previewWindow = options.previewWindow && !options.previewWindow.closed
        ? options.previewWindow
        : window.open("", "_blank");
    if (!previewWindow) {
        window.open(previewUrl, "_blank", "noopener");
        return;
    }
    const printOnLoad = options.printOnLoad ? "true" : "false";
    renderPreviewWindowState(previewWindow, title, {
        bodyHtml: `<iframe id="preview-frame" src="${previewUrl}" title="${escapeHtml(title)}"></iframe>`,
    });
    previewWindow.addEventListener("beforeunload", () => URL.revokeObjectURL(previewUrl), { once: true });
    const frame = previewWindow.document.getElementById("preview-frame");
    frame?.addEventListener("load", () => {
        if (options.printOnLoad) {
            setTimeout(() => {
                try {
                    frame.contentWindow.focus();
                    frame.contentWindow.print();
                } catch (_) {}
            }, 400);
        }
    });
    logClientEvent("document_preview_opened", {
        title,
        size_bytes: blob.size || null,
        print_on_load: Boolean(options.printOnLoad),
    });
}

async function openReceiptPdf(receiptId, options = {}) {
    const receipt = getEntityByKind("receipt", Number(receiptId));
    const blob = await apiFetch(`/api/v1/recibos/${receiptId}/pdf`);
    if (options.download) {
        downloadBlob(blob, buildReceiptPdfFilename(receipt));
        return;
    }
    openBlobPreview(blob, `Recibo ${receipt?.numero || receiptId}`, {
        printOnLoad: Boolean(options.printOnLoad),
    });
}

function renderFinance() {
    if (!userCanAccessFinance()) {
        return;
    }
    renderFinanceSummary();
    renderFinanceInsights();
    renderFinanceEntriesTable();
    renderReceiptsTable();
    renderNfeInvoices();
    renderFinanceReportsIssuedInvoices();
    renderContractReportsPanel();
    renderSimplesNationalPanel();
    renderCashLedger();
    bindEntityActions("finance");
    bindEntityActions("receipt");
    bindEntityActions("nfe");
    bindReceiptActions();
    bindNfeActions();
    bindQuickActions();
    bindFinanceFilters();
    bindReceiptFilters();
    bindNfeFilters();
    bindContractReportActions();
    bindSimplesSummaryRefresh();
    bindSimplesConfigActions();
    setFinanceWorkspaceView(state.financeScreen || "lancamentos");
    setNfeTabView(state.nfeTab || "issue");
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

function renderFinanceInsights() {
    const summary = state.cashFlowSummary || {
        recebido: 0,
        pendente: 0,
        vencido: 0,
        quantidade_recebida: 0,
        quantidade_pendente: 0,
        quantidade_vencida: 0,
    };
    const cashSummaryHtml = `
        <div class="finance-insight-grid">
            <article class="finance-insight-card">
                <span>Recebido</span>
                <strong>${formatCurrency(summary.recebido || 0)}</strong>
                <small>${summary.quantidade_recebida || 0} titulo(s) com baixa</small>
            </article>
            <article class="finance-insight-card">
                <span>Pendente</span>
                <strong>${formatCurrency(summary.pendente || 0)}</strong>
                <small>${summary.quantidade_pendente || 0} titulo(s) em aberto</small>
            </article>
            <article class="finance-insight-card is-alert">
                <span>Vencido</span>
                <strong>${formatCurrency(summary.vencido || 0)}</strong>
                <small>${summary.quantidade_vencida || 0} titulo(s) vencido(s)</small>
            </article>
        </div>
    `;
    ["finance-cashflow-summary", "finance-report-cashflow-summary"].forEach((id) => {
        const summaryTarget = document.getElementById(id);
        if (summaryTarget) {
            summaryTarget.innerHTML = cashSummaryHtml;
        }
    });

    const nfeSummaryTarget = document.getElementById("finance-nfe-summary");
    if (nfeSummaryTarget) {
        const invoices = state.nfeInvoices || [];
        const emittedInvoices = invoices.filter((item) => item.status === "emitida");
        const totalEmitted = emittedInvoices.reduce((total, item) => total + Number(item.valor_total || 0), 0);
        const generatedTitles = invoices.filter((item) => item.finance_entry_id).length;
        nfeSummaryTarget.innerHTML = `
            <div class="finance-insight-grid compact">
                <article class="finance-insight-card">
                    <span>NF-e emitidas</span>
                    <strong>${emittedInvoices.length}</strong>
                    <small>${formatCurrency(totalEmitted)}</small>
                </article>
                <article class="finance-insight-card">
                    <span>Titulos gerados</span>
                    <strong>${generatedTitles}</strong>
                    <small>Integracao financeira automatica</small>
                </article>
            </div>
        `;
    }
}

function renderFinanceEntriesTable() {
    setTableContent(
        "finance-table",
        ["Tipo", "Descricao", "Origem", "Valor", "Pago", "Saldo", "Vencimento", "Status", "Acoes"],
        getFilteredFinanceEntries().map((item) => {
            const payButton = item.status !== "pago" && Number(item.saldo_aberto ?? item.valor) > 0
                ? actionButton(
                    "pay-finance",
                    item.tipo === "receita" ? "Receber" : "Pagar",
                    `data-id="${item.id}" data-open-balance="${item.saldo_aberto ?? item.valor}"`,
                )
                : "";
            const parcelText = Number(item.total_parcelas || 1) > 1 ? `${item.parcela_atual}/${item.total_parcelas}` : "";
            const originLabel = item.nfe_id
                ? `NF-e ${item.nfe_id}`
                : item.recibo_id
                    ? `Recibo ${item.recibo_id}`
                : item.contrato_id
                    ? `Contrato ${item.contrato_id}`
                : item.os_id
                    ? `OS ${item.os_id}`
                    : item.origem;
            const actions = item.os_id || item.nfe_id || item.contrato_id
                ? `<div class="toolbar compact-toolbar">
                    <div class="toolbar-group">
                        <span class="origin-note">Gerado por ${escapeHtml(originLabel)}</span>
                        ${parcelText ? `<span class="badge">${escapeHtml(parcelText)}</span>` : ""}
                    </div>
                    ${payButton ? `<div class="toolbar-group">${payButton}</div>` : ""}
                </div>`
                : item.recibo_id
                    ? `<div class="toolbar compact-toolbar">
                        <div class="toolbar-group">
                            <span class="origin-note">Gerado por ${escapeHtml(originLabel)}</span>
                        </div>
                    </div>`
                : actionButtons("finance", item.id, payButton);
            return [
                badge(item.tipo, item.tipo === "despesa" ? "warn" : ""),
                `<div>${escapeHtml(item.descricao)}${parcelText ? `<div class="origin-note">Parcela ${escapeHtml(parcelText)}</div>` : ""}</div>`,
                item.nfe_id
                    ? `<div>${escapeHtml(originLabel)}<div class="origin-note">${escapeHtml(item.categoria || "Conta a receber")}</div></div>`
                    : item.contrato_id
                        ? `<div>${escapeHtml(originLabel)}<div class="origin-note">${escapeHtml(item.categoria || "Contrato recorrente")}</div></div>`
                    : item.os_id
                        ? `<div>${escapeHtml(originLabel)}<div class="origin-note">${escapeHtml(item.categoria || "Servico")}</div></div>`
                        : item.categoria || item.fornecedor_nome || "-",
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
}

function renderReceiptsTable() {
    setTableContent(
        "receipts-table",
        ["Numero", "Cliente", "Data", "Forma", "Valor", "OS", "Financeiro", "Acoes"],
        getFilteredReceipts().map((item) => [
            `<div><strong>${escapeHtml(item.numero)}</strong><div class="origin-note">${escapeHtml(item.descricao)}</div></div>`,
            item.cliente?.razao_social || "-",
            formatDate(item.data_recebimento),
            badge(item.forma_pagamento.replaceAll("_", " "), ""),
            formatCurrency(item.valor),
            item.os_numero || "-",
            item.finance_entry_id
                ? `<div>Lancamento #${item.finance_entry_id}<div class="origin-note">Baixa integrada no caixa</div></div>`
                : "Nao integrado",
            renderReceiptActionPanel(item),
        ]),
        "Nenhum recibo emitido.",
        { nonSortableTargets: [7], pageLength: 6 },
    );
}

function renderReceiptActionPanel(item) {
    return `
        <div class="toolbar compact-toolbar">
            <div class="toolbar-group">
                <button type="button" class="btn btn-sm ghost-button receipt-preview-action" data-id="${item.id}">Visualizar</button>
                <button type="button" class="btn btn-sm ghost-button receipt-print-action" data-id="${item.id}">Imprimir</button>
                <button type="button" class="btn btn-sm ghost-button receipt-pdf-action" data-id="${item.id}">PDF</button>
            </div>
            <div class="toolbar-group">
                <button type="button" class="btn btn-sm ghost-button action-button secondary edit-entity" data-kind="receipt" data-id="${item.id}">Editar</button>
                <button type="button" class="btn btn-sm ghost-button action-button danger delete-entity" data-kind="receipt" data-id="${item.id}">Excluir</button>
            </div>
        </div>
    `;
}

function renderNfeInvoices() {
    setTableContent(
        "nfe-table",
        ["Numero", "Cliente", "Emissao", "Vencimento", "Valor", "Financeiro", "Status", "Acoes"],
        getFilteredNfeInvoices().map((item) => {
            const financeInfo = item.finance_entry_id
                ? `<div>Lancamento #${item.finance_entry_id}<div class="origin-note">Consulta cruzada ativa</div></div>`
                : "Nao gerado";
            const fiscalStatus = item.status_processamento || item.status;
            const statusTone = fiscalStatus === "rejeitado" || item.status === "cancelada"
                ? "danger"
                : (fiscalStatus === "autorizado" ? "" : "warn");
            return [
                item.numero_nfe,
                item.cliente?.razao_social || "-",
                formatDate(item.data_emissao),
                formatDate(item.data_vencimento),
                formatCurrency(item.valor_total),
                financeInfo,
                `
                    <div class="nfe-status-stack">
                        ${badge(item.status, item.status === "cancelada" ? "danger" : "")}
                        ${badge(fiscalStatus, statusTone)}
                    </div>
                `,
                renderNfeActionPanel(item),
            ];
        }),
        "Nenhuma NF-e registrada.",
        { nonSortableTargets: [7], pageLength: 6 },
    );
}

function renderNfeActionPanel(item) {
    const canCancel = item.status !== "cancelada";
    const hasPdf = Boolean(item.pdf_url);
    const hasXml = Boolean(item.xml_url || item.xml_autorizado || item.xml_enviado);
    return `
        <div class="nfe-action-panel">
            <div class="nfe-action-grid">
                <button type="button" class="btn btn-sm ghost-button action-button secondary nfe-sync-status" data-id="${item.id}">Consultar</button>
                <button type="button" class="btn btn-sm ghost-button edit-entity" data-kind="nfe" data-id="${item.id}">Editar</button>
                <button type="button" class="btn btn-sm ghost-button nfe-download-xml" data-id="${item.id}" ${hasXml ? "" : "disabled"}>XML</button>
                <button type="button" class="btn btn-sm ghost-button nfe-open-pdf" data-id="${item.id}" ${hasPdf ? "" : "disabled"}>DANFE</button>
                <button type="button" class="btn btn-sm ghost-button action-button danger nfe-cancel" data-id="${item.id}" ${canCancel ? "" : "disabled"}>Cancelar</button>
            </div>
        </div>
    `;
}

function renderFinanceReportsIssuedInvoices() {
    const issuedInvoices = state.nfeInvoices
        .filter((item) => item.status === "emitida")
        .sort((left, right) => String(right.data_emissao || "").localeCompare(String(left.data_emissao || "")));
    setTableContent(
        "finance-reports-nfe-table",
        ["Numero", "Cliente", "Emissao", "Valor", "Financeiro", "Status fiscal"],
        issuedInvoices.map((item) => [
            item.numero_nfe,
            item.cliente?.razao_social || "-",
            formatDate(item.data_emissao),
            formatCurrency(item.valor_total),
            item.finance_entry_id
                ? `<div>Lancamento #${item.finance_entry_id}<div class="origin-note">Integrada ao contas a receber</div></div>`
                : "Nao gerado",
            badge(item.status_processamento || item.status, item.status_processamento === "rejeitado" ? "danger" : ""),
        ]),
        "Nenhuma NF-e emitida encontrada para relatorio.",
        { pageLength: 6 },
    );
}

function renderContractReportsPanel() {
    const target = document.getElementById("contract-reports-panel");
    if (!target) {
        return;
    }
    const report = state.contractReport || {
        resumo: {
            total_contratos: 0,
            ativos: 0,
            vencidos: 0,
            a_vencer: 0,
            com_cobranca_ativa: 0,
            valor_total_mensal_previsto: 0,
        },
        itens: [],
    };

    target.innerHTML = `
        <div class="section-heading compact">
            <h4>Relatorios de contratos</h4>
            <p>Filtros avancados, exportacao e integracao com cobrancas recorrentes.</p>
        </div>
        <div class="finance-filter-grid">
            <label>
                <span>Cliente</span>
                <select id="contract-report-customer-filter">
                    <option value="">Todos os clientes</option>
                    ${state.customers.map((item) => `<option value="${item.id}" ${String(item.id) === String(state.filters.contractReportCustomer || "") ? "selected" : ""}>${escapeHtml(item.razao_social)}</option>`).join("")}
                </select>
            </label>
            <label>
                <span>Status</span>
                <select id="contract-report-status-filter">
                    <option value="todos" ${state.filters.contractReportStatus === "todos" ? "selected" : ""}>Todos</option>
                    <option value="ativo" ${state.filters.contractReportStatus === "ativo" ? "selected" : ""}>Ativo</option>
                    <option value="a_vencer" ${state.filters.contractReportStatus === "a_vencer" ? "selected" : ""}>A vencer</option>
                    <option value="vencido" ${state.filters.contractReportStatus === "vencido" ? "selected" : ""}>Vencido</option>
                </select>
            </label>
            <label>
                <span>Inicio de</span>
                <input id="contract-report-start-filter" type="date" value="${escapeHtml(state.filters.contractReportStartDate || "")}">
            </label>
            <label>
                <span>Inicio ate</span>
                <input id="contract-report-end-filter" type="date" value="${escapeHtml(state.filters.contractReportEndDate || "")}">
            </label>
            <label>
                <span>Vencimento de</span>
                <input id="contract-report-due-start-filter" type="date" value="${escapeHtml(state.filters.contractReportDueStartDate || "")}">
            </label>
            <label>
                <span>Vencimento ate</span>
                <input id="contract-report-due-end-filter" type="date" value="${escapeHtml(state.filters.contractReportDueEndDate || "")}">
            </label>
            <label>
                <span>Cobranca ativa</span>
                <select id="contract-report-billing-filter">
                    <option value="todos" ${state.filters.contractReportBillingActive === "todos" ? "selected" : ""}>Todos</option>
                    <option value="true" ${state.filters.contractReportBillingActive === "true" ? "selected" : ""}>Sim</option>
                    <option value="false" ${state.filters.contractReportBillingActive === "false" ? "selected" : ""}>Nao</option>
                </select>
            </label>
            <div class="finance-filter-actions">
                <button type="button" class="btn btn-success" id="contract-report-refresh">Gerar relatorio</button>
                <button type="button" class="btn btn-default ghost-button" id="contract-report-export-xlsx">Exportar Excel</button>
                <button type="button" class="btn btn-default ghost-button" id="contract-report-export-pdf">Exportar PDF</button>
            </div>
        </div>
        <div class="finance-insight-grid compact">
            <article class="finance-insight-card"><span>Total contratos</span><strong>${report.resumo.total_contratos || 0}</strong></article>
            <article class="finance-insight-card"><span>Ativos</span><strong>${report.resumo.ativos || 0}</strong></article>
            <article class="finance-insight-card is-alert"><span>A vencer</span><strong>${report.resumo.a_vencer || 0}</strong></article>
            <article class="finance-insight-card is-alert"><span>Vencidos</span><strong>${report.resumo.vencidos || 0}</strong></article>
            <article class="finance-insight-card"><span>Cobranca ativa</span><strong>${report.resumo.com_cobranca_ativa || 0}</strong></article>
            <article class="finance-insight-card"><span>Valor mensal previsto</span><strong>${formatCurrency(report.resumo.valor_total_mensal_previsto || 0)}</strong></article>
        </div>
        <div id="contract-reports-table"></div>
    `;

    setTableContent(
        "contract-reports-table",
        ["Cliente", "Contrato", "Inicio", "Vencimento", "Status", "Valor", "Ultima cobranca", "Financeiro"],
        (report.itens || []).map((item) => [
            item.cliente_nome,
            `<div>${escapeHtml(item.nome)}<div class="origin-note">${escapeHtml(item.tipo_cobranca)} | ${item.gerar_cobranca_automatica ? "Cobranca automatica" : "Manual"}</div></div>`,
            formatDate(item.data_inicio),
            formatDate(item.data_vencimento),
            contractStatusBadge(item.status),
            formatCurrency(item.valor_mensal || 0),
            item.ultima_cobranca_gerada_em ? formatDate(item.ultima_cobranca_gerada_em) : "-",
            `<div>${escapeHtml(item.situacao_financeira)}<div class="origin-note">${item.ultimo_lancamento_id ? `Lancamento #${item.ultimo_lancamento_id}` : "Sem lancamento"}</div></div>`,
        ]),
        "Nenhum contrato encontrado para os filtros informados.",
        { pageLength: 6 },
    );
}

function bindContractReportActions() {
    const refreshButton = document.getElementById("contract-report-refresh");
    if (refreshButton && refreshButton.dataset.bound !== "true") {
        refreshButton.dataset.bound = "true";
        refreshButton.addEventListener("click", refreshContractReport);
    }

    const exportXlsxButton = document.getElementById("contract-report-export-xlsx");
    if (exportXlsxButton && exportXlsxButton.dataset.bound !== "true") {
        exportXlsxButton.dataset.bound = "true";
        exportXlsxButton.addEventListener("click", async () => {
            try {
                const blob = await apiFetch(buildContractReportUrl("/api/v1/contratos/relatorios.xlsx"));
                downloadBlob(blob, `relatorio_contratos_${todayIso().replaceAll("-", "")}.xlsx`);
            } catch (error) {
                toast(error.message);
            }
        });
    }

    const exportPdfButton = document.getElementById("contract-report-export-pdf");
    if (exportPdfButton && exportPdfButton.dataset.bound !== "true") {
        exportPdfButton.dataset.bound = "true";
        exportPdfButton.addEventListener("click", async () => {
            try {
                const blob = await apiFetch(buildContractReportUrl("/api/v1/contratos/relatorios.pdf"));
                openBlobPreview(blob, "Relatorio de Contratos");
            } catch (error) {
                toast(error.message);
            }
        });
    }
}

async function refreshContractReport() {
    state.filters.contractReportCustomer = document.getElementById("contract-report-customer-filter")?.value || "";
    state.filters.contractReportStatus = document.getElementById("contract-report-status-filter")?.value || "todos";
    state.filters.contractReportStartDate = document.getElementById("contract-report-start-filter")?.value || "";
    state.filters.contractReportEndDate = document.getElementById("contract-report-end-filter")?.value || "";
    state.filters.contractReportDueStartDate = document.getElementById("contract-report-due-start-filter")?.value || "";
    state.filters.contractReportDueEndDate = document.getElementById("contract-report-due-end-filter")?.value || "";
    state.filters.contractReportBillingActive = document.getElementById("contract-report-billing-filter")?.value || "todos";

    try {
        state.contractReport = await apiFetch(buildContractReportUrl());
        renderContractReportsPanel();
        bindContractReportActions();
        toast("Relatorio de contratos atualizado.");
    } catch (error) {
        toast(error.message);
    }
}

function bindReceiptActions() {
    const tableHost = document.getElementById("receipts-table");
    if (!tableHost || tableHost.dataset.bound === "true") {
        return;
    }
    tableHost.dataset.bound = "true";
    tableHost.addEventListener("click", async (event) => {
        const previewButton = event.target.closest(".receipt-preview-action");
        if (previewButton) {
            showReceiptPreview(previewButton.dataset.id);
            return;
        }

        const printButton = event.target.closest(".receipt-print-action");
        if (printButton) {
            try {
                await openReceiptPdf(printButton.dataset.id, { printOnLoad: true });
            } catch (error) {
                toast(error.message);
            }
            return;
        }

        const pdfButton = event.target.closest(".receipt-pdf-action");
        if (pdfButton) {
            try {
                await openReceiptPdf(pdfButton.dataset.id, { download: true });
                toast("PDF do recibo gerado com sucesso.");
            } catch (error) {
                toast(error.message);
            }
        }
    });
}

function bindNfeActions() {
    document.querySelectorAll(".nfe-sync-status").forEach((button) => {
        if (button.dataset.bound === "true") {
            return;
        }
        button.dataset.bound = "true";
        button.addEventListener("click", async () => {
            try {
                const invoice = await apiFetch(`/api/v1/nfe/${button.dataset.id}?sync=true`);
                await loadAllData();
                state.nfeWorkflow.lastIssuedInvoiceId = invoice.id;
                state.nfeTab = "issued";
                renderNfeEmissionWorkspace();
                renderNfeEmissionFeedback();
                toast("Status da NF-e atualizado com sucesso.");
            } catch (error) {
                toast(error.message);
            }
        });
    });

    document.querySelectorAll(".nfe-cancel").forEach((button) => {
        if (button.dataset.bound === "true") {
            return;
        }
        button.dataset.bound = "true";
        button.addEventListener("click", async () => {
            if (button.disabled) {
                return;
            }
            const justification = window.prompt("Informe a justificativa do cancelamento da NF-e:", "Cancelamento solicitado pelo emitente.");
            if (justification === null) {
                return;
            }
            try {
                const invoice = await apiFetch(`/api/v1/nfe/${button.dataset.id}`, {
                    method: "DELETE",
                    body: JSON.stringify({ justificativa: justification.trim() || null }),
                });
                state.nfeWorkflow.lastIssuedInvoiceId = invoice.id;
                state.nfeTab = "issued";
                await afterMutation("NF-e cancelada com sucesso.");
                renderNfeEmissionFeedback();
            } catch (error) {
                toast(error.message);
            }
        });
    });

    document.querySelectorAll(".nfe-download-xml").forEach((button) => {
        if (button.dataset.bound === "true") {
            return;
        }
        button.dataset.bound = "true";
        button.addEventListener("click", () => {
            if (button.disabled) {
                return;
            }
            const invoice = getEntityByKind("nfe", Number(button.dataset.id));
            if (!invoice) {
                return;
            }
            openNfeXml(invoice);
        });
    });

    document.querySelectorAll(".nfe-open-pdf").forEach((button) => {
        if (button.dataset.bound === "true") {
            return;
        }
        button.dataset.bound = "true";
        button.addEventListener("click", () => {
            if (button.disabled) {
                return;
            }
            const invoice = getEntityByKind("nfe", Number(button.dataset.id));
            if (!invoice) {
                return;
            }
            openNfePdf(invoice);
        });
    });
}

function openNfeXml(invoice) {
    if (invoice.xml_url) {
        window.open(invoice.xml_url, "_blank", "noopener");
        return;
    }
    const xmlContent = invoice.xml_autorizado || invoice.xml_enviado;
    if (!xmlContent) {
        toast("Nenhum XML disponivel para esta NF-e.");
        return;
    }
    const blob = new Blob([xmlContent], { type: "application/xml;charset=utf-8" });
    downloadBlob(blob, buildNfeXmlFilename(invoice));
}

function openNfePdf(invoice) {
    if (!invoice.pdf_url) {
        toast("Nenhum DANFE disponivel para esta NF-e.");
        return;
    }
    window.open(invoice.pdf_url, "_blank", "noopener");
}

function buildNfeXmlFilename(invoice) {
    const customer = sanitizeFilenamePart(invoice?.cliente?.razao_social || "cliente");
    return `nfe_${invoice?.numero_nfe || invoice?.id || "arquivo"}_${customer}.xml`;
}

function renderSimplesNationalPanel() {
    const summaryTarget = document.getElementById("simples-summary-card");
    if (summaryTarget) {
        const summary = state.simplesSummary || {
            referencia: state.filters.simplesReferenceMonth || new Date().toISOString().slice(0, 7),
            faturamento_bruto: 0,
            aliquota_aplicada: 0,
            imposto_estimado: 0,
            notas_emitidas: 0,
            anexo: "-",
        };
        summaryTarget.innerHTML = `
            <div class="finance-insight-grid compact">
                <article class="finance-insight-card">
                    <span>Referencia</span>
                    <strong>${escapeHtml(summary.referencia || "-")}</strong>
                    <small>Anexo ${escapeHtml(summary.anexo || "-")}</small>
                </article>
                <article class="finance-insight-card">
                    <span>Faturamento bruto</span>
                    <strong>${formatCurrency(summary.faturamento_bruto || 0)}</strong>
                    <small>${summary.notas_emitidas || 0} NF-e emitida(s)</small>
                </article>
                <article class="finance-insight-card">
                    <span>Aliquota aplicada</span>
                    <strong>${escapeHtml(String(summary.aliquota_aplicada || 0))}%</strong>
                    <small>Imposto estimado ${formatCurrency(summary.imposto_estimado || 0)}</small>
                </article>
            </div>
        `;
    }

    const listTarget = document.getElementById("simples-config-list");
    if (listTarget) {
        if (!state.simplesConfigs.length) {
            listTarget.innerHTML = `<div class="empty-state">Nenhuma configuracao do Simples cadastrada.</div>`;
            return;
        }
        listTarget.innerHTML = state.simplesConfigs.map((item) => `
            <article class="finance-config-card">
                <div class="finance-config-card-header">
                    <strong>${escapeHtml(item.anexo || "Sem anexo")} | ${escapeHtml(String(item.aliquota))}%</strong>
                    ${badge(item.vigente ? "Vigente" : "Historico", item.vigente ? "" : "warn")}
                </div>
                <div class="origin-note">Faixa: ${formatCurrency(item.faixa_faturamento_inicio || 0)} ate ${item.faixa_faturamento_fim ? formatCurrency(item.faixa_faturamento_fim) : "sem limite"}</div>
                <div class="toolbar compact-toolbar">
                    <div class="toolbar-group">
                        <button type="button" class="btn btn-sm ghost-button edit-simples-config" data-id="${item.id}">Editar</button>
                    </div>
                </div>
            </article>
        `).join("");

        listTarget.querySelectorAll(".edit-simples-config").forEach((button) => {
            button.addEventListener("click", () => startEditingSimplesConfig(Number(button.dataset.id)));
        });
    }
}

function getFilteredFinanceEntries() {
    const search = (state.filters.financeSearch || "").trim().toLowerCase();
    const status = state.filters.financeStatus || "todos";
    const customerId = state.filters.financeCustomer || "";
    const startDate = state.filters.financeStartDate || "";
    const endDate = state.filters.financeEndDate || "";
    return state.finance.filter((item) => {
        const customerMatches = !customerId || String(item.cliente_id || "") === String(customerId);
        const statusMatches = status === "todos" || item.status === status;
        const dueDate = item.vencimento || "";
        const startMatches = !startDate || dueDate >= startDate;
        const endMatches = !endDate || dueDate <= endDate;
        const searchMatches = !search || [
            item.descricao,
            item.referencia,
            item.categoria,
            item.fornecedor_nome,
            item.nfe_id ? `nfe ${item.nfe_id}` : "",
        ]
            .filter(Boolean)
            .join(" ")
            .toLowerCase()
            .includes(search);
        return customerMatches && statusMatches && startMatches && endMatches && searchMatches;
    });
}

function getFilteredNfeInvoices() {
    const search = (state.filters.nfeSearch || "").trim().toLowerCase();
    const status = state.filters.nfeStatus || "todos";
    const customerId = state.filters.nfeCustomer || "";
    return state.nfeInvoices.filter((item) => {
        const statusMatches = status === "todos" || item.status === status;
        const customerMatches = !customerId || String(item.cliente_id || "") === String(customerId);
        const searchMatches = !search || [
            item.numero_nfe,
            item.cliente?.razao_social,
            item.finance_entry_id ? String(item.finance_entry_id) : "",
        ]
            .filter(Boolean)
            .join(" ")
            .toLowerCase()
            .includes(search);
        return statusMatches && customerMatches && searchMatches;
    });
}

function startEditingSimplesConfig(configId) {
    const form = document.getElementById("simples-config-form");
    const config = state.simplesConfigs.find((item) => item.id === configId);
    if (!form || !config) {
        return;
    }
    openFinanceView("relatorios");
    fillForm(form, {
        faixa_faturamento_inicio: config.faixa_faturamento_inicio,
        faixa_faturamento_fim: config.faixa_faturamento_fim || "",
        aliquota: config.aliquota,
        anexo: config.anexo || "",
        vigente: String(config.vigente),
        observacoes: config.observacoes || "",
    });
    form.dataset.editingId = String(config.id);
    const note = document.getElementById("simples-config-mode-note");
    if (note) {
        note.classList.remove("hidden");
        note.textContent = `Editando configuracao #${config.id}.`;
    }
}

function renderProviderCompanies() {
    const target = document.getElementById("provider-companies-table");
    if (!target) {
        return;
    }
    if (!hasPermission("provider_companies.manage")) {
        target.innerHTML = `<div class="empty-state">Disponivel apenas para usuarios com permissao de empresas prestadoras.</div>`;
        return;
    }
    setTableContent(
        "provider-companies-table",
        ["Empresa", "Hierarquia", "CNPJ", "Cidade", "Usuarios vinculados", "Acoes"],
        state.providerCompanies.map((item) => [
            item.nome_fantasia ? `${item.razao_social} (${item.nome_fantasia})` : item.razao_social,
            item.empresa_pai_nome ? `Filial de ${item.empresa_pai_nome}` : "Matriz/independente",
            item.cnpj,
            item.cidade ? `${item.cidade}/${item.estado || ""}` : "-",
            item.usuarios_vinculados_nomes?.length ? item.usuarios_vinculados_nomes.join(", ") : "Nenhum usuario",
            actionButtons("providerCompany", item.id),
        ]),
        "Nenhuma empresa prestadora cadastrada.",
        { nonSortableTargets: [5] },
    );
    bindEntityActions("providerCompany");
}

function renderUsers() {
    const target = document.getElementById("users-table");
    if (!target) {
        return;
    }
    if (!hasPermission("users.manage")) {
        target.innerHTML = `<div class="empty-state">Disponivel apenas para usuarios com permissao de gestao de usuarios.</div>`;
        return;
    }
    setTableContent(
        "users-table",
        ["Nome", "Usuario", "Empresa", "Perfil", "Status", "Acoes"],
        state.users.map((item) => [
            item.nome,
            item.username,
            item.empresa_prestadora_nome || "-",
            item.role,
            badge(item.is_active ? "Ativo" : "Inativo", item.is_active ? "" : "warn"),
            actionButtons("user", item.id),
        ]),
        "Nenhum usuario cadastrado.",
        { nonSortableTargets: [5] },
    );
    bindEntityActions("user");
}

function renderLicenses() {
    const target = document.getElementById("licenses-table");
    if (!target) {
        return;
    }
    if (!hasPermission("licenses.manage")) {
        target.innerHTML = `<div class="empty-state">Disponivel apenas para usuarios com permissao de licencas.</div>`;
        return;
    }
    setTableContent(
        "licenses-table",
        ["Descricao", "Empresa", "Inicio", "Fim", "Max usuarios", "Status", "Acoes"],
        state.licenses.map((item) => [
            item.descricao,
            item.empresa_prestadora_nome || "Global",
            formatDate(item.start_date),
            formatDate(item.end_date),
            String(item.max_users),
            badge(item.status, item.status === "ativa" ? "" : item.status === "suspensa" ? "warn" : "danger"),
            actionButtons("license", item.id),
        ]),
        "Nenhuma licenca cadastrada.",
        { nonSortableTargets: [6] },
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
    const contractDashboard = state.contractDashboard || { a_vencer: 0, vencidos: 0 };
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
    setText("widget-contracts-due-soon", String(contractDashboard.a_vencer || 0));
    setText("widget-contracts-overdue", String(contractDashboard.vencidos || 0));
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
    return hasPermission("finance.view");
}

function buildButtonHtml({
    label,
    variant = "secondary",
    type = "button",
    size = "",
    classes = "",
    dataAttributes = "",
    hidden = false,
    disabled = false,
}) {
    const classNames = ["btn"];
    if (size) {
        classNames.push(size);
    }
    if (variant === "primary") {
        classNames.push("btn-primary");
    } else if (variant === "success") {
        classNames.push("btn-success");
    } else if (variant === "danger") {
        classNames.push("btn-danger");
    } else if (variant === "warning") {
        classNames.push("btn-warning");
    } else {
        classNames.push("btn-default", "ghost-button");
    }
    if (classes) {
        classNames.push(classes);
    }
    if (hidden) {
        classNames.push("hidden");
    }
    return `<button type="${type}" class="${classNames.join(" ")}" ${dataAttributes}${disabled ? " disabled" : ""}>${escapeHtml(label)}</button>`;
}

function actionButton(className, label, dataAttributes = "") {
    const variant = className.includes("danger") ? "danger" : "secondary";
    return buildButtonHtml({
        label,
        variant,
        type: "button",
        size: "btn-sm",
        classes: `action-button ${className}`,
        dataAttributes,
    });
}

function actionButtons(kind, id, extraHtml = "") {
    const extraGroup = extraHtml ? `<div class="toolbar-group">${extraHtml}</div>` : "";
    return `
        <div class="toolbar compact-toolbar">
            ${extraGroup}
            <div class="toolbar-group">
                ${buildButtonHtml({ label: "Editar", variant: "secondary", type: "button", size: "btn-sm", classes: "action-button secondary edit-entity", dataAttributes: `data-kind=\"${kind}\" data-id=\"${id}\"` })}
                ${buildButtonHtml({ label: "Excluir", variant: "danger", type: "button", size: "btn-sm", classes: "action-button danger delete-entity", dataAttributes: `data-kind=\"${kind}\" data-id=\"${id}\"` })}
            </div>
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
        if (button.dataset.quickActionBound === "true") {
            return;
        }
        button.dataset.quickActionBound = "true";
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
        if (button.dataset.quickActionBound === "true") {
            return;
        }
        button.dataset.quickActionBound = "true";
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
        if (button.dataset.quickActionBound === "true") {
            return;
        }
        button.dataset.quickActionBound = "true";
        button.addEventListener("click", async () => {
            try {
                await apiFetch(`/api/v1/os/${button.dataset.id}/baixar`, { method: "POST" });
                await afterMutation("Ordem de servico baixada com sucesso.");
            } catch (error) {
                toast(error.message);
            }
        });
    });

    document.querySelectorAll(".reopen-work-order").forEach((button) => {
        if (button.dataset.quickActionBound === "true") {
            return;
        }
        button.dataset.quickActionBound = "true";
        button.addEventListener("click", async () => {
            try {
                await apiFetch(`/api/v1/os/${button.dataset.id}/reabrir`, { method: "POST" });
                await afterMutation("Ordem de servico reaberta com sucesso.");
            } catch (error) {
                toast(error.message);
            }
        });
    });

    document.querySelectorAll(".reprint-work-order").forEach((button) => {
        if (button.dataset.quickActionBound === "true") {
            return;
        }
        button.dataset.quickActionBound = "true";
        button.addEventListener("click", async () => {
            try {
                await print_order(button.dataset.id);
            } catch (error) {
                toast(error.message);
            }
        });
    });
}

function getEntityByKind(kind, id) {
    const collection = getEntityCollectionByKind(kind);
    return collection?.find((item) => item.id === id) || null;
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
    if (kind === "contract") {
        state.contractWorkspace.customerId = item.cliente_id;
        switchView("clientes");
        fillForm(form, {
            cliente_nome: item.cliente_nome || "",
            nome: item.nome,
            data_inicio: item.data_inicio,
            data_vencimento: item.data_vencimento,
            valor_mensal: item.valor_mensal ?? 0,
            tipo_cobranca: item.tipo_cobranca || "mensal",
            dia_vencimento: item.dia_vencimento || "",
            gerar_cobranca_automatica: String(Boolean(item.gerar_cobranca_automatica)),
            observacoes: item.observacoes || "",
        });
        const fileNote = document.getElementById("contract-file-note");
        if (fileNote) {
            fileNote.textContent = item.arquivo_nome_original
                ? `Arquivo atual: ${item.arquivo_nome_original}. Envie um novo arquivo apenas se quiser substituir o existente.`
                : "Nenhum arquivo anexado. Anexe PDF, DOC, DOCX, imagem ou TXT ate 10 MB.";
        }
        renderCustomerContractsWorkspace();
        return;
    }
    if (kind === "product") {
        fillForm(form, { ...item, override_tributacao: String(item.override_tributacao) });
        syncProductTaxFields();
        hideNcmLiveResults();
        return;
    }
    if (kind === "providerCompany") {
        fillForm(form, {
            ...item,
            is_active: String(item.is_active),
            is_provider: String(item.is_provider),
            compartilha_visualizacao_estoque: String(item.compartilha_visualizacao_estoque),
            empresa_pai_id: item.empresa_pai_id || "",
        });
        Array.from(form.querySelector('[name="usuarios_vinculados_ids"]').options).forEach((option) => {
            option.selected = (item.usuarios_vinculados_ids || []).includes(Number(option.value));
        });
        switchProviderCompanyTab(state.providerCompanyTab || "dados");
        renderProviderCompanyLicenseWorkspace();
        return;
    }
    if (kind === "finance") {
        openFinanceView("lancamentos");
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
    if (kind === "receipt") {
        openFinanceView("recibos");
        fillReceiptForm(item);
        return;
    }
    if (kind === "nfe") {
        clearNfeEmissionFeedback();
        state.nfeTab = "issue";
        openFinanceView("nfe");
        fillForm(form, {
            ...item,
            cliente_id: item.cliente_id || "",
            gerar_financeiro: item.finance_entry_id ? "true" : "false",
            observacoes: item.observacoes || "",
            natureza_operacao: "Venda",
            ambiente: item.ambiente || "homologacao",
            referencia_externa: item.referencia_externa || "",
        });
        fillNfeItemRowsFromInvoice(item);
        renderNfeEmissionWorkspace();
        return;
    }
    if (kind === "user") {
        fillForm(form, {
            ...item,
            empresa_prestadora_id: item.empresa_prestadora_id || "",
            is_active: String(item.is_active),
            password: "",
        });
        const permissions = getEffectivePermissions(item.role, item.permissions || {});
        Object.entries(permissions).forEach(([key, value]) => {
            const field = form.querySelector(`[name="permission_${CSS.escape(key)}"]`);
            if (field) {
                field.checked = Boolean(value);
                field.disabled = item.role === "master";
            }
        });
        form.querySelector('[name="password"]').required = false;
        return;
    }
    if (kind === "license") {
        fillForm(form, { ...item, empresa_prestadora_id: item.empresa_prestadora_id || "" });
        return;
    }
    if (kind === "appointment") {
        openAppointmentView("new");
        fillAppointmentForm(item);
        return;
    }
    if (kind === "workOrder") {
        clearWorkOrderSaveFeedback();
        openWorkOrderView("new");
        fillWorkOrderForm(item);
        return;
    }
    fillForm(form, item);
}

function resetFormMode(kind) {
    const wasEditing = Boolean(state.editing[kind]);
    state.editing[kind] = null;
    const form = document.getElementById(formIdForKind(kind));
    form.reset();
    form.querySelector(".form-error").classList.add("hidden");
    form.querySelector(`[data-cancel-button="${kind}"]`).classList.add("hidden");
    form.querySelector(`[data-save-button="${kind}"]`).textContent = saveLabelForKind(kind);
    const note = form.querySelector(`[data-mode-note="${kind}"]`);
    note.classList.add("hidden");
    note.textContent = "";
    if (kind === "contract") {
        const customer = getEntityByKind("customer", Number(state.contractWorkspace.customerId || 0));
        fillForm(form, {
            cliente_nome: customer?.razao_social || "",
            valor_mensal: 0,
            tipo_cobranca: "mensal",
            dia_vencimento: "",
            gerar_cobranca_automatica: "false",
        });
        const fileNote = document.getElementById("contract-file-note");
        if (fileNote) {
            fileNote.textContent = "Anexe PDF, DOC, DOCX, imagem ou TXT ate 10 MB.";
        }
    }
    if (kind === "workOrder") {
        clearWorkOrderForm();
        if (wasEditing) {
            openWorkOrderView("registered");
        }
    }
    if (kind === "nfe") {
        clearNfeEmissionFeedback();
        const list = document.getElementById("nfe-items-list");
        if (list) {
            list.innerHTML = "";
        }
        ensureNfeItemRows();
        renderNfeEmissionWorkspace();
    }
    if (kind === "appointment") {
        clearAppointmentForm();
        if (wasEditing) {
            openAppointmentView("operational");
        }
    }
    if (kind === "receipt") {
        clearReceiptForm();
        if (wasEditing) {
            openFinanceView("recibos");
        }
    }
    if (kind === "providerCompany") {
        state.providerCompanyTab = "dados";
        Array.from(form.querySelector('[name="usuarios_vinculados_ids"]').options).forEach((option) => {
            option.selected = false;
        });
        clearProviderCompanyLicenseForm();
        switchProviderCompanyTab("dados");
        renderProviderCompanyLicenseWorkspace();
    }
    if (kind === "user") {
        form.querySelector('[name="password"]').required = true;
        const roleField = form.querySelector('[name="role"]');
        if (roleField) {
            applyUserRolePermissionPreset(roleField.value, form);
        }
    }
    if (kind === "product") {
        syncProductTaxFields();
        updateProductTaxSourceNote("Sem NCM vinculado. Informe um NCM para preencher automaticamente as aliquotas.");
        hideNcmLiveResults();
    }
}

function formIdForKind(kind) {
    return {
        customer: "customer-form",
        contract: "contract-form",
        product: "product-form",
        pest: "pest-form",
        technician: "technician-form",
        finance: "finance-form",
        receipt: "receipt-form",
        nfe: "nfe-form",
        workOrder: "work-order-form",
        appointment: "appointment-form",
        providerCompany: "provider-company-form",
        user: "user-form",
        license: "license-form",
    }[kind];
}

function saveLabelForKind(kind) {
    return {
        customer: "Salvar cliente",
        contract: "Salvar contrato",
        product: "Salvar produto",
        pest: "Salvar praga",
        technician: "Salvar tecnico",
        finance: "Salvar lancamento",
        receipt: "Salvar recibo",
        nfe: state.sefazReadiness?.provider === "sefaz_direct" ? "Emitir NF-e" : "Salvar NF-e",
        workOrder: "Salvar ordem de servico",
        appointment: "Salvar agendamento",
        providerCompany: "Salvar empresa",
        user: "Salvar usuario",
        license: "Salvar licenca",
    }[kind];
}

function fillForm(form, data) {
    Object.entries(data).forEach(([key, value]) => {
        const field = form.querySelector(`[name="${key}"]`);
        if (field) {
            if (field.type === "checkbox") {
                field.checked = Boolean(value);
                return;
            }
            field.value = value ?? "";
        }
    });
}

function fillWorkOrderForm(item) {
    const form = document.getElementById("work-order-form");
    const linkedAppointment = state.appointments
        .filter((appointment) => appointment.os_id === item.id && !appointment.agendamento_pai_id)
        .sort((a, b) => b.id - a.id)[0] || null;
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
        tipo_os: item.tipo_os || "avulsa",
        valor_servico: item.valor_servico,
        observacoes: item.observacoes || "",
        gerar_financeiro: state.finance.some((entry) => entry.os_id === item.id) ? "true" : "false",
        gerar_agendamento: linkedAppointment ? "true" : "false",
        tipo_servico_agendamento: linkedAppointment?.tipo_servico || "",
        duracao_prevista_minutos: linkedAppointment?.duracao_prevista_minutos || 60,
        observacoes_internas_agendamento: linkedAppointment?.observacoes_internas || "",
        instrucoes_tecnicas_agendamento: linkedAppointment?.instrucoes_tecnicas || "",
        retorno_revisita_agendamento: linkedAppointment?.retorno_revisita || "",
        sincronizar_google_agenda: linkedAppointment?.sincronizar_google ? "true" : "false",
    });
    state.workOrderPicker.productSearch = "";
    state.workOrderPicker.pestSearch = "";
    state.workOrderPicker.stagedProductIds = [];
    state.workOrderPicker.stagedPestIds = [];
    state.workOrderPicker.selectedPestIds = item.pragas.map((pest) => pest.praga.id);
    document.getElementById("product-picker-search").value = "";
    document.getElementById("pest-picker-search").value = "";
    document.getElementById("products-list").innerHTML = "";
    item.produtos.forEach((product) => {
        addProductRow({
            produto_id: product.produto_id,
            quantidade: product.quantidade,
            diluicao: product.diluicao,
        });
    });
    renderWorkOrderSelectors();
    renderWorkOrderFormHeader();
}

function fillReceiptForm(item) {
    const form = document.getElementById("receipt-form");
    fillForm(form, {
        cliente_id: String(item.cliente_id),
        os_id: item.os_id ? String(item.os_id) : "",
        data_recebimento: item.data_recebimento,
        valor: item.valor,
        forma_pagamento: item.forma_pagamento,
        descricao: item.descricao || "",
    });
    syncReceiptWorkOrderOptions();
    if (item.os_id) {
        form.querySelector('[name="os_id"]').value = String(item.os_id);
    }
    state.receiptPreview = item;
    renderReceiptPreview(item);
}

function fillAppointmentForm(item) {
    const form = document.getElementById("appointment-form");
    fillForm(form, {
        cliente_id: String(item.cliente_id),
        os_id: item.os_id ? String(item.os_id) : "",
        tecnico_id: item.tecnico_id ? String(item.tecnico_id) : "",
        tipo_servico: item.tipo_servico,
        data_agendamento: item.data_agendamento,
        hora_agendamento: formatTime(item.hora_agendamento),
        duracao_prevista_minutos: item.duracao_prevista_minutos,
        status: item.status,
        origem: item.origem,
        sincronizar_google: item.sincronizar_google ? "true" : "false",
        enviar_whatsapp: true,
        observacoes: item.observacoes || "",
        observacoes_internas: item.observacoes_internas || "",
        instrucoes_tecnicas: item.instrucoes_tecnicas || "",
        retorno_revisita: item.retorno_revisita || "",
    });
    syncAppointmentWorkOrderOptions();
    if (item.os_id) {
        form.querySelector('[name="os_id"]').value = String(item.os_id);
    }
    renderAppointmentCustomerSummary();
    renderAppointmentFormHeader();
}

function fillNfeItemRowsFromInvoice(item) {
    const list = document.getElementById("nfe-items-list");
    if (!list) {
        return;
    }
    list.innerHTML = "";
    let payload = null;
    try {
        payload = item?.payload_enviado ? JSON.parse(item.payload_enviado) : null;
    } catch {
        payload = null;
    }
    const items = Array.isArray(payload?.itens) ? payload.itens : [];
    if (!items.length) {
        addNfeItemRow({
            descricao: item?.observacoes ? `Servico referente a ${item.numero_nfe}` : "",
            quantidade: "1",
            valor_unitario: item?.valor_total || "",
            ncm: "",
        });
        renderNfeEmissionWorkspace();
        return;
    }
    items.forEach((entry) => addNfeItemRow(entry));
    renderNfeEmissionWorkspace();
}

function renderWorkOrderFormHeader() {
    const title = document.getElementById("work-order-form-title");
    const description = document.getElementById("work-order-form-description");
    const numberDisplay = document.getElementById("work-order-number-display");
    if (!title || !description) {
        return;
    }

    if (state.editing.workOrder) {
        const current = getEntityByKind("workOrder", state.editing.workOrder);
        if (numberDisplay) {
            numberDisplay.textContent = current?.numero || "Numero indisponivel";
        }
        title.textContent = "Editar ordem de servico";
        description.textContent = current
            ? `Atualize a OS ${current.numero}, revise itens, status e anexos antes de salvar as alteracoes.`
            : "Atualize os dados operacionais, itens aplicados e fotos vinculadas a esta ordem de servico.";
        return;
    }

    if (numberDisplay) {
        numberDisplay.textContent = "Sera gerado automaticamente ao salvar";
    }
    title.textContent = "Nova ordem de servico";
    description.textContent = "Preencha os dados operacionais, produtos aplicados, status e anexos. O numero da OS sera gerado automaticamente em sequencia.";
}

function renderAppointmentFormHeader() {
    const title = document.getElementById("appointment-form-title");
    const description = document.getElementById("appointment-form-description");
    if (!title || !description) {
        return;
    }

    if (state.editing.appointment) {
        const current = getEntityByKind("appointment", state.editing.appointment);
        title.textContent = "Editar agendamento";
        description.textContent = current
            ? `Atualize o compromisso #${current.id}, o status operacional e a vinculacao com OS quando necessario.`
            : "Atualize data, horario, tecnico, status e observacoes do compromisso.";
        return;
    }

    title.textContent = "Novo agendamento";
    description.textContent = "Crie compromissos manuais ou vinculados a ordens de servico com historico e status operacionais.";
}

async function deleteEntity(kind, id) {
    const endpointMap = {
        customer: "/api/v1/clientes",
        contract: "/api/v1/contratos",
        product: "/api/v1/produtos",
        pest: "/api/v1/pragas",
        technician: "/api/v1/tecnicos",
        finance: "/api/v1/financeiro",
        receipt: "/api/v1/recibos",
        nfe: "/api/v1/nfe",
        workOrder: "/api/v1/os",
        providerCompany: "/api/v1/empresas-prestadoras",
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

function digitsOnly(value) {
    return String(value || "").replace(/\D+/g, "");
}

function formatCep(value) {
    const digits = digitsOnly(value);
    if (digits.length !== 8) {
        return value || "";
    }
    return `${digits.slice(0, 5)}-${digits.slice(5)}`;
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
