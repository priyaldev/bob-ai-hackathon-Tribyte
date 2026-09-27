import { useRef, useState } from "react";

import {
  ArrowLeft,
  Upload,
  FileText,
  Database,
  X,
  Play,
  ShieldAlert,
  ClipboardPaste,
  CheckCircle2,
} from "lucide-react";

function NewInvestigation({
  onBack,
  onAnalyze,
}) {
  const fileInputRef =
    useRef(null);

  const [caseTitle, setCaseTitle] =
    useState("");

  const [context, setContext] =
    useState("");

  const [inputMode, setInputMode] =
    useState("file");

  const [file, setFile] =
    useState(null);

  const [rawText, setRawText] =
    useState("");

  const [isAnalyzing, setIsAnalyzing] =
    useState(false);

  const [error, setError] =
    useState("");

  const [dragActive, setDragActive] =
    useState(false);

  /*
   * ==========================================================
   * FILE PROCESSING
   * ==========================================================
   */

  const processFile = (
    selectedFile
  ) => {
    if (!selectedFile) {
      return;
    }

    const extension =
      selectedFile.name
        .split(".")
        .pop()
        .toLowerCase();

    if (
      !["csv", "json"].includes(
        extension
      )
    ) {
      setError(
        "Only CSV and JSON files are supported."
      );

      return;
    }

    setError("");

    setFile(selectedFile);

    const reader =
      new FileReader();

    reader.onload = () => {
      setRawText(
        String(
          reader.result || ""
        )
      );
    };

    reader.onerror = () => {
      setError(
        "Unable to read the selected file."
      );
    };

    reader.readAsText(
      selectedFile
    );
  };

  /*
   * ==========================================================
   * FILE CHANGE
   * ==========================================================
   */

  const handleFileChange = (
    event
  ) => {
    const selectedFile =
      event.target.files?.[0];

    processFile(
      selectedFile
    );

    event.target.value = "";
  };

  /*
   * ==========================================================
   * DRAG & DROP
   * ==========================================================
   */

  const handleDrop = (
    event
  ) => {
    event.preventDefault();

    setDragActive(false);

    const droppedFile =
      event.dataTransfer.files?.[0];

    processFile(
      droppedFile
    );
  };

  /*
   * ==========================================================
   * REMOVE FILE
   * ==========================================================
   */

  const removeFile = () => {
    setFile(null);
    setRawText("");
    setError("");
  };

  /*
   * ==========================================================
   * INPUT MODE
   * ==========================================================
   */

  const handleModeChange = (
    mode
  ) => {
    setInputMode(mode);
    setError("");

    if (mode === "file") {
      setRawText("");
    }

    if (mode === "text") {
      setFile(null);
    }
  };

  /*
   * ==========================================================
   * ANALYZE
   * ==========================================================
   */

  const handleAnalyze = async () => {
    setError("");

    if (!caseTitle.trim()) {
      setError(
        "Please enter a case title."
      );

      return;
    }

    if (!rawText.trim()) {
      setError(
        "Please upload investigation data or paste raw fraud intelligence."
      );

      return;
    }

    const payload = {
      case_title:
        caseTitle.trim(),

      context:
        context.trim(),

      input_type:
        inputMode === "file"
          ? "file"
          : "text",

      file_name:
        file
          ? file.name
          : null,

      raw_data:
        rawText,
    };

    setIsAnalyzing(true);

    try {
      await onAnalyze(
        payload
      );
    } catch (err) {
      setError(
        err?.message ||
          "Something went wrong while starting the investigation."
      );

      setIsAnalyzing(false);
    }
  };

  const characterCount =
    rawText.length;

  return (
    <div className="new-investigation-page">

      {/* =====================================================
          HEADER
      ====================================================== */}

      <header className="new-investigation-header">

        <button
          className="back-button"
          onClick={onBack}
          disabled={isAnalyzing}
        >
          <ArrowLeft size={18} />

          Dashboard
        </button>

        <div className="new-investigation-title">

          <span>
            INVESTIGATION WORKSPACE
          </span>

          <h1>
            New Investigation
          </h1>

          <p>
            Submit raw fraud intelligence
            for automated entity,
            relationship and fraud analysis.
          </p>

        </div>

        <div className="investigation-status">

          <ShieldAlert size={16} />

          AI ANALYSIS READY

        </div>

      </header>

      {/* =====================================================
          MAIN
      ====================================================== */}

      <main className="new-investigation-content">

        {/* ===================================================
            CASE INFORMATION
        ==================================================== */}

        <section className="creation-card">

          <div className="creation-card-heading">

            <div className="heading-icon">
              <FileText size={19} />
            </div>

            <div>

              <span>
                STEP 01
              </span>

              <h2>
                Case Information
              </h2>

            </div>

          </div>

          <div className="form-grid">

            <div className="form-group form-full">

              <label htmlFor="case-title">
                CASE TITLE
              </label>

              <input
                id="case-title"
                type="text"
                placeholder="e.g. Suspected SIM Swap & Mule Account Network"
                value={caseTitle}
                onChange={(event) =>
                  setCaseTitle(
                    event.target.value
                  )
                }
                disabled={isAnalyzing}
              />

            </div>

            <div className="form-group form-full">

              <label htmlFor="case-context">

                INVESTIGATION CONTEXT

                <span className="optional-label">
                  OPTIONAL
                </span>

              </label>

              <textarea
                id="case-context"
                rows="5"
                placeholder="Add any information already known about the case..."
                value={context}
                onChange={(event) =>
                  setContext(
                    event.target.value
                  )
                }
                disabled={isAnalyzing}
              />

            </div>

          </div>

        </section>

        {/* ===================================================
            RAW INTELLIGENCE
        ==================================================== */}

        <section className="creation-card">

          <div className="creation-card-heading">

            <div className="heading-icon">
              <Database size={19} />
            </div>

            <div>

              <span>
                STEP 02
              </span>

              <h2>
                Raw Fraud Intelligence
              </h2>

            </div>

          </div>

          <div className="intelligence-description">

            <p>
              Provide the original investigation
              data. The current frontend analyzer
              will process the uploaded JSON and
              build the investigation network.
            </p>

            <div className="ai-note">

              <CheckCircle2 size={15} />

              <span>
                Later this raw data will be sent
                to FastAPI and the AI engine.
              </span>

            </div>

          </div>

          {/* INPUT MODE */}

          <div className="input-mode-tabs">

            <button
              className={`input-mode ${
                inputMode === "file"
                  ? "active"
                  : ""
              }`}
              onClick={() =>
                handleModeChange(
                  "file"
                )
              }
              disabled={isAnalyzing}
            >

              <Upload size={18} />

              <div>

                <strong>
                  Upload Data
                </strong>

                <span>
                  CSV or JSON
                </span>

              </div>

            </button>

            <button
              className={`input-mode ${
                inputMode === "text"
                  ? "active"
                  : ""
              }`}
              onClick={() =>
                handleModeChange(
                  "text"
                )
              }
              disabled={isAnalyzing}
            >

              <ClipboardPaste
                size={18}
              />

              <div>

                <strong>
                  Paste Text
                </strong>

                <span>
                  Raw investigation notes
                </span>

              </div>

            </button>

          </div>

          {/* =================================================
              FILE MODE
          ================================================== */}

          {inputMode === "file" && (

            <div className="raw-input-area">

              {!file ? (

                <div
                  className={`upload-box ${
                    dragActive
                      ? "drag-active"
                      : ""
                  }`}
                  onDragOver={(event) => {
                    event.preventDefault();

                    setDragActive(
                      true
                    );
                  }}
                  onDragLeave={() =>
                    setDragActive(
                      false
                    )
                  }
                  onDrop={
                    handleDrop
                  }
                  onClick={() =>
                    fileInputRef.current?.click()
                  }
                >

                  <input
                    ref={
                      fileInputRef
                    }
                    type="file"
                    accept=".csv,.json"
                    onChange={
                      handleFileChange
                    }
                  />

                  <div className="upload-icon">

                    <Upload size={25} />

                  </div>

                  <strong>
                    Drop investigation
                    data here
                  </strong>

                  <span>
                    or click to browse files
                  </span>

                  <small>
                    Supported formats:
                    CSV, JSON
                  </small>

                </div>

              ) : (

                <div className="selected-file">

                  <div className="file-info">

                    <div className="file-icon">

                      <FileText size={20} />

                    </div>

                    <div>

                      <strong>
                        {file.name}
                      </strong>

                      <span>
                        {(
                          file.size /
                          1024
                        ).toFixed(1)}{" "}
                        KB
                      </span>

                    </div>

                  </div>

                  <button
                    className="remove-file"
                    onClick={
                      removeFile
                    }
                    disabled={
                      isAnalyzing
                    }
                    aria-label="Remove file"
                  >
                    <X size={17} />
                  </button>

                </div>

              )}

            </div>

          )}

          {/* =================================================
              TEXT MODE
          ================================================== */}

          {inputMode === "text" && (

            <div className="raw-text-container">

              <textarea
                className="raw-intelligence-textarea"
                placeholder={`Paste raw investigation intelligence here...

Example:

Victim Priya Patel reported an unauthorized UPI transaction of ₹85,000.

Her registered mobile number 9876543210 stopped working before the transaction.

The money was transferred to account ACC-45821.`}
                value={rawText}
                onChange={(event) =>
                  setRawText(
                    event.target.value
                  )
                }
                disabled={isAnalyzing}
              />

              <div className="text-input-footer">

                <span>
                  Raw text will be sent
                  to the investigation
                  analysis pipeline.
                </span>

                <strong>
                  {characterCount.toLocaleString()}{" "}
                  characters
                </strong>

              </div>

            </div>

          )}

          {/* =================================================
              DATA PREVIEW
          ================================================== */}

          {inputMode === "file" &&
            file && (

              <div className="raw-data-preview">

                <div className="preview-header">

                  <div>

                    <span>
                      DATA PREVIEW
                    </span>

                    <strong>
                      Raw file content
                    </strong>

                  </div>

                  <span className="preview-status">
                    READY
                  </span>

                </div>

                <pre>
                  {rawText.length >
                  2500
                    ? `${rawText.slice(
                        0,
                        2500
                      )}\n\n... preview truncated`
                    : rawText}
                </pre>

              </div>
            )}

        </section>

        {/* ===================================================
            PIPELINE
        ==================================================== */}

        <section className="pipeline-card">

          <div className="pipeline-heading">

            <div>

              <span>
                WHAT HAPPENS NEXT
              </span>

              <h2>
                Automated Investigation Pipeline
              </h2>

            </div>

            <Database size={20} />

          </div>

          <div className="pipeline-steps">

            <div className="pipeline-step">

              <div className="pipeline-number">
                01
              </div>

              <div>

                <strong>
                  Entity Extraction
                </strong>

                <span>
                  Identify persons,
                  phones, SIMs,
                  devices, accounts
                  and transactions.
                </span>

              </div>

            </div>

            <div className="pipeline-line"></div>

            <div className="pipeline-step">

              <div className="pipeline-number">
                02
              </div>

              <div>

                <strong>
                  Relationship Detection
                </strong>

                <span>
                  Identify connections
                  between extracted
                  entities.
                </span>

              </div>

            </div>

            <div className="pipeline-line"></div>

            <div className="pipeline-step">

              <div className="pipeline-number">
                03
              </div>

              <div>

                <strong>
                  Fraud Analysis
                </strong>

                <span>
                  Detect suspicious
                  patterns and
                  investigation indicators.
                </span>

              </div>

            </div>

            <div className="pipeline-line"></div>

            <div className="pipeline-step">

              <div className="pipeline-number">
                04
              </div>

              <div>

                <strong>
                  Network Generation
                </strong>

                <span>
                  Convert structured
                  intelligence into an
                  interactive fraud network.
                </span>

              </div>

            </div>

          </div>

        </section>

        {/* ERROR */}

        {error && (

          <div className="form-error">

            <ShieldAlert size={17} />

            <span>
              {error}
            </span>

          </div>

        )}

        {/* ACTIONS */}

        <div className="creation-actions">

          <button
            className="secondary-button"
            onClick={onBack}
            disabled={
              isAnalyzing
            }
          >
            Cancel
          </button>

          <button
            className="primary-button analyze-button"
            onClick={
              handleAnalyze
            }
            disabled={
              isAnalyzing
            }
          >

            {isAnalyzing ? (
              <>
                <span className="loading-spinner"></span>
                Analyzing...
              </>
            ) : (
              <>
                <Play size={17} />
                Analyze Investigation
              </>
            )}

          </button>

        </div>

      </main>

    </div>
  );
}

export default NewInvestigation;