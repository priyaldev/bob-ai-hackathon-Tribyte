from app.services.ai_service import analyze_text


text = """
Accused Rahul uses phone number 9876543210.
He uses device DEV12345.
Rahul transferred Rs 25000 to bank account ACC10001
on 2026-09-20.
Victim Priya transferred Rs 25000 to ACC10001.
The transaction TXN1001 was associated with the device.
"""


result = analyze_text(text)

print("\nCASE ID:")
print(result.case_id)

print("\nENTITIES:")

for entity in result.entities:
    print(
        entity.id,
        "|",
        entity.type,
        "|",
        entity.name,
    )

print("\nRELATIONSHIPS:")

for relationship in result.relationships:
    print(
        relationship.source,
        "->",
        relationship.type,
        "->",
        relationship.target,
        "| amount:",
        relationship.amount,
        "| timestamp:",
        relationship.timestamp,
    )