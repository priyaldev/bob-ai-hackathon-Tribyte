"""
test_full_pipeline.py
=====================
End-to-end test for the Cyber Fraud Network Analyzer pipeline.

Tests every fix applied:

    FIX P2  -- DEVICE -> ACCOUNT relationship is emitted as USES (not ASSOCIATED_WITH)
    FIX S1  -- Entity.role and Entity.description are populated for every entity
    FIX S2  -- MULTI_HOP_TRANSACTION description contains account names, not raw IDs
    FIX P1  -- SHARED_DEVICE fraud pattern fires when one device accesses multiple accounts
    FLOW    -- Full pipeline: extract -> fraud -> graph -> report

Run from src/backend/:

    python test_full_pipeline.py
"""

import sys
import os

# ── make "app" importable from src/backend ───────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from app.services.ai_service import _mock_analysis
from app.services.fraud_service import detect_fraud_patterns
from app.services.graph_service import build_graph
from app.services.report_service import generate_report

# ─────────────────────────────────────────────────────────────────────────────
# TEST INPUT
# ─────────────────────────────────────────────────────────────────────────────
#
# This text is deliberately crafted to exercise every fix:
#
#   • Two victims transferring to the SAME mule account  -> MULTIPLE_SOURCE_TRANSACTIONS
#   • One device logging in to TWO different accounts    -> SHARED_DEVICE  (was broken)
#   • A two-hop money chain (victim -> mule -> cashout)    -> MULTI_HOP_TRANSACTION
#   • All entities should have role + description        -> S1
#
CASE_TEXT = """
CASE NOTES 24/09

Caller: unknown male
Number seen in victim call log: 9123456780

Victim Anjali Gupta says she was contacted around 11:35 AM.
Caller claimed to be from customer support.
She was asked to make a small verification payment first.
Later she discovered Rs 75000 had gone from her account.

Txn ref TXN90871
From: Anjali's account
To: 3344556677
Amount: 75000
Time: 11:42

Same beneficiary appears in another complaint filed by Rajesh Patel.
Rajesh Patel transferred Rs 46000 to account 3344556677.
Transaction reference TXN90892.

Account 3344556677 is reportedly operated by Suresh Yadav.
Mobile number 9123456780 is associated with Suresh according to preliminary records.

Device ID DEV-4455 was observed during login activity for 3344556677.

Review of transaction history:
3344556677 -> 5566778899 : 90000
5566778899 -> 7788990011 : 85000

Second account 5566778899 is associated with Pankaj Kumar.

There are indications that DEV-4455 may also have been used to access 5566778899.
"""

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

PASS = "  [PASS]"
FAIL = "  [FAIL]"
SEP  = "=" * 68
_failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"{PASS}  {label}")
    else:
        msg = f"{FAIL}  {label}"
        if detail:
            msg += f"\n         ↳ {detail}"
        print(msg)
        _failures.append(label)


# ─────────────────────────────────────────────────────────────────────────────
# RUN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

print(SEP)
print("RUNNING FULL PIPELINE")
print(SEP)

analysis  = _mock_analysis(CASE_TEXT)
entities  = analysis.entities
rels      = analysis.relationships
patterns  = detect_fraud_patterns(entities, rels)
graph     = build_graph(entities, rels)
report    = generate_report(analysis.case_id, entities, rels, patterns)

# ─────────────────────────────────────────────────────────────────────────────
# 1. ENTITY EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

print()
print(SEP)
print("1. ENTITY EXTRACTION")
print(SEP)

entity_names = {e.name for e in entities}
entity_types = {e.name: e.type for e in entities}

print("   Extracted entities:")
for e in entities:
    print(f"     {e.id}  {e.type:12}  {e.name}")

check(
    "Account 3344556677 extracted as BANK_ACCOUNT (not PHONE)",
    entity_types.get("3344556677") == "BANK_ACCOUNT",
    f"actual type = {entity_types.get('3344556677')}",
)

check(
    "Account 5566778899 extracted as BANK_ACCOUNT",
    entity_types.get("5566778899") == "BANK_ACCOUNT",
    f"actual type = {entity_types.get('5566778899')}",
)

check(
    "Phone 9123456780 extracted as PHONE (not BANK_ACCOUNT)",
    entity_types.get("9123456780") == "PHONE",
    f"actual type = {entity_types.get('9123456780')}",
)

check(
    "Device DEV-4455 extracted",
    any(e.type == "DEVICE" and "4455" in e.name for e in entities),
)

check(
    "Victim Anjali Gupta extracted",
    any(e.type == "VICTIM" and "Anjali" in e.name for e in entities),
)

check(
    "Transaction TXN90871 extracted",
    any(e.type == "TRANSACTION" and "90871" in e.name for e in entities),
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. FIX S1 -- role and description populated
# ─────────────────────────────────────────────────────────────────────────────

print()
print(SEP)
print("2. FIX S1 -- Entity.role and Entity.description populated")
print(SEP)

missing_role = [e for e in entities if not e.role]
missing_desc = [e for e in entities if not e.description]

check(
    "Every entity has a non-empty role",
    len(missing_role) == 0,
    f"Missing role: {[e.name for e in missing_role]}",
)

check(
    "Every entity has a non-empty description",
    len(missing_desc) == 0,
    f"Missing description: {[e.name for e in missing_desc]}",
)

# Spot-check expected role labels
for e in entities:
    if e.type == "VICTIM":
        check(
            f"VICTIM entity '{e.name}' has role 'Victim'",
            e.role == "Victim",
            f"actual role = '{e.role}'",
        )
    if e.type == "DEVICE":
        check(
            f"DEVICE entity '{e.name}' has role 'Device'",
            e.role == "Device",
            f"actual role = '{e.role}'",
        )
    if e.type == "BANK_ACCOUNT":
        check(
            f"BANK_ACCOUNT entity '{e.name}' has role 'Bank Account'",
            e.role == "Bank Account",
            f"actual role = '{e.role}'",
        )

# ─────────────────────────────────────────────────────────────────────────────
# 3. FIX P2 -- DEVICE->ACCOUNT relationship type is USES not ASSOCIATED_WITH
# ─────────────────────────────────────────────────────────────────────────────

print()
print(SEP)
print("3. FIX P2 -- DEVICE->ACCOUNT relationship type")
print(SEP)

device_entity = next((e for e in entities if e.type == "DEVICE"), None)
acct_3344 = next((e for e in entities if e.name == "3344556677"), None)
acct_5566 = next((e for e in entities if e.name == "5566778899"), None)

print("   Relationships:")
for r in rels:
    src = next((e.name for e in entities if e.id == r.source), r.source)
    tgt = next((e.name for e in entities if e.id == r.target), r.target)
    print(f"     {src:20} --[{r.type}]--> {tgt}  amount={r.amount}")

if device_entity and acct_3344:
    dev_to_3344 = [
        r for r in rels
        if r.source == device_entity.id and r.target == acct_3344.id
    ]
    check(
        "DEV-4455 -> 3344556677 relationship exists",
        len(dev_to_3344) > 0,
    )
    check(
        "DEV-4455 -> 3344556677 type is USES (not ASSOCIATED_WITH)",
        any(r.type == "USES" for r in dev_to_3344),
        f"actual type(s) = {[r.type for r in dev_to_3344]}",
    )
else:
    check("DEV-4455 and account 3344556677 both extracted (prerequisite)", False,
          "Cannot test relationship without both entities")

if device_entity and acct_5566:
    dev_to_5566 = [
        r for r in rels
        if r.source == device_entity.id and r.target == acct_5566.id
    ]
    check(
        "DEV-4455 -> 5566778899 relationship exists",
        len(dev_to_5566) > 0,
    )
    check(
        "DEV-4455 -> 5566778899 type is USES (not ASSOCIATED_WITH)",
        any(r.type == "USES" for r in dev_to_5566),
        f"actual type(s) = {[r.type for r in dev_to_5566]}",
    )

# ─────────────────────────────────────────────────────────────────────────────
# 4. FRAUD PATTERN DETECTION
# ─────────────────────────────────────────────────────────────────────────────

print()
print(SEP)
print("4. FRAUD PATTERN DETECTION")
print(SEP)

pattern_types = [p["type"] for p in patterns]
print("   Patterns detected:")
for p in patterns:
    desc_safe = p["description"].encode("ascii", "replace").decode("ascii")
    print(f"     [{p['severity']:6}]  {p['type']}")
    print(f"              {desc_safe}")

# FIX P1 -- SHARED_DEVICE must now fire
check(
    "FIX P1: SHARED_DEVICE pattern fires (was completely broken before fix)",
    "SHARED_DEVICE" in pattern_types,
    "DEV-4455 accesses 2 accounts -- pattern should be detected",
)

# MULTIPLE_SOURCE_TRANSACTIONS -- mule account receives from 2 victims
check(
    "MULTIPLE_SOURCE_TRANSACTIONS fires for account 3344556677",
    "MULTIPLE_SOURCE_TRANSACTIONS" in pattern_types,
)

# FIX S2 -- MULTI_HOP description must contain names, not IDs
multi_hop = [p for p in patterns if p["type"] == "MULTI_HOP_TRANSACTION"]
check(
    "MULTI_HOP_TRANSACTION pattern fires (2-hop money chain)",
    len(multi_hop) > 0,
)
if multi_hop:
    desc = multi_hop[0]["description"]
    has_ids = any(
        token in desc
        for token in ["E001", "E002", "E003", "E004", "E005", "E006"]
    )
    has_name = any(
        name in desc
        for name in ["3344556677", "5566778899", "Anjali", "Rajesh"]
    )
    check(
        "FIX S2: MULTI_HOP description contains entity names, not raw IDs",
        has_name and not has_ids,
        f"description = {desc.encode('ascii','replace').decode('ascii')}",
    )

# ─────────────────────────────────────────────────────────────────────────────
# 5. GRAPH SERVICE
# ─────────────────────────────────────────────────────────────────────────────

print()
print(SEP)
print("5. GRAPH SERVICE")
print(SEP)

check(
    "graph.nodes count matches entities count",
    len(graph["nodes"]) == len(entities),
    f"nodes={len(graph['nodes'])} entities={len(entities)}",
)

check(
    "graph.edges count matches relationships count",
    len(graph["edges"]) == len(rels),
    f"edges={len(graph['edges'])} rels={len(rels)}",
)

node_ids  = {n["id"] for n in graph["nodes"]}
edge_srcs = {e["source"] for e in graph["edges"]}
edge_tgts = {e["target"] for e in graph["edges"]}

check(
    "All edge source IDs exist as node IDs",
    edge_srcs.issubset(node_ids),
    f"dangling sources = {edge_srcs - node_ids}",
)

check(
    "All edge target IDs exist as node IDs",
    edge_tgts.issubset(node_ids),
    f"dangling targets = {edge_tgts - node_ids}",
)

# ─────────────────────────────────────────────────────────────────────────────
# 6. REPORT SERVICE
# ─────────────────────────────────────────────────────────────────────────────

print()
print(SEP)
print("6. REPORT SERVICE")
print(SEP)

check(
    "report.case_id matches analysis.case_id",
    report["case_id"] == analysis.case_id,
)

check(
    "report.total_transaction_amount > 0",
    report["total_transaction_amount"] > 0,
    f"total = {report['total_transaction_amount']}",
)

check(
    "report.pattern_count matches detected patterns",
    report["pattern_count"] == len(patterns),
    f"report says {report['pattern_count']}, actual = {len(patterns)}",
)

check(
    "report.entity_counts contains BANK_ACCOUNT",
    report["entity_counts"].get("BANK_ACCOUNT", 0) > 0,
)

check(
    "report.recommended_actions is non-empty",
    len(report.get("recommended_actions", [])) > 0,
)

# ─────────────────────────────────────────────────────────────────────────────
# FINAL RESULT
# ─────────────────────────────────────────────────────────────────────────────

print()
print(SEP)
if _failures:
    print(f"RESULT: {len(_failures)} check(s) FAILED")
    for f in _failures:
        print(f"  FAIL  {f}")
    sys.exit(1)
else:
    print(f"RESULT: ALL CHECKS PASSED")
print(SEP)
