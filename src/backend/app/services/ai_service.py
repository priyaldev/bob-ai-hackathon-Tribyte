import json
import logging
import os
import re
import uuid
from typing import Any, Dict, List, Optional, cast

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

        name_lower = name.lower()
        key = (name_lower, entity_type)

        if key in seen:
            return

        # If a longer name for the same entity type already exists
        # that starts with this name (e.g. "Rahul Mehta" already
        # added and we are about to add "Rahul"), skip the shorter one.
        for existing in entities:
            if (
                existing.type == entity_type
                and existing.name.lower().startswith(name_lower + " ")
            ):
                return

        # If we are adding a longer name that is a fuller version of
        # a short name already registered, upgrade the existing entry
        # instead of creating a duplicate.
        for existing in entities:
            if (
                existing.type == entity_type
                and name_lower.startswith(existing.name.lower() + " ")
            ):
                existing.name = name
                seen.discard((existing.name.lower(), entity_type))
                seen.add(key)
                return

        seen.add(key)

        # Derive a human-readable role label and description for the UI
        _role_labels = {
            "PERSON": "Person of Interest",
            "VICTIM": "Victim",
            "PHONE": "Phone Number",
            "DEVICE": "Device",
            "BANK_ACCOUNT": "Bank Account",
            "UPI_ID": "UPI ID",
            "TRANSACTION": "Transaction Reference",
        }
        role = _role_labels.get(entity_type, entity_type)
        description = f"{role} identified in the investigation notes."

        entities.append(
            Entity(
                id=_entity_id(len(entities) + 1),
                name=name,
                type=entity_type,
                role=role,
                description=description,
                metadata=metadata or {},
            )
        )

    # --------------------------------------------------------
    # BANK ACCOUNT
    #
    # Two forms:
    #   1. Prefixed:  ACC-1234, ACCOUNT 56789
    #   2. Bare numeric: 10–18 digit number that appears
    #      right after "account", "a/c", "account number"
    #      or "account no" in the text.
    #
    # Bare numbers are extracted FIRST so the phone
    # de-duplication guard below can skip them.
    # --------------------------------------------------------

    account_numbers: set = set()

    # Form 3 – arrow-notation transfer lines: "3344556677 -> 5566778899 : 90000"
    # Both the left-hand and right-hand numbers are bank accounts.
    # This must run BEFORE the phone extractor so those numbers are
    # registered in account_numbers and are not misclassified as phones.
    arrow_transfer_pattern = (
        r"\b(\d{7,18})\s*[-=]>\s*(\d{7,18})\s*[:|]\s*[\d,]+"
    )
    for m in re.finditer(arrow_transfer_pattern, text):
        for num in (m.group(1), m.group(2)):
            if num not in account_numbers:
                account_numbers.add(num)
                add_entity(num, "BANK_ACCOUNT")

    # Form 1 – explicitly-prefixed tokens: ACC10001, ACC-9999, ACCOUNT_5678
    # Separator is [-_] only (no space) so "account 4587123690" is handled
    # by Form 2 instead of matching here.
    # The captured ID must contain at least one digit to reject plain words
    # like "access" (ACC + ess).
    # We capture the whole token (ACC10001) as the canonical name so it
    # does not duplicate with a bare numeric from Form 2.
    account_prefix_pattern = (
        r"\b((?:ACC|ACCOUNT)[-_]?[A-Z0-9]*\d[A-Z0-9]{0,19})\b"
    )

    for match in re.findall(
        account_prefix_pattern,
        text,
        re.IGNORECASE,
    ):
        token = match.upper()
        # Reject if the match IS the word "ACCOUNT" with no digits
        if not re.search(r"\d", token):
            continue
        # Strip trailing non-digit noise (shouldn't happen but guard anyway)
        account_numbers.add(token)
        add_entity(token, "BANK_ACCOUNT")

    # Form 2 – bare numeric preceded by account-context keyword:
    # "account 4587123690", "account number 4587123690", "a/c 123"
    # Skip numbers already registered by Form 1 (e.g. "10001" from
    # ACC10001 and then again from "account number ACC10001").
    bare_account_pattern = (
        r"\b(?:account(?:\s+(?:number|no\.?))?|a/c)\s+"
        r"(\d{7,18})\b"
    )

    for match in re.findall(
        bare_account_pattern,
        text,
        re.IGNORECASE,
    ):
        # Skip if a prefixed form already registered this number
        if match not in account_numbers and match.upper() not in account_numbers:
            account_numbers.add(match)
            add_entity(match, "BANK_ACCOUNT")

    # --------------------------------------------------------
    # PHONE
    #
    # Indian mobile: starts 6-9, 10 digits.
    # Skip numbers already claimed as bank accounts.
    # --------------------------------------------------------

    phone_pattern = r"\b(?:\+91[-\s]?)?[6-9]\d{9}\b"

    for match in re.findall(phone_pattern, text):

        normalized = re.sub(r"[\s-]", "", match)

        if normalized.startswith("+91"):
            normalized = normalized[3:]

        # Do not misclassify a bare account number as a phone
        if normalized in account_numbers:
            continue

        add_entity(
            normalized,
            "PHONE",
            {"country": "IN"},
        )

    # --------------------------------------------------------
    # DEVICE
    #
    # Matches DEV-1024, DEV_99, DEV101, DEVICE-X3 etc.
    # The separator between prefix and ID is [-_] only
    # (no space) to avoid matching "device records" etc.
    # --------------------------------------------------------

    device_pattern = (
        r"\b(?:DEV|DEVICE)[-_]([A-Za-z0-9]{2,30})\b"
        r"|\b(?:DEV|DEVICE)([A-Za-z0-9]{3,30})\b"
    )

    for m in re.finditer(device_pattern, text, re.IGNORECASE):
        # Group 1 = with separator (DEV-1024), group 2 = without (DEV12345)
        raw = m.group(1) or m.group(2)
        prefix = m.group(0).split(raw)[0].rstrip("-_")
        full = f"{prefix.upper()}-{raw.upper()}" if m.group(1) else f"{prefix.upper()}{raw.upper()}"
        add_entity(full, "DEVICE")

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
    #
    # Captures full name (first + optional last).
    # --------------------------------------------------------

    # Victim keyword is matched case-insensitively, but the captured
    # name must start with a real capital letter (not IGNORECASE) to
    # avoid greedy matching of lowercase words like "transferred".
    victim_pattern = (
        r"(?i:\b(?:victim|victim name)\s*[:\-]?\s*)"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"
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
    # Three detection strategies:
    #
    # 1. Title prefix:  Mr/Mrs/Ms/Dr Rahul Mehta
    # 2. Role prefix:   Accused/Kingpin/Mule Rahul
    # 3. Narrative context:
    #      "complaint from Amit Verma"
    #      "connected to Rahul Mehta"
    #      "associated with Neeraj Singh"
    #      "belonging to <Name>"
    # --------------------------------------------------------

    person_patterns = [
        # Strategy 1 & 2 – title/role prefix
        (
            r"\b(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Accused|"
            r"Kingpin|Mule)\s+"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"
        ),
        # Strategy 3 – narrative context verbs/prepositions
        (
            r"\b(?:connected to|associated with|"
            r"belonging to|belongs to|"
            r"complaint from|reported by|"
            r"linked to)\s+"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"
        ),
        # Strategy 4 – person as the grammatical subject of a financial verb
        # "Rajesh Patel transferred …", "Priya sent …", "Kumar paid …"
        (
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"
            r"\s+(?:transferred|sent|paid|deposited|credited|received)"
        ),
        # Strategy 5 – "filed by <Name>", "complaint filed by <Name>"
        (
            r"\bfiled\s+by\s+"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"
        ),
    ]

    for person_pattern in person_patterns:
        for match in re.findall(person_pattern, text):

            # Don't duplicate an explicit victim
            is_victim = any(
                entity.name.lower() == match.lower()
                and entity.type == "VICTIM"
                for entity in entities
            )

            if not is_victim:
                add_entity(match, "PERSON")

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
    # Arrow-notation transfers  (pre-pass, before sentence loop)
    #
    # Handles lines like:
    #   3344556677 -> 5566778899 : 90000
    #   3344556677 -> 5566778899 = 90000
    # Both endpoints must already be registered as BANK_ACCOUNT
    # entities (guaranteed by the entity extractor's Form 3 pass).
    # --------------------------------------------------------

    arrow_rel_pattern = (
        r"\b(\d{7,18})\s*[-=]>\s*(\d{7,18})\s*[:|]\s*([\d,]+(?:\.\d+)?)"
    )
    for m in re.finditer(arrow_rel_pattern, text):
        src_num, tgt_num, amt_str = m.group(1), m.group(2), m.group(3)
        src_ent = next((e for e in entities if e.name == src_num and e.type == "BANK_ACCOUNT"), None)
        tgt_ent = next((e for e in entities if e.name == tgt_num and e.type == "BANK_ACCOUNT"), None)
        if src_ent and tgt_ent:
            try:
                amt_val: Optional[float] = float(amt_str.replace(",", ""))
            except ValueError:
                amt_val = None
            add_relationship(src_ent, tgt_ent, "TRANSFERRED_TO", amount=amt_val)

    # --------------------------------------------------------
    # Multi-line transaction block parser  (pre-pass)
    #
    # Handles blocks like:
    #   Txn ref TXN90871
    #   From: Anjali's account      ← or "From: Anjali Gupta"
    #   To: 3344556677
    #   Amount: 75000
    #   Time: 11:42
    #
    # We scan a 6-line window: look for a "To: <account>" line,
    # then search the preceding lines for a "From: <name/account>"
    # and a numeric amount on any nearby line.
    # --------------------------------------------------------

    lines = text.splitlines()
    for line_idx, line in enumerate(lines):
        to_m = re.match(r"^\s*[Tt]o\s*:\s*(\d{7,18})", line)
        if not to_m:
            continue
        tgt_num = to_m.group(1)
        tgt_ent = next((e for e in entities if e.name == tgt_num and e.type == "BANK_ACCOUNT"), None)
        if not tgt_ent:
            continue

        # Look in the 5 lines before for "From: <something>"
        window_start = max(0, line_idx - 5)
        window = lines[window_start:line_idx]

        from_ent: Optional[Entity] = None
        for wline in window:
            from_m = re.match(r"^\s*[Ff]rom\s*:\s*(.+)", wline)
            if not from_m:
                continue
            # Strip possessive + "account" suffix ("Anjali's account" -> "Anjali")
            raw_from = re.sub(
                r"['\u2019]s\s+account\b", "", from_m.group(1).strip(),
                flags=re.IGNORECASE,
            ).strip()
            raw_from_lower = raw_from.lower()
            # Try to match against known entities by name.
            # Check both directions:
            #   "Anjali Gupta" in "Anjali Gupta"  (full name in text)
            #   "Anjali" in "Anjali Gupta"         (first-name abbreviated)
            for e in entities:
                if e.type not in ("PERSON", "VICTIM", "BANK_ACCOUNT"):
                    continue
                ename_lower = e.name.lower()
                first_token = ename_lower.split()[0]
                if (
                    ename_lower in raw_from_lower        # full name in text
                    or raw_from_lower in ename_lower     # text is prefix of name
                    or first_token == raw_from_lower     # first name only
                ):
                    from_ent = e
                    break
            if from_ent:
                break

        if not from_ent:
            continue

        # Look for "Amount: <number>" in the same window (after "From")
        block_lines = lines[window_start: line_idx + 3]
        block_text = " ".join(block_lines)
        amt_m = re.search(r"[Aa]mount\s*:\s*([\d,]+(?:\.\d+)?)", block_text)
        block_amount: Optional[float] = None
        if amt_m:
            try:
                block_amount = float(amt_m.group(1).replace(",", ""))
            except ValueError:
                pass

        add_relationship(from_ent, tgt_ent, "TRANSFERRED_TO", amount=block_amount)

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

        # Match entities whose full name OR first name (first token)
        # appears in the sentence. This handles cases like
        # "Riya later noticed..." when the entity is "Riya Sharma",
        # or "associated with Rahul" when entity is "Rahul Mehta".
        sentence_entities = [
            entity
            for entity in entities
            if entity.name.lower() in sentence_lower
            or (
                len(entity.name.split()) > 1
                and entity.name.split()[0].lower() in sentence_lower
            )
        ]

        if not sentence_entities:
            continue

        # ----------------------------------------------------
        # Amount and timestamp belong to this sentence
        # ----------------------------------------------------

        amount = _extract_amount(sentence)
        timestamp = _extract_date(sentence)

        # ----------------------------------------------------
        # PERSON / VICTIM -> PHONE  (USES / ASSOCIATED_WITH)
        # Also handles:
        #  "received a call from X" → victim ASSOCIATED_WITH phone
        #  "phone number X is associated with Y"
        # ----------------------------------------------------

        phones_in_sentence = [
            e for e in sentence_entities if e.type == "PHONE"
        ]

        if phones_in_sentence and any(
            keyword in sentence_lower
            for keyword in [
                "uses phone", "uses mobile",
                "mobile number", "phone number", "phone",
                "associated with", "call from", "received a call",
            ]
        ):
            actors = [
                e for e in sentence_entities
                if e.type in ("PERSON", "VICTIM")
            ]

            for actor in actors:
                for phone in phones_in_sentence:
                    add_relationship(actor, phone, "USES")

        # ----------------------------------------------------
        # PHONE -> DEVICE  (ASSOCIATED_WITH)
        # "phone number was found associated with device DEV-X"
        # ----------------------------------------------------

        if any(
            keyword in sentence_lower
            for keyword in [
                "associated with device",
                "found associated with device",
            ]
        ):
            for phone in phones_in_sentence:
                for device in [
                    e for e in sentence_entities if e.type == "DEVICE"
                ]:
                    add_relationship(phone, device, "ASSOCIATED_WITH")

        # ----------------------------------------------------
        # PERSON / VICTIM -> DEVICE  (USES)
        # ----------------------------------------------------

        if any(
            keyword in sentence_lower
            for keyword in [
                "uses device",
                "used device",
                "using device",
                "device id",
                "found associated with device",
                "associated with device",
            ]
        ) or any(
            e.type == "DEVICE" for e in sentence_entities
        ):

            actors = [
                e for e in sentence_entities
                if e.type in ("PERSON", "VICTIM")
            ]

            devices = [
                e for e in sentence_entities
                if e.type == "DEVICE"
            ]

            for actor in actors:
                for device in devices:
                    add_relationship(actor, device, "USES")

        # ----------------------------------------------------
        # DEVICE -> BANK ACCOUNT  (USES)
        # Sentence like: "device DEV-1024 was used to access
        # both account X and account Y"
        # Also handles: "observed during login activity for"
        # ----------------------------------------------------

        if any(
            keyword in sentence_lower
            for keyword in [
                "access", "accesses", "accessed",
                "login activity", "observed during",
            ]
        ):

            devices = [
                e for e in sentence_entities
                if e.type == "DEVICE"
            ]

            accounts = [
                e for e in sentence_entities
                if e.type == "BANK_ACCOUNT"
            ]

            for device in devices:
                for account in accounts:
                    add_relationship(
                        device, account, "USES"
                    )

        # ----------------------------------------------------
        # PERSON -> BANK ACCOUNT  (BELONGS_TO / ASSOCIATED_WITH)
        # ----------------------------------------------------

        if any(
            keyword in sentence_lower
            for keyword in [
                "bank account",
                "belongs",
                "owns",
                "connected to",
                "associated with",
            ]
        ):

            persons = [
                e for e in sentence_entities
                if e.type in ("PERSON", "VICTIM")
            ]

            accounts = [
                e for e in sentence_entities
                if e.type == "BANK_ACCOUNT"
            ]

            for person in persons:
                for account in accounts:
                    # Use BELONGS_TO when ownership language present,
                    # ASSOCIATED_WITH for looser wording
                    rel_type = (
                        "BELONGS_TO"
                        if any(
                            kw in sentence_lower
                            for kw in ["belongs", "owns", "connected to"]
                        )
                        else "ASSOCIATED_WITH"
                    )
                    add_relationship(person, account, rel_type)

        # ----------------------------------------------------
        # PERSON / ACCOUNT -> PHONE  (ASSOCIATED_WITH)
        # "phone number X is associated with Rahul"
        # ----------------------------------------------------

        if any(
            keyword in sentence_lower
            for keyword in [
                "associated with",
                "is associated",
                "phone number",
                "phone",
            ]
        ):

            persons = [
                e for e in sentence_entities
                if e.type in ("PERSON", "VICTIM")
            ]

            phones = [
                e for e in sentence_entities
                if e.type == "PHONE"
            ]

            for person in persons:
                for phone in phones:
                    add_relationship(person, phone, "USES")

        # ----------------------------------------------------
        # TRANSFER  (PERSON/VICTIM/ACCOUNT -> ACCOUNT/UPI)
        #
        # For account-to-account transfers the direction is
        # inferred by position: whichever account appears
        # earlier in the sentence is the sender.
        # Covers "transferred", "sent", "paid", "deposited",
        # "credited", and UPI-style phrases like
        # "UPI transaction of Rs X from … to account Y".
        # ----------------------------------------------------

        transfer_keywords = [
            "transferred", "transfer",
            "sent", "paid", "deposited", "credited",
            "upi transaction", "transaction of",
        ]

        if any(kw in sentence_lower for kw in transfer_keywords):

            potential_senders = [
                e for e in sentence_entities
                if e.type in ("PERSON", "VICTIM", "BANK_ACCOUNT")
            ]

            potential_targets = [
                e for e in sentence_entities
                if e.type in ("BANK_ACCOUNT", "UPI_ID")
            ]

            for sender in potential_senders:
                for target in potential_targets:
                    if sender.id == target.id:
                        continue

                    # For account→account: enforce positional order.
                    # If both are accounts, the one that appears first
                    # in the sentence is the sender.
                    if (
                        sender.type == "BANK_ACCOUNT"
                        and target.type == "BANK_ACCOUNT"
                    ):
                        pos_sender = sentence_lower.find(
                            sender.name.lower()
                        )
                        pos_target = sentence_lower.find(
                            target.name.lower()
                        )
                        if pos_sender > pos_target:
                            # Target appears before sender → skip
                            # (the reversed pair will be caught
                            #  when sender/target are swapped)
                            continue

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

    def complete(self, messages: list) -> str:
        """
        Send *messages* to the model via the chat API and return the
        generated text.

        Parameters
        ----------
        messages:
            List of ``{"role": ..., "content": ...}`` dicts.  Should contain
            at minimum a ``system`` message followed by a ``user`` message.

        Raises
        ------
        WatsonxUnavailableError
            On any network or SDK error.
        """
        try:
            response = self._model.chat(
                messages=messages,
                params={
                    "max_new_tokens": 1024,
                    "temperature": 0.0,
                    "repetition_penalty": 1.05,
                },
            )
            return cast(str, response["choices"][0]["message"]["content"])

        except Exception as exc:
            raise WatsonxUnavailableError(
                f"watsonx chat failed: {exc}"
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

# _SYSTEM_MESSAGE = """You are a cyber-fraud intelligence extraction engine.
# Given an unstructured case description, extract all entities and relationships
# and return ONLY a single valid JSON object — no prose, no markdown fences.

# ## Entity types
# PERSON, VICTIM, PHONE, DEVICE, BANK_ACCOUNT, UPI_ID, TRANSACTION

# ## Relationship types
# USES, BELONGS_TO, TRANSFERRED_TO, ASSOCIATED_WITH

# ## Rules
# 1. Every entity must have: id (E001, E002 …), name, type, metadata (object, may be empty).
# 2. Every relationship must have: source (entity id), target (entity id), type.
#    Optional fields: amount (float, INR), timestamp (ISO-8601 or DD/MM/YYYY).
# 3. Resolve pronouns: replace "He"/"She"/"They" with the unambiguous antecedent's name.
# 4. Deduplicate: same name (case-insensitive) + same type → use one entity with one id.
# 5. Drop relationships whose source or target id does not appear in the entities list.
# 6. Ignore unknown entity and relationship types.

# ## Example input
# Accused Rahul uses phone 9876543210. He uses device DEV99. Victim Priya transferred Rs 5000 to ACC001 on 2026-01-15.

# ## Example output
# {
#   "entities": [
#     {"id": "E001", "name": "Rahul", "type": "PERSON", "metadata": {}},
#     {"id": "E002", "name": "9876543210", "type": "PHONE", "metadata": {"country": "IN"}},
#     {"id": "E003", "name": "DEV99", "type": "DEVICE", "metadata": {}},
#     {"id": "E004", "name": "Priya", "type": "VICTIM", "metadata": {"role": "victim"}},
#     {"id": "E005", "name": "ACC001", "type": "BANK_ACCOUNT", "metadata": {}}
#   ],
#   "relationships": [
#     {"source": "E001", "target": "E002", "type": "USES"},
#     {"source": "E001", "target": "E003", "type": "USES"},
#     {"source": "E004", "target": "E005", "type": "TRANSFERRED_TO", "amount": 5000.0, "timestamp": "2026-01-15"}
#   ]
# }
# """
_SYSTEM_MESSAGE = """You are a cyber-fraud intelligence extraction engine.

Your task is to convert unstructured cyber-fraud investigation notes into a
structured graph of entities and relationships.

Return ONLY one valid JSON object.
Do NOT return markdown.
Do NOT return explanations.
Do NOT return ```json fences.

============================================================
ENTITY TYPES
============================================================

Allowed entity types:

PERSON
VICTIM
PHONE
DEVICE
BANK_ACCOUNT
UPI_ID
TRANSACTION

Rules:

1. Every entity must have:
   - id
   - name
   - type
   - metadata

2. IDs must be sequential:
   E001, E002, E003, ...

3. Deduplicate entities:
   Same real-world entity must receive only ONE entity ID.

4. Preserve complete names.

   Example:
   "Suresh Yadav" must be extracted as:

   {
     "name": "Suresh Yadav",
     "type": "PERSON"
   }

   Do NOT shorten it to "Suresh" if the full name is available.

5. A person mentioned by first name later should resolve to the previously
   identified full name when the context is unambiguous.

   Example:
   "Suresh Yadav..."
   later:
   "Mobile number ... is associated with Suresh"

   Resolve "Suresh" to "Suresh Yadav".

============================================================
TRANSACTION ENTITY RULES
============================================================

A TRANSACTION entity represents a transaction reference/identifier.

Examples:

TXN90871
TXN90892
TRANSACTION-1001

These MUST be represented as TRANSACTION entities.

IMPORTANT:

Amounts are NOT transaction entities.

For example:

Amount: 75000

MUST NOT create:

{
  "type": "TRANSACTION",
  "name": "75000"
}

Instead, 75000 must be stored as the "amount" property of the
corresponding TRANSFERRED_TO relationship.

Therefore:

"Transaction reference TXN90871"
"Amount 75000"

means:

TRANSACTION = TXN90871
amount = 75000

============================================================
BANK ACCOUNT VS PHONE
============================================================

A numeric value may represent either a PHONE or BANK_ACCOUNT.

Use contextual evidence.

Phone examples:

9123456780
9876543210

Bank account examples:

3344556677
5566778899
4587123690

IMPORTANT:

If a number appears in an account-transfer expression:

3344556677 -> 5566778899 : 90000

then BOTH numbers MUST be treated as BANK_ACCOUNT entities,
not PHONE entities.

Likewise:

5566778899 -> 7788990011 : 85000

means all three numbers are BANK_ACCOUNT entities when they occur
in this transaction-chain context.

Do not classify an account number as PHONE merely because it has
10 digits.

============================================================
TRANSACTION BLOCKS
============================================================

Investigation notes may describe one transaction across multiple lines.

For example:

Txn ref TXN90871
From: Anjali's account
To: 3344556677
Amount: 75000
Time: 11:42

These lines represent ONE transaction event.

Interpret them together as:

transaction_id = TXN90871
source = Anjali Gupta
target = 3344556677
amount = 75000
timestamp = 11:42

If "Anjali's account" clearly refers to Anjali Gupta's account,
the TRANSFERRED_TO relationship must originate from Anjali Gupta.

DO NOT treat the amount as an entity.

DO NOT treat the transaction ID as the source of the money.

Correct:

Anjali Gupta -> TRANSFERRED_TO -> 3344556677
amount = 75000
timestamp = 11:42

Incorrect:

TXN90871 -> TRANSFERRED_TO -> 3344556677

============================================================
ACCOUNT-TO-ACCOUNT TRANSFERS
============================================================

The following notation represents a financial transfer:

3344556677 -> 5566778899 : 90000

Interpret it as:

3344556677 -> TRANSFERRED_TO -> 5566778899
amount = 90000

Another example:

5566778899 -> 7788990011 : 85000

Interpret it as:

5566778899 -> TRANSFERRED_TO -> 7788990011
amount = 85000

IMPORTANT:

The source and target MUST be the BANK_ACCOUNT entities.

Do NOT use the TRANSACTION entity as the source or target.

============================================================
TRANSACTION REFERENCES
============================================================

Transaction references provide identifying information about a
transaction but are not normally the source or target of the
TRANSFERRED_TO relationship.

Example:

Txn ref TXN90871
From: Anjali Gupta
To: 3344556677
Amount: 75000

Create:

TRANSACTION entity:
TXN90871

AND:

Anjali Gupta -> TRANSFERRED_TO -> 3344556677

with:

amount = 75000

timestamp = appropriate timestamp if available.

Do NOT create:

TXN90871 -> TRANSFERRED_TO -> 3344556677

unless the input explicitly states that the transaction entity
itself participates in a relationship.

============================================================
PEOPLE AND ACCOUNTS
============================================================

If the text says:

"Account 3344556677 is operated by Suresh Yadav."

create:

Suresh Yadav -> ASSOCIATED_WITH -> 3344556677

If the text says:

"Account 5566778899 is associated with Pankaj Kumar."

create:

Pankaj Kumar -> ASSOCIATED_WITH -> 5566778899

Do not infer ownership when the text only says "associated with",
"reported", "appears connected", or similar uncertain language.

Preserve the evidence rather than inventing facts.

============================================================
PHONE RELATIONSHIPS
============================================================

If the text says:

"Mobile number 9123456780 is associated with Suresh."

and Suresh clearly refers to Suresh Yadav:

Suresh Yadav -> ASSOCIATED_WITH -> 9123456780

If the text says:

"Phone number 9876543210 is associated with Rahul."

and Rahul clearly refers to Rahul Mehta:

Rahul Mehta -> ASSOCIATED_WITH -> 9876543210

============================================================
DEVICE RELATIONSHIPS
============================================================

If the text says:

"Device DEV-4455 was observed during login activity for 3344556677."

create:

DEV-4455 -> USES -> 3344556677

If the same device was used to access multiple accounts:

DEV-4455 -> USES -> Account A
DEV-4455 -> USES -> Account B

Do not merge the two accounts.

============================================================
TIMESTAMPS
============================================================

Preserve explicit timestamps.

Examples:

11:42
11:35 AM
2026-09-20
20/09/2026

If only a time is provided, use the time as provided.

Do not invent a date.

If an exact date and time are available, normalize them to ISO-8601
when possible.

============================================================
AMOUNTS
============================================================

Extract INR amounts as numeric values.

Examples:

Rs 75,000 -> 75000.0
₹32,000 -> 32000.0
Amount 46000 -> 46000.0

Amounts belong on TRANSFERRED_TO relationships.

Do NOT create entities from amounts.

============================================================
PRONOUNS AND REFERENCES
============================================================

Resolve pronouns when the antecedent is unambiguous.

Example:

"Rahul uses phone 9876543210. He also uses device DEV123."

"He" = Rahul.

Resolve shortened references when unambiguous.

Example:

"Suresh Yadav is associated with account 3344556677.
The mobile number is associated with Suresh."

"Suresh" = Suresh Yadav.

============================================================
UNCERTAINTY
============================================================

Do not convert allegations or investigation leads into confirmed facts.

Examples:

"reportedly operated by"
"appears to be connected to"
"preliminary records"
"may have been used"
"indications suggest"

must not cause the person to be labeled as a confirmed offender.

The entity should remain PERSON unless the text explicitly identifies
the person as a victim or another supported entity type.

============================================================
RELATIONSHIP TYPES
============================================================

Allowed relationship types:

USES
BELONGS_TO
TRANSFERRED_TO
ASSOCIATED_WITH

Every relationship must have:

source
target
type

Optional:

amount
timestamp

The source and target MUST be valid entity IDs.

============================================================
DEDUPLICATION
============================================================

Do not create duplicate entities.

For example:

"Suresh Yadav"
"Suresh"

should resolve to the same PERSON when context makes the reference
unambiguous.

Likewise:

"3344556677"
"account 3344556677"

refer to the same BANK_ACCOUNT.

============================================================
IMPORTANT FINAL VALIDATION
============================================================

Before returning the JSON, verify:

1. Every entity has id, name, type and metadata.
2. Every entity type is allowed.
3. Every relationship source exists.
4. Every relationship target exists.
5. No amount is represented as a TRANSACTION entity.
6. Transaction references such as TXN90871 remain intact.
7. Account-to-account arrow transfers use BANK_ACCOUNT entities.
8. Full person names are preserved.
9. Duplicate entities are merged.
10. Do not invent relationships that are not supported by the text.
11. Do not identify a person as a confirmed offender unless explicitly
    supported by the input.
12. Return ONLY valid JSON.

============================================================
OUTPUT FORMAT
============================================================

{
  "entities": [
    {
      "id": "E001",
      "name": "entity name",
      "type": "ENTITY_TYPE",
      "metadata": {}
    }
  ],
  "relationships": [
    {
      "source": "E001",
      "target": "E002",
      "type": "RELATIONSHIP_TYPE",
      "amount": 75000.0,
      "timestamp": "11:42"
    }
  ]
}
"""


def _build_prompt(text: str) -> str:
    return (
        f"{_SYSTEM_MESSAGE}\n"
        f"## Case text\n{text.strip()}\n\n"
        f"## Output (JSON only)\n"
    )


def _build_messages(text: str) -> list:
    """Return a chat-API messages list with separate system and user roles."""
    user_content = (
        f"## Case text\n{text.strip()}\n\n"
        f"## Output (JSON only)\n"
    )
    return [
        {"role": "system", "content": _SYSTEM_MESSAGE},
        {"role": "user", "content": user_content},
    ]


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

            _role_labels = {
                "PERSON": "Person of Interest",
                "VICTIM": "Victim",
                "PHONE": "Phone Number",
                "DEVICE": "Device",
                "BANK_ACCOUNT": "Bank Account",
                "UPI_ID": "UPI ID",
                "TRANSACTION": "Transaction Reference",
            }
            role = _role_labels.get(etype, etype)
            description = f"{role} identified in the investigation notes."

            entities.append(
                Entity(
                    id=new_id,
                    name=name,
                    type=etype,
                    role=role,
                    description=description,
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
        messages = _build_messages(text)
        raw = _get_adapter().complete(messages)
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
