"""
Pytest suite for app.services.ai_service
=========================================

Tests cover:
  - Basic extraction (smoke)
  - False-positive suppression
  - Duplicate-entity deduplication
  - Pronoun-resolution in fallback path
  - Relationship amount & timestamp capture
  - Empty-input guard
  - Ambiguous multi-party relationships (no crash)
  - watsonx success path (mocked adapter)
  - watsonx API failure → graceful fallback
  - watsonx malformed JSON → graceful fallback
  - watsonx extra / unknown entity types → sanitised
  - watsonx duplicate IDs in LLM response → deduplicated
  - Relationships referencing non-existent IDs → silently dropped
"""

import json
import os

import pytest

# ---------------------------------------------------------------------------
# Make sure USE_LLM is *off* for all non-watsonx tests so the module-level
# flag is False when this process loads ai_service.  Individual watsonx tests
# temporarily patch the module attribute directly.
# ---------------------------------------------------------------------------
os.environ.setdefault("USE_LLM", "false")

from app.services.ai_service import (  # noqa: E402
    WatsonxUnavailableError,
    _build_prompt,
    _mock_analysis,
    _parse_llm_response,
    analyze_text,
)


# ===========================================================================
# Fixtures
# ===========================================================================

STANDARD_TEXT = """
Accused Rahul uses phone number 9876543210.
He uses device DEV12345.
Rahul transferred Rs 25000 to bank account ACC10001 on 2026-09-20.
Victim Priya transferred Rs 25000 to ACC10001.
The transaction TXN1001 was associated with the device.
"""


# ===========================================================================
# 1. Basic extraction smoke test
# ===========================================================================

class TestBasicExtraction:

    def test_returns_case_analysis(self):
        result = analyze_text(STANDARD_TEXT)
        assert result.case_id.startswith("CASE-")
        assert isinstance(result.entities, list)
        assert isinstance(result.relationships, list)

    def test_phone_extracted(self):
        result = analyze_text(STANDARD_TEXT)
        phones = [e for e in result.entities if e.type == "PHONE"]
        assert any(e.name == "9876543210" for e in phones), (
            "Expected phone 9876543210 in entities"
        )

    def test_device_extracted(self):
        result = analyze_text(STANDARD_TEXT)
        devices = [e for e in result.entities if e.type == "DEVICE"]
        assert any("DEV12345" in e.name for e in devices)

    def test_bank_account_extracted(self):
        result = analyze_text(STANDARD_TEXT)
        accounts = [e for e in result.entities if e.type == "BANK_ACCOUNT"]
        assert any("ACC10001" in e.name for e in accounts)

    def test_victim_extracted(self):
        result = analyze_text(STANDARD_TEXT)
        victims = [e for e in result.entities if e.type == "VICTIM"]
        assert any(e.name == "Priya" for e in victims)

    def test_person_extracted(self):
        result = analyze_text(STANDARD_TEXT)
        persons = [e for e in result.entities if e.type == "PERSON"]
        assert any(e.name == "Rahul" for e in persons)

    def test_transaction_extracted(self):
        result = analyze_text(STANDARD_TEXT)
        transactions = [e for e in result.entities if e.type == "TRANSACTION"]
        assert any("1001" in e.name for e in transactions)


# ===========================================================================
# 2. False-positive suppression
# ===========================================================================

class TestFalsePositiveSuppression:

    def test_generic_word_account_not_entity(self):
        """The bare word 'account' must not become an entity."""
        result = analyze_text(
            "The suspect opened a bank account last week."
        )
        for entity in result.entities:
            assert entity.name.lower() != "account"

    def test_generic_word_device_not_entity(self):
        result = analyze_text(
            "Police recovered a device from the scene."
        )
        for entity in result.entities:
            assert entity.name.lower() != "device"

    def test_generic_word_victim_not_entity(self):
        result = analyze_text(
            "The victim reported the fraud to police."
        )
        # 'victim' alone should NOT create a VICTIM entity (no name follows)
        for entity in result.entities:
            assert entity.name.lower() not in ("victim",)

    def test_no_short_garbage_entities(self):
        result = analyze_text(
            "Mr. X sent money."  # 'X' is only one char — not a valid name
        )
        # Should produce 0 or only valid entities; no single-char names
        for entity in result.entities:
            assert len(entity.name) > 1


# ===========================================================================
# 3. Duplicate entity deduplication
# ===========================================================================

class TestDeduplication:

    def test_same_phone_twice_one_entity(self):
        text = (
            "Accused Rahul uses phone 9123456789. "
            "Later Rahul called from 9123456789 again."
        )
        result = analyze_text(text)
        phones = [e for e in result.entities if e.type == "PHONE"]
        names = [e.name for e in phones]
        assert names.count("9123456789") == 1, (
            f"Phone duplicated: {names}"
        )

    def test_same_person_twice_one_entity(self):
        text = (
            "Accused Ravi transferred Rs 1000 to ACC2001. "
            "Accused Ravi also owns ACC2002."
        )
        result = analyze_text(text)
        persons = [e for e in result.entities if e.type == "PERSON"]
        names = [e.name.lower() for e in persons]
        assert names.count("ravi") == 1, (
            f"Person duplicated: {names}"
        )

    def test_same_account_twice_one_entity(self):
        text = (
            "Priya transferred to ACC5001. "
            "Victim Priya again transferred Rs 500 to ACC5001."
        )
        result = analyze_text(text)
        accounts = [e for e in result.entities if e.type == "BANK_ACCOUNT"]
        names = [e.name for e in accounts]
        assert names.count("ACC5001") == 1


# ===========================================================================
# 4. Pronoun resolution in fallback
# ===========================================================================

class TestPronounResolutionFallback:

    def test_he_device_linked_to_person(self):
        """
        The deterministic fallback does not resolve 'He' to 'Rahul', but it
        must not crash.  If DEV12345 appears later the device entity is still
        created.
        """
        text = (
            "Accused Rahul uses phone 9876543210. "
            "He uses device DEV12345."
        )
        result = analyze_text(text)
        devices = [e for e in result.entities if e.type == "DEVICE"]
        assert any("DEV12345" in e.name for e in devices), (
            "Device entity missing from fallback extraction"
        )


# ===========================================================================
# 5. Relationship amount and timestamp
# ===========================================================================

class TestRelationshipMetadata:

    def test_amount_captured(self):
        text = (
            "Victim Priya transferred Rs 25000 to ACC10001 on 2026-09-20."
        )
        result = analyze_text(text)
        transfers = [
            r for r in result.relationships
            if r.type == "TRANSFERRED_TO"
        ]
        assert transfers, "No TRANSFERRED_TO relationship found"
        assert any(r.amount == 25000.0 for r in transfers), (
            f"Amount 25000 not found: {[r.amount for r in transfers]}"
        )

    def test_timestamp_captured(self):
        text = (
            "Victim Priya transferred Rs 25000 to ACC10001 on 2026-09-20."
        )
        result = analyze_text(text)
        transfers = [
            r for r in result.relationships
            if r.type == "TRANSFERRED_TO"
        ]
        assert any(r.timestamp == "2026-09-20" for r in transfers), (
            f"Timestamp not found: {[r.timestamp for r in transfers]}"
        )

    def test_slash_date_format_captured(self):
        text = (
            "Victim Priya transferred Rs 1000 to ACC99 on 20/09/2026."
        )
        result = analyze_text(text)
        transfers = [
            r for r in result.relationships
            if r.type == "TRANSFERRED_TO"
        ]
        assert any(r.timestamp == "20/09/2026" for r in transfers)


# ===========================================================================
# 6. Empty-input guard
# ===========================================================================

class TestInputValidation:

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            analyze_text("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            analyze_text("   \n\t  ")


# ===========================================================================
# 7. Ambiguous relationships — no crash
# ===========================================================================

class TestAmbiguousRelationships:

    def test_two_people_two_accounts_no_crash(self):
        text = (
            "Accused Ravi owns bank account ACC3001. "
            "Accused Sanjay owns bank account ACC3002. "
            "Some transfer happened between accounts."
        )
        result = analyze_text(text)
        # Must not raise; may produce 0 or more relationships
        assert isinstance(result.relationships, list)

    def test_no_relationship_without_matching_entities(self):
        text = "A mysterious transfer happened."
        result = analyze_text(text)
        # No named entities → no relationships expected
        assert result.relationships == []


# ===========================================================================
# Helpers for watsonx tests
# ===========================================================================

def _make_valid_llm_json(
    entities=None,
    relationships=None,
) -> str:
    payload = {
        "entities": entities or [
            {
                "id": "E001",
                "name": "Vikram",
                "type": "PERSON",
                "metadata": {},
            },
            {
                "id": "E002",
                "name": "9001234567",
                "type": "PHONE",
                "metadata": {"country": "IN"},
            },
        ],
        "relationships": relationships or [
            {
                "source": "E001",
                "target": "E002",
                "type": "USES",
            }
        ],
    }
    return json.dumps(payload)


# ===========================================================================
# 8. watsonx success path
# ===========================================================================

class TestWatsonxSuccess:

    def test_llm_entities_returned(self, mocker):
        mocker.patch(
            "app.services.ai_service._get_adapter"
        ).return_value.complete.return_value = _make_valid_llm_json()

        import app.services.ai_service as svc
        mocker.patch.object(svc, "USE_LLM", True)

        result = svc.analyze_text("Vikram uses 9001234567.")

        entity_names = [e.name for e in result.entities]
        assert "Vikram" in entity_names
        assert "9001234567" in entity_names

    def test_llm_relationship_returned(self, mocker):
        mocker.patch(
            "app.services.ai_service._get_adapter"
        ).return_value.complete.return_value = _make_valid_llm_json()

        import app.services.ai_service as svc
        mocker.patch.object(svc, "USE_LLM", True)

        result = svc.analyze_text("Vikram uses 9001234567.")

        rel_types = [r.type for r in result.relationships]
        assert "USES" in rel_types

    def test_llm_result_is_case_analysis(self, mocker):
        mocker.patch(
            "app.services.ai_service._get_adapter"
        ).return_value.complete.return_value = _make_valid_llm_json()

        import app.services.ai_service as svc
        mocker.patch.object(svc, "USE_LLM", True)

        from app.models.case import CaseAnalysis
        result = svc.analyze_text("Vikram uses 9001234567.")
        assert isinstance(result, CaseAnalysis)


# ===========================================================================
# 9. watsonx API failure → fallback
# ===========================================================================

class TestWatsonxAPIFailure:

    def test_unavailable_error_falls_back(self, mocker):
        mock_adapter = mocker.MagicMock()
        mock_adapter.complete.side_effect = WatsonxUnavailableError(
            "Connection refused"
        )
        mocker.patch(
            "app.services.ai_service._get_adapter",
            return_value=mock_adapter,
        )

        import app.services.ai_service as svc
        mocker.patch.object(svc, "USE_LLM", True)

        result = svc.analyze_text(STANDARD_TEXT)
        # Fallback still returns a CaseAnalysis
        from app.models.case import CaseAnalysis
        assert isinstance(result, CaseAnalysis)
        assert result.case_id.startswith("CASE-")

    def test_generic_exception_falls_back(self, mocker):
        mock_adapter = mocker.MagicMock()
        mock_adapter.complete.side_effect = RuntimeError("timeout")
        mocker.patch(
            "app.services.ai_service._get_adapter",
            return_value=mock_adapter,
        )

        import app.services.ai_service as svc
        mocker.patch.object(svc, "USE_LLM", True)

        result = svc.analyze_text(STANDARD_TEXT)
        assert result.case_id.startswith("CASE-")


# ===========================================================================
# 10. watsonx malformed JSON → fallback
# ===========================================================================

class TestWatsonxMalformedJSON:

    def test_garbage_response_falls_back(self, mocker):
        mocker.patch(
            "app.services.ai_service._get_adapter"
        ).return_value.complete.return_value = (
            "Sorry, I cannot help with that."
        )

        import app.services.ai_service as svc
        mocker.patch.object(svc, "USE_LLM", True)

        result = svc.analyze_text(STANDARD_TEXT)
        from app.models.case import CaseAnalysis
        assert isinstance(result, CaseAnalysis)

    def test_partial_json_falls_back(self, mocker):
        mocker.patch(
            "app.services.ai_service._get_adapter"
        ).return_value.complete.return_value = '{"entities": ['

        import app.services.ai_service as svc
        mocker.patch.object(svc, "USE_LLM", True)

        result = svc.analyze_text(STANDARD_TEXT)
        assert result.case_id.startswith("CASE-")

    def test_markdown_fence_stripped(self):
        """_parse_llm_response must strip ```json … ``` fences."""
        raw = "```json\n" + _make_valid_llm_json() + "\n```"
        result = _parse_llm_response(raw, STANDARD_TEXT)
        entity_names = [e.name for e in result.entities]
        assert "Vikram" in entity_names


# ===========================================================================
# 11. Extra / unknown entity types sanitised
# ===========================================================================

class TestUnknownEntityTypes:

    def test_unknown_type_dropped(self):
        payload = json.dumps(
            {
                "entities": [
                    {
                        "id": "E001",
                        "name": "Vikram",
                        "type": "HACKER",  # unknown type
                        "metadata": {},
                    }
                ],
                "relationships": [],
            }
        )
        result = _parse_llm_response(payload, STANDARD_TEXT)
        assert all(e.type != "HACKER" for e in result.entities)

    def test_known_type_kept(self):
        payload = _make_valid_llm_json()
        result = _parse_llm_response(payload, STANDARD_TEXT)
        assert any(e.type == "PERSON" for e in result.entities)


# ===========================================================================
# 12. Duplicate IDs in LLM response → deduplicated
# ===========================================================================

class TestLLMDuplicateIDs:

    def test_same_name_type_deduplicated(self):
        payload = json.dumps(
            {
                "entities": [
                    {
                        "id": "E001",
                        "name": "Vikram",
                        "type": "PERSON",
                        "metadata": {},
                    },
                    {
                        "id": "E002",
                        "name": "vikram",  # same name, different case
                        "type": "PERSON",
                        "metadata": {},
                    },
                ],
                "relationships": [],
            }
        )
        result = _parse_llm_response(payload, STANDARD_TEXT)
        persons = [e for e in result.entities if e.type == "PERSON"]
        assert len(persons) == 1, (
            f"Expected 1 PERSON entity, got {len(persons)}: {persons}"
        )

    def test_duplicate_relationship_deduplicated(self):
        payload = json.dumps(
            {
                "entities": [
                    {
                        "id": "E001",
                        "name": "Vikram",
                        "type": "PERSON",
                        "metadata": {},
                    },
                    {
                        "id": "E002",
                        "name": "9001234567",
                        "type": "PHONE",
                        "metadata": {},
                    },
                ],
                "relationships": [
                    {"source": "E001", "target": "E002", "type": "USES"},
                    {"source": "E001", "target": "E002", "type": "USES"},
                ],
            }
        )
        result = _parse_llm_response(payload, STANDARD_TEXT)
        uses_rels = [r for r in result.relationships if r.type == "USES"]
        assert len(uses_rels) == 1, (
            f"Expected 1 USES relationship, got {len(uses_rels)}"
        )


# ===========================================================================
# 13. Relationships with non-existent IDs → dropped
# ===========================================================================

class TestDanglingRelationshipIDs:

    def test_dangling_source_dropped(self):
        payload = json.dumps(
            {
                "entities": [
                    {
                        "id": "E001",
                        "name": "Vikram",
                        "type": "PERSON",
                        "metadata": {},
                    },
                ],
                "relationships": [
                    # E999 does not exist
                    {
                        "source": "E999",
                        "target": "E001",
                        "type": "USES",
                    },
                ],
            }
        )
        result = _parse_llm_response(payload, STANDARD_TEXT)
        assert result.relationships == [], (
            "Relationship with dangling source should be dropped"
        )

    def test_dangling_target_dropped(self):
        payload = json.dumps(
            {
                "entities": [
                    {
                        "id": "E001",
                        "name": "Vikram",
                        "type": "PERSON",
                        "metadata": {},
                    },
                ],
                "relationships": [
                    # E999 does not exist
                    {
                        "source": "E001",
                        "target": "E999",
                        "type": "BELONGS_TO",
                    },
                ],
            }
        )
        result = _parse_llm_response(payload, STANDARD_TEXT)
        assert result.relationships == []

    def test_valid_relationship_kept(self):
        payload = _make_valid_llm_json()
        result = _parse_llm_response(payload, STANDARD_TEXT)
        assert len(result.relationships) == 1
