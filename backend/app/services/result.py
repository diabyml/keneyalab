"""Clinical result entry, validation, escalation, and verification."""

import uuid
from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlmodel import Session, col, select

from app.core.exceptions import (
    BusinessRuleError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.models import User
from app.models.lis import (
    Analyte,
    AnalyteDataType,
    AnalyteResult,
    AnalyteResultComment,
    AuditAction,
    AuditLog,
    Catalog,
    CriticalNotification,
    CriticalNotificationAcknowledge,
    CriticalNotificationCountPublic,
    CriticalNotificationCreate,
    CriticalNotificationDetailPublic,
    CriticalNotificationListPublic,
    CriticalRecipientPublic,
    CriticalRecipientsPublic,
    FormulaResultType,
    Order,
    OrderCatalogItemAnalyte,
    OrderItem,
    OrderItemSpecimen,
    OrderSpecimen,
    OrderStatus,
    Patient,
    ResultAnalyteWorkspacePublic,
    ResultBulkEntryRequest,
    ResultBulkVerificationPublic,
    ResultCommentDetailPublic,
    ResultCommentRequest,
    ResultConsistencyOutcomePublic,
    ResultCorrectionHistoryPublic,
    ResultCorrectionRequest,
    ResultEntryValue,
    ResultInterpretationUpdate,
    ResultQueueItemPublic,
    ResultQueuePublic,
    ResultReflexOutcomePublic,
    ResultStatus,
    ResultSubmissionPublic,
    ResultTestWorkspacePublic,
    ResultValidationOutcomePublic,
    ResultVerificationSkipPublic,
    ResultWorkspacePublic,
    RuleSeverity,
    SortOrder,
    SpecimenStatus,
    ValidationRuleSimulationRequest,
)
from app.repositories import result as result_repo
from app.services import automated_rule as automated_rule_service
from app.services import formula_engine
from app.services import permission as permission_service
from app.services import validation_rule as validation_rule_service

ELIGIBLE_ORDER_STATUSES = {
    OrderStatus.collected,
    OrderStatus.in_progress,
    OrderStatus.partial_results,
    OrderStatus.completed,
}


def _display_name(full_name: str | None, email: str | None) -> str:
    return full_name or email or "Utilisateur"


def _age_years(birth_date: date, today: date | None = None) -> int:
    current = today or date.today()
    return current.year - birth_date.year - (
        (current.month, current.day) < (birth_date.month, birth_date.day)
    )


def _notification_public(
    *,
    notification: CriticalNotification,
    accession_number: str,
    patient_name: str,
    analyte: Analyte,
    result_value: str | None,
    notified_by_name: str,
    notified_to_name: str,
    acknowledged_by_name: str | None,
) -> CriticalNotificationDetailPublic:
    return CriticalNotificationDetailPublic(
        **notification.model_dump(),
        accession_number=accession_number,
        patient_name=patient_name,
        analyte_code=analyte.code,
        analyte_name=analyte.name,
        result_value=result_value,
        notified_by_name=notified_by_name,
        notified_to_name=notified_to_name,
        acknowledged_by_name=acknowledged_by_name,
    )


def _validate_basic_value(analyte: Analyte, value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise BusinessRuleError(f"Le résultat de {analyte.name} est requis")
    if analyte.is_calculated:
        raise BusinessRuleError(
            f"Le résultat calculé {analyte.name} ne peut pas être saisi manuellement"
        )
    if analyte.data_type == AnalyteDataType.numeric:
        formula_engine.parse_decimal(cleaned, label=analyte.name)
    elif analyte.data_type == AnalyteDataType.options:
        options = {
            item.strip()
            for item in (analyte.options_data or [])
            if isinstance(item, str) and item.strip()
        }
        if cleaned not in options:
            raise BusinessRuleError(f"Option invalide pour {analyte.name}")
    return cleaned


def _validate_result(
    *,
    session: Session,
    order: Order,
    patient,
    analyte: Analyte,
    value: str,
    result_id: uuid.UUID | None,
) -> tuple[ResultValidationOutcomePublic, uuid.UUID | None]:
    previous = result_repo.get_previous_verified_value(
        session=session,
        patient_id=patient.id,
        analyte_id=analyte.id,
        exclude_result_id=result_id,
    )
    simulation = validation_rule_service.simulate_rule(
        session=session,
        simulation_in=ValidationRuleSimulationRequest(
            analyte_id=analyte.id,
            age_years=_age_years(patient.date_of_birth),
            gender=patient.gender,
            patient_context_id=order.patient_context_id,
            result_value=value,
            previous_value=previous,
        ),
    )
    if not simulation.is_valid:
        raise BusinessRuleError(f"{analyte.name}: {simulation.message}")
    return (
        ResultValidationOutcomePublic(
            classification=simulation.classification,
            message=simulation.message,
            is_abnormal=simulation.is_abnormal,
            is_critical=simulation.is_critical,
            delta_flag=simulation.delta_flag,
        ),
        simulation.matched_rule.id if simulation.matched_rule else None,
    )


def _workspace_value_map(
    workspace: ResultWorkspacePublic,
) -> dict[str, str]:
    values: dict[str, str] = {}
    for test in workspace.tests:
        for analyte in test.analytes:
            if analyte.result_value is not None:
                values[analyte.analyte_code.upper()] = analyte.result_value
    return values


def _evaluate_consistency(
    *,
    session: Session,
    workspace: ResultWorkspacePublic,
    raise_on_error: bool = True,
) -> list[ResultConsistencyOutcomePublic]:
    values = _workspace_value_map(workspace)
    analyte_ids = [
        analyte.analyte_id
        for test in workspace.tests
        for analyte in test.analytes
    ]
    rows = result_repo.get_consistency_rules(
        session=session, analyte_ids=analyte_ids
    )
    rules = {rule.id: rule for rule, _ in rows}
    outcomes: list[ResultConsistencyOutcomePublic] = []
    for rule in rules.values():
        references = formula_engine.extract_references(rule.formula)
        if not references or any(code not in values for code in references):
            continue
        valid, _ = formula_engine.evaluate_formula(
            formula=rule.formula,
            values=values,
            expected_result_type=FormulaResultType.boolean,
        )
        if valid:
            continue
        outcome = ResultConsistencyOutcomePublic(
            rule_id=rule.id,
            name=rule.name,
            severity=rule.severity,
            message=rule.error_message,
        )
        outcomes.append(outcome)
        if raise_on_error and rule.severity == RuleSeverity.error:
            raise BusinessRuleError(rule.error_message)
    return outcomes


def _calculate_analytes(
    *, session: Session, order: Order, patient, user_id: uuid.UUID
) -> None:
    rows = result_repo.get_workspace_rows(session=session, order_id=order.id)
    by_item: dict[uuid.UUID, list] = defaultdict(list)
    for row in rows:
        by_item[row[0].id].append(row)
    now = datetime.now(timezone.utc)
    for item_rows in by_item.values():
        values = {
            row[4].code.upper(): row[8].result_value
            for row in item_rows
            if row[8] is not None and row[8].result_value is not None
        }
        for row in item_rows:
            item, _, _, _, analyte, _, specimen, _, current = row[:9]
            if not analyte.is_calculated or not analyte.calculation_formula:
                continue
            references = formula_engine.extract_references(analyte.calculation_formula)
            if any(code not in values for code in references):
                continue
            calculated, _ = formula_engine.evaluate_formula(
                formula=analyte.calculation_formula,
                values=values,
                expected_result_type=FormulaResultType.number,
            )
            value = str(Decimal(calculated).quantize(Decimal("0.01")))
            validation, rule_id = _validate_result(
                session=session,
                order=order,
                patient=patient,
                analyte=analyte,
                value=value,
                result_id=current.id if current else None,
            )
            db_result = current or result_repo.create(
                session=session,
                db_obj=AnalyteResult(
                    order_item_id=item.id,
                    analyte_id=analyte.id,
                    specimen_id=specimen.id,
                ),
            )
            if db_result.status == ResultStatus.verified:
                continue
            db_result.result_value = value
            db_result.validation_rule_id = rule_id
            db_result.is_abnormal = validation.is_abnormal
            db_result.is_critical = validation.is_critical
            db_result.delta_flag = validation.delta_flag
            db_result.status = ResultStatus.resulted
            db_result.resulted_by_id = user_id
            db_result.resulted_at = now
            session.add(db_result)


def _refresh_order_status(*, session: Session, order: Order) -> None:
    rows = result_repo.get_workspace_rows(session=session, order_id=order.id)
    results = [row[8] for row in rows]
    if not results or all(result is None for result in results):
        order.status = OrderStatus.collected
    elif all(
        result is not None and result.status == ResultStatus.verified
        for result in results
    ):
        order.status = OrderStatus.completed
    elif any(
        result is not None and result.status == ResultStatus.verified
        for result in results
    ):
        order.status = OrderStatus.partial_results
    else:
        order.status = OrderStatus.in_progress
    session.add(order)


def get_workspace(
    *, session: Session, order_id: uuid.UUID, include_audit: bool = False
) -> ResultWorkspacePublic:
    header = result_repo.get_order_header(session=session, order_id=order_id)
    if header is None:
        raise NotFoundError("Demande non trouvée")
    order, patient, context, doctor = header
    interpretation_user = (
        session.get(User, order.interpretation_updated_by_id)
        if order.interpretation_updated_by_id
        else None
    )
    rows = result_repo.get_workspace_rows(session=session, order_id=order_id)
    result_ids = [row[8].id for row in rows if row[8] is not None]
    comments_by_result: dict[uuid.UUID, list[ResultCommentDetailPublic]] = defaultdict(list)
    for comment, user in result_repo.get_comments(
        session=session, result_ids=result_ids
    ):
        comments_by_result[comment.analyte_result_id].append(
            ResultCommentDetailPublic(
                **comment.model_dump(),
                user_name=_display_name(user.full_name, user.email),
            )
        )

    corrections_by_result: dict[
        uuid.UUID, list[ResultCorrectionHistoryPublic]
    ] = defaultdict(list)
    if include_audit:
        for audit, user in result_repo.get_result_audits(
            session=session, result_ids=result_ids
        ):
            if not isinstance(audit.new_values, dict):
                continue
            reason = audit.new_values.get("correction_reason")
            if not reason:
                continue
            corrections_by_result[audit.record_id].append(
                ResultCorrectionHistoryPublic(
                    id=audit.id,
                    old_value=(
                        audit.old_values.get("result_value")
                        if isinstance(audit.old_values, dict)
                        else None
                    ),
                    new_value=audit.new_values.get("result_value"),
                    reason=reason,
                    performed_by_name=(
                        _display_name(user.full_name, user.email) if user else None
                    ),
                    performed_at=audit.performed_at,
                )
            )

    notifications_by_result: dict[
        uuid.UUID, list[CriticalNotificationDetailPublic]
    ] = defaultdict(list)
    analyte_by_result = {
        row[8].id: row[4] for row in rows if row[8] is not None
    }
    value_by_result = {
        row[8].id: row[8].result_value for row in rows if row[8] is not None
    }
    for (
        notification,
        by_name,
        by_email,
        to_name,
        to_email,
        ack_name,
        ack_email,
    ) in result_repo.get_notifications(session=session, result_ids=result_ids):
        notifications_by_result[notification.analyte_result_id].append(
            _notification_public(
                notification=notification,
                accession_number=order.accession_number,
                patient_name=f"{patient.first_name} {patient.last_name}",
                analyte=analyte_by_result[notification.analyte_result_id],
                result_value=value_by_result[notification.analyte_result_id],
                notified_by_name=_display_name(by_name, by_email),
                notified_to_name=_display_name(to_name, to_email),
                acknowledged_by_name=(
                    _display_name(ack_name, ack_email)
                    if ack_name or ack_email
                    else None
                ),
            )
        )

    tests: dict[uuid.UUID, ResultTestWorkspacePublic] = {}
    for row in rows:
        (
            item,
            catalog,
            category,
            _snapshot,
            analyte,
            unit,
            specimen,
            specimen_type,
            result,
            resulted_name,
            resulted_email,
            verified_name,
            verified_email,
        ) = row
        test = tests.setdefault(
            item.id,
            ResultTestWorkspacePublic(
                order_item_id=item.id,
                catalog_id=catalog.id,
                catalog_code=catalog.code,
                catalog_name=catalog.name,
                category_id=category.id if category else None,
                category_name=category.name if category else None,
                is_reflex_added=item.is_reflex_added,
            ),
        )
        notifications = (
            notifications_by_result.get(result.id, []) if result else []
        )
        validation = None
        if result and result.result_value is not None:
            classification = (
                "critical"
                if result.is_critical
                else "delta"
                if result.delta_flag
                else "abnormal"
                if result.is_abnormal
                else "normal"
            )
            validation = ResultValidationOutcomePublic(
                classification=classification,
                message="Résultat validé",
                is_abnormal=result.is_abnormal,
                is_critical=result.is_critical,
                delta_flag=result.delta_flag,
            )
        image_url = None
        if (
            result
            and result.result_value
            and analyte.data_type == AnalyteDataType.image
        ):
            from app.services import object_storage

            image_url = object_storage.presigned_url(result.result_value)
        test.analytes.append(
            ResultAnalyteWorkspacePublic(
                result_id=result.id if result else None,
                analyte_id=analyte.id,
                analyte_code=analyte.code,
                analyte_name=analyte.name,
                data_type=analyte.data_type,
                unit_name=unit.name if unit else None,
                options_data=analyte.options_data,
                reference_text=analyte.reference_text,
                is_calculated=analyte.is_calculated,
                specimen_id=specimen.id,
                specimen_type_name=specimen_type.name,
                result_value=result.result_value if result else None,
                image_url=image_url,
                status=result.status if result else ResultStatus.pending,
                validation_rule_id=result.validation_rule_id if result else None,
                validation=validation,
                is_abnormal=result.is_abnormal if result else False,
                is_critical=result.is_critical if result else False,
                delta_flag=result.delta_flag if result else False,
                resulted_by_name=(
                    _display_name(resulted_name, resulted_email)
                    if resulted_name or resulted_email
                    else None
                ),
                resulted_at=result.resulted_at if result else None,
                verified_by_name=(
                    _display_name(verified_name, verified_email)
                    if verified_name or verified_email
                    else None
                ),
                verified_at=result.verified_at if result else None,
                escalation_required=bool(
                    result
                    and result.is_critical
                    and not notifications
                ),
                critical_notifications=notifications,
                comments=(
                    comments_by_result.get(result.id, []) if result else []
                ),
                corrections=(
                    corrections_by_result.get(result.id, []) if result else []
                ),
            )
        )

    for test in tests.values():
        test.resulted_count = sum(
            item.status in {ResultStatus.resulted, ResultStatus.verified}
            for item in test.analytes
        )
        test.verified_count = sum(
            item.status == ResultStatus.verified for item in test.analytes
        )
    workspace = ResultWorkspacePublic(
        order_id=order.id,
        revision_number=order.revision_number,
        accession_number=order.accession_number,
        patient_id=patient.id,
        patient_identifier=patient.identifier,
        patient_name=f"{patient.first_name} {patient.last_name}",
        patient_date_of_birth=patient.date_of_birth,
        patient_gender=patient.gender,
        patient_context_id=order.patient_context_id,
        patient_context_name=context.name if context else None,
        doctor_name=(
            f"{doctor.first_name} {doctor.last_name}" if doctor else None
        ),
        order_status=order.status,
        interpretation_html=order.interpretation_html,
        interpretation_updated_by_name=(
            _display_name(interpretation_user.full_name, interpretation_user.email)
            if interpretation_user
            else None
        ),
        interpretation_updated_at=order.interpretation_updated_at,
        tests=list(tests.values()),
    )
    workspace.total_count = sum(len(test.analytes) for test in workspace.tests)
    workspace.resulted_count = sum(
        test.resulted_count for test in workspace.tests
    )
    workspace.verified_count = sum(
        test.verified_count for test in workspace.tests
    )
    workspace.consistency_outcomes = _evaluate_consistency(
        session=session,
        workspace=workspace,
        raise_on_error=False,
    )
    consistency_blocker = next(
        (
            outcome.message
            for outcome in workspace.consistency_outcomes
            if outcome.severity == RuleSeverity.error
        ),
        None,
    )
    for test in workspace.tests:
        for analyte in test.analytes:
            if analyte.result_id is None:
                analyte.verification_blocker = (
                    "Le résultat doit être saisi avant vérification"
                )
                continue
            result = next(
                (
                    row[8]
                    for row in rows
                    if row[8] is not None and row[8].id == analyte.result_id
                ),
                None,
            )
            if result is None:
                continue
            blocker = _verification_blocker(
                session=session,
                result=result,
                consistency_blocker=consistency_blocker,
            )
            analyte.verification_eligible = blocker is None
            analyte.verification_blocker = blocker
    return workspace


def update_interpretation(
    *,
    session: Session,
    order_id: uuid.UUID,
    request: ResultInterpretationUpdate,
    user_id: uuid.UUID,
) -> ResultWorkspacePublic:
    order = result_repo.get_order_for_update(session=session, order_id=order_id)
    if order is None:
        raise NotFoundError("Demande non trouvée")
    if order.status == OrderStatus.cancelled:
        raise ConflictError("Une demande annulée ne peut pas être modifiée")
    from app.services import report as report_service

    raw_html = request.interpretation_html or ""
    sanitized_html = report_service.sanitize_html(raw_html)
    if not report_service.html_to_plain_text(sanitized_html) and (
        "data-variable-kind" not in sanitized_html
    ):
        sanitized_html = ""
    old_values = {
        "interpretation_html": order.interpretation_html,
        "interpretation_updated_by_id": (
            str(order.interpretation_updated_by_id)
            if order.interpretation_updated_by_id
            else None
        ),
        "interpretation_updated_at": (
            order.interpretation_updated_at.isoformat()
            if order.interpretation_updated_at
            else None
        ),
    }
    now = datetime.now(timezone.utc)
    order.interpretation_html = sanitized_html or None
    order.interpretation_updated_by_id = user_id if sanitized_html else None
    order.interpretation_updated_at = now if sanitized_html else None
    session.add(order)
    session.add(
        AuditLog(
            table_name="orders",
            record_id=order.id,
            action=AuditAction.update,
            old_values=old_values,
            new_values={
                "interpretation_html": order.interpretation_html,
                "interpretation_updated_by_id": (
                    str(order.interpretation_updated_by_id)
                    if order.interpretation_updated_by_id
                    else None
                ),
                "interpretation_updated_at": (
                    order.interpretation_updated_at.isoformat()
                    if order.interpretation_updated_at
                    else None
                ),
            },
            performed_by_id=user_id,
        )
    )
    session.commit()
    return get_workspace(session=session, order_id=order.id)


def enter_results(
    *,
    session: Session,
    order_id: uuid.UUID,
    request: ResultBulkEntryRequest,
    user_id: uuid.UUID,
) -> ResultSubmissionPublic:
    order = result_repo.get_order_for_update(session=session, order_id=order_id)
    if order is None:
        raise NotFoundError("Demande non trouvée")
    if order.status not in ELIGIBLE_ORDER_STATUSES:
        raise ConflictError(
            "Cette demande n'est pas disponible pour la saisie des résultats"
        )
    item = session.get(OrderItem, request.order_item_id)
    if item is None or item.order_id != order.id or not item.is_active:
        raise NotFoundError("Examen de la demande non trouvé")
    patient = result_repo.get_order_header(
        session=session, order_id=order.id
    )[1]
    allowed_analytes = {
        analyte.id: analyte
        for _snapshot, analyte in session.exec(
            select(OrderCatalogItemAnalyte, Analyte)
            .join(Analyte, OrderCatalogItemAnalyte.analyte_id == Analyte.id)
            .where(
                OrderCatalogItemAnalyte.order_item_id == item.id,
                OrderCatalogItemAnalyte.is_active == True,  # noqa: E712
            )
        ).all()
    }
    linked_specimens = {
        specimen.id: specimen
        for specimen in session.exec(
            select(OrderSpecimen)
            .join(
                OrderItemSpecimen,
                OrderItemSpecimen.order_specimen_id == OrderSpecimen.id,
            )
            .where(
                OrderItemSpecimen.order_item_id == item.id,
                OrderSpecimen.is_superseded == False,  # noqa: E712
            )
        ).all()
    }
    now = datetime.now(timezone.utc)
    saved_ids: list[uuid.UUID] = []
    critical_ids: list[uuid.UUID] = []
    for entry in request.values:
        analyte = allowed_analytes.get(entry.analyte_id)
        specimen = linked_specimens.get(entry.specimen_id)
        if analyte is None or specimen is None:
            raise BusinessRuleError(
                "Un résultat ne correspond pas à cet examen"
            )
        if specimen.status not in {
            SpecimenStatus.collected,
            SpecimenStatus.processed,
        }:
            raise ConflictError("Le prélèvement requis n'est pas collecté")
        value = _validate_basic_value(analyte, entry.result_value)
        current = result_repo.get_active_result(
            session=session,
            order_item_id=item.id,
            analyte_id=analyte.id,
            specimen_id=specimen.id,
        )
        user = session.get(User, user_id)
        action = "edit" if current and current.result_value is not None else "enter"
        if user is None or not permission_service.check_permission(
            session=session,
            user=user,
            resource="results",
            action=action,
        ):
            raise ForbiddenError(
                "L'utilisateur ne dispose pas de privilèges suffisants"
            )
        if current is not None and current.status == ResultStatus.verified:
            raise ConflictError("Un résultat vérifié ne peut plus être modifié")
        validation, rule_id = _validate_result(
            session=session,
            order=order,
            patient=patient,
            analyte=analyte,
            value=value,
            result_id=current.id if current else None,
        )
        db_result = current or result_repo.create(
            session=session,
            db_obj=AnalyteResult(
                order_item_id=item.id,
                analyte_id=analyte.id,
                specimen_id=specimen.id,
            ),
        )
        db_result.result_value = value
        db_result.instrument_id = entry.instrument_id
        db_result.validation_rule_id = rule_id
        db_result.is_abnormal = validation.is_abnormal
        db_result.is_critical = validation.is_critical
        db_result.delta_flag = validation.delta_flag
        db_result.status = ResultStatus.resulted
        db_result.resulted_by_id = user_id
        db_result.resulted_at = now
        session.add(db_result)
        session.flush()
        saved_ids.append(db_result.id)
        if db_result.is_critical:
            critical_ids.append(db_result.id)

    _calculate_analytes(
        session=session, order=order, patient=patient, user_id=user_id
    )
    workspace = get_workspace(session=session, order_id=order.id)
    consistency = _evaluate_consistency(session=session, workspace=workspace)
    reflex = _evaluate_reflexes(
        session=session, order=order, workspace=workspace, user_id=user_id
    )
    _refresh_order_status(session=session, order=order)
    session.commit()
    workspace = get_workspace(session=session, order_id=order.id)
    workspace.consistency_outcomes = consistency
    workspace.reflex_outcomes = reflex
    return ResultSubmissionPublic(
        workspace=workspace,
        saved_result_ids=saved_ids,
        critical_result_ids=critical_ids,
        consistency_outcomes=consistency,
        reflex_outcomes=reflex,
    )


def upload_image_result(
    *,
    session: Session,
    order_id: uuid.UUID,
    order_item_id: uuid.UUID,
    analyte_id: uuid.UUID,
    specimen_id: uuid.UUID,
    content_type: str | None,
    data: bytes,
    user_id: uuid.UUID,
) -> ResultSubmissionPublic:
    analyte = session.get(Analyte, analyte_id)
    if analyte is None or analyte.data_type != AnalyteDataType.image:
        raise BusinessRuleError("Cet analyte n'accepte pas d'image")
    current = result_repo.get_active_result(
        session=session,
        order_item_id=order_item_id,
        analyte_id=analyte_id,
        specimen_id=specimen_id,
    )
    old_key = current.result_value if current else None
    from app.services import object_storage

    object_key = object_storage.upload_result_image(
        order_id=order_id,
        order_item_id=order_item_id,
        analyte_id=analyte_id,
        content_type=content_type,
        data=data,
    )
    try:
        response = enter_results(
            session=session,
            order_id=order_id,
            request=ResultBulkEntryRequest(
                order_item_id=order_item_id,
                values=[
                    ResultEntryValue(
                        analyte_id=analyte_id,
                        specimen_id=specimen_id,
                        result_value=object_key,
                    )
                ],
            ),
            user_id=user_id,
        )
    except Exception:
        object_storage.delete_object(object_key)
        raise
    if old_key and old_key != object_key:
        object_storage.delete_object(old_key)
    return response


def _evaluate_reflexes(
    *,
    session: Session,
    order: Order,
    workspace: ResultWorkspacePublic,
    user_id: uuid.UUID,
) -> list[ResultReflexOutcomePublic]:
    values_by_id = {
        analyte.analyte_id: analyte.result_value
        for test in workspace.tests
        for analyte in test.analytes
        if analyte.result_value is not None
    }
    rules = result_repo.get_reflex_rules(
        session=session, analyte_ids=list(values_by_id)
    )
    existing_catalog_ids = {
        item.catalog_id
        for item in session.exec(
            select(OrderItem).where(
                OrderItem.order_id == order.id,
                OrderItem.is_active == True,  # noqa: E712
            )
        ).all()
    }
    outcomes: list[ResultReflexOutcomePublic] = []
    for rule in rules:
        value = values_by_id.get(rule.trigger_analyte_id)
        if value is None or not automated_rule_service._evaluate_reflex(
            operator_value=rule.trigger_operator,
            trigger_value=rule.trigger_value,
            sample_value=value,
        ):
            continue
        catalog = session.get(Catalog, rule.action_catalog_id)
        if catalog is None or catalog.is_deleted:
            continue
        added = catalog.id not in existing_catalog_ids
        if added:
            from app.services import order as order_service

            added_ids = order_service.add_reflex_catalog(
                session=session,
                order=order,
                catalog_id=catalog.id,
                performed_by_id=user_id,
            )
            existing_catalog_ids.update(added_ids)
        outcomes.append(
            ResultReflexOutcomePublic(
                rule_id=rule.id,
                catalog_id=catalog.id,
                catalog_code=catalog.code,
                catalog_name=catalog.name,
                added=added,
            )
        )
    return outcomes


def add_comment(
    *,
    session: Session,
    result_id: uuid.UUID,
    request: ResultCommentRequest,
    user_id: uuid.UUID,
) -> ResultCommentDetailPublic:
    result = session.get(AnalyteResult, result_id)
    if result is None or result.is_superseded:
        raise NotFoundError("Résultat non trouvé")
    comment = result_repo.create(
        session=session,
        db_obj=AnalyteResultComment(
            analyte_result_id=result.id,
            user_id=user_id,
            comment=request.comment.strip(),
        ),
    )
    user = session.get(User, user_id)
    session.commit()
    return ResultCommentDetailPublic(
        id=comment.id,
        analyte_result_id=comment.analyte_result_id,
        user_id=comment.user_id,
        comment=comment.comment,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        user_name=_display_name(
            user.full_name if user else None, user.email if user else None
        ),
    )


def create_critical_notification(
    *,
    session: Session,
    result_id: uuid.UUID,
    request: CriticalNotificationCreate,
    user_id: uuid.UUID,
) -> CriticalNotificationDetailPublic:
    result = result_repo.get_result_for_update(
        session=session, result_id=result_id
    )
    if result is None or result.is_superseded:
        raise NotFoundError("Résultat non trouvé")
    if not result.is_critical:
        raise BusinessRuleError("Ce résultat n'est pas critique")
    existing = session.exec(
        select(CriticalNotification).where(
            CriticalNotification.analyte_result_id == result.id,
            CriticalNotification.acknowledged == False,  # noqa: E712
        )
    ).first()
    if existing is not None:
        return get_critical_notification(
            session=session,
            notification_id=existing.id,
        )
    recipient = session.get(User, request.notified_to_id)
    if (
        recipient is None
        or not recipient.is_active
        or not result_repo.is_critical_recipient(
            session=session,
            user_id=recipient.id,
        )
    ):
        raise BusinessRuleError("Destinataire non disponible")
    notification = result_repo.create(
        session=session,
        db_obj=CriticalNotification(
            analyte_result_id=result.id,
            notified_by_id=user_id,
            notified_to_id=recipient.id,
            method=request.method,
            notes=(request.notes or "").strip() or None,
        ),
    )
    session.commit()
    return get_critical_notification(session=session, notification_id=notification.id)


def acknowledge_critical_notification(
    *,
    session: Session,
    notification_id: uuid.UUID,
    request: CriticalNotificationAcknowledge,
    user_id: uuid.UUID,
) -> CriticalNotificationDetailPublic:
    notification = session.exec(
        select(CriticalNotification)
        .where(CriticalNotification.id == notification_id)
        .with_for_update()
    ).first()
    if notification is None:
        raise NotFoundError("Notification critique non trouvée")
    if notification.acknowledged:
        raise ConflictError("Cette notification est déjà acquittée")
    notification.acknowledged = True
    notification.acknowledged_at = datetime.now(timezone.utc)
    notification.acknowledged_by_id = user_id
    extra_notes = (request.notes or "").strip()
    if extra_notes:
        notification.notes = (
            f"{notification.notes}\n{extra_notes}"
            if notification.notes
            else extra_notes
        )
    session.add(notification)
    session.commit()
    return get_critical_notification(session=session, notification_id=notification.id)


def _verification_blocker(
    *,
    session: Session,
    result: AnalyteResult,
    consistency_blocker: str | None = None,
) -> str | None:
    if result.status == ResultStatus.verified:
        return "Résultat déjà vérifié"
    if result.result_value is None or result.status != ResultStatus.resulted:
        return "Le résultat doit être saisi avant vérification"
    if consistency_blocker:
        return consistency_blocker
    if result.is_critical:
        acknowledged = session.exec(
            select(CriticalNotification.id).where(
                CriticalNotification.analyte_result_id == result.id,
                CriticalNotification.acknowledged == True,  # noqa: E712
            )
        ).first()
        if acknowledged is None:
            return "La valeur critique doit être notifiée et acquittée"
    return None


def verify_result(
    *, session: Session, result_id: uuid.UUID, user_id: uuid.UUID
) -> ResultWorkspacePublic:
    result = result_repo.get_result_for_update(
        session=session, result_id=result_id
    )
    if result is None or result.is_superseded:
        raise NotFoundError("Résultat non trouvé")
    blocker = _verification_blocker(session=session, result=result)
    if blocker:
        raise BusinessRuleError(blocker)
    result.status = ResultStatus.verified
    result.verified_by_id = user_id
    result.verified_at = datetime.now(timezone.utc)
    session.add(result)
    item = session.get(OrderItem, result.order_item_id)
    if item is None:
        raise NotFoundError("Examen de la demande non trouvé")
    order = result_repo.get_order_for_update(
        session=session, order_id=item.order_id
    )
    if order is None:
        raise NotFoundError("Demande non trouvée")
    _refresh_order_status(session=session, order=order)
    session.commit()
    return get_workspace(session=session, order_id=order.id)


def correct_verified_result(
    *,
    session: Session,
    result_id: uuid.UUID,
    request: ResultCorrectionRequest,
    user_id: uuid.UUID,
) -> ResultWorkspacePublic:
    result = result_repo.get_result_for_update(
        session=session, result_id=result_id
    )
    if result is None or result.is_superseded:
        raise NotFoundError("Résultat non trouvé")
    if result.status != ResultStatus.verified:
        raise ConflictError("Seul un résultat vérifié peut être corrigé")
    reason = request.reason.strip()
    if not reason:
        raise BusinessRuleError("Le motif de correction est requis")
    item = session.get(OrderItem, result.order_item_id)
    analyte = session.get(Analyte, result.analyte_id)
    if item is None or analyte is None:
        raise NotFoundError("Résultat non trouvé")
    order = result_repo.get_order_for_update(
        session=session, order_id=item.order_id
    )
    if order is None:
        raise NotFoundError("Demande non trouvée")
    patient = result_repo.get_order_header(
        session=session, order_id=order.id
    )[1]
    value = _validate_basic_value(analyte, request.result_value)
    validation, rule_id = _validate_result(
        session=session,
        order=order,
        patient=patient,
        analyte=analyte,
        value=value,
        result_id=result.id,
    )
    old_values = {
        "result_value": result.result_value,
        "instrument_id": str(result.instrument_id) if result.instrument_id else None,
        "status": result.status.value,
        "verified_by_id": (
            str(result.verified_by_id) if result.verified_by_id else None
        ),
        "verified_at": result.verified_at.isoformat() if result.verified_at else None,
    }
    result.result_value = value
    result.instrument_id = request.instrument_id
    result.validation_rule_id = rule_id
    result.is_abnormal = validation.is_abnormal
    result.is_critical = validation.is_critical
    result.delta_flag = validation.delta_flag
    result.status = ResultStatus.resulted
    result.resulted_by_id = user_id
    result.resulted_at = datetime.now(timezone.utc)
    result.verified_by_id = None
    result.verified_at = None
    session.add(result)
    reports = result_repo.get_active_reports(session=session, order_id=order.id)
    for report in reports:
        report.is_voided = True
        session.add(report)
    session.add(
        AuditLog(
            table_name="analyte_results",
            record_id=result.id,
            action=AuditAction.update,
            old_values=old_values,
            new_values={
                "result_value": value,
                "instrument_id": (
                    str(request.instrument_id) if request.instrument_id else None
                ),
                "status": ResultStatus.resulted.value,
                "verified_by_id": None,
                "verified_at": None,
                "correction_reason": reason,
                "voided_report_count": len(reports),
            },
            performed_by_id=user_id,
        )
    )
    _refresh_order_status(session=session, order=order)
    session.commit()
    return get_workspace(session=session, order_id=order.id, include_audit=True)


def correct_verified_image_result(
    *,
    session: Session,
    result_id: uuid.UUID,
    reason: str,
    content_type: str | None,
    data: bytes,
    user_id: uuid.UUID,
) -> ResultWorkspacePublic:
    result = result_repo.get_result_for_update(
        session=session, result_id=result_id
    )
    if result is None or result.is_superseded:
        raise NotFoundError("Résultat non trouvé")
    analyte = session.get(Analyte, result.analyte_id)
    item = session.get(OrderItem, result.order_item_id)
    if (
        analyte is None
        or item is None
        or analyte.data_type != AnalyteDataType.image
    ):
        raise BusinessRuleError("Ce résultat n'est pas une image")
    old_key = result.result_value
    from app.services import object_storage

    object_key = object_storage.upload_result_image(
        order_id=item.order_id,
        order_item_id=item.id,
        analyte_id=analyte.id,
        content_type=content_type,
        data=data,
    )
    try:
        workspace = correct_verified_result(
            session=session,
            result_id=result.id,
            request=ResultCorrectionRequest(
                result_value=object_key,
                reason=reason,
            ),
            user_id=user_id,
        )
    except Exception:
        object_storage.delete_object(object_key)
        raise
    if old_key and old_key != object_key:
        object_storage.delete_object(old_key)
    return workspace


def verify_order(
    *, session: Session, order_id: uuid.UUID, user_id: uuid.UUID
) -> ResultBulkVerificationPublic:
    order = result_repo.get_order_for_update(session=session, order_id=order_id)
    if order is None:
        raise NotFoundError("Demande non trouvée")
    workspace = get_workspace(session=session, order_id=order.id)
    results = result_repo.get_order_results_for_update(
        session=session, order_id=order.id
    )
    results_by_key = {
        (result.order_item_id, result.analyte_id, result.specimen_id): result
        for result in results
    }
    consistency_blocker = next(
        (
            outcome.message
            for outcome in workspace.consistency_outcomes
            if outcome.severity == RuleSeverity.error
        ),
        None,
    )
    skipped: list[ResultVerificationSkipPublic] = []
    eligible: list[AnalyteResult] = []
    for test in workspace.tests:
        for analyte in test.analytes:
            result = results_by_key.get(
                (test.order_item_id, analyte.analyte_id, analyte.specimen_id)
            )
            if result is not None and result.status == ResultStatus.verified:
                continue
            blocker = (
                _verification_blocker(
                    session=session,
                    result=result,
                    consistency_blocker=consistency_blocker,
                )
                if result is not None
                else "Le résultat doit être saisi avant vérification"
            )
            if blocker:
                skipped.append(
                    ResultVerificationSkipPublic(
                        result_id=result.id if result else None,
                        order_item_id=test.order_item_id,
                        analyte_id=analyte.analyte_id,
                        specimen_id=analyte.specimen_id,
                        analyte_name=analyte.analyte_name,
                        message=blocker,
                    )
                )
                continue
            eligible.append(result)

    now = datetime.now(timezone.utc)
    for result in eligible:
        result.status = ResultStatus.verified
        result.verified_by_id = user_id
        result.verified_at = now
        session.add(result)
    _refresh_order_status(session=session, order=order)
    session.commit()
    return ResultBulkVerificationPublic(
        workspace=get_workspace(session=session, order_id=order.id),
        verified_count=len(eligible),
        skipped_count=len(skipped),
        verified_result_ids=[result.id for result in eligible],
        skipped=skipped,
    )


def get_queue(
    *,
    session: Session,
    mode: str,
    skip: int = 0,
    limit: int = 25,
    search: str | None = None,
    category_id: uuid.UUID | None = None,
    flagged: bool | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    sort_order: SortOrder = SortOrder.desc,
) -> ResultQueuePublic:
    ids, count = result_repo.get_queue(
        session=session,
        mode=mode,
        skip=skip,
        limit=limit,
        search=search,
        category_id=category_id,
        flagged=flagged,
        created_from=created_from,
        created_to=created_to,
        sort_order=sort_order,
    )
    data = []
    for order_id in ids:
        workspace = get_workspace(session=session, order_id=order_id)
        categories = list(
            dict.fromkeys(
                test.category_name
                for test in workspace.tests
                if test.category_name
            )
        )
        order = session.get(Order, order_id)
        data.append(
            ResultQueueItemPublic(
                order_id=workspace.order_id,
                accession_number=workspace.accession_number,
                patient_id=workspace.patient_id,
                patient_identifier=workspace.patient_identifier,
                patient_name=workspace.patient_name,
                order_status=workspace.order_status,
                category_summary=", ".join(categories) or "Sans catégorie",
                total_count=workspace.total_count,
                resulted_count=workspace.resulted_count,
                verified_count=workspace.verified_count,
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
                created_at=order.created_at if order else None,
            )
        )
    return ResultQueuePublic(data=data, count=count)


def get_recipients(
    *, session: Session, search: str | None, skip: int, limit: int
) -> CriticalRecipientsPublic:
    users, count = result_repo.get_recipient_users(
        session=session, search=search, skip=skip, limit=limit
    )
    return CriticalRecipientsPublic(
        data=[
            CriticalRecipientPublic(
                id=user.id,
                name=_display_name(user.full_name, user.email),
                email=str(user.email),
            )
            for user in users
        ],
        count=count,
    )


def get_critical_notification(
    *, session: Session, notification_id: uuid.UUID
) -> CriticalNotificationDetailPublic:
    rows = _critical_rows(session=session, notification_id=notification_id)
    if not rows:
        raise NotFoundError("Notification critique non trouvée")
    return _critical_row_public(rows[0])


def _critical_rows(
    *,
    session: Session,
    notification_id: uuid.UUID | None = None,
    acknowledged: bool | None = None,
    search: str | None = None,
):
    notified_by = User.__table__.alias("notified_by")
    notified_to = User.__table__.alias("notified_to")
    acknowledged_by = User.__table__.alias("acknowledged_by")
    statement = (
        select(
            CriticalNotification,
            AnalyteResult,
            Analyte,
            Order,
            Patient,
            notified_by.c.full_name,
            notified_by.c.email,
            notified_to.c.full_name,
            notified_to.c.email,
            acknowledged_by.c.full_name,
            acknowledged_by.c.email,
        )
        .join(AnalyteResult, CriticalNotification.analyte_result_id == AnalyteResult.id)
        .join(Analyte, AnalyteResult.analyte_id == Analyte.id)
        .join(OrderItem, AnalyteResult.order_item_id == OrderItem.id)
        .join(Order, OrderItem.order_id == Order.id)
        .join(Patient, Order.patient_id == Patient.id)
        .join(notified_by, CriticalNotification.notified_by_id == notified_by.c.id)
        .join(notified_to, CriticalNotification.notified_to_id == notified_to.c.id)
        .join(
            acknowledged_by,
            CriticalNotification.acknowledged_by_id == acknowledged_by.c.id,
            isouter=True,
        )
    )
    if notification_id is not None:
        statement = statement.where(CriticalNotification.id == notification_id)
    if acknowledged is not None:
        statement = statement.where(CriticalNotification.acknowledged == acknowledged)
    if search:
        query = f"%{search.strip()}%"
        statement = statement.where(
            col(Order.accession_number).ilike(query)
            | col(Patient.identifier).ilike(query)
            | col(Patient.first_name).ilike(query)
            | col(Patient.last_name).ilike(query)
            | col(Analyte.name).ilike(query)
        )
    return list(
        session.execute(
            statement.order_by(col(CriticalNotification.created_at).desc())
        ).all()
    )

def _critical_row_public(row) -> CriticalNotificationDetailPublic:
    (
        notification,
        result,
        analyte,
        order,
        patient,
        by_name,
        by_email,
        to_name,
        to_email,
        ack_name,
        ack_email,
    ) = row
    return _notification_public(
        notification=notification,
        accession_number=order.accession_number,
        patient_name=f"{patient.first_name} {patient.last_name}",
        analyte=analyte,
        result_value=result.result_value,
        notified_by_name=_display_name(by_name, by_email),
        notified_to_name=_display_name(to_name, to_email),
        acknowledged_by_name=(
            _display_name(ack_name, ack_email) if ack_name or ack_email else None
        ),
    )


def get_critical_notifications(
    *,
    session: Session,
    skip: int,
    limit: int,
    acknowledged: bool | None,
    search: str | None,
) -> CriticalNotificationListPublic:
    rows = _critical_rows(
        session=session, acknowledged=acknowledged, search=search
    )
    return CriticalNotificationListPublic(
        data=[_critical_row_public(row) for row in rows[skip : skip + limit]],
        count=len(rows),
    )


def get_unacknowledged_count(*, session: Session) -> CriticalNotificationCountPublic:
    count = session.exec(
        select(CriticalNotification.id).where(
            CriticalNotification.acknowledged == False  # noqa: E712
        )
    ).all()
    return CriticalNotificationCountPublic(count=len(count))
