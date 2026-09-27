import json
import logging
import os
import re
import uuid
from typing import Any, Dict, List, Optional

from app.models.case import CaseAnalysis
from app.models.entities import Entity
from app.models.relationships import Relationship

logger = logging.getLogger(__name__)

# ============================================================
# Configuration
# ============================================================

USE_LLM = os.getenv("USE_LLM", "false").lower() == "true"

WATSONX_API_KEY = os.getenv("WATSONX_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_URL = os.getenv(
    "WATSONX_URL",
    "https://us-south.ml.cloud.ibm.com",
)
WATSONX_MODEL_ID = os.getenv(
    "WATSONX_MODEL_ID",
    "ibm/granite-13b-instruct-v2",
)

# ============================================================
# Utility functions
# ============================================================

VALID_ENTITY_TYPES = {
    "PERSON",
    "VICTIM",
    "PHONE",
    "DEVICE",
    "BANK_ACCOUNT",
    "UPI_ID",
    "TRANSACTION",
}

VALID_RELATIONSHIP_TYPES = {
    "USES",
    "BELONGS_TO",
    "TRANSFERRED_TO",
    "ASSOCIATED_WITH",
}


def _generate_case_id() -> str:
    """Generate a short unique case ID."""
    return f"CASE-{uuid.uuid4().hex[:8].upper()}"


def _entity_id(index: int) -> str:
    """Generate deterministic entity IDs."""
    return f"E{index:03d}"


def _clean_name(value: str) -> str:
    """Clean extracted entity text."""
    return value.strip(" .,;:()[]{}\"'")


# ============================================================
# Deterministic fallback extractor
# ============================================================

def _extract_entities_mock(text: str) -> List[Entity]:
    """
    Deterministic fallback entity extraction.

    This is only a fallback for development/demo purposes.
    The main intelligence extraction will eventually use
    IBM watsonx.ai.
    """

    entities: List[Entity] = []
    seen = set()

    # --------------------------------------------------------
    # Generic entity creation
    # --------------------------------------------------------

    def add_entity(
        name: str,
        entity_type: str,
        metadata=None,
    ):
        name = _clean_name(name)

        ignored_terms = {
            "account",
            "accused",
            "device",
            "transaction",
            "phone",
            "mobile",
            "victim",
            "person",
            "bank",
        }

        if not name:
            return

        if name.lower() in ignored_terms:
            return

        key = (name.lower(), entity_type)

        if key in seen:
            return

        seen.add(key)

        entities.append(
            Entity(
                id=_entity_id(len(entities) + 1),
                name=name,
                type=entity_type,
                metadata=metadata or {},
            )
        )

    # --------------------------------------------------------
    # PHONE
    # --------------------------------------------------------

    phone_pattern = r"\b(?:\+91[-\s]?)?[6-9]\d{9}\b"

    for match in re.findall(phone_pattern, text):

        normalized = re.sub(r"[\s-]", "", match)

        if normalized.startswith("+91"):
            normalized = normalized[3:]

        add_entity(
            normalized,
            "PHONE",
            {"country": "IN"},
        )

    # --------------------------------------------------------
    # BANK ACCOUNT
    #
    # Must contain at least one digit.
    # --------------------------------------------------------

    account_pattern = (
        r"\b(?:ACC|ACCOUNT)[-_ ]?[A-Z0-9]{4,20}\b"
    )

    for match in re.findall(
        account_pattern,
        text,
        re.IGNORECASE,
    ):

        add_entity(
            match.upper(),
            "BANK_ACCOUNT",
        )

    # --------------------------------------------------------
    # DEVICE
    #
    # Must contain at least one digit.
    # --------------------------------------------------------

    device_pattern = (
        r"\b(?:DEV|DEVICE)[-_ ]?[A-Za-z0-9]{3,30}\b"
    )

    for match in re.findall(
        device_pattern,
        text,
        re.IGNORECASE,
    ):

        add_entity(
            match.upper(),
            "DEVICE",
        )

    # --------------------------------------------------------
    # UPI ID
    # --------------------------------------------------------

    upi_pattern = (
        r"\b[a-zA-Z0-9._-]+@"
        r"(?:okaxis|oksbi|okicici|okhdfcbank|"
        r"ybl|ibl|paytm)\b"
    )

    for match in re.findall(
        upi_pattern,
        text,
        re.IGNORECASE,
    ):

        add_entity(
            match,
            "UPI_ID",
        )

    # --------------------------------------------------------
    # TRANSACTION ID
    #
    # Extract only the actual ID, not the word
    # "TRANSACTION".
    # --------------------------------------------------------

    transaction_pattern = (
        r"\b(?:TXN|TRANSACTION)[-_ ]?"
        r"(?:ID[-_ ]?)?"
        r"([A-Z]*\d[A-Z0-9]{3,29})\b"
    )

    for match in re.findall(
        transaction_pattern,
        text,
        re.IGNORECASE,
    ):

        add_entity(
            match.upper(),
            "TRANSACTION",
        )

    # --------------------------------------------------------
    # EXPLICIT VICTIM
    # --------------------------------------------------------

    victim_pattern = (
        r"\b(?:victim|victim name)"
        r"\s*[:\-]?\s*"
        r"([A-Z][a-z]+)"
    )

    for match in re.findall(
        victim_pattern,
        text,
        re.IGNORECASE,
    ):

        add_entity(
            match,
            "VICTIM",
            {"role": "victim"},
        )

    # --------------------------------------------------------
    # PERSON
    #
    # Supports:
    # Accused Rahul
    # Mr Rahul
    # Mrs Priya
    # Ms Priya
    # --------------------------------------------------------

    person_pattern = (
        r"\b(?:Mr\.?|Mrs\.?|Ms\.?|Accused|"
        r"Kingpin|Mule)\s+"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"
    )

    for match in re.findall(
        person_pattern,
        text,
    ):

        # Don't duplicate an explicit victim
        is_victim = any(
            entity.name.lower() == match.lower()
            and entity.type == "VICTIM"
            for entity in entities
        )

        if not is_victim:

            add_entity(
                match,
                "PERSON",
            )

    return entities


# ============================================================
# Relationship extraction
# ============================================================

def _find_entity(
    entities: List[Entity],
    value: str,
) -> Optional[Entity]:

    value = value.lower().strip()

    for entity in entities:
        if entity.name.lower() == value:
            return entity

    return None


def _extract_amount(text: str) -> Optional[float]:

    patterns = [
        r"(?:rs\.?|₹|inr)\s*([\d,]+(?:\.\d+)?)",
        r"([\d,]+(?:\.\d+)?)\s*(?:rs\.?|inr)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            value = match.group(1).replace(",", "")

            try:
                return float(value)
            except ValueError:
                pass

    return None


def _extract_date(text: str) -> Optional[str]:

    patterns = [
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b\d{2}/\d{2}/\d{4}\b",
    ]

    for pattern in patterns:

        match = re.search(pattern, text)

        if match:
            return match.group(0)

    return None


def _extract_relationships(
    text: str,
    entities: List[Entity],
) -> List[Relationship]:

    relationships: List[Relationship] = []

    # --------------------------------------------------------
    # Helper
    # --------------------------------------------------------

    def add_relationship(
        source: Entity,
        target: Entity,
        relationship_type: str,
        amount=None,
        timestamp=None,
    ):

        # Prevent duplicate relationships
        for existing in relationships:

            if (
                existing.source == source.id
                and existing.target == target.id
                and existing.type == relationship_type
            ):
                return

        relationships.append(
            Relationship(
                source=source.id,
                target=target.id,
                type=relationship_type,
                amount=amount,
                timestamp=timestamp,
            )
        )

    # --------------------------------------------------------
    # Split text into sentences
    # --------------------------------------------------------

    sentences = re.split(
        r"(?<=[.!?])\s+|\n+",
        text,
    )

    # --------------------------------------------------------
    # Process each sentence independently
    # --------------------------------------------------------

    for sentence in sentences:

        sentence_lower = sentence.lower()

        sentence_entities = [
            entity
            for entity in entities
            if entity.name.lower() in sentence_lower
        ]

        if not sentence_entities:
            continue

        # ----------------------------------------------------
        # Amount and timestamp belong to this sentence
        # ----------------------------------------------------

        amount = _extract_amount(sentence)
        timestamp = _extract_date(sentence)

        # ----------------------------------------------------
        # PERSON -> PHONE
        # ----------------------------------------------------

        if any(
            keyword in sentence_lower
            for keyword in [
                "uses phone",
                "uses mobile",
                "mobile number",
                "phone number",
                "phone",
            ]
        ):

            persons = [
                e for e in sentence_entities
                if e.type == "PERSON"
            ]

            phones = [
                e for e in sentence_entities
                if e.type == "PHONE"
            ]

            for person in persons:

                for phone in phones:

                    add_relationship(
                        person,
                        phone,
                        "USES",
                    )

        # ----------------------------------------------------
        # PERSON -> DEVICE
        # ----------------------------------------------------

        if any(
            keyword in sentence_lower
            for keyword in [
                "uses device",
                "device",
                "using device",
                "device id",
            ]
        ):

            persons = [
                e for e in sentence_entities
                if e.type == "PERSON"
            ]

            devices = [
                e for e in sentence_entities
                if e.type == "DEVICE"
            ]

            for person in persons:

                for device in devices:

                    add_relationship(
                        person,
                        device,
                        "USES",
                    )

        # ----------------------------------------------------
        # PERSON -> BANK ACCOUNT
        # ----------------------------------------------------

        if any(
            keyword in sentence_lower
            for keyword in [
                "account",
                "bank account",
                "belongs",
                "owns",
            ]
        ):

            persons = [
                e for e in sentence_entities
                if e.type == "PERSON"
            ]

            accounts = [
                e for e in sentence_entities
                if e.type == "BANK_ACCOUNT"
            ]

            for person in persons:

                for account in accounts:

                    add_relationship(
                        person,
                        account,
                        "BELONGS_TO",
                    )

        # ----------------------------------------------------
        # TRANSFER
        # ----------------------------------------------------

        if any(
            keyword in sentence_lower
            for keyword in [
                "transferred",
                "transfer",
                "sent",
                "paid",
                "deposited",
                "credited",
            ]
        ):

            senders = [
                e for e in sentence_entities
                if e.type in [
                    "PERSON",
                    "VICTIM",
                ]
            ]

            targets = [
                e for e in sentence_entities
                if e.type in [
                    "BANK_ACCOUNT",
                    "UPI_ID",
                ]
            ]

            for sender in senders:

                for target in targets:

                    add_relationship(
                        sender,
                        target,
                        "TRANSFERRED_TO",
                        amount=amount,
                        timestamp=timestamp,
                    )

    return relationships


# ============================================================
# Mock analysis (deterministic fallback)
# ============================================================

def _mock_analysis(text: str) -> CaseAnalysis:

    entities = _extract_entities_mock(text)

    relationships = _extract_relationships(
        text,
        entities,
    )

    return CaseAnalysis(
        case_id=_generate_case_id(),
        entities=entities,
        relationships=relationships,
    )


# ============================================================
# IBM watsonx.ai adapter
# ============================================================

class WatsonxUnavailableError(Exception):
    """Raised when the watsonx.ai API cannot be reached."""


class WatsonxAdapter:
    """
    Thin wrapper around ibm_watsonx_ai ModelInference.

    Instantiated lazily once when USE_LLM=true and credentials
    are present.  All HTTP / SDK errors are re-raised as
    WatsonxUnavailableError so callers can fall back cleanly.
    """

    def __init__(self) -> None:
        try:
            from ibm_watsonx_ai import Credentials
            from ibm_watsonx_ai.foundation_models import ModelInference

            credentials = Credentials(
                url=WATSONX_URL,
                api_key=WATSONX_API_KEY,
            )

            self._model = ModelInference(
                model_id=WATSONX_MODEL_ID,
                credentials=credentials,
                project_id=WATSONX_PROJECT_ID,
            )

        except Exception as exc:
            raise WatsonxUnavailableError(
                f"Could not initialise watsonx adapter: {exc}"
            ) from exc

    def complete(self, prompt: str) -> str:
        """
        Send *prompt* to the model and return the generated text.

        Raises
        ------
        WatsonxUnavailableError
            On any network or SDK error.
        """
        try:
            response = self._model.generate_text(
                prompt=prompt,
                params={
                    "max_new_tokens": 1024,
                    "temperature": 0.0,
                    "repetition_penalty": 1.05,
                },
            )
            return response  # ModelInference.generate_text returns str

        except Exception as exc:
            raise WatsonxUnavailableError(
                f"watsonx generate_text failed: {exc}"
            ) from exc


# Module-level lazy singleton — created at most once per process
_adapter: Optional[WatsonxAdapter] = None


def _get_adapter() -> WatsonxAdapter:
    global _adapter
    if _adapter is None:
        _adapter = WatsonxAdapter()
    return _adapter


# ============================================================
# Prompt builder
# ============================================================

_SYSTEM_MESSAGE = """You are a cyber-fraud intelligence extraction engine.
Given an unstructured case description, extract all entities and relationships
and return ONLY a single valid JSON object — no prose, no markdown fences.

## Entity types
PERSON, VICTIM, PHONE, DEVICE, BANK_ACCOUNT, UPI_ID, TRANSACTION

## Relationship types
USES, BELONGS_TO, TRANSFERRED_TO, ASSOCIATED_WITH

## Rules
1. Every entity must have: id (E001, E002 …), name, type, metadata (object, may be empty).
2. Every relationship must have: source (entity id), target (entity id), type.
   Optional fields: amount (float, INR), timestamp (ISO-8601 or DD/MM/YYYY).
3. Resolve pronouns: replace "He"/"She"/"They" with the unambiguous antecedent's name.
4. Deduplicate: same name (case-insensitive) + same type → use one entity with one id.
5. Drop relationships whose source or target id does not appear in the entities list.
6. Ignore unknown entity and relationship types.

## Example input
Accused Rahul uses phone 9876543210. He uses device DEV99. Victim Priya transferred Rs 5000 to ACC001 on 2026-01-15.

## Example output
{
  "entities": [
    {"id": "E001", "name": "Rahul", "type": "PERSON", "metadata": {}},
    {"id": "E002", "name": "9876543210", "type": "PHONE", "metadata": {"country": "IN"}},
    {"id": "E003", "name": "DEV99", "type": "DEVICE", "metadata": {}},
    {"id": "E004", "name": "Priya", "type": "VICTIM", "metadata": {"role": "victim"}},
    {"id": "E005", "name": "ACC001", "type": "BANK_ACCOUNT", "metadata": {}}
  ],
  "relationships": [
    {"source": "E001", "target": "E002", "type": "USES"},
    {"source": "E001", "target": "E003", "type": "USES"},
    {"source": "E004", "target": "E005", "type": "TRANSFERRED_TO", "amount": 5000.0, "timestamp": "2026-01-15"}
  ]
}
"""


def _build_prompt(text: str) -> str:
    return (
        f"{_SYSTEM_MESSAGE}\n"
        f"## Case text\n{text.strip()}\n\n"
        f"## Output (JSON only)\n"
    )


# ============================================================
# LLM response parser
# ============================================================

def _parse_llm_response(raw: str, fallback_text: str) -> CaseAnalysis:
    """
    Parse the raw LLM output string into a CaseAnalysis.

    Falls back to _mock_analysis on any parse / validation error.
    """

    # Strip markdown code fences if the model added them
    cleaned = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        raw.strip(),
        flags=re.MULTILINE,
    )

    try:
        data: Dict[str, Any] = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.warning("LLM returned non-JSON (%s) – using fallback", exc)
        return _mock_analysis(fallback_text)

    # --------------------------------------------------------
    # Build entities — deduplicate and reassign sequential IDs
    # --------------------------------------------------------

    raw_entities: List[Dict[str, Any]] = data.get("entities", [])
    entities: List[Entity] = []
    # Maps original LLM-assigned id → normalised id
    id_map: Dict[str, str] = {}
    seen: set = set()

    for raw_ent in raw_entities:
        try:
            etype = str(raw_ent.get("type", "")).upper()
            if etype not in VALID_ENTITY_TYPES:
                continue

            name = _clean_name(str(raw_ent.get("name", "")))
            if not name:
                continue

            key = (name.lower(), etype)
            if key in seen:
                # Map duplicate LLM id to the existing entity id
                for e in entities:
                    if (e.name.lower(), e.type) == key:
                        id_map[str(raw_ent.get("id", ""))] = e.id
                        break
                continue

            seen.add(key)
            new_id = _entity_id(len(entities) + 1)
            id_map[str(raw_ent.get("id", ""))] = new_id

            entities.append(
                Entity(
                    id=new_id,
                    name=name,
                    type=etype,
                    metadata=raw_ent.get("metadata") or {},
                )
            )

        except Exception as exc:
            logger.warning("Skipping malformed entity (%s): %s", exc, raw_ent)

    # --------------------------------------------------------
    # Build relationships — drop any with dangling IDs
    # --------------------------------------------------------

    valid_ids = {e.id for e in entities}
    raw_rels: List[Dict[str, Any]] = data.get("relationships", [])
    relationships: List[Relationship] = []
    seen_rels: set = set()

    for raw_rel in raw_rels:
        try:
            rtype = str(raw_rel.get("type", "")).upper()
            if rtype not in VALID_RELATIONSHIP_TYPES:
                continue

            src_llm = str(raw_rel.get("source", ""))
            tgt_llm = str(raw_rel.get("target", ""))

            src_id = id_map.get(src_llm)
            tgt_id = id_map.get(tgt_llm)

            if src_id not in valid_ids or tgt_id not in valid_ids:
                continue

            rel_key = (src_id, tgt_id, rtype)
            if rel_key in seen_rels:
                continue
            seen_rels.add(rel_key)

            amount: Optional[float] = None
            raw_amount = raw_rel.get("amount")
            if raw_amount is not None:
                try:
                    amount = float(raw_amount)
                except (TypeError, ValueError):
                    pass

            timestamp: Optional[str] = raw_rel.get("timestamp")

            relationships.append(
                Relationship(
                    source=src_id,
                    target=tgt_id,
                    type=rtype,
                    amount=amount,
                    timestamp=timestamp,
                )
            )

        except Exception as exc:
            logger.warning("Skipping malformed relationship (%s): %s", exc, raw_rel)

    try:
        return CaseAnalysis(
            case_id=_generate_case_id(),
            entities=entities,
            relationships=relationships,
        )
    except Exception as exc:
        logger.warning("CaseAnalysis validation failed (%s) – using fallback", exc)
        return _mock_analysis(fallback_text)


# ============================================================
# watsonx orchestrator
# ============================================================

def _watsonx_analysis(text: str) -> CaseAnalysis:
    try:
        prompt = _build_prompt(text)
        raw = _get_adapter().complete(prompt)
        return _parse_llm_response(raw, text)
    except WatsonxUnavailableError:
        logger.warning("watsonx unavailable – using deterministic fallback")
        return _mock_analysis(text)
    except Exception as exc:
        logger.warning("Unexpected LLM error (%s) – using deterministic fallback", exc)
        return _mock_analysis(text)


# ============================================================
# Public API
# ============================================================

def analyze_text(text: str) -> CaseAnalysis:
    """
    Main AI extraction function.

    Parameters
    ----------
    text:
        Unstructured cyber-fraud intelligence.

    Returns
    -------
    CaseAnalysis:
        Structured entities and relationships.

    Notes
    -----
    When USE_LLM=true the request is routed to the IBM watsonx.ai
    extraction layer (ibm/granite-13b-instruct-v2 by default).
    On any API or parse failure the deterministic fallback is
    used transparently so the service never returns an error to
    the caller.

    When USE_LLM=false (default) the deterministic regex-based
    extractor is used directly.
    """

    if not text or not text.strip():
        raise ValueError(
            "Case intelligence text cannot be empty."
        )

    if not USE_LLM:
        return _mock_analysis(text)

    return _watsonx_analysis(text)
