"""Seed one all-in-one demo order with normal, abnormal, and critical results.

Run from the backend container or backend directory:
    python -m app.seed_demo_order_results

This script is for local/demo environments. It only replaces data tied to the
PAT-DEMO-ALL-IN-ONE patient identifier and reuses the existing demo catalog.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from datetime import date

from sqlalchemy import delete
from sqlmodel import Session, col, select

from app.core.db import engine
from app.models import User
from app.models.lis import (
    AnalyteResult,
    AnalyteResultComment,
    Catalog,
    CriticalMethod,
    CriticalNotification,
    CriticalNotificationAcknowledge,
    CriticalNotificationCreate,
    CustomerCredit,
    Doctor,
    DoctorCommissionEntry,
    GenderType,
    Invoice,
    InvoiceBalanceTransfer,
    InvoiceLine,
    Notification,
    Order,
    OrderCatalogItemAnalyte,
    OrderCreate,
    OrderItem,
    OrderItemSpecimen,
    OrderRevision,
    OrderSpecimen,
    Patient,
    PatientContext,
    PaymentRefund,
    PaymentTransaction,
    Report,
    ResultBulkEntryRequest,
    ResultEntryValue,
    ResultStatus,
)
from app.services import order as order_service
from app.services import result as result_service
from app.services import specimen as specimen_service

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

DEMO_PATIENT_IDENTIFIER = "PAT-DEMO-ALL-IN-ONE"
DEMO_PATIENT_FIRST_NAME = "Aminata"
DEMO_PATIENT_LAST_NAME = "Démo Tous Résultats"
DEMO_DOCTOR_FIRST_NAME = "Démo"
DEMO_DOCTOR_LAST_NAME = "Prescripteur"
DEMO_CONTEXT_NAME = "Ambulatoire"

EXPECTED_CATALOG_CODES = {
    "NFS",
    "GLY",
    "UREE",
    "CREAT",
    "IONO",
    "CA",
    "LIP",
    "HEP",
    "CRP",
    "TSH",
    "T4L",
    "HBA1C",
    "TPINR",
    "TCA",
    "BU",
    "ECBU",
    "P_RENAL",
    "P_METAB",
    "P_HEP_COMPLET",
    "P_CARDIO",
    "P_PREOP",
}

RESULT_VALUES = {
    "ALT": "32",
    "AST": "85",
    "BILD": "0.2",
    "BILT": "0.8",
    "CA": "9.2",
    "CHOL": "180",
    "CL": "103",
    "CREAT": "1.0",
    "CRP": "240",
    "ECBU_CULTURE": "Culture négative après 24h",
    "ECBU_DIRECT": "Leucocyturie significative avec rares bactéries observées.",
    "FT4": "1.2",
    "GGT": "95",
    "GLU": "45",
    "GLU_U": "+++",
    "HB": "11.2",
    "HBA1C": "6.4",
    "HCT": "39",
    "HDL": "55",
    "INR": "1.0",
    "K": "6.4",
    "LEU_U": "Positif",
    "LYMPH": "2.1",
    "MCH": "29",
    "MCV": "85",
    "NA": "140",
    "NEUT": "4.2",
    "NITRITES_U": "Positif",
    "PAL": "95",
    "PLT": "42",
    "PROT_U": "++",
    "RBC": "4.6",
    "TCA": "32",
    "TG": "120",
    "TP": "88",
    "TSH": "2.1",
    "UREE": "32",
    "WBC": "12.5",
}


@dataclass
class SeedSummary:
    patient_identifier: str
    accession_number: str
    item_count: int
    result_count: int
    abnormal_count: int
    critical_count: int
    acknowledged_count: int
    verified_count: int
    skipped_count: int
    order_status: str


def main() -> None:
    with Session(engine) as session:
        try:
            summary = seed_demo_order_results(session)
        except RuntimeError as error:
            logger.error(str(error))
            sys.exit(1)
    print_summary(summary)


def seed_demo_order_results(session: Session) -> SeedSummary:
    user = first_active_superuser(session)
    ensure_demo_catalog_present(session)
    patient = upsert_demo_patient(session)
    doctor = upsert_demo_doctor(session)
    context = upsert_demo_context(session)
    session.commit()

    delete_existing_demo_operational_data(session, patient)
    session.commit()

    catalog_ids = active_orderable_catalog_ids(session)
    order = order_service.create_order(
        session=session,
        request=OrderCreate(
            patient_id=patient.id,
            doctor_id=doctor.id,
            patient_context_id=context.id,
            notes="Demande de démonstration: résultats normaux, anormaux et critiques.",
            catalog_ids=catalog_ids,
        ),
        created_by_id=user.id,
        can_override_prices=True,
        can_discount=True,
        can_collect_payment=True,
    )

    specimen_service.collect_all(
        session=session,
        order_id=order.id,
        collected_by_id=user.id,
    )
    enter_all_results(session=session, order_id=order.id, user_id=user.id)
    acknowledged_count = notify_and_acknowledge_criticals(
        session=session,
        order_id=order.id,
        user_id=user.id,
    )
    verification = result_service.verify_order(
        session=session,
        order_id=order.id,
        user_id=user.id,
    )
    workspace = result_service.get_workspace(session=session, order_id=order.id)

    return SeedSummary(
        patient_identifier=workspace.patient_identifier,
        accession_number=workspace.accession_number,
        item_count=len(workspace.tests),
        result_count=sum(len(test.analytes) for test in workspace.tests),
        abnormal_count=sum(
            analyte.is_abnormal
            for test in workspace.tests
            for analyte in test.analytes
        ),
        critical_count=sum(
            analyte.is_critical
            for test in workspace.tests
            for analyte in test.analytes
        ),
        acknowledged_count=acknowledged_count,
        verified_count=verification.verified_count,
        skipped_count=verification.skipped_count,
        order_status=workspace.order_status.value,
    )


def first_active_superuser(session: Session) -> User:
    user = session.exec(
        select(User)
        .where(User.is_superuser == True, User.is_active == True)  # noqa: E712
        .order_by(col(User.created_at).asc())
    ).first()
    if user is None:
        raise RuntimeError(
            "Aucun superutilisateur actif trouvé. Initialisez la base avant ce seed."
        )
    return user


def ensure_demo_catalog_present(session: Session) -> None:
    rows = session.exec(
        select(Catalog.code).where(Catalog.code.in_(EXPECTED_CATALOG_CODES))
    ).all()
    missing = sorted(EXPECTED_CATALOG_CODES - set(rows))
    if missing:
        raise RuntimeError(
            "Catalogue de démonstration incomplet. Codes manquants: "
            f"{', '.join(missing)}.\n"
            "Exécutez d'abord: docker compose exec backend "
            "python -m app.seed_catalog_demo --confirm-delete"
        )


def upsert_demo_patient(session: Session) -> Patient:
    patient = session.exec(
        select(Patient).where(Patient.identifier == DEMO_PATIENT_IDENTIFIER)
    ).first()
    values = {
        "identifier": DEMO_PATIENT_IDENTIFIER,
        "first_name": DEMO_PATIENT_FIRST_NAME,
        "last_name": DEMO_PATIENT_LAST_NAME,
        "date_of_birth": date(1987, 4, 12),
        "gender": GenderType.female,
        "phone": "+223 70 12 34 56",
        "address": "Hamdallaye ACI 2000, Bamako",
        "is_deleted": False,
    }
    if patient is None:
        patient = Patient(**values)
    else:
        patient.sqlmodel_update(values)
    session.add(patient)
    session.flush()
    return patient


def upsert_demo_doctor(session: Session) -> Doctor:
    doctor = session.exec(
        select(Doctor).where(
            Doctor.first_name == DEMO_DOCTOR_FIRST_NAME,
            Doctor.last_name == DEMO_DOCTOR_LAST_NAME,
        )
    ).first()
    values = {
        "first_name": DEMO_DOCTOR_FIRST_NAME,
        "last_name": DEMO_DOCTOR_LAST_NAME,
        "provenance": "Clinique Démo Keneya",
        "phone": "+223 20 22 33 44",
        "is_deleted": False,
    }
    if doctor is None:
        doctor = Doctor(**values)
    else:
        doctor.sqlmodel_update(values)
    session.add(doctor)
    session.flush()
    return doctor


def upsert_demo_context(session: Session) -> PatientContext:
    context = session.exec(
        select(PatientContext).where(PatientContext.name == DEMO_CONTEXT_NAME)
    ).first()
    if context is None:
        context = PatientContext(name=DEMO_CONTEXT_NAME)
    context.is_deleted = False
    session.add(context)
    session.flush()
    return context


def delete_existing_demo_operational_data(session: Session, patient: Patient) -> None:
    order_ids = list(
        session.exec(select(Order.id).where(Order.patient_id == patient.id)).all()
    )
    if not order_ids:
        return
    invoice_ids = list(
        session.exec(select(Invoice.id).where(Invoice.order_id.in_(order_ids))).all()
    )
    payment_ids = (
        list(
            session.exec(
                select(PaymentTransaction.id).where(
                    PaymentTransaction.invoice_id.in_(invoice_ids)
                )
            ).all()
        )
        if invoice_ids
        else []
    )
    result_ids = list(
        session.exec(
            select(AnalyteResult.id)
            .join(OrderItem, AnalyteResult.order_item_id == OrderItem.id)
            .where(OrderItem.order_id.in_(order_ids))
        ).all()
    )
    item_ids = list(
        session.exec(select(OrderItem.id).where(OrderItem.order_id.in_(order_ids))).all()
    )
    specimen_ids = list(
        session.exec(
            select(OrderSpecimen.id).where(OrderSpecimen.order_id.in_(order_ids))
        ).all()
    )

    if payment_ids:
        session.exec(delete(PaymentRefund).where(PaymentRefund.payment_id.in_(payment_ids)))
    if invoice_ids:
        session.exec(
            delete(InvoiceBalanceTransfer).where(
                InvoiceBalanceTransfer.source_invoice_id.in_(invoice_ids)
                | InvoiceBalanceTransfer.target_invoice_id.in_(invoice_ids)
            )
        )
        session.exec(
            delete(CustomerCredit).where(CustomerCredit.source_invoice_id.in_(invoice_ids))
        )
        session.exec(delete(PaymentTransaction).where(PaymentTransaction.id.in_(payment_ids)))
        session.exec(delete(InvoiceLine).where(InvoiceLine.invoice_id.in_(invoice_ids)))
        session.exec(delete(Invoice).where(Invoice.id.in_(invoice_ids)))
    if result_ids:
        session.exec(
            delete(CriticalNotification).where(
                CriticalNotification.analyte_result_id.in_(result_ids)
            )
        )
        session.exec(
            delete(AnalyteResultComment).where(
                AnalyteResultComment.analyte_result_id.in_(result_ids)
            )
        )
        session.exec(delete(AnalyteResult).where(AnalyteResult.id.in_(result_ids)))
    if item_ids:
        session.exec(
            delete(OrderCatalogItemAnalyte).where(
                OrderCatalogItemAnalyte.order_item_id.in_(item_ids)
            )
        )
        session.exec(
            delete(OrderItemSpecimen).where(OrderItemSpecimen.order_item_id.in_(item_ids))
        )
        session.exec(delete(OrderItem).where(OrderItem.id.in_(item_ids)))
    if specimen_ids:
        session.exec(delete(OrderSpecimen).where(OrderSpecimen.id.in_(specimen_ids)))
    session.exec(delete(Report).where(Report.order_id.in_(order_ids)))
    session.exec(delete(Notification).where(Notification.order_id.in_(order_ids)))
    session.exec(
        delete(DoctorCommissionEntry).where(DoctorCommissionEntry.order_id.in_(order_ids))
    )
    session.exec(delete(OrderRevision).where(OrderRevision.order_id.in_(order_ids)))
    session.exec(delete(Order).where(Order.id.in_(order_ids)))
    session.flush()


def active_orderable_catalog_ids(session: Session) -> list:
    rows = session.exec(
        select(Catalog)
        .where(
            Catalog.code.in_(EXPECTED_CATALOG_CODES),
            Catalog.is_orderable == True,  # noqa: E712
            Catalog.is_deleted == False,  # noqa: E712
        )
        .order_by(col(Catalog.type).asc(), col(Catalog.code).asc())
    ).all()
    return [catalog.id for catalog in rows]


def enter_all_results(*, session: Session, order_id, user_id) -> None:
    workspace = result_service.get_workspace(session=session, order_id=order_id)
    for test in workspace.tests:
        values: list[ResultEntryValue] = []
        for analyte in test.analytes:
            if analyte.is_calculated:
                continue
            value = RESULT_VALUES.get(analyte.analyte_code)
            if value is None:
                raise RuntimeError(
                    "Aucune valeur de démonstration pour l'analyte "
                    f"{analyte.analyte_code} ({analyte.analyte_name})"
                )
            values.append(
                ResultEntryValue(
                    analyte_id=analyte.analyte_id,
                    specimen_id=analyte.specimen_id,
                    result_value=value,
                )
            )
        if values:
            result_service.enter_results(
                session=session,
                order_id=order_id,
                request=ResultBulkEntryRequest(
                    order_item_id=test.order_item_id,
                    values=values,
                ),
                user_id=user_id,
            )


def notify_and_acknowledge_criticals(*, session: Session, order_id, user_id) -> int:
    critical_results = session.exec(
        select(AnalyteResult)
        .join(OrderItem, AnalyteResult.order_item_id == OrderItem.id)
        .where(
            OrderItem.order_id == order_id,
            AnalyteResult.is_critical == True,  # noqa: E712
            AnalyteResult.is_superseded == False,  # noqa: E712
            AnalyteResult.status == ResultStatus.resulted,
        )
        .order_by(col(AnalyteResult.created_at).asc())
    ).all()
    acknowledged = 0
    for db_result in critical_results:
        notification = result_service.create_critical_notification(
            session=session,
            result_id=db_result.id,
            request=CriticalNotificationCreate(
                notified_to_id=user_id,
                method=CriticalMethod.call,
                notes="Notification critique générée par le seed de démonstration.",
            ),
            user_id=user_id,
        )
        result_service.acknowledge_critical_notification(
            session=session,
            notification_id=notification.id,
            request=CriticalNotificationAcknowledge(
                notes="Acquittement automatique pour démonstration."
            ),
            user_id=user_id,
        )
        acknowledged += 1
    return acknowledged


def print_summary(summary: SeedSummary) -> None:
    logger.info("Seed all-in-one terminé.")
    logger.info("  Patient: %s", summary.patient_identifier)
    logger.info("  Demande: %s", summary.accession_number)
    logger.info("  Examens: %s", summary.item_count)
    logger.info("  Résultats: %s", summary.result_count)
    logger.info("  Anormaux: %s", summary.abnormal_count)
    logger.info("  Critiques: %s", summary.critical_count)
    logger.info("  Notifications acquittées: %s", summary.acknowledged_count)
    logger.info(
        "  Vérification: %s vérifiés, %s ignorés",
        summary.verified_count,
        summary.skipped_count,
    )
    logger.info("  Statut final: %s", summary.order_status)


if __name__ == "__main__":
    main()
