import os
import re
import uuid
from typing import Dict, List, Optional

from app.models.case import CaseAnalysis
from app.models.entities import Entity
from app.models.relationships import Relationship


# ============================================================
# Configuration
# ============================================================

USE_LLM = os.getenv("USE_LLM", "false").lower() == "true"


# ============================================================
# Utility functions
# ============================================================

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
    IBM/Bob.
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
        # r"\b(?:ACC|ACCOUNT)[-_ ]?"
        # r"[A-Z0-9]*\d[A-Z0-9]{3,19}\b"
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
        # r"\b(?:DEV|DEVICE)[-_ ]?"
        # r"[A-Z0-9]*\d[A-Z0-9]{2,29}\b"
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
# Mock analysis
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
    If LLM integration is enabled, this function can route
    the request to the IBM/Bob extraction layer.

    Currently the deterministic fallback is used so the
    application remains runnable without external services.
    """

    if not text or not text.strip():
        raise ValueError(
            "Case intelligence text cannot be empty."
        )

    # --------------------------------------------------------
    # Current development/demo mode
    # --------------------------------------------------------

    if not USE_LLM:
        return _mock_analysis(text)

    # --------------------------------------------------------
    # IBM/Bob integration will be added here.
    # --------------------------------------------------------

    return _mock_analysis(text)