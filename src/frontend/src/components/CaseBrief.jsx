import { useRef } from "react";
import {
  X,
  Download,
  FileText,
  AlertTriangle,
  Users,
  Link,
  ShieldAlert,
  CheckSquare,
} from "lucide-react";

/* ------------------------------------------------------------------ */
/* Helpers                                                              */
/* ------------------------------------------------------------------ */

function today() {
  return new Date().toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
}

function severityColor(severity = "") {
  switch (severity.toUpperCase()) {
    case "HIGH":   return "#ff7777";
    case "MEDIUM": return "#f5a623";
    default:       return "#6fbf73";
  }
}

function entityTypeLabel(type = "") {
  const map = {
    PERSON:       "Person",
    VICTIM:       "Victim",
    PHONE:        "Phone",
    DEVICE:       "Device",
    BANK_ACCOUNT: "Bank Account",
    UPI_ID:       "UPI ID",
    TRANSACTION:  "Transaction",
  };
  return map[type.toUpperCase()] || type;
}

/* ------------------------------------------------------------------ */
/* Print / download                                                     */
/* ------------------------------------------------------------------ */

function printBrief(ref) {
  const content = ref.current?.innerHTML;
  if (!content) return;

  const win = window.open("", "_blank");
  win.document.write(`<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Case Brief</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, "Segoe UI", system-ui, sans-serif;
      font-size: 13px; line-height: 1.6;
      color: #1f2328; background: #fff; padding: 36px;
    }
    .brief-header { border-bottom: 2px solid #e5e7eb; padding-bottom: 16px; margin-bottom: 24px; }
    .brief-header h1 { font-size: 22px; font-weight: 700; }
    .brief-meta { color: #57606a; font-size: 12px; margin-top: 6px; display: flex; gap: 24px; }
    .brief-section { margin-bottom: 24px; }
    .brief-section h2 { font-size: 13px; font-weight: 700; text-transform: uppercase;
      letter-spacing: .06em; color: #57606a; margin-bottom: 10px;
      padding-bottom: 6px; border-bottom: 1px solid #e5e7eb; }
    table { width: 100%; border-collapse: collapse; font-size: 12px; }
    th { text-align: left; padding: 6px 10px; background: #f7f8fa;
      border: 1px solid #e5e7eb; font-weight: 600; color: #57606a; }
    td { padding: 6px 10px; border: 1px solid #e5e7eb; }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 999px;
      font-size: 11px; font-weight: 700; }
    .badge-high { background: #fff0f0; color: #cc2222; }
    .badge-medium { background: #fff8ec; color: #a06000; }
    .badge-low { background: #f0fff4; color: #1a7a35; }
    .summary-box { background: #f7f8fa; border: 1px solid #e5e7eb;
      border-radius: 8px; padding: 14px; font-size: 13px; }
    .rec-item { padding: 5px 0; display: flex; gap: 8px; }
    .rec-item::before { content: "→"; color: #3b82d4; font-weight: 700; }
    .pattern-block { border: 1px solid #e5e7eb; border-radius: 8px;
      padding: 12px; margin-bottom: 10px; }
    .pattern-block h3 { font-size: 13px; font-weight: 700; margin-bottom: 4px; }
    .pattern-block p { color: #57606a; font-size: 12px; }
    .footer { margin-top: 36px; padding-top: 12px; border-top: 1px solid #e5e7eb;
      color: #57606a; font-size: 11px; text-align: center; }
    @media print { body { padding: 20px; } }
  </style>
</head>
<body>${content}</body>
</html>`);
  win.document.close();
  win.focus();
  setTimeout(() => { win.print(); }, 400);
}

/* ------------------------------------------------------------------ */
/* Modal                                                                */
/* ------------------------------------------------------------------ */

function CaseBrief({ caseData, onClose }) {
  const printRef = useRef(null);

  const {
    case_id,
    case_title,
    status,
    summary,
    entities = [],
    relationships = [],
    patterns = [],
    recommendations = [],
    report = {},
  } = caseData;

  const recs = recommendations.length
    ? recommendations
    : report.recommended_actions || [];

  const totalAmount = report.total_transaction_amount ?? null;

  // Group entities by type for the table
  const entityGroups = entities.reduce((acc, e) => {
    const label = entityTypeLabel(e.type);
    (acc[label] = acc[label] || []).push(e);
    return acc;
  }, {});

  return (
    <div
      className="brief-overlay"
      onClick={(ev) => {
        if (ev.target === ev.currentTarget) onClose();
      }}
    >
      <div className="brief-modal">

        {/* ── Modal toolbar ── */}
        <div className="brief-toolbar">
          <div className="brief-toolbar-title">
            <FileText size={17} />
            Case Brief
          </div>
          <div className="brief-toolbar-actions">
            <button
              className="brief-download-btn"
              onClick={() => printBrief(printRef)}
              title="Print / Save as PDF"
            >
              <Download size={15} />
              Export PDF
            </button>
            <button
              className="brief-close-btn"
              onClick={onClose}
              title="Close"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* ── Printable content ── */}
        <div className="brief-body" ref={printRef}>

          {/* Header */}
          <div className="brief-header">
            <h1>{case_title || "Cyber Fraud Investigation"}</h1>
            <div className="brief-meta">
              <span>Case ID: <strong>{case_id}</strong></span>
              <span>Generated: <strong>{today()}</strong></span>
              <span>
                Risk:{" "}
                <strong style={{ color: severityColor(status) }}>
                  {status}
                </strong>
              </span>
            </div>
          </div>

          {/* Case Summary */}
          <div className="brief-section">
            <h2>
              <FileText size={13} style={{ marginRight: 6 }} />
              Case Summary
            </h2>
            <div className="summary-box">
              {summary || report.summary || "No summary available."}
            </div>
            {totalAmount != null && totalAmount > 0 && (
              <p className="brief-stat-line">
                Total transaction amount identified:{" "}
                <strong>₹{totalAmount.toLocaleString("en-IN")}</strong>
              </p>
            )}
          </div>

          {/* Entities */}
          <div className="brief-section">
            <h2>
              <Users size={13} style={{ marginRight: 6 }} />
              Identified Entities ({entities.length})
            </h2>
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Type</th>
                </tr>
              </thead>
              <tbody>
                {entities.map((e) => (
                  <tr key={e.id}>
                    <td><code>{e.id}</code></td>
                    <td>{e.name}</td>
                    <td>{entityTypeLabel(e.type)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Relationships */}
          {relationships.length > 0 && (
            <div className="brief-section">
              <h2>
                <Link size={13} style={{ marginRight: 6 }} />
                Relationships ({relationships.length})
              </h2>
              <table>
                <thead>
                  <tr>
                    <th>From</th>
                    <th>Relationship</th>
                    <th>To</th>
                    <th>Amount</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {relationships.map((r, i) => {
                    const src = entities.find((e) => e.id === r.source);
                    const tgt = entities.find((e) => e.id === r.target);
                    return (
                      <tr key={i}>
                        <td>{src ? src.name : r.source}</td>
                        <td>{r.type}</td>
                        <td>{tgt ? tgt.name : r.target}</td>
                        <td>
                          {r.amount != null
                            ? `₹${r.amount.toLocaleString("en-IN")}`
                            : "—"}
                        </td>
                        <td>{r.timestamp || "—"}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Fraud Patterns */}
          {patterns.length > 0 && (
            <div className="brief-section">
              <h2>
                <ShieldAlert size={13} style={{ marginRight: 6 }} />
                Detected Fraud Patterns ({patterns.length})
              </h2>
              {patterns.map((p, i) => (
                <div className="pattern-block" key={i}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                    <h3>{p.type}</h3>
                    <span
                      className={`badge badge-${(p.severity || "").toLowerCase()}`}
                    >
                      {p.severity}
                    </span>
                  </div>
                  <p>{p.description}</p>
                </div>
              ))}
            </div>
          )}

          {/* Recommended Actions */}
          {recs.length > 0 && (
            <div className="brief-section">
              <h2>
                <CheckSquare size={13} style={{ marginRight: 6 }} />
                Recommended Investigative Actions
              </h2>
              {recs.map((rec, i) => (
                <div className="rec-item" key={i}>{rec}</div>
              ))}
            </div>
          )}

          <div className="footer">
            Generated by CyberTrace — Fraud Intelligence · {today()} · CONFIDENTIAL
          </div>

        </div>
      </div>
    </div>
  );
}

export default CaseBrief;
