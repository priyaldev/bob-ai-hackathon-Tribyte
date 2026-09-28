# Problem Statement

**Cyber Fraud Network Analyzer**

Real Case: Jamtara SIM-swap ring (Jharkhand) — 95,000+ UPI fraud cases in FY2023. Investigators manually traced
connections between bank accounts, SIM cards, and devices over weeks. Most cases went unsolved due to lack of network
visualization tools.
Build a Bob-powered investigation tool that takes unstructured cyber fraud intelligence (transaction records, call logs,
device IDs, accused names — mock inputs), extracts entities and relationships, identifies the fraud pattern type, maps
the organizational hierarchy (kingpin → mule → victims), and generates an FIR-ready case brief with recommended
actions.

## Background

Cyber fraud investigations are becoming increasingly data-intensive and relationship-driven. A single fraud incident can leave behind traces across transaction records, phone numbers, bank accounts, UPI identifiers, device IDs, call logs, and people involved in the case.

The challenge is not simply finding individual pieces of evidence, it is understanding how those pieces are connected.

In a typical investigation, an analyst may have to manually examine scattered records and progressively connect a victim to an account, an account to a phone number, a phone number to a device, and one account to another through subsequent transactions. The resulting network may span dozens or hundreds of entities, making it difficult to see the larger structure of the fraud operation.

## The Problem

The core problem is fragmented cyber-fraud intelligence.

Investigators often receive valuable information as unstructured or semi-structured data—complaints, transaction records, call logs, device information, account details, and investigation notes. However, these inputs do not naturally reveal the network connecting the entities.

For example, a single investigation may contain:

Victim → Bank Account → Phone Number → Device → Another Account → Another Person

When these relationships are buried inside large amounts of raw information, identifying patterns such as multiple victims sending money to the same account, shared devices, repeated identifiers, and multi-hop fund movement becomes difficult and time-consuming.

The challenge is therefore to transform fragmented investigation data into a connected, explainable fraud network that investigators can understand and act upon.

## Who is Affected

The primary users are cybercrime investigators, digital-forensics teams, fraud analysts, and law-enforcement personnel who need to reconstruct fraud networks from multiple sources of evidence.

They are particularly affected when an investigation contains:

- Multiple victims and transactions
- Numerous bank accounts or UPI identifiers
- Shared phone numbers or devices
- Multiple intermediary accounts
- Large volumes of unstructured investigation notes
- Relationships that are not explicitly documented in one place

For these users, the challenge is not a lack of data—it is the difficulty of connecting the data into an understandable investigation picture.

## Why It Matters

In cyber fraud investigations, time and connectivity matter.

A suspicious transaction by itself may provide only a small piece of the investigation. Its real significance may emerge only when it is connected to another account, device, phone number, person, or victim.

Manual investigation can make this process difficult because analysts must repeatedly search, compare, correlate, and reconstruct relationships across different records.

A missed relationship can mean a missed lead.

A hidden multi-hop transaction can obscure the movement of funds.

A shared device or phone number connecting multiple entities can remain unnoticed when information is viewed only as isolated records.

The result is a gap between having evidence and being able to see the network represented by that evidence.

Our goal is to reduce that gap by turning raw fraud intelligence into an interactive and explainable investigation view—helping investigators move from “What happened?” toward “How are these entities connected?”

## Why Existing Solutions Fall Short

Traditional investigation workflows and record-based tools are effective at storing and searching individual pieces of information, but they do not necessarily provide a unified view of the relationships between those pieces.

Investigators may need to manually:

- Read unstructured complaints and investigation notes.
- Extract people, accounts, phone numbers, devices, and transactions.
- Identify relationships between those entities.
- Trace transaction paths across multiple accounts.
- Look for repeated or suspicious patterns.
- Reconstruct the network mentally or through separate tools.
- Prepare an investigation summary from the collected evidence.

This creates a fragmented investigation workflow.

What is missing is an investigation layer that can take heterogeneous fraud intelligence, automatically extract entities and relationships, identify potentially suspicious network patterns, visualize the connections, and produce a structured investigation brief from the same underlying evidence.

That is the gap our Cyber Fraud Network Analyzer is designed to address.
