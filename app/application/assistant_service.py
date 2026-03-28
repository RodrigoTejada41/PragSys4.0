from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Iterable

from app.application.schemas import AssistantChatResponse
from app.core.permissions import has_permission
from app.infrastructure.models import User


def _normalize_text(value: str | None) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return "".join(char for char in normalized if not unicodedata.combining(char)).strip().lower()


def _dedupe_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


MODULE_LABELS = {
    "dashboard": "Dashboard",
    "clientes": "Clientes",
    "produtos": "Produtos",
    "estoque": "Estoque",
    "ordens": "Ordens de servico",
    "agenda": "Agenda",
    "financeiro": "Financeiro",
    "configuracoes": "Configuracoes",
    "usuarios": "Usuarios",
    "empresas": "Empresas prestadoras",
    "licencas": "Licencas",
}


VIEW_TO_MODULE = {
    "dashboard": "dashboard",
    "clientes": "clientes",
    "produtos": "produtos",
    "estoque": "estoque",
    "estoque-importacoes": "estoque",
    "estoque-estrutura": "estoque",
    "estoque-balanco": "estoque",
    "estoque-inventario": "estoque",
    "estoque-etiquetas": "estoque",
    "estoque-transferencias": "estoque",
    "ordens": "ordens",
    "ordens-nova": "ordens",
    "ordens-cadastradas": "ordens",
    "agenda": "agenda",
    "agenda-novo": "agenda",
    "agenda-operacional": "agenda",
    "financeiro": "financeiro",
    "financeiro-lancamentos": "financeiro",
    "financeiro-recibos": "financeiro",
    "financeiro-nfe": "financeiro",
    "financeiro-caixa": "financeiro",
    "financeiro-relatorios": "financeiro",
    "configuracoes": "configuracoes",
    "usuarios": "usuarios",
    "empresas": "empresas",
    "licencas": "licencas",
}


MODULE_REQUIREMENTS = {
    "dashboard": (),
    "clientes": ("customers.view",),
    "produtos": ("stock.manage",),
    "estoque": ("stock.view",),
    "ordens": ("work_orders.view",),
    "agenda": ("appointments.view",),
    "financeiro": ("finance.view",),
    "configuracoes": ("settings.view",),
    "usuarios": ("users.manage",),
    "empresas": ("provider_companies.manage",),
    "licencas": ("licenses.manage",),
}


MODULE_SUGGESTIONS = {
    "dashboard": [
        "O que eu consigo acompanhar neste dashboard?",
        "Como checar pendencias rapidamente?",
        "Quais atalhos voce recomenda para comecar o dia?",
    ],
    "clientes": [
        "Como cadastrar um novo cliente?",
        "Como vincular contrato a um cliente?",
        "Quais dados sao obrigatorios no cadastro?",
    ],
    "produtos": [
        "Como cadastrar um produto corretamente?",
        "Qual a diferenca entre produtos e estoque?",
        "Como definir unidade de medida e estoque minimo?",
    ],
    "estoque": [
        "Como dar baixa no estoque?",
        "Como importar uma planilha de estoque?",
        "Como fazer balanco ou inventario?",
    ],
    "ordens": [
        "Como criar uma OS?",
        "Como gerar certificado e relatorio tecnico?",
        "Quais campos revisar antes de concluir a OS?",
    ],
    "agenda": [
        "Como criar um agendamento?",
        "Como reagendar um atendimento?",
        "Como acompanhar a agenda operacional?",
    ],
    "financeiro": [
        "Como lancar uma receita ou despesa?",
        "Como emitir recibo?",
        "Como verificar o fluxo de caixa?",
    ],
    "configuracoes": [
        "Quais dados tecnicos preciso configurar?",
        "Como subir licencas e assinatura?",
        "Como evitar bloqueio na geracao de documentos?",
    ],
    "usuarios": [
        "Como cadastrar um usuario com permissoes?",
        "Qual a diferenca entre Master, Admin e Operador?",
        "Como vincular um usuario a empresa correta?",
    ],
    "empresas": [
        "Como cadastrar uma empresa prestadora?",
        "Como funciona matriz e filial no sistema?",
        "Quando ativar compartilhamento visual de estoque?",
    ],
    "licencas": [
        "Como cadastrar uma licenca do sistema?",
        "Como validar periodo e limite de usuarios?",
        "Quem pode gerenciar licencas?",
    ],
}


@dataclass(frozen=True)
class ModuleGuide:
    label: str
    overview: str
    actions: tuple[str, ...]
    best_practice: str


MODULE_GUIDES = {
    "dashboard": ModuleGuide(
        label="Dashboard",
        overview="Aqui voce acompanha indicadores operacionais, estoque em alerta, financeiro pendente e atalhos para os modulos mais usados.",
        actions=(
            "Revisar alertas de estoque e pendencias financeiras logo no inicio do expediente.",
            "Usar os atalhos do painel para abrir diretamente a area operacional que precisa de acao.",
            "Conferir contratos e agendamentos proximos antes de distribuir a equipe.",
        ),
        best_practice="Use o dashboard como triagem rapida, mas execute cada acao no modulo proprio para manter o fluxo organizado.",
    ),
    "clientes": ModuleGuide(
        label="Clientes",
        overview="No modulo Clientes voce registra cadastro completo e gerencia contratos vinculados sem misturar isso com OS ou financeiro.",
        actions=(
            "Preencha razao social, documento, telefone e endereco antes de salvar.",
            "Selecione o cliente na base para cadastrar ou acompanhar contratos vinculados.",
            "Revise cidade, estado e contato principal para evitar erro em agenda e documentos.",
        ),
        best_practice="Mantenha CPF/CNPJ e endereco sempre atualizados, porque esses dados reaparecem em OS, recibos e relatorios.",
    ),
    "produtos": ModuleGuide(
        label="Produtos",
        overview="Produtos guarda o catalogo tecnico e fiscal. O saldo e as movimentacoes ficam no modulo Estoque.",
        actions=(
            "Cadastre nome, categoria, unidade de medida, registro e estoque minimo.",
            "Use este cadastro para preparar itens que depois serao movimentados no estoque.",
            "Revise codigo de barras, QR Code e dados fiscais antes de usar o produto em OS ou NF-e.",
        ),
        best_practice="Evite usar o cadastro de produtos para operacao diaria; a movimentacao correta deve acontecer no modulo Estoque.",
    ),
    "estoque": ModuleGuide(
        label="Estoque",
        overview="O modulo Estoque concentra entradas, saidas, ajustes, importacoes, balanco, inventario, etiquetas e transferencias por empresa.",
        actions=(
            "Para dar baixa, abra Estoque > Operacao, escolha Saida, informe produto, quantidade e motivo.",
            "Para inventario, use a pagina Inventario e registre leituras continuas por armazem/local.",
            "Para cargas em massa, use Importacoes com CSV, XLSX ou XML e revise o log antes de concluir.",
        ),
        best_practice="Sempre informe motivo e local fisico. Isso melhora a rastreabilidade e evita divergencia entre saldo e historico.",
    ),
    "ordens": ModuleGuide(
        label="Ordens de servico",
        overview="Em Ordens de servico voce cria novas OS, consulta as registradas e gera documentos tecnicos vinculados.",
        actions=(
            "Use Nova ordem para preencher cliente, tecnico, execucao, produtos aplicados e observacoes.",
            "Depois de salvar, gere OS, relatorio tecnico e certificado diretamente a partir da ordem.",
            "Use Ordens cadastradas para pesquisar por cliente, numero, data e status.",
        ),
        best_practice="Antes de emitir documentos, confira configuracoes tecnicas da empresa, assinatura e licencas.",
    ),
    "agenda": ModuleGuide(
        label="Agenda",
        overview="A Agenda separa o cadastro de novos agendamentos da operacao diaria para facilitar confirmacao, reagendamento e acompanhamento.",
        actions=(
            "Use Novo agendamento para criar compromissos vinculados a cliente, tecnico e OS quando existir.",
            "Use Agenda operacional para filtrar por status, tecnico e periodo.",
            "Revise envio de WhatsApp e sincronizacao Google antes de salvar um agendamento critico.",
        ),
        best_practice="Confirme data, hora e tecnico antes de salvar para reduzir retrabalho e mensagens indevidas ao cliente.",
    ),
    "financeiro": ModuleGuide(
        label="Financeiro",
        overview="O modulo Financeiro organiza lancamentos, recibos, NF-e, fluxo de caixa e relatorios financeiros em paginas separadas.",
        actions=(
            "Abra Lancamentos para registrar receitas e despesas.",
            "Use Recibos para emitir comprovantes vinculados ao cliente e a OS quando necessario.",
            "Consulte Fluxo de caixa e Relatorios para apoiar fechamento e acompanhamento.",
        ),
        best_practice="Mantenha origem e categoria corretas nos lancamentos para que relatorios e resumo mensal fiquem confiaveis.",
    ),
    "configuracoes": ModuleGuide(
        label="Configuracoes",
        overview="Configuracoes centraliza dados institucionais, documentos tecnicos, integracoes, e manutencao controlada do sistema.",
        actions=(
            "Preencha dados da empresa, responsavel tecnico, registro, licencas e CIT.",
            "Suba licenca sanitaria, licenca ambiental e assinatura para liberar documentos.",
            "Revise integracoes e parametros antes de mexer em processos que impactam operacao.",
        ),
        best_practice="Use esta area como cadastro institucional. Alteracoes aqui afetam OS, relatorios tecnicos, certificados e integrações.",
    ),
    "usuarios": ModuleGuide(
        label="Usuarios",
        overview="No modulo Usuarios voce gerencia nivel de acesso, permissoes granulares e empresa vinculada de cada usuario.",
        actions=(
            "Defina o nivel principal do usuario: Master, Admin, Operador ou Gestor de estoque.",
            "Ajuste checkboxes de permissao para liberar somente os modulos necessarios.",
            "Sempre vincule o usuario a uma empresa prestadora valida antes de salvar.",
        ),
        best_practice="Prefira liberar apenas o necessario. Isso reduz erro operacional e protege dados entre empresas.",
    ),
    "empresas": ModuleGuide(
        label="Empresas prestadoras",
        overview="Empresas prestadoras organiza multiempresa, matriz/filial e compartilhamento controlado de visao de estoque.",
        actions=(
            "Cadastre a empresa como prestadora antes de cadastrar usuarios vinculados.",
            "Use a relacao matriz/filial somente quando houver compartilhamento administrativo real.",
            "Ative compartilhamento de visualizacao de estoque apenas quando a regra operacional pedir.",
        ),
        best_practice="Nao use esta area para clientes atendidos. Ela e exclusiva para empresas prestadoras do proprio sistema.",
    ),
    "licencas": ModuleGuide(
        label="Licencas",
        overview="Licencas controla vigencia, limite de usuarios e status do acesso do sistema por empresa.",
        actions=(
            "Cadastre descricao, periodo de vigencia, status e limite de usuarios.",
            "Associe a licenca a empresa correta quando a operacao for multiempresa.",
            "Revise vigencia antes de onboarding ou renovacao para evitar bloqueio indevido.",
        ),
        best_practice="Mantenha datas e status consistentes, porque o sistema valida acesso com base nessa informacao.",
    ),
}


def _resolve_module(current_view: str | None) -> str:
    normalized_view = (current_view or "dashboard").strip().lower()
    return VIEW_TO_MODULE.get(normalized_view, "dashboard")


def _user_can_access_module(current_user: User, module_key: str) -> bool:
    if current_user.role == "master":
        return True
    requirements = MODULE_REQUIREMENTS.get(module_key, ())
    if not requirements:
        return True
    permissions = getattr(current_user, "permissions", None)
    return all(has_permission(current_user.role, permissions, permission) for permission in requirements)


def _available_module_labels(current_user: User) -> list[str]:
    visible = [
        label
        for key, label in MODULE_LABELS.items()
        if _user_can_access_module(current_user, key)
    ]
    return visible[:6]


def _permission_guidance(current_user: User) -> str:
    if current_user.role == "master":
        return "Seu perfil MASTER tem acesso completo ao sistema, inclusive empresas prestadoras, licencas e configuracoes sensiveis."
    if current_user.role == "admin":
        return "Seu perfil ADMIN opera no escopo da empresa vinculada. Voce pode gerenciar operacao, usuarios da sua empresa e configuracoes permitidas, mas nao gerencia empresas prestadoras nem licencas globais."
    if current_user.role == "gestor_estoque":
        return "Seu perfil Gestor de estoque prioriza cadastro de produtos, movimentacoes, inventario e importacoes dentro da empresa vinculada."
    return "Seu perfil OPERADOR trabalha no escopo da empresa vinculada e depende das permissoes liberadas para cada modulo."


def _format_module_help(module_key: str, current_user: User) -> tuple[str, list[str]]:
    guide = MODULE_GUIDES[module_key]
    allowed = _user_can_access_module(current_user, module_key)
    suggestions = MODULE_SUGGESTIONS.get(module_key, [])[:3]
    if not allowed:
        available = ", ".join(_available_module_labels(current_user)) or "modulos liberados ao seu perfil"
        answer = (
            f"Voce esta na area {guide.label}, mas o seu perfil atual nao tem permissao para operar este modulo. "
            f"{_permission_guidance(current_user)} Hoje eu consigo te orientar melhor nos modulos liberados: {available}."
        )
        return answer, suggestions

    bullet_steps = " ".join(f"{index}. {step}" for index, step in enumerate(guide.actions, start=1))
    answer = f"{guide.overview} Passo a passo sugerido: {bullet_steps} Boas praticas: {guide.best_practice}"
    return answer, suggestions


def _answer_stock_question(message: str, current_user: User) -> tuple[str, list[str]]:
    if not _user_can_access_module(current_user, "estoque"):
        return _format_module_help("estoque", current_user)

    if "invent" in message:
        return (
            "Para inventario, abra Estoque > Inventario, escolha empresa, armazem e local, inicie a sessao e registre as leituras dos produtos. Ao finalizar, o sistema compara quantidade contada com saldo do sistema e gera as divergencias para ajuste.",
            ["Como fazer balanco de estoque?", "Como ler codigo no inventario?", "Como ver o historico de movimentacoes?"],
        )
    if "import" in message or "planilha" in message or "xml" in message or "csv" in message or "xlsx" in message:
        return (
            "Para importar estoque, abra Estoque > Importacoes, selecione o arquivo CSV, XLSX ou XML, revise os erros retornados e confirme apenas depois de validar empresa, produto, unidade e quantidade. O sistema grava log da importacao para auditoria.",
            ["Posso cadastrar produto automaticamente na importacao?", "Como corrigir erro de importacao?", "Como baixar o modelo da planilha?"],
        )
    if "transfer" in message:
        return (
            "Para transferir estoque, use Estoque > Transferencias, selecione origem e destino, leia ou escolha o produto, informe a quantidade e confirme. O saldo nao e somado entre unidades: cada empresa e local mantem rastreabilidade propria.",
            ["Como configurar armazens e locais?", "Como funciona transferencia entre filiais?", "Como consultar historico de transferencias?"],
        )
    if "balanc" in message or "ajuste" in message:
        return (
            "Para balanco, abra Estoque > Balanco, selecione o produto, informe saldo contado e justificativa. O sistema registra saldo anterior, saldo final, usuario, data e motivo do ajuste para auditoria.",
            ["Como abrir um inventario?", "Como dar entrada ou saida manual?", "Como ver quem fez o ajuste?"],
        )
    return (
        "Para dar baixa no estoque, siga este fluxo: 1. Abra Estoque > Operacao. 2. Escolha Saida. 3. Selecione ou leia o produto. 4. Informe quantidade, motivo e local fisico. 5. Confirme para atualizar saldo e historico. Se preferir, eu posso te orientar em importacao, balanco, inventario ou transferencias.",
        ["Como fazer balanco de estoque?", "Como importar planilha de estoque?", "O que posso fazer nesta tela?"],
    )


def _answer_work_order_question(message: str, current_user: User) -> tuple[str, list[str]]:
    if not _user_can_access_module(current_user, "ordens"):
        return _format_module_help("ordens", current_user)

    if "certificado" in message or "relatorio" in message:
        return (
            "Depois de salvar a OS, abra a ordem cadastrada e gere OS, relatorio tecnico ou certificado. Antes disso, revise em Configuracoes os dados tecnicos da empresa, assinatura, licenca sanitaria, licenca ambiental e CIT, porque o sistema bloqueia documentos incompletos.",
            ["Como criar uma OS?", "Quais dados tecnicos sao obrigatorios?", "Como revisar OS cadastradas?"],
        )
    return (
        "Para criar uma OS, use Ordens de servico > Nova ordem, preencha cliente, tecnico, data, horarios, local de execucao, produtos aplicados e observacoes. Salve primeiro; depois gere OS, relatorio tecnico e certificado pela ordem cadastrada.",
        ["Como gerar certificado e relatorio tecnico?", "Quais campos revisar antes de concluir a OS?", "Como pesquisar OS cadastradas?"],
    )


def _answer_finance_question(current_user: User) -> tuple[str, list[str]]:
    if not _user_can_access_module(current_user, "financeiro"):
        return _format_module_help("financeiro", current_user)
    return (
        "No Financeiro voce trabalha em paginas separadas: Lancamentos para receitas e despesas, Recibos para comprovantes, NF-e para emissao fiscal, Fluxo de caixa para acompanhamento e Relatorios para consolidacao. Comece sempre pela pagina que corresponde ao tipo de registro que voce precisa gerar.",
        ["Como lancar uma receita?", "Como emitir um recibo?", "Como verificar fluxo de caixa?"],
    )


def _answer_settings_question(current_user: User) -> tuple[str, list[str]]:
    if not _user_can_access_module(current_user, "configuracoes"):
        return _format_module_help("configuracoes", current_user)
    return (
        "Em Configuracoes, priorize Dados tecnicos / Empresa: responsavel tecnico, conselho, numero e UF do registro, licenca sanitaria, licenca ambiental, assinatura e CIT. Esses dados alimentam OS, relatorios tecnicos e certificados automaticamente.",
        ["Como subir licencas e assinatura?", "Por que um documento foi bloqueado?", "Quais dados tecnicos sao obrigatorios?"],
    )


def build_assistant_reply(
    current_user: User,
    message: str | None,
    current_view: str | None,
    current_title: str | None = None,
) -> AssistantChatResponse:
    normalized_message = _normalize_text(message)
    module_key = _resolve_module(current_view)
    current_module_label = MODULE_GUIDES[module_key].label
    suggestions = MODULE_SUGGESTIONS.get(module_key, MODULE_SUGGESTIONS["dashboard"])[:3]

    if not normalized_message:
        answer, suggestions = _format_module_help(module_key, current_user)
        answer = (
            f"Estou olhando a tela {current_module_label}"
            f"{f' ({current_title})' if current_title else ''}. "
            f"{answer} {_permission_guidance(current_user)}"
        )
        return AssistantChatResponse(
            answer=answer,
            current_module=current_module_label,
            current_view=current_view,
            suggestions=suggestions,
        )

    if any(term in normalized_message for term in ("permiss", "perfil", "acesso")):
        answer = _permission_guidance(current_user)
        suggestions = ["O que posso fazer nesta tela?", "Quais modulos meu perfil acessa?", "Como cadastrar um usuario?"]
    elif "estoque" in normalized_message or "baixa" in normalized_message or "inventario" in normalized_message:
        answer, suggestions = _answer_stock_question(normalized_message, current_user)
    elif "os" in normalized_message or "ordem" in normalized_message or "certificado" in normalized_message:
        answer, suggestions = _answer_work_order_question(normalized_message, current_user)
    elif "finance" in normalized_message or "recibo" in normalized_message or "caixa" in normalized_message:
        answer, suggestions = _answer_finance_question(current_user)
    elif "configur" in normalized_message or "licenca" in normalized_message or "cit" in normalized_message:
        answer, suggestions = _answer_settings_question(current_user)
    elif any(term in normalized_message for term in ("usuario", "permissao", "master", "admin", "operador")):
        answer, suggestions = _format_module_help("usuarios", current_user)
    elif any(term in normalized_message for term in ("empresa", "matriz", "filial")):
        answer, suggestions = _format_module_help("empresas", current_user)
    elif any(term in normalized_message for term in ("cliente", "contrato")):
        answer, suggestions = _format_module_help("clientes", current_user)
    elif any(term in normalized_message for term in ("relatorio", "dashboard", "atalho")):
        answer, suggestions = _format_module_help(module_key, current_user)
    elif any(term in normalized_message for term in ("o que posso fazer", "onde estou", "nesta tela", "nessa tela", "me guie")):
        answer, suggestions = _format_module_help(module_key, current_user)
    else:
        answer, suggestions = _format_module_help(module_key, current_user)
        answer = (
            f"Baseado no sistema real, aqui esta a orientacao mais segura para a tela atual. "
            f"{answer} Se voce quiser, posso te responder passo a passo em um fluxo especifico."
        )

    return AssistantChatResponse(
        answer=answer,
        current_module=current_module_label,
        current_view=current_view,
        suggestions=_dedupe_preserve_order(suggestions)[:3],
    )
