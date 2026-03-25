from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Iterable, Optional, Union
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session, joinedload

from app.application.schemas import (
    AppointmentCreate,
    AppointmentDashboardRead,
    AppointmentStatusUpdate,
    AppointmentUpdate,
)
from app.application.google_calendar_service import google_calendar_request
from app.core.config import get_settings
from app.core.exceptions import BusinessRuleViolation
from app.domain.enums import AppointmentSource, AppointmentStatus, GoogleSyncStatus, WorkOrderStatus
from app.infrastructure.models import Appointment, AppointmentHistory, AppointmentWhatsAppLog, Customer, Technician, User, WorkOrder

ACTIVE_APPOINTMENT_STATUSES = {
    AppointmentStatus.PENDENTE.value,
    AppointmentStatus.CONFIRMADO.value,
    AppointmentStatus.EM_DESLOCAMENTO.value,
    AppointmentStatus.EM_ATENDIMENTO.value,
}

FINISHED_APPOINTMENT_STATUSES = {
    AppointmentStatus.CONCLUIDO.value,
    AppointmentStatus.REAGENDADO.value,
    AppointmentStatus.CANCELADO.value,
    AppointmentStatus.NAO_REALIZADO.value,
}


def _appointment_query(db: Session):
    return db.query(Appointment).options(
        joinedload(Appointment.cliente),
        joinedload(Appointment.ordem_servico),
        joinedload(Appointment.tecnico),
        joinedload(Appointment.usuario_responsavel),
        joinedload(Appointment.usuario_ultima_atualizacao),
        joinedload(Appointment.historico).joinedload(AppointmentHistory.usuario),
        joinedload(Appointment.whatsapp_logs).joinedload(AppointmentWhatsAppLog.usuario),
    )


def _clean_required_text(value: Optional[str], message: str) -> str:
    cleaned = " ".join(str(value or "").split()).strip()
    if not cleaned:
        raise BusinessRuleViolation(message)
    return cleaned


def _clean_optional_text(value: Optional[str]) -> Optional[str]:
    cleaned = " ".join(str(value or "").split()).strip()
    return cleaned or None


def _compose_customer_address(customer: Customer) -> str:
    parts = [customer.endereco]
    if customer.numero:
        parts.append(customer.numero)
    if customer.complemento:
        parts.append(customer.complemento)
    if customer.bairro:
        parts.append(customer.bairro)
    parts.append(f"{customer.cidade}/{customer.estado}")
    return ", ".join(filter(None, parts))


def _get_customer_or_fail(db: Session, customer_id: int) -> Customer:
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise BusinessRuleViolation("Cliente informado para o agendamento nao existe.")
    return customer


def _get_technician_or_fail(db: Session, technician_id: Optional[int], require_active: bool = False) -> Optional[Technician]:
    if technician_id is None:
        return None
    query = db.query(Technician).filter(Technician.id == technician_id)
    if require_active:
        query = query.filter(Technician.ativo.is_(True))
    technician = query.first()
    if not technician:
        raise BusinessRuleViolation("Tecnico informado para o agendamento nao existe ou esta inativo.")
    return technician


def _get_work_order_or_fail(db: Session, work_order_id: Optional[int]) -> Optional[WorkOrder]:
    if work_order_id is None:
        return None
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not work_order:
        raise BusinessRuleViolation("Ordem de servico vinculada ao agendamento nao encontrada.")
    return work_order


def _get_user_or_fail(db: Session, user_id: Optional[int]) -> Optional[User]:
    if user_id is None:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BusinessRuleViolation("Usuario responsavel pelo agendamento nao encontrado.")
    return user


def _serialize_history_entry(entry: AppointmentHistory) -> AppointmentHistory:
    entry.usuario_nome = entry.usuario.nome if entry.usuario else None
    return entry


def _serialize_whatsapp_log(entry: AppointmentWhatsAppLog) -> AppointmentWhatsAppLog:
    entry.usuario_nome = entry.usuario.nome if entry.usuario else None
    return entry


def _serialize_appointment(appointment: Appointment) -> Appointment:
    appointment.cliente_nome = appointment.cliente.razao_social
    appointment.os_numero = appointment.ordem_servico.numero if appointment.ordem_servico else None
    appointment.tecnico_nome = appointment.tecnico.nome if appointment.tecnico else None
    appointment.usuario_responsavel_nome = appointment.usuario_responsavel.nome if appointment.usuario_responsavel else None
    appointment.usuario_ultima_atualizacao_nome = (
        appointment.usuario_ultima_atualizacao.nome if appointment.usuario_ultima_atualizacao else None
    )
    appointment.historico = [_serialize_history_entry(entry) for entry in appointment.historico]
    appointment.whatsapp_logs = [_serialize_whatsapp_log(entry) for entry in appointment.whatsapp_logs]
    return appointment


def _appointment_interval(appointment_date: date, appointment_time: time, duration_minutes: int) -> tuple[datetime, datetime]:
    start = datetime.combine(appointment_date, appointment_time)
    end = start + timedelta(minutes=duration_minutes)
    return start, end


def _assert_technician_availability(
    db: Session,
    technician_id: Optional[int],
    appointment_date: date,
    appointment_time: time,
    duration_minutes: int,
    current_appointment_id: Optional[int] = None,
) -> None:
    if technician_id is None:
        return

    candidate_start, candidate_end = _appointment_interval(appointment_date, appointment_time, duration_minutes)
    query = _appointment_query(db).filter(
        Appointment.tecnico_id == technician_id,
        Appointment.data_agendamento == appointment_date,
        Appointment.status.in_(ACTIVE_APPOINTMENT_STATUSES),
    )
    if current_appointment_id is not None:
        query = query.filter(Appointment.id != current_appointment_id)

    for other in query.all():
        other_start, other_end = _appointment_interval(
            other.data_agendamento,
            other.hora_agendamento,
            other.duracao_prevista_minutos,
        )
        if candidate_start < other_end and candidate_end > other_start:
            raise BusinessRuleViolation(
                f"Conflito de horario para o tecnico '{other.tecnico.nome if other.tecnico else technician_id}' "
                f"com o agendamento #{other.id} ({other.cliente.razao_social} as {other.hora_agendamento.strftime('%H:%M')})."
            )


def _log_appointment_history(
    db: Session,
    appointment: Appointment,
    user_id: Optional[int],
    action: str,
    details: Optional[str],
    previous_status: Optional[str] = None,
    new_status: Optional[str] = None,
) -> None:
    db.add(
        AppointmentHistory(
            agendamento_id=appointment.id,
            usuario_id=user_id,
            acao=action,
            status_anterior=previous_status,
            status_novo=new_status,
            detalhes=_clean_optional_text(details),
        )
    )


def _build_google_event_payload(appointment: Appointment) -> dict:
    settings = get_settings()
    try:
        company_timezone = ZoneInfo(settings.company_timezone)
    except ZoneInfoNotFoundError:
        company_timezone = timezone.utc
    start_dt = datetime.combine(appointment.data_agendamento, appointment.hora_agendamento, tzinfo=company_timezone)
    end_dt = start_dt + timedelta(minutes=appointment.duracao_prevista_minutos)
    description_lines = [
        f"Cliente: {appointment.cliente_nome}",
        f"Telefone: {appointment.telefone}",
        f"Endereco: {appointment.endereco_completo}",
        f"Tipo de servico: {appointment.tipo_servico}",
    ]
    if appointment.os_numero:
        description_lines.append(f"OS vinculada: {appointment.os_numero}")
    if appointment.observacoes:
        description_lines.append(f"Observacoes: {appointment.observacoes}")
    if appointment.observacoes_internas:
        description_lines.append(f"Observacoes internas: {appointment.observacoes_internas}")
    if appointment.instrucoes_tecnicas:
        description_lines.append(f"Instrucoes tecnicas: {appointment.instrucoes_tecnicas}")
    if appointment.retorno_revisita:
        description_lines.append(f"Retorno/Revisita: {appointment.retorno_revisita}")

    return {
        "summary": f"{appointment.cliente_nome} | {appointment.tipo_servico}",
        "location": appointment.endereco_completo,
        "description": "\n".join(description_lines),
        "start": {
            "dateTime": start_dt.isoformat(),
            "timeZone": settings.company_timezone if str(company_timezone) != "UTC" else "UTC",
        },
        "end": {
            "dateTime": end_dt.isoformat(),
            "timeZone": settings.company_timezone if str(company_timezone) != "UTC" else "UTC",
        },
        "extendedProperties": {
            "private": {
                "appointment_id": str(appointment.id),
                "customer_id": str(appointment.cliente_id),
                "work_order_id": str(appointment.os_id or ""),
            }
        },
    }


def _set_google_sync_state(
    appointment: Appointment,
    status: GoogleSyncStatus,
    calendar_id: Optional[str] = None,
    message: Optional[str] = None,
    event_id: Optional[str] = None,
) -> None:
    appointment.google_sync_status = status.value
    appointment.google_sync_message = _clean_optional_text(message)
    if calendar_id is not None:
        appointment.google_calendar_id = calendar_id
    if event_id is not None:
        appointment.google_calendar_event_id = event_id


def _sync_google_for_appointment(
    db: Session,
    appointment: Appointment,
    *,
    remove_event: bool = False,
    raise_on_error: bool = False,
    user_id: Optional[int] = None,
) -> Appointment:
    if not appointment.sincronizar_google:
        _set_google_sync_state(
            appointment,
            GoogleSyncStatus.DESCONECTADO,
            appointment.google_calendar_id,
            "Sincronizacao com Google Agenda desabilitada.",
        )
        db.flush()
        return appointment

    try:
        integration_user_id = user_id or appointment.usuario_ultima_atualizacao_id or appointment.usuario_responsavel_id
        if remove_event and appointment.google_calendar_event_id:
            _, calendar_id = google_calendar_request(
                db,
                integration_user_id,
                "DELETE",
                f"events/{appointment.google_calendar_event_id}",
            )
            _set_google_sync_state(
                appointment,
                GoogleSyncStatus.SINCRONIZADO,
                calendar_id,
                "Evento removido do Google Agenda.",
                "",
            )
            _log_appointment_history(db, appointment, user_id, "google_delete", "Evento removido da agenda Google.")
            db.flush()
            return appointment

        payload = _build_google_event_payload(_serialize_appointment(appointment))
        if appointment.google_calendar_event_id:
            response, calendar_id = google_calendar_request(
                db,
                integration_user_id,
                "PATCH",
                f"events/{appointment.google_calendar_event_id}",
                payload,
            )
        else:
            response, calendar_id = google_calendar_request(
                db,
                integration_user_id,
                "POST",
                "events",
                payload,
            )
        _set_google_sync_state(
            appointment,
            GoogleSyncStatus.SINCRONIZADO,
            calendar_id,
            "Evento sincronizado com Google Agenda.",
            response.get("id") if response else appointment.google_calendar_event_id,
        )
        _log_appointment_history(db, appointment, user_id, "google_sync", "Agendamento sincronizado com Google Agenda.")
        db.flush()
    except BusinessRuleViolation as exc:
        _set_google_sync_state(appointment, GoogleSyncStatus.FALHA, appointment.google_calendar_id, exc.message)
        _log_appointment_history(db, appointment, user_id, "google_sync_fail", exc.message)
        db.flush()
        if raise_on_error:
            raise
    return appointment


def _validate_appointment_payload(
    db: Session,
    payload: Union[AppointmentCreate, AppointmentUpdate],
    current_appointment_id: Optional[int] = None,
) -> tuple[Customer, Optional[Technician], Optional[WorkOrder], dict]:
    customer = _get_customer_or_fail(db, payload.cliente_id)
    technician = _get_technician_or_fail(db, payload.tecnico_id, require_active=False)
    work_order = _get_work_order_or_fail(db, payload.os_id)

    if work_order and work_order.cliente_id != customer.id:
        raise BusinessRuleViolation("A ordem de servico vinculada pertence a outro cliente.")
    if work_order and technician and work_order.tecnico_id != technician.id:
        raise BusinessRuleViolation("O tecnico do agendamento deve ser compativel com a OS vinculada.")
    if payload.tecnico_id is not None:
        _get_technician_or_fail(db, payload.tecnico_id, require_active=True)

    normalized_service_type = _clean_required_text(payload.tipo_servico, "Informe o tipo de servico do agendamento.")
    normalized_notes = _clean_optional_text(payload.observacoes)
    normalized_internal = _clean_optional_text(payload.observacoes_internas)
    normalized_instructions = _clean_optional_text(payload.instrucoes_tecnicas)
    normalized_follow_up = _clean_optional_text(payload.retorno_revisita)

    if payload.agendamento_pai_id:
        parent = _appointment_query(db).filter(Appointment.id == payload.agendamento_pai_id).first()
        if not parent:
            raise BusinessRuleViolation("Agendamento de origem para retorno/revisita nao encontrado.")
        if parent.cliente_id != customer.id:
            raise BusinessRuleViolation("O retorno ou revisita deve permanecer vinculado ao mesmo cliente.")

    _assert_technician_availability(
        db,
        payload.tecnico_id,
        payload.data_agendamento,
        payload.hora_agendamento,
        payload.duracao_prevista_minutos,
        current_appointment_id=current_appointment_id,
    )

    return customer, technician, work_order, {
        "tipo_servico": normalized_service_type,
        "observacoes": normalized_notes,
        "observacoes_internas": normalized_internal,
        "instrucoes_tecnicas": normalized_instructions,
        "retorno_revisita": normalized_follow_up,
        "telefone": customer.telefone,
        "endereco_completo": _compose_customer_address(customer),
    }


def _sync_linked_work_order_from_appointment(appointment: Appointment) -> None:
    if not appointment.ordem_servico:
        return

    work_order = appointment.ordem_servico
    work_order.cliente_id = appointment.cliente_id
    if appointment.tecnico_id is not None:
        work_order.tecnico_id = appointment.tecnico_id
    work_order.data_execucao = appointment.data_agendamento
    work_order.hora_inicio = appointment.hora_agendamento
    if appointment.status == AppointmentStatus.CONCLUIDO.value:
        work_order.status = WorkOrderStatus.CONCLUIDA.value
    elif appointment.status in {
        AppointmentStatus.CONFIRMADO.value,
        AppointmentStatus.EM_DESLOCAMENTO.value,
        AppointmentStatus.EM_ATENDIMENTO.value,
    } and work_order.status != WorkOrderStatus.CONCLUIDA.value:
        work_order.status = WorkOrderStatus.EM_EXECUCAO.value
    elif appointment.status == AppointmentStatus.PENDENTE.value and work_order.status != WorkOrderStatus.CONCLUIDA.value:
        work_order.status = WorkOrderStatus.ABERTA.value


def list_appointments(db: Session) -> list[Appointment]:
    appointments = _appointment_query(db).order_by(Appointment.data_agendamento.asc(), Appointment.hora_agendamento.asc()).all()
    return [_serialize_appointment(item) for item in appointments]


def get_appointment(db: Session, appointment_id: int) -> Appointment:
    appointment = _appointment_query(db).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise BusinessRuleViolation("Agendamento nao encontrado.")
    return _serialize_appointment(appointment)


def create_appointment(
    db: Session,
    payload: AppointmentCreate,
    current_user_id: Optional[int] = None,
    *,
    sync_google_after_commit: bool = True,
) -> Appointment:
    from app.modules.whatsapp.service import send_appointment_whatsapp_message

    _get_user_or_fail(db, current_user_id)
    customer, _, _, normalized = _validate_appointment_payload(db, payload)
    appointment = Appointment(
        cliente_id=customer.id,
        os_id=payload.os_id,
        tecnico_id=payload.tecnico_id,
        usuario_responsavel_id=current_user_id,
        usuario_ultima_atualizacao_id=current_user_id,
        agendamento_pai_id=payload.agendamento_pai_id,
        tipo_servico=normalized["tipo_servico"],
        telefone=normalized["telefone"],
        endereco_completo=normalized["endereco_completo"],
        data_agendamento=payload.data_agendamento,
        hora_agendamento=payload.hora_agendamento,
        duracao_prevista_minutos=payload.duracao_prevista_minutos,
        observacoes=normalized["observacoes"],
        observacoes_internas=normalized["observacoes_internas"],
        instrucoes_tecnicas=normalized["instrucoes_tecnicas"],
        retorno_revisita=normalized["retorno_revisita"],
        status=payload.status.value,
        origem=payload.origem.value,
        sincronizar_google=payload.sincronizar_google,
    )
    if appointment.sincronizar_google:
        appointment.google_sync_status = GoogleSyncStatus.PENDENTE.value
    db.add(appointment)
    db.flush()
    appointment = get_appointment(db, appointment.id)
    _sync_linked_work_order_from_appointment(appointment)
    _log_appointment_history(
        db,
        appointment,
        current_user_id,
        "create",
        "Agendamento criado.",
        new_status=appointment.status,
    )
    db.commit()
    appointment = get_appointment(db, appointment.id)
    if (
        get_settings().whatsapp_enabled
        and appointment.status not in {AppointmentStatus.CANCELADO.value, AppointmentStatus.NAO_REALIZADO.value}
    ):
        appointment = send_appointment_whatsapp_message(
            db,
            appointment.id,
            current_user_id=current_user_id,
            automatic=True,
        )
    if sync_google_after_commit and appointment.sincronizar_google:
        _sync_google_for_appointment(db, appointment, user_id=current_user_id)
        db.commit()
        appointment = get_appointment(db, appointment.id)
    return appointment


def update_appointment(
    db: Session,
    appointment_id: int,
    payload: AppointmentUpdate,
    current_user_id: Optional[int] = None,
    *,
    sync_google_after_commit: bool = True,
) -> Appointment:
    appointment = get_appointment(db, appointment_id)
    customer, _, _, normalized = _validate_appointment_payload(db, payload, current_appointment_id=appointment_id)
    previous_status = appointment.status
    previous_date = appointment.data_agendamento
    previous_time = appointment.hora_agendamento

    appointment.cliente_id = customer.id
    appointment.os_id = payload.os_id
    appointment.tecnico_id = payload.tecnico_id
    appointment.usuario_ultima_atualizacao_id = current_user_id
    appointment.agendamento_pai_id = payload.agendamento_pai_id
    appointment.tipo_servico = normalized["tipo_servico"]
    appointment.telefone = normalized["telefone"]
    appointment.endereco_completo = normalized["endereco_completo"]
    appointment.data_agendamento = payload.data_agendamento
    appointment.hora_agendamento = payload.hora_agendamento
    appointment.duracao_prevista_minutos = payload.duracao_prevista_minutos
    appointment.observacoes = normalized["observacoes"]
    appointment.observacoes_internas = normalized["observacoes_internas"]
    appointment.instrucoes_tecnicas = normalized["instrucoes_tecnicas"]
    appointment.retorno_revisita = normalized["retorno_revisita"]
    appointment.sincronizar_google = payload.sincronizar_google

    is_rescheduled = previous_date != payload.data_agendamento or previous_time != payload.hora_agendamento
    target_status = payload.status.value
    if is_rescheduled and target_status not in {
        AppointmentStatus.CANCELADO.value,
        AppointmentStatus.CONCLUIDO.value,
        AppointmentStatus.NAO_REALIZADO.value,
    }:
        target_status = AppointmentStatus.REAGENDADO.value
    appointment.status = target_status
    if appointment.sincronizar_google and not appointment.google_calendar_event_id:
        appointment.google_sync_status = GoogleSyncStatus.PENDENTE.value
    elif not appointment.sincronizar_google:
        appointment.google_sync_status = GoogleSyncStatus.DESCONECTADO.value
        appointment.google_sync_message = "Sincronizacao com Google Agenda desabilitada."
    _sync_linked_work_order_from_appointment(appointment)

    history_action = "reschedule" if is_rescheduled else "update"
    details = "Agendamento reagendado." if is_rescheduled else "Agendamento atualizado."
    _log_appointment_history(db, appointment, current_user_id, history_action, details, previous_status, appointment.status)
    db.commit()
    appointment = get_appointment(db, appointment.id)
    if sync_google_after_commit and appointment.sincronizar_google:
        _sync_google_for_appointment(db, appointment, user_id=current_user_id)
        db.commit()
        appointment = get_appointment(db, appointment.id)
    return appointment


def update_appointment_status(
    db: Session,
    appointment_id: int,
    payload: AppointmentStatusUpdate,
    current_user_id: Optional[int] = None,
    *,
    sync_google_after_commit: bool = True,
) -> Appointment:
    appointment = get_appointment(db, appointment_id)
    previous_status = appointment.status
    appointment.status = payload.status.value
    appointment.usuario_ultima_atualizacao_id = current_user_id
    _log_appointment_history(
        db,
        appointment,
        current_user_id,
        "status_change",
        payload.detalhes or f"Status alterado para {payload.status.value}.",
        previous_status,
        appointment.status,
    )
    _sync_linked_work_order_from_appointment(appointment)
    db.commit()
    appointment = get_appointment(db, appointment.id)
    if sync_google_after_commit:
        should_remove = appointment.status in {
            AppointmentStatus.CANCELADO.value,
            AppointmentStatus.NAO_REALIZADO.value,
        }
        _sync_google_for_appointment(
            db,
            appointment,
            remove_event=should_remove,
            user_id=current_user_id,
        )
        db.commit()
        appointment = get_appointment(db, appointment.id)
    return appointment


def get_appointment_dashboard(db: Session) -> AppointmentDashboardRead:
    appointments = list_appointments(db)
    counts = {status.value: 0 for status in AppointmentStatus}
    for item in appointments:
        counts[item.status] = counts.get(item.status, 0) + 1
    return AppointmentDashboardRead(
        total=len(appointments),
        pendente=counts[AppointmentStatus.PENDENTE.value],
        confirmado=counts[AppointmentStatus.CONFIRMADO.value],
        em_deslocamento=counts[AppointmentStatus.EM_DESLOCAMENTO.value],
        em_atendimento=counts[AppointmentStatus.EM_ATENDIMENTO.value],
        concluido=counts[AppointmentStatus.CONCLUIDO.value],
        reagendado=counts[AppointmentStatus.REAGENDADO.value],
        cancelado=counts[AppointmentStatus.CANCELADO.value],
        nao_realizado=counts[AppointmentStatus.NAO_REALIZADO.value],
    )


def sync_appointment_google_event(db: Session, appointment_id: int, current_user_id: Optional[int] = None) -> Appointment:
    appointment = get_appointment(db, appointment_id)
    if not appointment.sincronizar_google:
        raise BusinessRuleViolation(
            "Ative a sincronizacao com Google Agenda neste agendamento antes de usar a sincronizacao manual."
        )
    _sync_google_for_appointment(db, appointment, raise_on_error=True, user_id=current_user_id)
    db.commit()
    return get_appointment(db, appointment_id)


def sync_work_order_appointment(
    db: Session,
    work_order: WorkOrder,
    *,
    current_user_id: Optional[int],
    generate_appointment: bool,
    service_type: Optional[str],
    duration_minutes: int,
    internal_notes: Optional[str],
    technical_instructions: Optional[str],
    follow_up_notes: Optional[str],
    sync_google: bool,
) -> tuple[Optional[Appointment], bool]:
    appointment = (
        _appointment_query(db)
        .filter(
            Appointment.os_id == work_order.id,
            Appointment.origem == AppointmentSource.ORDEM_SERVICO.value,
            Appointment.agendamento_pai_id.is_(None),
        )
        .order_by(Appointment.id.desc())
        .first()
    )

    if not generate_appointment:
        if appointment and appointment.status not in FINISHED_APPOINTMENT_STATUSES:
            previous_status = appointment.status
            appointment.status = AppointmentStatus.CANCELADO.value
            appointment.usuario_ultima_atualizacao_id = current_user_id
            _log_appointment_history(
                db,
                appointment,
                current_user_id,
                "cancel",
                "Agendamento automatico cancelado porque a OS nao deve mais gerar agenda.",
                previous_status,
                appointment.status,
            )
        return appointment, False

    customer = _get_customer_or_fail(db, work_order.cliente_id)
    _get_technician_or_fail(db, work_order.tecnico_id, require_active=True)
    _assert_technician_availability(
        db,
        work_order.tecnico_id,
        work_order.data_execucao,
        work_order.hora_inicio,
        duration_minutes,
        current_appointment_id=appointment.id if appointment else None,
    )

    if appointment is None:
        appointment = Appointment(
            cliente_id=work_order.cliente_id,
            os_id=work_order.id,
            tecnico_id=work_order.tecnico_id,
            usuario_responsavel_id=current_user_id,
            usuario_ultima_atualizacao_id=current_user_id,
            tipo_servico=_clean_required_text(service_type or "Atendimento vinculado a OS", "Informe o tipo de servico."),
            telefone=customer.telefone,
            endereco_completo=_compose_customer_address(customer),
            data_agendamento=work_order.data_execucao,
            hora_agendamento=work_order.hora_inicio,
            duracao_prevista_minutos=duration_minutes,
            observacoes=_clean_optional_text(work_order.observacoes),
            observacoes_internas=_clean_optional_text(internal_notes),
            instrucoes_tecnicas=_clean_optional_text(technical_instructions),
            retorno_revisita=_clean_optional_text(follow_up_notes),
            status=AppointmentStatus.PENDENTE.value,
            origem=AppointmentSource.ORDEM_SERVICO.value,
            sincronizar_google=sync_google,
            google_sync_status=(GoogleSyncStatus.PENDENTE.value if sync_google else GoogleSyncStatus.DESCONECTADO.value),
        )
        db.add(appointment)
        db.flush()
        _log_appointment_history(
            db,
            appointment,
            current_user_id,
            "create_from_work_order",
            f"Agendamento automatico criado a partir da OS {work_order.numero}.",
            new_status=appointment.status,
        )
        return appointment, True

    previous_status = appointment.status
    date_changed = appointment.data_agendamento != work_order.data_execucao or appointment.hora_agendamento != work_order.hora_inicio
    appointment.cliente_id = work_order.cliente_id
    appointment.tecnico_id = work_order.tecnico_id
    appointment.usuario_ultima_atualizacao_id = current_user_id
    appointment.tipo_servico = _clean_required_text(service_type or appointment.tipo_servico, "Informe o tipo de servico.")
    appointment.telefone = customer.telefone
    appointment.endereco_completo = _compose_customer_address(customer)
    appointment.data_agendamento = work_order.data_execucao
    appointment.hora_agendamento = work_order.hora_inicio
    appointment.duracao_prevista_minutos = duration_minutes
    appointment.observacoes = _clean_optional_text(work_order.observacoes)
    appointment.observacoes_internas = _clean_optional_text(internal_notes)
    appointment.instrucoes_tecnicas = _clean_optional_text(technical_instructions)
    appointment.retorno_revisita = _clean_optional_text(follow_up_notes)
    appointment.sincronizar_google = sync_google
    if date_changed and appointment.status not in FINISHED_APPOINTMENT_STATUSES:
        appointment.status = AppointmentStatus.REAGENDADO.value
    elif appointment.status in {AppointmentStatus.CANCELADO.value, AppointmentStatus.NAO_REALIZADO.value}:
        appointment.status = AppointmentStatus.PENDENTE.value
    if sync_google and not appointment.google_calendar_event_id:
        appointment.google_sync_status = GoogleSyncStatus.PENDENTE.value
    elif not sync_google:
        appointment.google_sync_status = GoogleSyncStatus.DESCONECTADO.value
        appointment.google_sync_message = "Sincronizacao com Google Agenda desabilitada."
    _log_appointment_history(
        db,
        appointment,
        current_user_id,
        "sync_from_work_order",
        f"Agendamento atualizado a partir da OS {work_order.numero}.",
        previous_status,
        appointment.status,
    )
    return appointment, False
