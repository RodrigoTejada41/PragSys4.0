from __future__ import annotations

import unicodedata
from typing import Iterable

from app.application.schemas import AssistantChatResponse
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


MODULE_TITLES = {
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

CONTEXT_GUIDES = {
    "estoque": (
        "O modulo Estoque concentra entradas, saidas, balanco, inventario, transferencias, importacoes e etiquetas.",
        [
            "Como cadastrar produto",
            "Como dar baixa no estoque",
            "Como fazer inventario",
        ],
    ),
    "ordens": (
        "Ordens de servico organiza a criacao da OS, preenchimento tecnico, produtos aplicados e geracao de documentos.",
        [
            "Como criar uma OS",
            "Como preencher a O.S.",
            "Como gerar certificado",
        ],
    ),
    "financeiro": (
        "Financeiro concentra lancamentos, recibos, fluxo de caixa e relatorios.",
        [
            "Como usar o financeiro",
            "Como emitir recibo",
            "Como ver fluxo de caixa",
        ],
    ),
    "clientes": (
        "Clientes guarda o cadastro principal e o contexto para contratos vinculados.",
        [
            "Como cadastrar cliente",
            "Como cadastrar contrato",
            "Como acompanhar vencimento de contrato",
        ],
    ),
    "configuracoes": (
        "Configuracoes centraliza dados tecnicos, certificados, molduras, backup e restauracao.",
        [
            "Como configurar responsavel tecnico",
            "Como anexar licencas",
            "Como gerar backup",
        ],
    ),
}

RESTRICTED_HELP = {
    "empresa prestadora": "Empresas prestadoras",
    "licenca": "Licencas",
}


ANSWER_BANK = {
    "cadastrar produto": (
        "Como cadastrar produto. Esse cadastro serve para registrar produtos usados no estoque, nas movimentacoes, no inventario e nas baixas de campo. Onde fica: Menu Produtos > Novo produto. Passo a passo: 1. Abra Produtos. 2. Clique em Novo produto. 3. Preencha nome, categoria, unidade e estoque minimo. 4. Salve o cadastro. Exemplo: Inseticida Premium | Unidade ML | Quantidade inicial 5000 | Estoque minimo 1000. Dica: se o produto for fracionado em atendimento, use a unidade correta para evitar erro na baixa. Proximo passo recomendado: registrar a entrada inicial no Estoque.",
        ["Como registrar entrada", "Como dar baixa no estoque", "Como usar QR Code ou codigo de barras"],
        "Produtos",
    ),
    "dar baixa no estoque": (
        "Como dar baixa no estoque. A baixa registra o consumo real do produto e atualiza o historico de rastreabilidade. Onde fica: Menu Estoque > Operacao. Passo a passo: 1. Abra Estoque > Operacao. 2. Escolha Saida. 3. Selecione ou leia o produto. 4. Informe quantidade, motivo e local fisico. 5. Confirme a movimentacao. Exemplo: baixa de 500 ML de inseticida usado em atendimento tecnico. Dica: descreva o motivo com clareza para facilitar auditoria. Proximo passo recomendado: revisar o historico e o saldo final do item.",
        ["Como registrar entrada", "Como fazer inventario", "Como transferir estoque"],
        "Estoque",
    ),
    "fazer inventario": (
        "Como fazer inventario. O inventario compara a contagem fisica com o saldo do sistema. Onde fica: Menu Estoque > Inventario. Passo a passo: 1. Abra Inventario. 2. Selecione empresa, armazem e local. 3. Inicie a sessao. 4. Leia ou selecione os produtos e informe as contagens. 5. Finalize para gerar divergencias. Exemplo: contagem do estoque do veiculo ao final do expediente. Dica: nao misture locais fisicos diferentes na mesma sessao. Proximo passo recomendado: usar o Balanco para ajustar diferencas com justificativa.",
        ["Como transferir estoque", "Como usar QR Code ou codigo de barras", "Como controlar unidade em ML, KG e UN"],
        "Estoque",
    ),
    "criar uma os": (
        "Como criar uma OS. Esse fluxo registra o atendimento tecnico e prepara os documentos vinculados. Onde fica: Menu Ordens de servico > Nova ordem de servico. Passo a passo: 1. Abra Nova ordem. 2. Selecione cliente e tecnico. 3. Informe data, local e horarios. 4. Preencha servico executado, orientacoes e observacoes. 5. Salve a ordem. Exemplo: OS de desinsetizacao com horario 08:00-09:30. Dica: informe horarios separados de inicio e fim. Proximo passo recomendado: adicionar produtos usados e gerar os documentos da ordem.",
        ["Como preencher a O.S.", "Como gerar certificado", "Como gerar relatorio"],
        "Ordens de servico",
    ),
    "preencher a o.s.": (
        "Como preencher a O.S.. O preenchimento correto evita retrabalho e bloqueio documental. Onde fica: dentro do formulario da ordem de servico. Passo a passo: 1. Revise cliente e endereco. 2. Confirme tecnico e horarios. 3. Descreva o servico executado. 4. Inclua orientacoes e observacoes tecnicas. 5. Salve e revise a ordem cadastrada. Exemplo: aplicacao interna com orientacao para nao limpar a area tratada por 24 horas. Dica: nao deixe observacoes tecnicas vazias quando houve condicao especial no atendimento. Proximo passo recomendado: gerar relatorio tecnico e certificado.",
        ["Como gerar certificado", "Como gerar moldura", "Como finalizar atendimento"],
        "Ordens de servico",
    ),
    "gerar certificado": (
        "Como gerar certificado. O certificado usa os dados tecnicos configurados pela empresa e a ordem salva. Onde fica: na OS cadastrada, apos salvar a ordem. Passo a passo: 1. Salve a OS. 2. Abra a ordem cadastrada. 3. Clique em Certificado. 4. Revise o documento gerado. 5. Imprima ou compartilhe. Exemplo: certificado com assinatura, licencas e CIT. Dica: se houver bloqueio, revise Configuracoes > Dados tecnicos / Empresa. Proximo passo recomendado: validar relatorio tecnico ou moldura, se fizer parte do fluxo.",
        ["Como gerar moldura", "Como configurar responsavel tecnico", "Como anexar licencas"],
        "Ordens de servico",
    ),
    "usar o financeiro": (
        "Como usar o financeiro. Esse modulo organiza lancamentos, recibos, fluxo de caixa e relatorios. Onde fica: Menu Financeiro. Passo a passo: 1. Abra Financeiro. 2. Escolha a pagina adequada: Lancamentos, Recibos, Caixa ou Relatorios. 3. Registre ou consulte os dados do periodo. 4. Revise status, categoria e origem antes de salvar. Exemplo: lancamento de receita e emissao do recibo correspondente. Dica: mantenha a origem e a categoria coerentes para melhorar os relatorios. Proximo passo recomendado: se precisar de comprovante, siga para Recibos.",
        ["Como emitir recibo", "Como ver fluxo de caixa", "Como acompanhar vencimento de contrato"],
        "Financeiro",
    ),
    "cadastrar contrato": (
        "Como cadastrar contrato. O contrato organiza vigencia, cobranca e recorrencia do cliente. Onde fica: Menu Clientes > selecione o cliente > Contratos. Passo a passo: 1. Selecione o cliente. 2. Abra a area de contratos. 3. Preencha vigencia, valor e tipo de cobranca. 4. Salve o contrato. Exemplo: contrato mensal com cobranca automatica no dia 10. Dica: revise datas de inicio e fim para evitar contratos ativos fora da vigencia. Proximo passo recomendado: acompanhar vencimentos e lancamentos financeiros vinculados.",
        ["Como acompanhar vencimento de contrato", "Como usar o financeiro", "Como cadastrar cliente"],
        "Contratos",
    ),
    "responsavel tecnico": (
        "Como configurar responsavel tecnico. Esse cadastro institucional libera OS, relatorios e certificados. Onde fica: Menu Configuracoes > Dados tecnicos / Empresa. Passo a passo: 1. Abra Configuracoes. 2. Preencha nome do responsavel, conselho, numero e UF. 3. Salve a configuracao. Exemplo: Dra. Marina Campos | CRBio | 123456 | SP. Dica: mantenha o registro sempre atualizado. Proximo passo recomendado: subir assinatura e anexar as licencas da empresa.",
        ["Como anexar licencas", "Como gerar certificado", "Como gerar moldura"],
        "Configuracoes",
    ),
    "anexar licencas": (
        "Como anexar licencas. O sistema usa as licencas sanitaria e ambiental nos documentos tecnicos. Onde fica: Menu Configuracoes > Dados tecnicos / Empresa. Passo a passo: 1. Abra Configuracoes. 2. Localize os uploads das licencas. 3. Envie os arquivos corretos. 4. Revise os dados extraidos do PDF, quando existirem. 5. Salve a configuracao. Exemplo: licenca ambiental em PDF com numero e validade extraidos. Dica: se algum dado nao vier no PDF, complete manualmente. Proximo passo recomendado: gerar um certificado ou relatorio para validar o resultado.",
        ["Como configurar responsavel tecnico", "Como gerar backup", "Como restaurar backup"],
        "Configuracoes",
    ),
    "gerar backup": (
        "Como gerar backup. O backup cria uma copia de seguranca do banco antes de mudancas importantes. Onde fica: Menu Configuracoes > Manutencao do banco. Passo a passo: 1. Abra Configuracoes. 2. Va para manutencao do banco. 3. Clique em backup. 4. Baixe e guarde o arquivo. Exemplo: backup feito antes de deploy ou restauracao. Dica: sempre gere backup antes de qualquer acao destrutiva. Proximo passo recomendado: se precisar recuperar dados, use o fluxo de restauracao com confirmacao.",
        ["Como restaurar backup", "Como usar configuracoes", "Como controlar permissoes de usuario"],
        "Configuracoes",
    ),
    "restaurar backup": (
        "Como restaurar backup. A restauracao substitui o estado atual por uma copia valida do banco. Onde fica: Menu Configuracoes > Manutencao do banco. Passo a passo: 1. Abra Configuracoes. 2. Localize a opcao de restaurar backup. 3. Selecione o arquivo. 4. Digite a confirmacao exigida. 5. Aguarde o processo finalizar. Exemplo: restauracao de base homologada em ambiente de desenvolvimento. Dica: nunca restaure sem ter um backup atual do estado que sera substituido. Proximo passo recomendado: validar login, health e os modulos principais.",
        ["Como gerar backup", "Como usar configuracoes", "Como acompanhar vencimento de contrato"],
        "Configuracoes",
    ),
    "controlar permissoes de usuario": (
        "Como controlar permissoes de usuario. O sistema usa nivel de acesso e permissoes granulares. Onde fica: Menu Usuarios. Passo a passo: 1. Abra Usuarios. 2. Escolha o nivel principal. 3. Vincule a empresa. 4. Marque apenas as permissoes necessarias. 5. Salve e teste o usuario. Exemplo: Admin da empresa com acesso operacional amplo, mas sem empresas prestadoras e licencas globais. Dica: prefira o menor privilegio necessario. Proximo passo recomendado: validar se o menu exibido corresponde as permissoes configuradas.",
        ["Como cadastrar usuario", "Como cadastrar empresa prestadora", "Como usar configuracoes"],
        "Usuarios",
    ),
}


def _resolve_module(current_view: str | None) -> str:
    normalized_view = (current_view or "dashboard").strip().lower()
    return VIEW_TO_MODULE.get(normalized_view, "dashboard")


def build_assistant_reply(current_user: User, message: str | None, current_view: str | None, current_title: str | None = None) -> AssistantChatResponse:
    normalized_message = _normalize_text(message)
    module_key = _resolve_module(current_view)
    current_module = MODULE_TITLES.get(module_key, "Ajuda do sistema")
    context_overview, context_suggestions = CONTEXT_GUIDES.get(
        module_key,
        ("Escolha um dos modulos da central de ajuda para aprender o fluxo correspondente ao sistema.", ["Estoque", "Ordem de Servico", "Configuracoes"]),
    )

    if not normalized_message:
        answer = (
            f"Estou olhando a tela {current_module}"
            f"{f' ({current_title})' if current_title else ''}. "
            f"{context_overview} Seu perfil atual e {str(current_user.role).upper()} e eu vou priorizar apenas recursos compativeis com esse acesso."
        )
        return AssistantChatResponse(
            answer=answer,
            current_module=current_module,
            current_view=current_view,
            suggestions=context_suggestions,
        )

    if current_user.role != "master":
        for keyword, label in RESTRICTED_HELP.items():
            if keyword in normalized_message:
                return AssistantChatResponse(
                    answer=(
                        f"Seu perfil atual nao tem permissao para operar {label}. "
                        f"Eu posso te orientar nos modulos liberados ao seu acesso, sem inventar rotinas fora do seu escopo."
                    ),
                    current_module=current_module,
                    current_view=current_view,
                    suggestions=context_suggestions,
                )

    best_key = None
    best_score = 0
    for key in ANSWER_BANK:
        score = sum(1 for token in normalized_message.split() if token in key)
        if score > best_score:
            best_key = key
            best_score = score

    if not best_key:
        answer = (
            f"Nao encontrei um topico especifico para essa pergunta, mas posso te ajudar pelo contexto atual. "
            f"{context_overview}"
        )
        return AssistantChatResponse(
            answer=answer,
            current_module=current_module,
            current_view=current_view,
            suggestions=context_suggestions,
        )

    answer, suggestions, module_title = ANSWER_BANK[best_key]
    return AssistantChatResponse(
        answer=answer,
        current_module=module_title,
        current_view=current_view,
        suggestions=_dedupe_preserve_order(suggestions)[:3],
    )
