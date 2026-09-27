import {
  AlertTriangle,
  ShieldAlert,
} from "lucide-react";

function FraudAnalysis({
  patterns = [],
}) {
  return (
    <div className="fraud-analysis">

      <div className="section-title">

        <div>

          <span>
            AI INVESTIGATION
          </span>

          <h2>
            Fraud Analysis
          </h2>

        </div>

        <ShieldAlert
          size={24}
        />

      </div>

      {patterns.length === 0 ? (

        <div className="pattern-card">

          <p>
            No suspicious patterns
            were identified in the
            submitted investigation data.
          </p>

        </div>

      ) : (

        patterns.map(
          (
            pattern,
            index
          ) => (

            <div
              className="pattern-card"
              key={index}
            >

              <div className="pattern-header">

                <div>

                  <span className="pattern-label">
                    DETECTED PATTERN
                  </span>

                  <h3>
                    {pattern.type}
                  </h3>

                </div>

                <span className="severity">
                  {pattern.severity}
                </span>

              </div>

              <p>
                {pattern.description}
              </p>

              <div className="indicator">

                <AlertTriangle
                  size={15}
                />

                Evidence-based
                indicator

              </div>

            </div>

          )
        )

      )}

    </div>
  );
}

export default FraudAnalysis;