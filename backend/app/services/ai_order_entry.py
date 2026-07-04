"""AI-backed quick intake for order entry."""

from __future__ import annotations

import json
import uuid
from datetime import date
from typing import Any, Protocol

import httpx
from pydantic import BaseModel, Field, ValidationError
from sqlmodel import Session

from app.core.config import settings
from app.core.exceptions import BusinessRuleError
from app.models.lis import (
    CatalogSummaryPublic,
    DoctorWithTitlePublic,
    GenderType,
    OrderEntryAssistantCatalogSuggestion,
    OrderEntryAssistantDoctorDraft,
    OrderEntryAssistantPatientDraft,
    OrderEntryAssistantRequest,
    OrderEntryAssistantResponse,
    PatientPublic,
    SortOrder,
)
from app.services import catalog as catalog_service
from app.services import doctor as doctor_service
from app.services import patient as patient_service


class AIIntakePatient(BaseModel):
    identifier: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    gender: GenderType | None = None
    phone: str | None = None
    address: str | None = None
    confidence: float = Field(default=0, ge=0, le=1)
    warnings: list[str] = Field(default_factory=list)


class AIIntakeDoctor(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    provenance: str | None = None
    phone: str | None = None
    title_name: str | None = None
    confidence: float = Field(default=0, ge=0, le=1)
    warnings: list[str] = Field(default_factory=list)


class AIIntakeCatalogSuggestion(BaseModel):
    catalog_id: uuid.UUID
    confidence: float = Field(ge=0, le=1)
    reason: str | None = None
    matched_terms: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AIIntakeResult(BaseModel):
    patient: AIIntakePatient | None = None
    doctor: AIIntakeDoctor | None = None
    catalog_suggestions: list[AIIntakeCatalogSuggestion] = Field(default_factory=list)
    unmatched_phrases: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class OrderEntryAIProvider(Protocol):
    def extract_intake(
        self, *, text: str, catalog_options: list[CatalogSummaryPublic]
    ) -> AIIntakeResult:
        """Extract structured order intake from free-form French text."""


class OpenAICompatibleOrderEntryProvider:
    def __init__(
        self, *, api_key: str, base_url: str, model: str, api_style: str
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_style = api_style

    def extract_intake(
        self, *, text: str, catalog_options: list[CatalogSummaryPublic]
    ) -> AIIntakeResult:
        catalog_context = _catalog_context(catalog_options)
        if self.api_style == "chat_completions":
            return self._extract_with_chat_completions(
                text=text,
                catalog_context=catalog_context,
            )
        return self._extract_with_responses(
            text=text,
            catalog_context=catalog_context,
        )

    def _extract_with_responses(
        self, *, text: str, catalog_context: list[dict[str, str | None]]
    ) -> AIIntakeResult:
        payload = {
            "model": self.model,
            "input": _messages(text=text, catalog_context=catalog_context),
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "keneya_order_entry_intake",
                    "strict": True,
                    "schema": _response_schema(),
                }
            },
        }
        response: httpx.Response | None = None
        try:
            response = httpx.post(
                _api_url(base_url=self.base_url, path="/v1/responses"),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise BusinessRuleError(_provider_error_message(response)) from exc

        try:
            return AIIntakeResult.model_validate_json(
                _extract_response_text(response.json())
            )
        except (KeyError, TypeError, ValidationError, json.JSONDecodeError) as exc:
            raise BusinessRuleError(
                "La réponse de l'assistant IA est invalide"
            ) from exc

    def _extract_with_chat_completions(
        self, *, text: str, catalog_context: list[dict[str, str | None]]
    ) -> AIIntakeResult:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": _messages(text=text, catalog_context=catalog_context),
            "response_format": {"type": "json_object"},
            "max_tokens": 4000,
            "stream": False,
        }
        response: httpx.Response | None = None
        try:
            response = httpx.post(
                _api_url(base_url=self.base_url, path="/chat/completions"),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise BusinessRuleError(_provider_error_message(response)) from exc

        try:
            return AIIntakeResult.model_validate_json(
                _extract_chat_completion_text(response.json())
            )
        except (KeyError, TypeError, ValidationError, json.JSONDecodeError) as exc:
            raise BusinessRuleError(
                "La réponse de l'assistant IA est invalide"
            ) from exc


def get_order_entry_provider() -> OrderEntryAIProvider:
    if settings.AI_PROVIDER == "none" or not settings.AI_API_KEY:
        raise BusinessRuleError("Assistant IA non configuré")
    if settings.AI_PROVIDER == "openai_compatible":
        return OpenAICompatibleOrderEntryProvider(
            api_key=settings.AI_API_KEY,
            base_url=settings.AI_BASE_URL,
            model=settings.AI_MODEL,
            api_style=settings.AI_API_STYLE,
        )
    raise BusinessRuleError("Fournisseur IA non supporté")


def generate_order_entry_intake(
    *, session: Session, request: OrderEntryAssistantRequest
) -> OrderEntryAssistantResponse:
    text = request.text.strip()
    if len(text) < 3:
        raise BusinessRuleError("La dictée est trop courte")

    catalog_options, _ = catalog_service.get_catalogs(
        session=session,
        limit=settings.AI_ORDER_ASSISTANT_CATALOG_LIMIT,
        is_orderable=True,
        is_deleted=False,
        exclude_empty_panels=True,
        sort_by="code",
    )
    ai_result = get_order_entry_provider().extract_intake(
        text=text, catalog_options=catalog_options
    )
    catalog_by_id = {item.id: item for item in catalog_options}

    suggestions: list[OrderEntryAssistantCatalogSuggestion] = []
    dropped_count = 0
    seen_catalog_ids: set[uuid.UUID] = set()
    for suggestion in ai_result.catalog_suggestions:
        catalog = catalog_by_id.get(suggestion.catalog_id)
        if catalog is None:
            dropped_count += 1
            continue
        if catalog.id in seen_catalog_ids:
            continue
        seen_catalog_ids.add(catalog.id)
        warnings = list(suggestion.warnings)
        if suggestion.confidence < settings.AI_ORDER_ASSISTANT_CONFIDENCE_THRESHOLD:
            warnings.append("Correspondance à vérifier")
        suggestions.append(
            OrderEntryAssistantCatalogSuggestion(
                catalog=catalog,
                confidence=suggestion.confidence,
                reason=_clean_optional(suggestion.reason),
                matched_terms=_clean_list(suggestion.matched_terms),
                warnings=_clean_list(warnings),
            )
        )

    warnings = _clean_list(ai_result.warnings)
    if dropped_count:
        warnings.append(
            "Certaines suggestions IA ont été ignorées car elles ne sont pas disponibles"
        )

    patient_draft = _patient_public_draft(ai_result.patient)
    doctor_draft = _doctor_public_draft(ai_result.doctor)
    return OrderEntryAssistantResponse(
        patient_draft=patient_draft,
        patient_matches=_match_patients(session=session, draft=patient_draft),
        doctor_draft=doctor_draft,
        doctor_matches=_match_doctors(session=session, draft=doctor_draft),
        catalog_suggestions=suggestions,
        unmatched_phrases=_clean_list(ai_result.unmatched_phrases),
        warnings=warnings,
    )


def _patient_public_draft(
    draft: AIIntakePatient | None,
) -> OrderEntryAssistantPatientDraft | None:
    if draft is None:
        return None
    warnings = _clean_list(draft.warnings)
    if draft.first_name and not draft.last_name:
        warnings.append("Nom du patient manquant")
    if draft.last_name and not draft.first_name:
        warnings.append("Prénom du patient manquant")
    if (draft.first_name or draft.last_name) and draft.date_of_birth is None:
        warnings.append("Date de naissance du patient à confirmer")
    return OrderEntryAssistantPatientDraft(
        identifier=_clean_optional(draft.identifier),
        first_name=_clean_optional(draft.first_name),
        last_name=_clean_optional(draft.last_name),
        date_of_birth=draft.date_of_birth,
        gender=draft.gender,
        phone=_clean_optional(draft.phone),
        address=_clean_optional(draft.address),
        confidence=draft.confidence,
        warnings=warnings,
    )


def _doctor_public_draft(
    draft: AIIntakeDoctor | None,
) -> OrderEntryAssistantDoctorDraft | None:
    if draft is None:
        return None
    warnings = _clean_list(draft.warnings)
    if draft.first_name and not draft.last_name:
        warnings.append("Nom du médecin manquant")
    if draft.last_name and not draft.first_name:
        warnings.append("Prénom du médecin manquant")
    return OrderEntryAssistantDoctorDraft(
        first_name=_clean_optional(draft.first_name),
        last_name=_clean_optional(draft.last_name),
        provenance=_clean_optional(draft.provenance),
        phone=_clean_optional(draft.phone),
        title_name=_clean_optional(draft.title_name),
        confidence=draft.confidence,
        warnings=warnings,
    )


def _match_patients(
    *, session: Session, draft: OrderEntryAssistantPatientDraft | None
) -> list[PatientPublic]:
    if draft is None:
        return []
    searches = [
        draft.identifier,
        draft.phone,
        draft.first_name,
        draft.last_name,
        " ".join(item for item in [draft.first_name, draft.last_name] if item).strip(),
    ]
    matches: dict[uuid.UUID, PatientPublic] = {}
    for search in searches:
        cleaned = _clean_optional(search)
        if cleaned is None:
            continue
        patients, _ = patient_service.get_patients(
            session=session,
            search=cleaned,
            limit=5,
            sort_by="created_at",
            sort_order=SortOrder.desc,
        )
        for patient in patients:
            matches[patient.id] = PatientPublic.model_validate(patient)
    return list(matches.values())[:5]


def _match_doctors(
    *, session: Session, draft: OrderEntryAssistantDoctorDraft | None
) -> list[DoctorWithTitlePublic]:
    if draft is None:
        return []
    searches = [
        draft.phone,
        draft.provenance,
        draft.first_name,
        draft.last_name,
        " ".join(item for item in [draft.first_name, draft.last_name] if item).strip(),
    ]
    matches: dict[uuid.UUID, DoctorWithTitlePublic] = {}
    for search in searches:
        cleaned = _clean_optional(search)
        if cleaned is None:
            continue
        rows, _ = doctor_service.get_doctors(
            session=session,
            search=cleaned,
            limit=5,
            sort_by="created_at",
            sort_order=SortOrder.desc,
        )
        for doctor, title in rows:
            matches[doctor.id] = DoctorWithTitlePublic(
                **doctor.model_dump(),
                title_name=title.name if title else None,
            )
    return list(matches.values())[:5]


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _clean_list(values: list[str]) -> list[str]:
    return [cleaned for value in values if (cleaned := value.strip())]


def _catalog_context(
    catalog_options: list[CatalogSummaryPublic],
) -> list[dict[str, str | None]]:
    return [
        {
            "id": str(item.id),
            "code": item.code,
            "name": item.name,
            "type": item.type.value,
            "category": item.category_name,
        }
        for item in catalog_options
    ]


def _messages(
    *, text: str, catalog_context: list[dict[str, str | None]]
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "Tu es un assistant de saisie pour un laboratoire médical au Mali. "
                "Analyse une dictée française de demande d'examens. "
                "Retourne uniquement un objet JSON valide compatible avec le schéma demandé. "
                "N'ajoute aucun texte hors JSON. "
                "Retourne uniquement les informations présentes ou fortement déduites. "
                "Ne diagnostique pas. Ne crée pas d'identité. "
                "Utilise seulement les IDs catalogue fournis."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "schema_attendu": {
                        "patient": {
                            "identifier": "string|null",
                            "first_name": "string|null",
                            "last_name": "string|null",
                            "date_of_birth": "YYYY-MM-DD|null",
                            "gender": "male|female|null",
                            "phone": "string|null",
                            "address": "string|null",
                            "confidence": "number 0..1",
                            "warnings": ["string"],
                        },
                        "doctor": {
                            "first_name": "string|null",
                            "last_name": "string|null",
                            "provenance": "string|null",
                            "phone": "string|null",
                            "title_name": "string|null",
                            "confidence": "number 0..1",
                            "warnings": ["string"],
                        },
                        "catalog_suggestions": [
                            {
                                "catalog_id": "uuid",
                                "confidence": "number 0..1",
                                "reason": "string|null",
                                "matched_terms": ["string"],
                                "warnings": ["string"],
                            }
                        ],
                        "unmatched_phrases": ["string"],
                        "warnings": ["string"],
                    },
                    "dictee": text,
                    "catalogue_disponible": catalog_context,
                },
                ensure_ascii=False,
            ),
        },
    ]


def _api_url(*, base_url: str, path: str) -> str:
    normalized_base = base_url.rstrip("/")
    if normalized_base.endswith("/v1") and path.startswith("/v1/"):
        return f"{normalized_base}{path[3:]}"
    return f"{normalized_base}{path}"


def _provider_error_message(response: httpx.Response | None) -> str:
    fallback = "L'assistant IA n'a pas pu traiter la dictée"
    if response is None:
        return fallback
    try:
        payload = response.json()
    except json.JSONDecodeError:
        return fallback
    detail = payload.get("error")
    if isinstance(detail, dict) and isinstance(detail.get("message"), str):
        return f"{fallback} : {detail['message'][:300]}"
    if isinstance(detail, str):
        return f"{fallback} : {detail[:300]}"
    return fallback


def _extract_response_text(payload: dict[str, Any]) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text
    for output in payload.get("output", []):
        if not isinstance(output, dict):
            continue
        for content in output.get("content", []):
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                return content["text"]
    raise KeyError("output_text")


def _extract_chat_completion_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise KeyError("choices")
    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise KeyError("message")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise KeyError("content")
    return content


def _nullable_string(max_length: int | None = None) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": ["string", "null"]}
    if max_length is not None:
        schema["maxLength"] = max_length
    return schema


def _response_schema() -> dict[str, Any]:
    patient_schema = {
        "type": ["object", "null"],
        "additionalProperties": False,
        "properties": {
            "identifier": _nullable_string(100),
            "first_name": _nullable_string(100),
            "last_name": _nullable_string(100),
            "date_of_birth": {"type": ["string", "null"], "format": "date"},
            "gender": {"type": ["string", "null"], "enum": ["male", "female", None]},
            "phone": _nullable_string(50),
            "address": _nullable_string(),
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "identifier",
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "phone",
            "address",
            "confidence",
            "warnings",
        ],
    }
    doctor_schema = {
        "type": ["object", "null"],
        "additionalProperties": False,
        "properties": {
            "first_name": _nullable_string(100),
            "last_name": _nullable_string(100),
            "provenance": _nullable_string(255),
            "phone": _nullable_string(50),
            "title_name": _nullable_string(100),
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "first_name",
            "last_name",
            "provenance",
            "phone",
            "title_name",
            "confidence",
            "warnings",
        ],
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "patient": patient_schema,
            "doctor": doctor_schema,
            "catalog_suggestions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "catalog_id": {"type": "string", "format": "uuid"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "reason": _nullable_string(),
                        "matched_terms": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "warnings": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": [
                        "catalog_id",
                        "confidence",
                        "reason",
                        "matched_terms",
                        "warnings",
                    ],
                },
            },
            "unmatched_phrases": {"type": "array", "items": {"type": "string"}},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "patient",
            "doctor",
            "catalog_suggestions",
            "unmatched_phrases",
            "warnings",
        ],
    }
