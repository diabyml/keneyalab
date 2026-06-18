import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlmodel import Session, select

from app.core.exceptions import ConflictError
from app.models import User
from app.models.lis import (
    Analyte,
    AnalyteDataType,
    AnalyteResult,
    AuditLog,
    Catalog,
    CatalogItemAnalyte,
    CatalogSpecimenRequirement,
    CatalogType,
    CriticalMethod,
    CriticalNotificationCreate,
    GenderType,
    Invoice,
    OrderCatalogItemAnalyte,
    OrderCreate,
    OrderItem,
    OrderItemAnalyteCustomizeRequest,
    OrderItemSpecimen,
    OrderSpecimen,
    OrderStatus,
    Patient,
    ResultBulkEntryRequest,
    ResultCommentRequest,
    ResultCorrectionRequest,
    ResultEntryValue,
    ResultStatus,
    SpecimenType,
)
from app.services.order import create_order, customize_order_item_analytes
from app.services.result import (
    add_comment,
    correct_verified_result,
    create_critical_notification,
    enter_results,
    get_queue,
    get_workspace,
    upload_image_result,
    verify_order,
)
from app.services.specimen import collect_all


@pytest.fixture(scope="module", autouse=True)
def cleanup_result_orders(db: Session):
    yield
    db.rollback()
    db.execute(
        text(
            "DELETE FROM invoices WHERE order_id IN ("
            "SELECT o.id FROM orders o JOIN patients p ON p.id = o.patient_id "
            "WHERE p.identifier LIKE 'PAT-RES-%')"
        )
    )
    db.execute(
        text(
            "DELETE FROM critical_notifications WHERE analyte_result_id IN ("
            "SELECT ar.id FROM analyte_results ar "
            "JOIN order_items oi ON oi.id = ar.order_item_id "
            "JOIN orders o ON o.id = oi.order_id "
            "JOIN patients p ON p.id = o.patient_id "
            "WHERE p.identifier LIKE 'PAT-RES-%')"
        )
    )
    db.execute(
        text(
            "DELETE FROM analyte_results WHERE order_item_id IN ("
            "SELECT oi.id FROM order_items oi "
            "JOIN orders o ON o.id = oi.order_id "
            "JOIN patients p ON p.id = o.patient_id "
            "WHERE p.identifier LIKE 'PAT-RES-%')"
        )
    )
    db.execute(
        text(
            "DELETE FROM orders WHERE patient_id IN ("
            "SELECT id FROM patients WHERE identifier LIKE 'PAT-RES-%')"
        )
    )
    db.execute(text("DELETE FROM patients WHERE identifier LIKE 'PAT-RES-%'"))
    db.execute(text("DELETE FROM catalog WHERE code LIKE 'RES-%'"))
    db.execute(text("DELETE FROM analytes WHERE code LIKE 'ANA-%'"))
    db.execute(
        text("DELETE FROM specimen_types WHERE name LIKE 'Sérum résultats %'")
    )
    db.commit()


def _result_order(
    db: Session,
    *,
    analyte_count: int = 1,
    data_type: AnalyteDataType = AnalyteDataType.numeric,
):
    suffix = uuid.uuid4().hex[:8].upper()
    patient = Patient(
        identifier=f"PAT-RES-{suffix}",
        first_name="Aminata",
        last_name="Diallo",
        date_of_birth=date(1992, 5, 4),
        gender=GenderType.female,
    )
    specimen_type = SpecimenType(
        name=f"Sérum résultats {suffix}",
        color="#dc2626",
    )
    catalog = Catalog(
        type=CatalogType.item,
        code=f"RES-{suffix}",
        name=f"Test résultats {suffix}",
        price=Decimal("2500.00"),
    )
    analytes = [
        Analyte(
            code=f"ANA-{suffix}-{index}",
            name=f"Analyte résultats {suffix} {index}",
            data_type=data_type,
        )
        for index in range(analyte_count)
    ]
    db.add_all([patient, specimen_type, catalog, *analytes])
    db.flush()
    db.add_all(
        [
            CatalogSpecimenRequirement(
                catalog_id=catalog.id,
                specimen_type_id=specimen_type.id,
                volume_ml=Decimal("2.00"),
            ),
            *[
                CatalogItemAnalyte(
                    catalog_item_id=catalog.id,
                    analyte_id=analyte.id,
                    sort_order=index,
                )
                for index, analyte in enumerate(analytes)
            ],
        ]
    )
    db.commit()
    user = db.exec(select(User).where(User.is_superuser == True)).first()  # noqa: E712
    assert user is not None
    order = create_order(
        session=db,
        request=OrderCreate(patient_id=patient.id, catalog_ids=[catalog.id]),
        created_by_id=user.id,
        can_override_prices=True,
        can_discount=True,
        can_collect_payment=True,
    )
    item = db.exec(
        select(OrderItem).where(OrderItem.order_id == order.id)
    ).one()
    specimen = db.exec(
        select(OrderSpecimen)
        .join(
            OrderItemSpecimen,
            OrderItemSpecimen.order_specimen_id == OrderSpecimen.id,
        )
        .where(OrderItemSpecimen.order_item_id == item.id)
    ).one()
    return (
        order,
        user,
        item,
        specimen,
        analytes[0] if analyte_count == 1 else analytes,
    )


def test_result_entry_requires_collection_and_completes_after_verification(
    db: Session,
) -> None:
    order, user, item, specimen, analyte = _result_order(db)
    request = ResultBulkEntryRequest(
        order_item_id=item.id,
        values=[
            ResultEntryValue(
                analyte_id=analyte.id,
                specimen_id=specimen.id,
                result_value="12.5",
            )
        ],
    )

    with pytest.raises(ConflictError):
        enter_results(
            session=db,
            order_id=order.id,
            request=request,
            user_id=user.id,
        )
    db.rollback()

    collect_all(session=db, order_id=order.id, collected_by_id=user.id)
    workspace = get_workspace(session=db, order_id=order.id)
    assert workspace.total_count == 1
    submission = enter_results(
        session=db,
        order_id=order.id,
        request=request,
        user_id=user.id,
    )
    assert submission.workspace.order_status == OrderStatus.in_progress
    assert submission.workspace.resulted_count == 1
    result_id = submission.saved_result_ids[0]

    updated = enter_results(
        session=db,
        order_id=order.id,
        request=request.model_copy(
            update={
                "values": [
                    ResultEntryValue(
                        analyte_id=analyte.id,
                        specimen_id=specimen.id,
                        result_value="13.0",
                    )
                ]
            }
        ),
        user_id=user.id,
    )
    assert updated.saved_result_ids == [result_id]
    active_results = db.exec(
        select(AnalyteResult).where(
            AnalyteResult.order_item_id == item.id,
            AnalyteResult.is_superseded == False,  # noqa: E712
        )
    ).all()
    assert len(active_results) == 1
    assert active_results[0].result_value == "13.0"

    comment = add_comment(
        session=db,
        result_id=result_id,
        request=ResultCommentRequest(comment="Contrôle technique conforme"),
        user_id=user.id,
    )
    assert comment.comment == "Contrôle technique conforme"

    queue = get_queue(session=db, mode="verification")
    assert order.id in {item.order_id for item in queue.data}

    verification = verify_order(session=db, order_id=order.id, user_id=user.id)
    assert verification.verified_count == 1
    assert verification.skipped_count == 0
    assert verification.workspace.order_status == OrderStatus.completed
    assert (
        verification.workspace.verified_count
        == verification.workspace.total_count
        == 1
    )
    result = db.get(AnalyteResult, result_id)
    verified_item = db.get(OrderItem, item.id)
    assert result is not None and result.status == ResultStatus.verified
    assert verified_item is not None and verified_item.order_id == order.id


def test_image_result_upload_updates_workspace(db: Session, monkeypatch) -> None:
    order, user, item, specimen, analyte = _result_order(
        db,
        data_type=AnalyteDataType.image,
    )
    collect_all(session=db, order_id=order.id, collected_by_id=user.id)
    object_key = "results/orders/test-image.png"
    uploaded: list[dict] = []

    from app.services import object_storage

    def fake_upload_result_image(**kwargs):
        uploaded.append(kwargs)
        return object_key

    monkeypatch.setattr(
        object_storage,
        "upload_result_image",
        fake_upload_result_image,
    )
    monkeypatch.setattr(
        object_storage,
        "presigned_url",
        lambda key: f"https://storage.local/{key}",
    )
    monkeypatch.setattr(object_storage, "delete_object", lambda key: None)

    submission = upload_image_result(
        session=db,
        order_id=order.id,
        order_item_id=item.id,
        analyte_id=analyte.id,
        specimen_id=specimen.id,
        content_type="image/png",
        data=b"png",
        user_id=user.id,
    )

    assert uploaded[0]["content_type"] == "image/png"
    assert uploaded[0]["data"] == b"png"
    assert submission.saved_result_ids
    workspace_analyte = submission.workspace.tests[0].analytes[0]
    assert workspace_analyte.data_type == AnalyteDataType.image
    assert workspace_analyte.status == ResultStatus.resulted
    assert workspace_analyte.result_value == object_key
    assert workspace_analyte.image_url == f"https://storage.local/{object_key}"


def test_critical_notification_creation_is_idempotent(db: Session) -> None:
    order, user, item, specimen, analyte = _result_order(db)
    collect_all(session=db, order_id=order.id, collected_by_id=user.id)
    submission = enter_results(
        session=db,
        order_id=order.id,
        request=ResultBulkEntryRequest(
            order_item_id=item.id,
            values=[
                ResultEntryValue(
                    analyte_id=analyte.id,
                    specimen_id=specimen.id,
                    result_value="99",
                )
            ],
        ),
        user_id=user.id,
    )
    result = db.get(AnalyteResult, submission.saved_result_ids[0])
    assert result is not None
    result.is_critical = True
    db.add(result)
    db.commit()
    request = CriticalNotificationCreate(
        notified_to_id=user.id,
        method=CriticalMethod.call,
        notes="Notification test",
    )

    created = create_critical_notification(
        session=db,
        result_id=result.id,
        request=request,
        user_id=user.id,
    )
    repeated = create_critical_notification(
        session=db,
        result_id=result.id,
        request=request,
        user_id=user.id,
    )

    assert repeated.id == created.id
    assert repeated.patient_name == "Aminata Diallo"
    assert repeated.notified_to_name == (user.full_name or user.email)

    verification = verify_order(
        session=db, order_id=order.id, user_id=user.id
    )
    assert verification.verified_count == 0
    assert verification.skipped_count == 1
    assert verification.skipped[0].message == (
        "La valeur critique doit être notifiée et acquittée"
    )


def test_verify_order_verifies_eligible_results_and_skips_missing(
    db: Session,
) -> None:
    order, user, item, specimen, analytes = _result_order(db, analyte_count=2)
    assert isinstance(analytes, list)
    collect_all(session=db, order_id=order.id, collected_by_id=user.id)
    submission = enter_results(
        session=db,
        order_id=order.id,
        request=ResultBulkEntryRequest(
            order_item_id=item.id,
            values=[
                ResultEntryValue(
                    analyte_id=analytes[0].id,
                    specimen_id=specimen.id,
                    result_value="12.5",
                )
            ],
        ),
        user_id=user.id,
    )

    first, second = submission.workspace.tests[0].analytes
    assert first.verification_eligible is True
    assert first.verification_blocker is None
    assert second.verification_eligible is False
    assert second.verification_blocker == (
        "Le résultat doit être saisi avant vérification"
    )

    verification = verify_order(
        session=db, order_id=order.id, user_id=user.id
    )

    assert verification.verified_count == 1
    assert verification.skipped_count == 1
    assert verification.skipped[0].analyte_id == analytes[1].id
    assert verification.workspace.verified_count == 1
    assert verification.workspace.order_status == OrderStatus.partial_results


def test_customize_order_analytes_supersedes_results_without_touching_invoice(
    db: Session,
) -> None:
    order, user, item, specimen, analytes = _result_order(db, analyte_count=2)
    assert isinstance(analytes, list)
    collect_all(session=db, order_id=order.id, collected_by_id=user.id)
    submission = enter_results(
        session=db,
        order_id=order.id,
        request=ResultBulkEntryRequest(
            order_item_id=item.id,
            values=[
                ResultEntryValue(
                    analyte_id=analytes[0].id,
                    specimen_id=specimen.id,
                    result_value="12.5",
                )
            ],
        ),
        user_id=user.id,
    )
    verify_order(session=db, order_id=order.id, user_id=user.id)
    invoice_before = db.exec(
        select(Invoice).where(Invoice.order_id == order.id, Invoice.is_voided == False)  # noqa: E712
    ).one()
    invoice_signature = (
        invoice_before.id,
        invoice_before.version,
        invoice_before.total_amount,
        invoice_before.net_amount,
        invoice_before.amount_paid,
    )

    detail = customize_order_item_analytes(
        session=db,
        order_id=order.id,
        item_id=item.id,
        request=OrderItemAnalyteCustomizeRequest(
            analyte_ids=[analytes[1].id],
            reason="Analyte non requis pour ce patient",
            expected_revision=order.revision_number,
        ),
        performed_by_id=user.id,
    )

    assert [analyte.analyte_id for analyte in detail.items[0].analytes] == [
        analytes[1].id
    ]
    removed_result = db.get(AnalyteResult, submission.saved_result_ids[0])
    assert removed_result is not None and removed_result.is_superseded is True
    invoice_after = db.exec(
        select(Invoice).where(Invoice.order_id == order.id, Invoice.is_voided == False)  # noqa: E712
    ).one()
    assert (
        invoice_after.id,
        invoice_after.version,
        invoice_after.total_amount,
        invoice_after.net_amount,
        invoice_after.amount_paid,
    ) == invoice_signature
    snapshots = db.exec(
        select(OrderCatalogItemAnalyte).where(
            OrderCatalogItemAnalyte.order_item_id == item.id
        )
    ).all()
    assert {snapshot.analyte_id for snapshot in snapshots if snapshot.is_active} == {
        analytes[1].id
    }


def test_correct_verified_result_reopens_and_audits(db: Session) -> None:
    order, user, item, specimen, analyte = _result_order(db)
    collect_all(session=db, order_id=order.id, collected_by_id=user.id)
    submission = enter_results(
        session=db,
        order_id=order.id,
        request=ResultBulkEntryRequest(
            order_item_id=item.id,
            values=[
                ResultEntryValue(
                    analyte_id=analyte.id,
                    specimen_id=specimen.id,
                    result_value="12.5",
                )
            ],
        ),
        user_id=user.id,
    )
    verify_order(session=db, order_id=order.id, user_id=user.id)

    workspace = correct_verified_result(
        session=db,
        result_id=submission.saved_result_ids[0],
        request=ResultCorrectionRequest(
            result_value="13.2",
            reason="Correction après contrôle qualité",
        ),
        user_id=user.id,
    )

    corrected = db.get(AnalyteResult, submission.saved_result_ids[0])
    assert corrected is not None
    assert corrected.result_value == "13.2"
    assert corrected.status == ResultStatus.resulted
    assert corrected.verified_by_id is None
    assert corrected.verified_at is None
    assert workspace.order_status == OrderStatus.in_progress
    audits = db.exec(
        select(AuditLog).where(
            AuditLog.table_name == "analyte_results",
            AuditLog.record_id == corrected.id,
        )
    ).all()
    assert audits[-1].old_values["result_value"] == "12.5"
    assert audits[-1].new_values["result_value"] == "13.2"
    assert (
        audits[-1].new_values["correction_reason"]
        == "Correction après contrôle qualité"
    )
    assert workspace.tests[0].analytes[0].corrections[-1].reason == (
        "Correction après contrôle qualité"
    )
