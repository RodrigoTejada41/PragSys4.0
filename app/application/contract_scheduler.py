import logging
import threading
from datetime import date

from sqlalchemy.exc import IntegrityError

from app.application.contracts_service import run_contract_maintenance
from app.core.config import get_settings
from app.infrastructure.db import get_session_local
from app.infrastructure.models import BackgroundJobRun

LOGGER = logging.getLogger(__name__)


class ContractMaintenanceScheduler:
    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._last_run_date: date | None = None

    def start(self) -> None:
        settings = get_settings()
        if not settings.contract_scheduler_enabled:
            LOGGER.info("contract_scheduler_disabled")
            return
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="contract-maintenance", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._thread = None

    def _run_loop(self) -> None:
        poll_seconds = max(int(get_settings().contract_scheduler_poll_seconds), 60)
        while not self._stop_event.is_set():
            today = date.today()
            if self._last_run_date != today:
                self._run_once()
                self._last_run_date = today
            self._stop_event.wait(poll_seconds)

    def _run_once(self) -> None:
        session = get_session_local()()
        run_date = date.today()
        try:
            if not claim_daily_job_run(session, "contract_maintenance", run_date):
                LOGGER.info("contract_scheduler_cycle_skipped reason=already_claimed")
                return
            result = run_contract_maintenance(session)
            LOGGER.info("contract_scheduler_cycle_completed result=%s", result)
        except Exception:
            release_daily_job_run(session, "contract_maintenance", run_date)
            LOGGER.exception("contract_scheduler_cycle_failed")
        finally:
            session.close()


def claim_daily_job_run(session, task_name: str, run_date: date) -> bool:
    session.add(BackgroundJobRun(task_name=task_name, run_date=run_date))
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return False
    return True


def release_daily_job_run(session, task_name: str, run_date: date) -> None:
    try:
        session.rollback()
        session.query(BackgroundJobRun).filter(
            BackgroundJobRun.task_name == task_name,
            BackgroundJobRun.run_date == run_date,
        ).delete(synchronize_session=False)
        session.commit()
    except Exception:
        session.rollback()
        LOGGER.exception("contract_scheduler_claim_release_failed task_name=%s run_date=%s", task_name, run_date)


contract_scheduler = ContractMaintenanceScheduler()
