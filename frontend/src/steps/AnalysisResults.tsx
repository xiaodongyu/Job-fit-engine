/**
 * Step 3: Analysis Results - Display fit analysis and generated resume.
 */
import type { AnalyzeFitResponse, ResumeGenerateResponse } from '../api';
import type { Step } from '../types';
import { getScoreClass } from '../types';

interface AnalysisResultsProps {
  isAnalyzing: boolean;
  isGenerating: boolean;
  isExporting: boolean;
  analysis: AnalyzeFitResponse | null;
  generatedResume: ResumeGenerateResponse | null;
  error: string | null;
  showResumeEvidence: boolean;
  setShowResumeEvidence: (show: boolean) => void;
  showJDEvidence: boolean;
  setShowJDEvidence: (show: boolean) => void;
  setStep: (step: Step) => void;
  handleGenerate: () => void;
  handleExportDocx: () => void;
  handleStartOver: () => void;
}

export function AnalysisResults({
  isAnalyzing,
  isGenerating,
  isExporting,
  analysis,
  generatedResume,
  error,
  showResumeEvidence,
  setShowResumeEvidence,
  showJDEvidence,
  setShowJDEvidence,
  setStep,
  handleGenerate,
  handleExportDocx,
  handleStartOver,
}: AnalysisResultsProps) {
  return (
    <div className="card" style={{ maxWidth: '800px' }}>
      <h2><span className="icon">📈</span> Analysis Results</h2>

      {isAnalyzing && (
        <div className="loading">
          <div className="spinner" />
          <span className="loading-text">Analyzing your resume against job requirements...</span>
        </div>
      )}

      {error && <div className="error">{error}</div>}

      {analysis && (
        <>
          {/* Role Recommendations */}
          <div className="results-section">
            <h3>🎯 Role Fit</h3>
            {analysis.recommended_roles.map((role, i) => (
              <div key={i} className="role-card">
                <div className="role-card-header">
                  <span className="role-name">{role.role}</span>
                  <span className={`score-badge ${getScoreClass(role.score)}`}>
                    {Math.round(role.score * 100)}% Match
                  </span>
                </div>
                <ul className="reasons-list">
                  {role.reasons.map((reason, j) => (
                    <li key={j}>{reason}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* Requirements */}
          <div className="results-section">
            <h3>📋 Requirements (from JD)</h3>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ color: 'var(--accent-warning)', marginBottom: '0.5rem' }}>Must Have</label>
              <div className="tag-list">
                {analysis.requirements.must_have.map((req, i) => (
                  <span key={i} className="tag tag-must">{req}</span>
                ))}
              </div>
            </div>
            <div>
              <label style={{ color: 'var(--accent-secondary)', marginBottom: '0.5rem' }}>Nice to Have</label>
              <div className="tag-list">
                {analysis.requirements.nice_to_have.map((req, i) => (
                  <span key={i} className="tag tag-nice">{req}</span>
                ))}
              </div>
            </div>
          </div>

          {/* Gap Analysis */}
          <div className="results-section">
            <h3>🔍 Gap Analysis</h3>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ color: 'var(--accent-success)', marginBottom: '0.5rem' }}>Matched (from Resume)</label>
              <div className="tag-list">
                {analysis.gap.matched.map((item, i) => (
                  <span key={i} className="tag tag-match">✓ {item}</span>
                ))}
              </div>
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ color: 'var(--accent-error)', marginBottom: '0.5rem' }}>Missing / Gaps</label>
              <div className="tag-list">
                {analysis.gap.missing.map((item, i) => (
                  <span key={i} className="tag tag-missing">✗ {item}</span>
                ))}
              </div>
            </div>

            {analysis.gap.ask_user_questions.length > 0 && (
              <div className="questions-list">
                <h4>❓ Clarification Needed</h4>
                <ul>
                  {analysis.gap.ask_user_questions.map((q, i) => (
                    <li key={i}>{q}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Evidence Collapsibles */}
          <div className="collapsible">
            <div
              className="collapsible-header"
              onClick={() => setShowResumeEvidence(!showResumeEvidence)}
            >
              <span>📄 Resume Evidence ({analysis.evidence.resume_chunks.length} chunks)</span>
              <span>{showResumeEvidence ? '▲' : '▼'}</span>
            </div>
            {showResumeEvidence && (
              <div className="collapsible-content">
                {analysis.evidence.resume_chunks.map((chunk, i) => (
                  <div key={i} className="evidence-chunk">
                    <div className="chunk-header">
                      <span className="chunk-id">{chunk.chunk_id}</span>
                      <span className="chunk-score">Score: {chunk.score.toFixed(3)}</span>
                    </div>
                    <p>{chunk.text}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="collapsible">
            <div
              className="collapsible-header"
              onClick={() => setShowJDEvidence(!showJDEvidence)}
            >
              <span>📝 JD Evidence ({analysis.evidence.jd_chunks.length} chunks)</span>
              <span>{showJDEvidence ? '▲' : '▼'}</span>
            </div>
            {showJDEvidence && (
              <div className="collapsible-content">
                {analysis.evidence.jd_chunks.map((chunk, i) => (
                  <div key={i} className="evidence-chunk">
                    <div className="chunk-header">
                      <span className="chunk-id">{chunk.chunk_id}</span>
                      <span className="chunk-score">Score: {chunk.score.toFixed(3)}</span>
                    </div>
                    <p>{chunk.text}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Generate Resume Button */}
          <div className="btn-group" style={{ marginTop: '2rem' }}>
            <button
              className="btn btn-primary"
              onClick={handleGenerate}
              disabled={isGenerating}
            >
              {isGenerating ? 'Generating...' : '✨ Generate Tailored Resume'}
            </button>
          </div>

          {/* Generated Resume */}
          {generatedResume && (
            <div className="results-section" style={{ marginTop: '2rem' }}>
              <h3>📝 Generated Resume</h3>

              {/* Chat-like assistant message */}
              <div className="chat-bubble">
                <div className="chat-avatar">🤖</div>
                <div className="chat-content">
                  <div className="chat-header">AI Resume Writer</div>
                  <div className="resume-output">
                    {generatedResume.resume_markdown}
                  </div>
                </div>
              </div>

              {/* Download button */}
              <div className="btn-group" style={{ marginTop: '1rem' }}>
                <button
                  className="btn btn-secondary"
                  onClick={handleExportDocx}
                  disabled={isExporting}
                >
                  {isExporting ? '⏳ Exporting...' : '📄 Download .docx'}
                </button>
              </div>

              {generatedResume.need_info.length > 0 && (
                <div className="need-info">
                  <h4>📝 Need Info (not in resume)</h4>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                    These JD requirements couldn't be matched to your resume evidence:
                  </p>
                  <ul>
                    {generatedResume.need_info.map((item, i) => (
                      <li key={i}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </>
      )}

      <div className="btn-group" style={{ marginTop: '2rem' }}>
        <button className="btn btn-secondary" onClick={() => setStep(2)}>
          ← Change Role
        </button>
        <button className="btn btn-secondary" onClick={handleStartOver}>
          Start Over
        </button>
      </div>
    </div>
  );
}
