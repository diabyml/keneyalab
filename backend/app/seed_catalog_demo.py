"""Destructive demo seed for catalog, validations, and automated rules.

Run from the backend container or backend directory:
    python -m app.seed_catalog_demo --confirm-delete

This script is for local/demo environments. It physically deletes catalog
dependent operational data, then rebuilds catalog setup data from scratch.
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Iterable
from decimal import Decimal
from typing import Any, TypeVar

from sqlalchemy import delete
from sqlmodel import Session, select

from app.core.db import engine
from app.models import (
    Analyte,
    AnalyteDataType,
    AnalyteResult,
    AnalyteResultComment,
    Catalog,
    CatalogItemAnalyte,
    CatalogPanelItem,
    CatalogSpecimenRequirement,
    CatalogType,
    Category,
    ConsistencyRule,
    ConsistencyRuleAnalyte,
    CriticalNotification,
    DoctorCommissionEntry,
    DoctorCommissionPayment,
    DoctorCommissionPaymentEntry,
    FormulaResultType,
    InsurancePricing,
    Invoice,
    Notification,
    Order,
    OrderCatalogItemAnalyte,
    OrderItem,
    OrderSpecimen,
    PatientContext,
    ReflexRule,
    Report,
    RuleSeverity,
    SpecimenType,
    TargetGenderType,
    TriggerOperator,
    Unit,
    ValidationRule,
)
from app.services import formula as formula_service

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)
T = TypeVar("T")

DELETE_ORDER = [
    DoctorCommissionPaymentEntry,
    DoctorCommissionPayment,
    DoctorCommissionEntry,
    Invoice,
    Report,
    Notification,
    CriticalNotification,
    AnalyteResultComment,
    AnalyteResult,
    OrderCatalogItemAnalyte,
    OrderItem,
    OrderSpecimen,
    Order,
    InsurancePricing,
    ReflexRule,
    ConsistencyRuleAnalyte,
    ConsistencyRule,
    ValidationRule,
    CatalogPanelItem,
    CatalogSpecimenRequirement,
    CatalogItemAnalyte,
    Catalog,
    Analyte,
    Category,
    SpecimenType,
    Unit,
]


def main() -> None:
    args = parse_args()
    if not args.confirm_delete:
        logger.info("Mode protégé: aucune donnée supprimée.")
        logger.info("Cette commande supprimera et recréera les tables suivantes:")
        for model in DELETE_ORDER:
            logger.info("  - %s", model.__tablename__)
        logger.info("\nRelancez avec --confirm-delete pour exécuter le seed.")
        return

    with Session(engine) as session:
        delete_existing_data(session)
        seed_catalog_data(session)
        session.commit()
        print_summary(session)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed destructif du catalogue, validations et règles automatisées."
    )
    parser.add_argument(
        "--confirm-delete",
        action="store_true",
        help="Confirme la suppression physique des données catalogues et dépendantes.",
    )
    return parser.parse_args()


def delete_existing_data(session: Session) -> None:
    logger.info("Suppression des données existantes du système catalogue...")
    for model in DELETE_ORDER:
        session.exec(delete(model))
    session.flush()


def seed_catalog_data(session: Session) -> None:
    units = create_units(session)
    specimen_types = create_specimen_types(session)
    categories = create_categories(session)
    contexts = ensure_patient_contexts(session)
    analytes = create_analytes(session, units)
    catalog = create_catalog(session, categories)
    attach_analytes(session, catalog, analytes)
    attach_specimens(session, catalog, specimen_types)
    attach_panels(session, catalog)
    create_validation_rules(session, analytes, contexts)
    create_automated_rules(session, analytes, catalog)


def create_units(session: Session) -> dict[str, Unit]:
    data = [
        "g/L",
        "g/dL",
        "mg/L",
        "mg/dL",
        "mmol/L",
        "µmol/L",
        "UI/L",
        "U/L",
        "%",
        "10^9/L",
        "10^12/L",
        "fL",
        "pg",
        "ng/mL",
        "ng/dL",
        "mUI/L",
        "s",
        "ratio",
    ]
    return keyed_by_name(session, [Unit(name=name) for name in data])


def create_specimen_types(session: Session) -> dict[str, SpecimenType]:
    data = [
        ("Sang total EDTA", "Tube violet, anticoagulant EDTA", "#7c3aed"),
        ("Sérum", "Tube sec ou tube gel après coagulation", "#facc15"),
        ("Plasma hépariné", "Tube vert hépariné", "#16a34a"),
        ("Plasma citraté", "Tube bleu citraté 3,2 %", "#2563eb"),
        ("Urine", "Flacon stérile pour urine fraîche", "#fef3c7"),
        ("Selles", "Pot stérile pour selles", "#92400e"),
        ("Écouvillon nasopharyngé", "Écouvillon avec milieu de transport", "#dc2626"),
    ]
    return keyed_by_name(
        session,
        [
            SpecimenType(name=name, description=description, color=color)
            for name, description, color in data
        ],
    )


def create_categories(session: Session) -> dict[str, Category]:
    names = [
        "Hématologie",
        "Biochimie",
        "Immunologie",
        "Coagulation",
        "Microbiologie",
        "Urines",
        "Panels",
    ]
    return keyed_by_name(
        session,
        [Category(name=name, sort_order=index + 1) for index, name in enumerate(names)],
    )


def ensure_patient_contexts(session: Session) -> dict[str, PatientContext]:
    names = ["Ambulatoire", "Hospitalisé", "Urgence", "Grossesse"]
    contexts: dict[str, PatientContext] = {}
    for name in names:
        existing = session.exec(select(PatientContext).where(PatientContext.name == name)).first()
        if existing is None:
            existing = PatientContext(name=name)
            session.add(existing)
            session.flush()
        else:
            existing.is_deleted = False
            session.add(existing)
        contexts[name] = existing
    return contexts


def create_analytes(session: Session, units: dict[str, Unit]) -> dict[str, Analyte]:
    rows: list[dict[str, Any]] = [
        numeric("HB", "Hémoglobine", "g/dL", "Valeurs usuelles adulte: 12,0 - 17,5 g/dL"),
        numeric("HCT", "Hématocrite", "%", "Interprétation selon âge et sexe."),
        numeric("RBC", "Globules rouges", "10^12/L", "Numération érythrocytaire."),
        numeric("WBC", "Leucocytes", "10^9/L", "Numération leucocytaire totale."),
        numeric("PLT", "Plaquettes", "10^9/L", "Numération plaquettaire."),
        numeric("MCV", "Volume globulaire moyen", "fL", "Indice érythrocytaire."),
        numeric("MCH", "Teneur corpusculaire moyenne en hémoglobine", "pg", "Indice érythrocytaire."),
        numeric("NEUT", "Neutrophiles", "10^9/L", "Formule leucocytaire."),
        numeric("LYMPH", "Lymphocytes", "10^9/L", "Formule leucocytaire."),
        numeric("GLU", "Glycémie", "mg/dL", "À interpréter selon le contexte clinique."),
        numeric("UREE", "Urée", "mg/dL", "Fonction rénale et hydratation."),
        numeric("CREAT", "Créatinine", "mg/dL", "Fonction rénale."),
        numeric("NA", "Sodium", "mmol/L", "Ionogramme sanguin."),
        numeric("K", "Potassium", "mmol/L", "Ionogramme sanguin."),
        numeric("CL", "Chlorure", "mmol/L", "Ionogramme sanguin."),
        numeric("CA", "Calcium total", "mg/dL", "Calcémie totale."),
        numeric("CHOL", "Cholestérol total", "mg/dL", "Bilan lipidique."),
        numeric("HDL", "Cholestérol HDL", "mg/dL", "Bilan lipidique."),
        numeric("LDL", "Cholestérol LDL calculé", "mg/dL", "Formule de Friedewald si triglycérides compatibles.", True, "{CHOL} - {HDL} - ({TG} / 5)"),
        numeric("TG", "Triglycérides", "mg/dL", "Bilan lipidique."),
        numeric("RATIO_CHOL_HDL", "Ratio cholestérol total / HDL", "ratio", "Ratio cardiovasculaire calculé.", True, "{CHOL} / {HDL}"),
        numeric("AST", "ASAT", "U/L", "Transaminase hépatique."),
        numeric("ALT", "ALAT", "U/L", "Transaminase hépatique."),
        numeric("GGT", "Gamma-GT", "U/L", "Enzyme hépatobiliaire."),
        numeric("PAL", "Phosphatases alcalines", "U/L", "Enzyme hépatobiliaire."),
        numeric("BILT", "Bilirubine totale", "mg/dL", "Bilan hépatique."),
        numeric("BILD", "Bilirubine directe", "mg/dL", "Bilan hépatique."),
        numeric("CRP", "Protéine C-réactive", "mg/L", "Marqueur inflammatoire."),
        numeric("TSH", "TSH ultrasensible", "mUI/L", "Exploration thyroïdienne."),
        numeric("FT4", "Thyroxine libre T4L", "ng/dL", "Exploration thyroïdienne complémentaire."),
        numeric("HBA1C", "Hémoglobine glyquée HbA1c", "%", "Suivi glycémique sur 2 à 3 mois."),
        numeric("TP", "Taux de prothrombine", "%", "Coagulation."),
        numeric("INR", "INR", "ratio", "Surveillance anticoagulante."),
        numeric("TCA", "Temps de céphaline activée", "s", "Coagulation."),
        options("NITRITES_U", "Nitrites urinaires", ["Négatif", "Positif"]),
        options("LEU_U", "Leucocytes urinaires", ["Négatif", "Trace", "Positif", "Fortement positif"]),
        options("PROT_U", "Protéines urinaires", ["Négatif", "Trace", "+", "++", "+++"]),
        options("GLU_U", "Glucose urinaire", ["Négatif", "Trace", "+", "++", "+++"]),
        text("ECBU_DIRECT", "Examen direct ECBU", "Description microscopique en français."),
        text("ECBU_CULTURE", "Culture ECBU", "Résultat de culture et antibiogramme si applicable."),
    ]
    analytes: dict[str, Analyte] = {}
    for row in rows:
        unit = units.get(row.pop("unit_name")) if row.get("unit_name") else None
        analyte = Analyte(**row, unit_id=unit.id if unit else None)
        session.add(analyte)
        session.flush()
        analytes[analyte.code] = analyte
    return analytes


def numeric(
    code: str,
    name: str,
    unit_name: str,
    reference_text: str,
    is_calculated: bool = False,
    calculation_formula: str | None = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "name": name,
        "unit_name": unit_name,
        "data_type": AnalyteDataType.numeric,
        "reference_text": reference_text,
        "is_calculated": is_calculated,
        "calculation_formula": calculation_formula,
    }


def options(code: str, name: str, values: list[str]) -> dict[str, Any]:
    return {
        "code": code,
        "name": name,
        "unit_name": None,
        "data_type": AnalyteDataType.options,
        "options_data": values,
        "reference_text": "Résultat qualitatif.",
    }


def text(code: str, name: str, reference_text: str) -> dict[str, Any]:
    return {
        "code": code,
        "name": name,
        "unit_name": None,
        "data_type": AnalyteDataType.text,
        "reference_text": reference_text,
    }


def create_catalog(session: Session, categories: dict[str, Category]) -> dict[str, Catalog]:
    rows = [
        item("NFS", "Numération formule sanguine", "Hématologie", "3500.00"),
        item("GLY", "Glycémie à jeun", "Biochimie", "1500.00"),
        item("UREE", "Urée sanguine", "Biochimie", "1500.00"),
        item("CREAT", "Créatinine sanguine", "Biochimie", "2000.00"),
        item("IONO", "Ionogramme sanguin", "Biochimie", "4500.00"),
        item("CA", "Calcémie", "Biochimie", "2500.00"),
        item("LIP", "Bilan lipidique", "Biochimie", "6500.00"),
        item("HEP", "Bilan hépatique", "Biochimie", "9000.00"),
        item("CRP", "Protéine C-réactive", "Immunologie", "5000.00"),
        item("TSH", "TSH ultrasensible", "Immunologie", "8000.00"),
        item("T4L", "Thyroxine libre T4L", "Immunologie", "9000.00"),
        item("HBA1C", "Hémoglobine glyquée HbA1c", "Biochimie", "7000.00"),
        item("TPINR", "TP - INR", "Coagulation", "4500.00"),
        item("TCA", "Temps de céphaline activée", "Coagulation", "3500.00"),
        item("BU", "Bandelette urinaire", "Urines", "2000.00"),
        item("ECBU", "Examen cytobactériologique des urines", "Microbiologie", "9000.00"),
        panel("P_RENAL", "Bilan rénal", "Panels"),
        panel("P_METAB", "Bilan métabolique", "Panels"),
        panel("P_HEP_COMPLET", "Bilan hépatique complet", "Panels"),
        panel("P_CARDIO", "Bilan cardiovasculaire", "Panels"),
        panel("P_PREOP", "Bilan préopératoire", "Panels"),
    ]
    catalog: dict[str, Catalog] = {}
    for row in rows:
        category_name = row.pop("category")
        entry = Catalog(**row, category_id=categories[category_name].id)
        session.add(entry)
        session.flush()
        catalog[entry.code] = entry
    return catalog


def item(code: str, name: str, category: str, price: str) -> dict[str, Any]:
    return catalog_row(CatalogType.item, code, name, category, price)


def panel(code: str, name: str, category: str) -> dict[str, Any]:
    return catalog_row(CatalogType.panel, code, name, category, "0.00")


def catalog_row(
    type_: CatalogType, code: str, name: str, category: str, price: str
) -> dict[str, Any]:
    return {
        "type": type_,
        "code": code,
        "name": name,
        "category": category,
        "price": Decimal(price),
        "is_orderable": True,
    }


def attach_analytes(
    session: Session, catalog: dict[str, Catalog], analytes: dict[str, Analyte]
) -> None:
    mapping = {
        "NFS": ["HB", "HCT", "RBC", "WBC", "PLT", "MCV", "MCH", "NEUT", "LYMPH"],
        "GLY": ["GLU"],
        "UREE": ["UREE"],
        "CREAT": ["CREAT"],
        "IONO": ["NA", "K", "CL"],
        "CA": ["CA"],
        "LIP": ["CHOL", "HDL", "TG", "LDL", "RATIO_CHOL_HDL"],
        "HEP": ["AST", "ALT", "GGT", "PAL", "BILT", "BILD"],
        "CRP": ["CRP"],
        "TSH": ["TSH"],
        "T4L": ["FT4"],
        "HBA1C": ["HBA1C"],
        "TPINR": ["TP", "INR"],
        "TCA": ["TCA"],
        "BU": ["NITRITES_U", "LEU_U", "PROT_U", "GLU_U"],
        "ECBU": ["ECBU_DIRECT", "ECBU_CULTURE", "NITRITES_U", "LEU_U"],
    }
    for catalog_code, analyte_codes in mapping.items():
        for index, analyte_code in enumerate(analyte_codes, start=1):
            session.add(
                CatalogItemAnalyte(
                    catalog_item_id=catalog[catalog_code].id,
                    analyte_id=analytes[analyte_code].id,
                    sort_order=index,
                )
            )
    session.flush()


def attach_specimens(
    session: Session, catalog: dict[str, Catalog], specimen_types: dict[str, SpecimenType]
) -> None:
    rows = [
        ("NFS", "Sang total EDTA", "2.00", "Tube EDTA bien homogénéisé. Éviter les caillots."),
        ("GLY", "Plasma hépariné", "1.00", "Prélèvement à jeun recommandé. Centrifuger rapidement."),
        ("UREE", "Sérum", "1.00", "Sérum non hémolysé."),
        ("CREAT", "Sérum", "1.00", "Sérum non hémolysé."),
        ("IONO", "Plasma hépariné", "1.00", "Éviter l'hémolyse, acheminer rapidement."),
        ("CA", "Sérum", "1.00", "Sérum non hémolysé."),
        ("LIP", "Sérum", "1.00", "Jeûne de 12 heures recommandé."),
        ("HEP", "Sérum", "1.00", "Sérum non hémolysé."),
        ("CRP", "Sérum", "1.00", "Aucun jeûne requis."),
        ("TSH", "Sérum", "1.00", "Prélever de préférence le matin."),
        ("T4L", "Sérum", "1.00", "Prélever de préférence le matin."),
        ("HBA1C", "Sang total EDTA", "2.00", "Tube EDTA, conservation à 2-8 °C si délai."),
        ("TPINR", "Plasma citraté", "2.70", "Respecter le remplissage du tube citraté."),
        ("TCA", "Plasma citraté", "2.70", "Respecter le remplissage du tube citraté."),
        ("BU", "Urine", "10.00", "Urine fraîche, analyser dans les 2 heures."),
        ("ECBU", "Urine", "10.00", "Milieu de jet dans flacon stérile avant antibiotique si possible."),
    ]
    for catalog_code, specimen_name, volume, instructions in rows:
        session.add(
            CatalogSpecimenRequirement(
                catalog_id=catalog[catalog_code].id,
                specimen_type_id=specimen_types[specimen_name].id,
                volume_ml=Decimal(volume),
                instructions=instructions,
            )
        )
    session.flush()


def attach_panels(session: Session, catalog: dict[str, Catalog]) -> None:
    mapping = {
        "P_RENAL": ["UREE", "CREAT", "IONO"],
        "P_METAB": ["GLY", "UREE", "CREAT", "IONO", "CA"],
        "P_HEP_COMPLET": ["HEP", "TPINR"],
        "P_CARDIO": ["LIP", "GLY", "HBA1C", "CRP"],
        "P_PREOP": ["NFS", "GLY", "CREAT", "IONO", "TPINR", "TCA"],
    }
    for panel_code, test_codes in mapping.items():
        for index, test_code in enumerate(test_codes, start=1):
            session.add(
                CatalogPanelItem(
                    panel_id=catalog[panel_code].id,
                    test_id=catalog[test_code].id,
                    sort_order=index,
                )
            )
    session.flush()


def create_validation_rules(
    session: Session, analytes: dict[str, Analyte], contexts: dict[str, PatientContext]
) -> None:
    numeric_rules = [
        vr("HB", normal_min="13.0", normal_max="17.5", panic_min="7.0", panic_max="20.0", absurd_min="3.0", absurd_max="25.0", gender=TargetGenderType.male),
        vr("HB", normal_min="12.0", normal_max="16.0", panic_min="7.0", panic_max="20.0", absurd_min="3.0", absurd_max="25.0", gender=TargetGenderType.female),
        vr("WBC", normal_min="4.0", normal_max="10.0", panic_min="2.0", panic_max="30.0", absurd_min="0.1", absurd_max="100.0"),
        vr("PLT", normal_min="150", normal_max="450", panic_min="50", panic_max="1000", absurd_min="5", absurd_max="2000"),
        vr("GLU", normal_min="70", normal_max="110", panic_min="50", panic_max="400", absurd_min="20", absurd_max="800", context="Ambulatoire"),
        vr("GLU", normal_min="70", normal_max="180", panic_min="50", panic_max="400", absurd_min="20", absurd_max="800", context="Urgence", priority=5),
        vr("UREE", normal_min="15", normal_max="45", panic_max="150", absurd_min="1", absurd_max="300"),
        vr("CREAT", normal_min="0.6", normal_max="1.3", panic_max="5.0", absurd_min="0.1", absurd_max="20.0"),
        vr("NA", normal_min="135", normal_max="145", panic_min="120", panic_max="160", absurd_min="100", absurd_max="180"),
        vr("K", normal_min="3.5", normal_max="5.1", panic_min="2.8", panic_max="6.2", absurd_min="1.5", absurd_max="9.0"),
        vr("CL", normal_min="98", normal_max="107", panic_min="80", panic_max="125", absurd_min="60", absurd_max="150"),
        vr("CA", normal_min="8.6", normal_max="10.2", panic_min="7.0", panic_max="13.0", absurd_min="4.0", absurd_max="18.0"),
        vr("CHOL", normal_max="200", panic_max="350", absurd_max="600"),
        vr("HDL", normal_min="40", normal_max="90", absurd_min="5", absurd_max="150"),
        vr("LDL", normal_max="130", panic_max="250", absurd_min="0", absurd_max="500"),
        vr("TG", normal_max="150", panic_max="500", absurd_min="10", absurd_max="2000"),
        vr("AST", normal_max="40", panic_max="500", absurd_min="0", absurd_max="5000"),
        vr("ALT", normal_max="45", panic_max="500", absurd_min="0", absurd_max="5000"),
        vr("GGT", normal_max="60", panic_max="800", absurd_min="0", absurd_max="3000"),
        vr("PAL", normal_min="40", normal_max="130", panic_max="1000", absurd_min="0", absurd_max="3000"),
        vr("BILT", normal_max="1.2", panic_max="20", absurd_min="0", absurd_max="60"),
        vr("BILD", normal_max="0.3", panic_max="10", absurd_min="0", absurd_max="40"),
        vr("CRP", normal_max="5", panic_max="200", absurd_min="0", absurd_max="500"),
        vr("TSH", normal_min="0.4", normal_max="4.0", panic_min="0.01", panic_max="50", absurd_min="0", absurd_max="200"),
        vr("FT4", normal_min="0.8", normal_max="1.8", panic_min="0.3", panic_max="4.0", absurd_min="0", absurd_max="10"),
        vr("HBA1C", normal_min="4.0", normal_max="5.7", panic_max="14.0", absurd_min="2.0", absurd_max="20.0"),
        vr("TP", normal_min="70", normal_max="100", panic_min="20", absurd_min="1", absurd_max="150"),
        vr("INR", normal_min="0.8", normal_max="1.2", panic_max="5.0", absurd_min="0.5", absurd_max="15.0"),
        vr("TCA", normal_min="25", normal_max="40", panic_max="120", absurd_min="5", absurd_max="300"),
    ]
    for data in numeric_rules:
        context_name = data.pop("context", None)
        code = data.pop("code")
        gender = data.pop("gender", TargetGenderType.all)
        session.add(
            ValidationRule(
                analyte_id=analytes[code].id,
                target_gender=gender,
                required_context_id=contexts[context_name].id if context_name else None,
                **data,
            )
        )

    option_rules = [
        ("NITRITES_U", ["Négatif"], ["Positif"], ["Positif"]),
        ("LEU_U", ["Négatif", "Trace"], ["Positif"], ["Fortement positif"]),
        ("PROT_U", ["Négatif", "Trace"], ["+", "++"], ["+++"]),
        ("GLU_U", ["Négatif", "Trace"], ["+", "++"], ["+++"]),
    ]
    for code, allowed, abnormal, critical in option_rules:
        session.add(
            ValidationRule(
                analyte_id=analytes[code].id,
                allowed_values=allowed + [value for value in abnormal + critical if value not in allowed],
                abnormal_values=abnormal,
                critical_values=critical,
            )
        )
    session.add(
        ValidationRule(
            analyte_id=analytes["ECBU_DIRECT"].id,
            is_required=True,
            regex_pattern=r".{5,}",
            validation_message="Veuillez saisir une description microscopique exploitable.",
        )
    )
    session.flush()


def vr(code: str, **kwargs: Any) -> dict[str, Any]:
    return {"code": code, "priority": kwargs.pop("priority", 0), **kwargs}


def create_automated_rules(
    session: Session, analytes: dict[str, Analyte], catalog: dict[str, Catalog]
) -> None:
    consistency = [
        (
            "Cohérence sodium / chlorure",
            "{NA} - {CL} > 20 and {NA} - {CL} < 50",
            "Le sodium doit rester cohérent avec le chlorure.",
            "Écart sodium/chlorure incohérent, vérifier le prélèvement ou la saisie.",
            RuleSeverity.warning,
            ["NA", "CL"],
        ),
        (
            "LDL inférieur au cholestérol total",
            "{LDL} < {CHOL}",
            "Le LDL calculé ne doit pas dépasser le cholestérol total.",
            "LDL calculé supérieur au cholestérol total.",
            RuleSeverity.error,
            ["LDL", "CHOL", "HDL", "TG"],
        ),
        (
            "Bilirubine directe inférieure à totale",
            "{BILD} <= {BILT}",
            "La bilirubine directe ne peut pas dépasser la bilirubine totale.",
            "Bilirubine directe supérieure à la bilirubine totale.",
            RuleSeverity.error,
            ["BILD", "BILT"],
        ),
        (
            "Hématocrite cohérent avec hémoglobine",
            "abs({HCT} - ({HB} * 3)) < 8",
            "L'hématocrite est habituellement proche de trois fois l'hémoglobine.",
            "Hématocrite et hémoglobine incohérents.",
            RuleSeverity.warning,
            ["HCT", "HB"],
        ),
        (
            "Ratio cholestérol calculé plausible",
            "abs({RATIO_CHOL_HDL} - ({CHOL} / {HDL})) < 0.20",
            "Le ratio saisi/calculé doit correspondre au cholestérol total divisé par HDL.",
            "Ratio cholestérol/HDL incohérent.",
            RuleSeverity.warning,
            ["RATIO_CHOL_HDL", "CHOL", "HDL"],
        ),
    ]
    for name, formula, description, message, severity, codes in consistency:
        formula_service.validate_formula(
            session=session,
            formula=formula,
            expected_result_type=FormulaResultType.boolean,
            allowed_analyte_ids=[analytes[code].id for code in codes],
        )
        rule = ConsistencyRule(
            name=name,
            formula=formula,
            formula_description=description,
            error_message=message,
            severity=severity,
        )
        session.add(rule)
        session.flush()
        for code in codes:
            session.add(ConsistencyRuleAnalyte(rule_id=rule.id, analyte_id=analytes[code].id))

    reflex = [
        ("CRP", TriggerOperator.gt, "50", "NFS"),
        ("K", TriggerOperator.gt, "6.2", "IONO"),
        ("K", TriggerOperator.lt, "2.8", "IONO"),
        ("NITRITES_U", TriggerOperator.eq, "Positif", "ECBU"),
        ("LEU_U", TriggerOperator.in_, "Positif, Fortement positif", "ECBU"),
        ("TSH", TriggerOperator.gt, "10", "T4L"),
    ]
    for analyte_code, operator, value, catalog_code in reflex:
        session.add(
            ReflexRule(
                trigger_analyte_id=analytes[analyte_code].id,
                trigger_operator=operator,
                trigger_value=value,
                action_catalog_id=catalog[catalog_code].id,
            )
        )
    session.flush()


def keyed_by_name(session: Session, items: Iterable[T]) -> dict[str, T]:
    result: dict[str, T] = {}
    for item in items:
        session.add(item)
        session.flush()
        result[item.name] = item  # type: ignore[attr-defined]
    return result


def print_summary(session: Session) -> None:
    logger.info("\nSeed catalogue terminé.")
    for model in [
        Unit,
        SpecimenType,
        Category,
        PatientContext,
        Analyte,
        Catalog,
        CatalogItemAnalyte,
        CatalogSpecimenRequirement,
        CatalogPanelItem,
        ValidationRule,
        ConsistencyRule,
        ConsistencyRuleAnalyte,
        ReflexRule,
    ]:
        count = len(session.exec(select(model)).all())
        logger.info("  %-35s %s", model.__tablename__, count)


if __name__ == "__main__":
    main()
