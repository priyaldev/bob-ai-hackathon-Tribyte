import { useState } from "react";

import {
  ArrowLeft,
  FileText,
  Users,
  Smartphone,
  CreditCard,
  AlertTriangle,
} from "lucide-react";

import NetworkGraph from "../components/NetworkGraph";
import EntityDetails from "../components/EntityDetails";
import FraudAnalysis from "../components/FraudAnalysis";
import CaseBrief from "../components/CaseBrief";

function Investigation({
  caseData,
  onBack,
}) {
  const [selectedEntity, setSelectedEntity] =
    useState(null);

  const [showBrief, setShowBrief] =
    useState(false);

  const people =
    caseData.entities.filter(
      (entity) =>
        entity.type === "PERSON"
    ).length;

  const devices =
    caseData.entities.filter(
      (entity) =>
        entity.type === "DEVICE"
    ).length;

  const accounts =
    caseData.entities.filter(
      (entity) =>
        entity.type === "BANK_ACCOUNT"
    ).length;

  return (
    <>
    <div className="investigation-page">

      {/* =====================================================
          HEADER
      ====================================================== */}

      <header className="topbar">

        <button
          className="back-button"
          onClick={onBack}
        >
          <ArrowLeft size={18} />

          Cases
        </button>

        <div className="case-title">

          <span>
            {caseData.case_id}
          </span>

          <h1>
            {caseData.case_title}
          </h1>

        </div>

        <div
          className={`risk-badge${
            caseData.status === "LOW RISK"
              ? " risk-low"
              : caseData.status === "MEDIUM RISK"
              ? " risk-medium"
              : ""
          }`}
        >

          <AlertTriangle
            size={16}
          />

          {caseData.status}

        </div>

      </header>

      {/* =====================================================
          STATS
      ====================================================== */}

      <div className="stats-row">

        <div className="stat-card">

          <Users size={20} />

          <div>

            <span>
              PERSONS
            </span>

            <strong>
              {people}
            </strong>

          </div>

        </div>

        <div className="stat-card">

          <Smartphone size={20} />

          <div>

            <span>
              DEVICES
            </span>

            <strong>
              {devices}
            </strong>

          </div>

        </div>

        <div className="stat-card">

          <CreditCard size={20} />

          <div>

            <span>
              ACCOUNTS
            </span>

            <strong>
              {accounts}
            </strong>

          </div>

        </div>

        <div className="stat-card">

          <FileText size={20} />

          <div>

            <span>
              RELATIONSHIPS
            </span>

            <strong>
              {
                caseData.relationships
                  .length
              }
            </strong>

          </div>

        </div>

      </div>

      {/* =====================================================
          MAIN INVESTIGATION
      ====================================================== */}

      <main className="investigation-grid">

        <section className="graph-section">

          <div className="panel-heading">

            <div>

              <span>
                NETWORK INTELLIGENCE
              </span>

              <h2>
                Fraud Network
              </h2>

            </div>

            <div className="graph-legend">

              <span>
                ● Person
              </span>

              <span>
                ● Device
              </span>

              <span>
                ● Account
              </span>

            </div>

          </div>

          <NetworkGraph
            caseData={caseData}
            onEntitySelect={
              setSelectedEntity
            }
          />

        </section>

        {/* SIDE PANEL */}

        <aside className="side-panel">

          <FraudAnalysis
            patterns={
              caseData.patterns
            }
          />

          <EntityDetails
            entity={
              selectedEntity
            }
          />

        </aside>

      </main>

      {/* =====================================================
          CASE SUMMARY
      ====================================================== */}

      <div className="bottom-bar">

        <div>

          <span>
            CASE SUMMARY
          </span>

          <p>
            {caseData.summary}
          </p>

        </div>

        <button
          className="primary-button"
          onClick={() => setShowBrief(true)}
        >

          <FileText
            size={18}
          />

          Generate Case Brief

        </button>

      </div>

    </div>

    {showBrief && (
      <CaseBrief
        caseData={caseData}
        onClose={() => setShowBrief(false)}
      />
    )}

    </>
  );
}

export default Investigation;