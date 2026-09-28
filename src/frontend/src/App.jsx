import { useState } from "react";

import Investigation from "./pages/Investigation";
import NewInvestigation from "./pages/NewInvestigation";
import mockCase from "./data/mockCase";

import "./App.css";

/*
 * ============================================================
 * HELPER FUNCTIONS
 * ============================================================
 */

const createEntityId = (prefix, index) =>
  `${prefix}${String(index + 1).padStart(3, "0")}`;

/*
 * Safely convert any value to lowercase text.
 */
const lower = (value) => String(value || "").toLowerCase();

/*
 * Add an entity only if it does not already exist.
 */
function addEntity(entities, entityMap, entity) {
  if (!entityMap.has(entity.id)) {
    entityMap.set(entity.id, entity);
    entities.push(entity);
  }

  return entityMap.get(entity.id);
}

/*
 * Add a relationship while preventing duplicates.
 */
function addRelationship(
  relationships,
  source,
  target,
  type
) {
  if (!source || !target || source === target) {
    return;
  }

  const alreadyExists = relationships.some(
    (relationship) =>
      relationship.source === source &&
      relationship.target === target &&
      relationship.type === type
  );

  if (!alreadyExists) {
    relationships.push({
      source,
      target,
      type,
    });
  }
}

/*
 * ============================================================
 * TEMPORARY FRONTEND ANALYZER
 * ============================================================
 *
 * IMPORTANT:
 *
 * This is NOT the final AI engine.
 *
 * It allows the frontend to work with the uploaded JSON
 * while the backend + AI team member is building:
 *
 * React
 *   ↓
 * FastAPI
 *   ↓
 * IBM watsonx / Granite
 *   ↓
 * Fraud analysis
 *   ↓
 * Structured case
 *
 * Later this entire function can be replaced by the API call.
 * ============================================================
 */

function analyzeUploadedInvestigation(
  rawData,
  caseTitle,
  context
) {
  let data;

  /*
   * Parse uploaded JSON.
   */
  try {
    data = JSON.parse(rawData);
  } catch (error) {
    throw new Error(
      "The uploaded file is not valid JSON. Please upload a valid JSON investigation file."
    );
  }

  /*
   * ==========================================================
   * STORAGE
   * ==========================================================
   */

  const entities = [];
  const relationships = [];

  const entityMap = new Map();

  const personByName = new Map();
  const phoneByNumber = new Map();
  const simById = new Map();
  const deviceByImei = new Map();
  const accountByNumber = new Map();
  const transactionById = new Map();

  /*
   * ==========================================================
   * PERSONS
   * ==========================================================
   */

  const persons = Array.isArray(data.persons)
    ? data.persons
    : [];

  persons.forEach((person, index) => {
    if (!person?.name) return;

    const id = createEntityId("P", index);

    const entity = {
      id,
      type: "PERSON",
      name: person.name,
      role: String(
        person.role || "PERSON"
      ).toUpperCase(),
      description:
        `Person identified in the uploaded investigation. ` +
        `Role: ${person.role || "not specified"}.`,
    };

    addEntity(
      entities,
      entityMap,
      entity
    );

    personByName.set(
      lower(person.name),
      id
    );
  });

  /*
   * ==========================================================
   * VICTIMS
   * ==========================================================
   *
   * If a victim appears in "victims" but not in "persons",
   * create the person automatically.
   */

  const victims = Array.isArray(data.victims)
    ? data.victims
    : [];

  victims.forEach((victim) => {
    if (!victim?.name) return;

    const key = lower(victim.name);

    if (!personByName.has(key)) {
      const id = createEntityId(
        "P",
        personByName.size
      );

      addEntity(
        entities,
        entityMap,
        {
          id,
          type: "PERSON",
          name: victim.name,
          role: "VICTIM",
          description:
            victim.complaint ||
            "Victim identified in the investigation.",
        }
      );

      personByName.set(key, id);
    }
  });

  /*
   * ==========================================================
   * PHONE NUMBERS
   * ==========================================================
   */

  const phones = Array.isArray(data.phone_numbers)
    ? data.phone_numbers
    : [];

  phones.forEach((phone, index) => {
    if (!phone?.number) return;

    const id = createEntityId("PH", index);

    addEntity(
      entities,
      entityMap,
      {
        id,
        type: "PHONE",
        name: phone.number,
        role: "PHONE NUMBER",
        description:
          `Owner: ${phone.owner || "Unknown"}. ` +
          `Status: ${phone.status || "Not specified"}.`,
      }
    );

    phoneByNumber.set(
      String(phone.number),
      id
    );

    /*
     * Connect phone to owner.
     */
    if (phone.owner) {
      const personId = personByName.get(
        lower(phone.owner)
      );

      if (personId) {
        addRelationship(
          relationships,
          personId,
          id,
          "USES"
        );
      }
    }
  });

  /*
   * ==========================================================
   * SIM CARDS
   * ==========================================================
   */

  const sims = Array.isArray(data.sim_cards)
    ? data.sim_cards
    : [];

  sims.forEach((sim, index) => {
    if (!sim?.sim_id) return;

    const id = createEntityId("SIM", index);

    addEntity(
      entities,
      entityMap,
      {
        id,
        type: "SIM",
        name: sim.sim_id,
        role: "SIM CARD",
        description:
          `Phone number: ${
            sim.phone_number || "Unknown"
          }. Status: ${
            sim.status || "Not specified"
          }.`,
      }
    );

    simById.set(
      String(sim.sim_id),
      id
    );

    /*
     * SIM → PHONE
     */
    if (sim.phone_number) {
      const phoneId = phoneByNumber.get(
        String(sim.phone_number)
      );

      if (phoneId) {
        addRelationship(
          relationships,
          phoneId,
          id,
          "ASSOCIATED_WITH"
        );
      }
    }
  });

  /*
   * ==========================================================
   * DEVICES
   * ==========================================================
   */

  const devices = Array.isArray(data.devices)
    ? data.devices
    : [];

  devices.forEach((device, index) => {
    if (!device?.imei) return;

    const id = createEntityId("D", index);

    addEntity(
      entities,
      entityMap,
      {
        id,
        type: "DEVICE",
        name: `IMEI-${device.imei}`,
        role: "DEVICE",
        description:
          `IMEI: ${device.imei}. ` +
          `Location: ${
            device.location || "Unknown"
          }. ` +
          `Associated SIM: ${
            device.sim_id || "Unknown"
          }.`,
      }
    );

    deviceByImei.set(
      String(device.imei),
      id
    );

    /*
     * SIM → DEVICE
     */
    if (device.sim_id) {
      const simId = simById.get(
        String(device.sim_id)
      );

      if (simId) {
        addRelationship(
          relationships,
          simId,
          id,
          "USED_IN"
        );
      }
    }
  });

  /*
   * ==========================================================
   * BANK ACCOUNTS
   * ==========================================================
   */

  const accounts = Array.isArray(
    data.bank_accounts
  )
    ? data.bank_accounts
    : [];

  accounts.forEach((account, index) => {
    if (!account?.account_number) return;

    const id = createEntityId("A", index);

    let role = "BANK ACCOUNT";

    if (
      lower(account.flag).includes("mule")
    ) {
      role = "SUSPECTED MULE ACCOUNT";
    }

    addEntity(
      entities,
      entityMap,
      {
        id,
        type: "BANK_ACCOUNT",
        name: account.account_number,
        role,
        description:
          `Owner: ${
            account.owner || "Unknown"
          }. Bank: ${
            account.bank || "Unknown"
          }. Type: ${
            account.type || "Unknown"
          }.${
            account.flag
              ? ` Flag: ${account.flag}.`
              : ""
          }`,
      }
    );

    accountByNumber.set(
      String(account.account_number),
      id
    );

    /*
     * PERSON → ACCOUNT
     */
    if (account.owner) {
      const personId = personByName.get(
        lower(account.owner)
      );

      if (personId) {
        addRelationship(
          relationships,
          personId,
          id,
          "OWNS"
        );
      }
    }
  });

  /*
   * ==========================================================
   * VICTIM LINKS
   * ==========================================================
   */

  victims.forEach((victim) => {
    if (!victim?.name) return;

    const personId = personByName.get(
      lower(victim.name)
    );

    if (!personId) return;

    /*
     * Person → Phone
     */
    if (victim.phone) {
      const phoneId = phoneByNumber.get(
        String(victim.phone)
      );

      if (phoneId) {
        addRelationship(
          relationships,
          personId,
          phoneId,
          "USES"
        );
      }
    }

    /*
     * Person → Bank Account
     */
    if (victim.bank_account) {
      const accountId =
        accountByNumber.get(
          String(victim.bank_account)
        );

      if (accountId) {
        addRelationship(
          relationships,
          personId,
          accountId,
          "OWNS"
        );
      }
    }
  });

  /*
   * ==========================================================
   * TRANSACTIONS
   * ==========================================================
   */

  const transactions = Array.isArray(
    data.transactions
  )
    ? data.transactions
    : [];

  /*
   * Some transactions may point to an account that
   * does not have a full record in bank_accounts.
   *
   * Example:
   * ACC-99871
   *
   * Create an unidentified account node so that the
   * graph never contains a relationship pointing to
   * a missing node.
   */

  const ensureAccountExists = (
    accountNumber
  ) => {
    if (!accountNumber) return null;

    const existingId =
      accountByNumber.get(
        String(accountNumber)
      );

    if (existingId) {
      return existingId;
    }

    const nextIndex =
      accountByNumber.size;

    const id = createEntityId(
      "A",
      nextIndex
    );

    addEntity(
      entities,
      entityMap,
      {
        id,
        type: "BANK_ACCOUNT",
        name: accountNumber,
        role: "UNIDENTIFIED ACCOUNT",
        description:
          "Account referenced by a transaction but no detailed account record was provided in the uploaded investigation data.",
      }
    );

    accountByNumber.set(
      String(accountNumber),
      id
    );

    return id;
  };

  transactions.forEach(
    (transaction, index) => {
      if (!transaction?.transaction_id) {
        return;
      }

      const id = createEntityId(
        "T",
        index
      );

      const amount = Number(
        transaction.amount || 0
      );

      const currency =
        transaction.currency || "INR";

      const formattedAmount =
        amount.toLocaleString(
          "en-IN"
        );

      addEntity(
        entities,
        entityMap,
        {
          id,
          type: "TRANSACTION",
          name:
            currency === "INR"
              ? `₹${formattedAmount}`
              : `${currency} ${formattedAmount}`,
          role: `${
            transaction.method || "UNKNOWN"
          } TRANSACTION`,
          description:
            `Transaction ID: ${
              transaction.transaction_id
            }. Date: ${
              transaction.date || "Unknown"
            } ${
              transaction.time || ""
            }. From: ${
              transaction.source_account ||
              "Unknown"
            }. To: ${
              transaction.destination_account ||
              "Unknown"
            }. Amount: ${
              currency
            } ${formattedAmount}.`,
        }
      );

      transactionById.set(
        String(transaction.transaction_id),
        id
      );

      /*
       * Make sure source/destination accounts exist.
       */
      const sourceAccountId =
        ensureAccountExists(
          transaction.source_account
        );

      const destinationAccountId =
        ensureAccountExists(
          transaction.destination_account
        );

      /*
       * SOURCE ACCOUNT → TRANSACTION
       */
      if (sourceAccountId) {
        addRelationship(
          relationships,
          sourceAccountId,
          id,
          "SOURCE"
        );
      }

      /*
       * TRANSACTION → DESTINATION ACCOUNT
       */
      if (destinationAccountId) {
        addRelationship(
          relationships,
          id,
          destinationAccountId,
          "TRANSFERRED_TO"
        );
      }
    }
  );

  /*
   * ==========================================================
   * COMMUNICATIONS
   * ==========================================================
   */

  const communications =
    Array.isArray(data.communications)
      ? data.communications
      : [];

  communications.forEach(
    (communication) => {
      const fromId =
        personByName.get(
          lower(communication.from)
        );

      const toId =
        personByName.get(
          lower(communication.to)
        );

      if (fromId && toId) {
        addRelationship(
          relationships,
          fromId,
          toId,
          "COMMUNICATES_WITH"
        );
      }
    }
  );

  /*
   * ==========================================================
   * FRAUD PATTERN ANALYSIS
   * ==========================================================
   *
   * This is a temporary rule engine.
   *
   * Later:
   *
   * AI output
   *    ↓
   * Rule Engine
   *    ↓
   * patterns
   */

  const patterns = [];

  /*
   * ----------------------------------------------------------
   * SIM SWAP INDICATOR
   * ----------------------------------------------------------
   */

  const replacementSims =
    sims.filter((sim) =>
      lower(sim.status).includes(
        "replacement"
      )
    );

  const inactivePhones =
    phones.filter((phone) =>
      lower(phone.status).includes(
        "inactive"
      )
    );

  if (
    replacementSims.length > 0 ||
    inactivePhones.length > 0
  ) {
    const phoneNumbers =
      replacementSims
        .map((sim) => sim.phone_number)
        .filter(Boolean);

    patterns.push({
      type: "SIM-SWAP INDICATOR",
      severity: "HIGH",
      description:
        `The uploaded evidence contains ${
          replacementSims.length
        } replacement SIM record(s) and ${
          inactivePhones.length
        } phone record(s) showing inactivity before suspicious activity.${
          phoneNumbers.length
            ? ` Affected phone number(s): ${phoneNumbers.join(
                ", "
              )}.`
            : ""
        }`,
    });
  }

  /*
   * ----------------------------------------------------------
   * MULE ACCOUNT NETWORK
   * ----------------------------------------------------------
   */

  const incomingTransactions =
    new Map();

  transactions.forEach(
    (transaction) => {
      const destination =
        transaction.destination_account;

      if (!destination) return;

      if (
        !incomingTransactions.has(
          destination
        )
      ) {
        incomingTransactions.set(
          destination,
          []
        );
      }

      incomingTransactions
        .get(destination)
        .push(transaction);
    }
  );

  const muleAccounts = [];

  accounts.forEach((account) => {
    const accountNumber =
      account.account_number;

    const incoming =
      incomingTransactions.get(
        accountNumber
      ) || [];

    const explicitlyFlagged =
      lower(account.flag).includes(
        "mule"
      );

    if (
      explicitlyFlagged ||
      incoming.length >= 2
    ) {
      muleAccounts.push(
        accountNumber
      );
    }
  });

  if (muleAccounts.length > 0) {
    muleAccounts.forEach(
      (accountNumber) => {
        const incoming =
          incomingTransactions.get(
            accountNumber
          ) || [];

        const totalReceived =
          incoming.reduce(
            (sum, transaction) =>
              sum +
              Number(
                transaction.amount || 0
              ),
            0
          );

        patterns.push({
          type: "MULE ACCOUNT NETWORK",
          severity: "HIGH",
          description:
            `Account ${accountNumber} is connected to ${
              incoming.length
            } incoming transaction(s), ${
              incoming.length >= 2
                ? "including transfers from multiple source accounts"
                : "and is explicitly flagged as a suspected mule account"
            }. Total incoming value identified: INR ${totalReceived.toLocaleString(
              "en-IN"
            )}.`,
        });
      }
    );
  }

  /*
   * ----------------------------------------------------------
   * RAPID FUND MOVEMENT
   * ----------------------------------------------------------
   */

  const muleSet = new Set(
    muleAccounts
  );

  const outgoingFromMule =
    transactions.filter(
      (transaction) =>
        muleSet.has(
          transaction.source_account
        )
    );

  if (
    outgoingFromMule.length > 0
  ) {
    patterns.push({
      type: "RAPID FUND MOVEMENT",
      severity: "HIGH",
      description:
        `A suspected intermediary account was also used as the source of ${
          outgoingFromMule.length
        } subsequent transaction(s), indicating movement of funds after receipt.`,
    });
  }

  /*
   * ----------------------------------------------------------
   * SUSPECTED COORDINATION
   * ----------------------------------------------------------
   */

  if (communications.length > 0) {
    const communicationPairs =
      new Set(
        communications.map(
          (communication) =>
            `${communication.from} → ${communication.to}`
        )
      );

    patterns.push({
      type: "SUSPECTED COORDINATION",
      severity: "MEDIUM",
      description:
        `${
          communications.length
        } communication record(s) were identified involving ${
          communicationPairs.size
        } communication pair(s). These records should be correlated with transaction and SIM activity.`,
    });
  }

  /*
   * ==========================================================
   * RISK STATUS
   * ==========================================================
   */

  let status = "LOW RISK";

  if (
    patterns.some(
      (pattern) =>
        pattern.severity === "HIGH"
    )
  ) {
    status = "HIGH RISK";
  } else if (
    patterns.length > 0
  ) {
    status = "MEDIUM RISK";
  }

  /*
   * ==========================================================
   * SUMMARY
   * ==========================================================
   */

  const totalTransactionValue =
    transactions.reduce(
      (sum, transaction) =>
        sum +
        Number(
          transaction.amount || 0
        ),
      0
    );

  const generatedSummary =
    `The uploaded investigation ${
      data.incident_type
        ? `relates to ${data.incident_type.toLowerCase()}`
        : "contains suspected fraud activity"
    } in ${
      data.location || "the reported location"
    }. The dataset contains ${
      persons.length
    } persons, ${
      phones.length
    } phone number(s), ${
      sims.length
    } SIM card(s), ${
      devices.length
    } device(s), ${
      accountByNumber.size
    } bank account(s), and ${
      transactions.length
    } transaction(s) with a total identified value of INR ${totalTransactionValue.toLocaleString(
      "en-IN"
    )}. ${
      patterns.length
    } investigation pattern(s) were identified from the uploaded evidence.`;

  const summary =
    context?.trim() ||
    data.investigator_notes ||
    generatedSummary;

  /*
   * ==========================================================
   * RECOMMENDATIONS
   * ==========================================================
   */

  const recommendations = [];

  if (
    replacementSims.length > 0 ||
    inactivePhones.length > 0
  ) {
    recommendations.push(
      "Preserve telecom records related to SIM replacement and mobile-number activity."
    );

    recommendations.push(
      "Request relevant subscriber and SIM registration records from the telecom provider."
    );
  }

  if (
    muleAccounts.length > 0
  ) {
    recommendations.push(
      "Preserve transaction records and request KYC information for identified intermediary accounts."
    );
  }

  if (
    communications.length > 0
  ) {
    recommendations.push(
      "Preserve relevant call, SMS and communication metadata for identified persons."
    );
  }

  if (
    devices.length > 0
  ) {
    recommendations.push(
      "Examine linked device IMEI records and their association with SIM identities."
    );
  }

  recommendations.push(
    "Correlate transaction timestamps with SIM, device and communication activity."
  );

  recommendations.push(
    "Investigate relationships between victims, suspected intermediaries and other connected entities."
  );

  /*
   * ==========================================================
   * FINAL STRUCTURED CASE
   * ==========================================================
   */

  return {
    case_id:
      data.case_reference ||
      `CFN-${Date.now()
        .toString()
        .slice(-6)}`,

    case_title:
      caseTitle ||
      data.incident_type ||
      "Cyber Fraud Investigation",

    status,

    summary,

    entities,

    relationships,

    patterns,

    recommendations,
  };
}

/*
 * ============================================================
 * APP
 * ============================================================
 */

function App() {
  /*
   * dashboard
   * new-investigation
   * investigation
   */
  const [page, setPage] =
    useState("dashboard");

  /*
   * The case currently displayed by the
   * Investigation page.
   */
  const [currentCase, setCurrentCase] =
    useState(mockCase);

  const [isAnalyzing, setIsAnalyzing] =
    useState(false);

  /*
   * ==========================================================
   * CREATE / ANALYZE INVESTIGATION
   * ==========================================================
   */

  const handleAnalyze = async (
    investigationData
  ) => {
    setIsAnalyzing(true);

    try {
      /*
       * If the uploaded content is a JSON file, parse it
       * structurally using the frontend analyzer — it understands
       * the full structured schema (persons, bank_accounts,
       * transactions, devices, sim_cards, communications, …).
       *
       * For free-text / paste input, or CSV files, send the raw
       * text to the FastAPI backend NLP pipeline.
       */
      const isJsonUpload =
        investigationData.input_type === "file" &&
        investigationData.file_name?.toLowerCase().endsWith(".json");

      if (isJsonUpload) {
        /*
         * Route JSON file through the structured frontend analyzer.
         */
        const generatedCase = analyzeUploadedInvestigation(
          investigationData.raw_data,
          investigationData.case_title,
          investigationData.context
        );

        setCurrentCase(generatedCase);
        setPage("investigation");
        return;
      }

      /*
       * POST the raw text to the FastAPI backend.
       * The Vite dev proxy forwards /api → localhost:8000.
       */
      let response;
      try {
        response = await fetch(
          "/api/cases/analyze",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              text: investigationData.raw_data,
            }),
          }
        );
      } catch {
        throw new Error(
          "Cannot reach the backend. Make sure the FastAPI server is running on port 8000."
        );
      }

      if (!response.ok) {
        const errorData = await response
          .json()
          .catch(() => ({}));

        // FastAPI validation errors return detail as an array of objects
        const detail = errorData?.detail;
        const message =
          typeof detail === "string"
            ? detail
            : Array.isArray(detail)
            ? detail.map((d) => d.msg || String(d)).join("; ")
            : `Server error: ${response.status}`;

        throw new Error(message);
      }

      const apiCase = await response.json();

      /*
       * Merge the backend response with the UI-only fields
       * (case_title, status, summary, recommendations) so
       * Investigation.jsx renders correctly.
       */
      const generatedCase = {
        ...apiCase,
        case_title:
          investigationData.case_title ||
          "Cyber Fraud Investigation",
        status: (() => {
          const patterns = apiCase.patterns || [];
          if (
            patterns.some(
              (p) => p.severity === "HIGH"
            )
          )
            return "HIGH RISK";
          if (patterns.length > 0)
            return "MEDIUM RISK";
          return "LOW RISK";
        })(),
        summary:
          investigationData.context?.trim() ||
          apiCase.report?.summary ||
          `Case ${apiCase.case_id} — ${
            (apiCase.entities || []).length
          } entities, ${
            (apiCase.relationships || []).length
          } relationships extracted.`,
        recommendations:
          apiCase.report?.recommended_actions || [],
      };

      setCurrentCase(generatedCase);
      setPage("investigation");
    } finally {
      setIsAnalyzing(false);
    }
  };

  /*
   * ==========================================================
   * NEW INVESTIGATION
   * ==========================================================
   */

  if (
    page === "new-investigation"
  ) {
    return (
      <NewInvestigation
        onBack={() =>
          setPage("dashboard")
        }
        onAnalyze={handleAnalyze}
      />
    );
  }

  /*
   * ==========================================================
   * INVESTIGATION DASHBOARD
   * ==========================================================
   */

  if (
    page === "investigation"
  ) {
    return (
      <Investigation
        caseData={currentCase}
        onBack={() =>
          setPage("dashboard")
        }
      />
    );
  }

  /*
   * ==========================================================
   * MAIN DASHBOARD
   * ==========================================================
   */

  return (
    <div className="dashboard">

      {/* HEADER */}

      <header className="dashboard-header">

        <div>

          <span className="eyebrow">
            INVESTIGATION INTELLIGENCE PLATFORM
          </span>

          <h1>
            Cyber Fraud Network Analyzer
          </h1>

          <p>
            Transform fragmented cyber-fraud
            intelligence into an explainable
            investigation network.
          </p>

        </div>

        <button
          className="primary-button"
          onClick={() =>
            setPage(
              "new-investigation"
            )
          }
        >
          + New Investigation
        </button>

      </header>

      {/* STATS */}

      <section className="dashboard-stats">

        <div>
          <span>
            ACTIVE CASES
          </span>

          <strong>
            12
          </strong>
        </div>

        <div>
          <span>
            PERSONS
          </span>

          <strong>
            34
          </strong>
        </div>

        <div>
          <span>
            DEVICES
          </span>

          <strong>
            18
          </strong>
        </div>

        <div>
          <span>
            LINKED ACCOUNTS
          </span>

          <strong>
            27
          </strong>
        </div>

      </section>

      {/* RECENT CASES */}

      <section className="cases-section">

        <div className="section-heading">

          <div>

            <span>
              INVESTIGATION WORKSPACE
            </span>

            <h2>
              Recent Cases
            </h2>

          </div>

        </div>

        <div className="case-card">

          <div>

            <span className="case-id">
              {mockCase.case_id}
            </span>

            <h3>
              {mockCase.case_title}
            </h3>

            <p>
              {mockCase.summary}
            </p>

          </div>

          <div className="case-card-right">

            <span className="risk-badge">
              {mockCase.status}
            </span>

            <button
              className="secondary-button"
              onClick={() => {
                setCurrentCase(
                  mockCase
                );

                setPage(
                  "investigation"
                );
              }}
            >
              Open Investigation →
            </button>

          </div>

        </div>

      </section>

    </div>
  );
}

export default App;