from fastapi import APIRouter

from app.api.routes import (
    analytes,
    audit_logs,
    automated_rules,
    catalog,
    categories,
    critical_notifications,
    dashboard,
    doctor_commission_entries,
    doctor_commission_payments,
    doctors,
    finance_settings,
    formulas,
    insurance_pricings,
    insurance_providers,
    invoices,
    items,
    lab_settings,
    login,
    orders,
    patient_contexts,
    patients,
    payment_methods,
    private,
    rbac,
    rejection_reasons,
    reports,
    results,
    specimen_types,
    specimens,
    titles,
    units,
    users,
    utils,
    validation_rules,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(rbac.router)
api_router.include_router(titles.router)
api_router.include_router(units.router)
api_router.include_router(patient_contexts.router)
api_router.include_router(patients.router)
api_router.include_router(payment_methods.router)
api_router.include_router(rejection_reasons.router)
api_router.include_router(insurance_providers.router)
api_router.include_router(insurance_pricings.router)
api_router.include_router(specimen_types.router)
api_router.include_router(specimens.router)
api_router.include_router(categories.router)
api_router.include_router(doctors.router)
api_router.include_router(doctors.commission_router)
api_router.include_router(doctor_commission_entries.router)
api_router.include_router(doctor_commission_payments.router)
api_router.include_router(finance_settings.router)
api_router.include_router(lab_settings.router)
api_router.include_router(analytes.router)
api_router.include_router(audit_logs.router)
api_router.include_router(catalog.router)
api_router.include_router(orders.router)
api_router.include_router(invoices.router)
api_router.include_router(results.router)
api_router.include_router(reports.router)
api_router.include_router(critical_notifications.router)
api_router.include_router(dashboard.router)
api_router.include_router(validation_rules.router)
api_router.include_router(automated_rules.router)
api_router.include_router(formulas.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
