/**
 * Step 2: Role Selector - Choose target role and job description source.
 */
import type { RoleType } from '../api';
import type { JDSource, Step } from '../types';

interface RoleSelectorProps {
  targetRole: RoleType;
  setTargetRole: (role: RoleType) => void;
  jdSource: JDSource;
  setJdSource: (source: JDSource) => void;
  jdText: string;
  setJdText: (text: string) => void;
  linkedinUrl: string;
  setLinkedinUrl: (url: string) => void;
  isAnalyzing: boolean;
  error: string | null;
  setStep: (step: Step) => void;
  handleAnalyze: () => void;
}

export function RoleSelector({
  targetRole,
  setTargetRole,
  jdSource,
  setJdSource,
  jdText,
  setJdText,
  linkedinUrl,
  setLinkedinUrl,
  isAnalyzing,
  error,
  setStep,
  handleAnalyze,
}: RoleSelectorProps) {
  const hasCustomJd = jdSource === 'custom' && jdText.trim().length > 0;
  const hasLinkedInUrl = jdSource === 'linkedin' && linkedinUrl.trim().length > 0;
  const disableAnalyze = isAnalyzing || (!hasCustomJd && !hasLinkedInUrl && jdSource !== 'curated');

  return (
    <div className="card">
      <h2><span className="icon">🎯</span> Select Target Role</h2>

      <div className="role-selector">
        <div
          className={`role-option ${targetRole === 'SWE' ? 'selected' : ''}`}
          onClick={() => setTargetRole('SWE')}
        >
          <div className="role-icon">💻</div>
          <div className="role-title">Software Engineer</div>
          <div className="role-desc">Full-stack, Backend, Frontend</div>
        </div>
        <div
          className={`role-option ${targetRole === 'DS' ? 'selected' : ''}`}
          onClick={() => setTargetRole('DS')}
        >
          <div className="role-icon">📊</div>
          <div className="role-title">Data Scientist</div>
          <div className="role-desc">Analytics, Statistics, ML</div>
        </div>
        <div
          className={`role-option ${targetRole === 'MLE' ? 'selected' : ''}`}
          onClick={() => setTargetRole('MLE')}
        >
          <div className="role-icon">🤖</div>
          <div className="role-title">ML Engineer</div>
          <div className="role-desc">MLOps, Production ML</div>
        </div>
        <div
          className={`role-option ${targetRole === 'OTHER' ? 'selected' : ''}`}
          onClick={() => setTargetRole('OTHER')}
        >
          <div className="role-icon">🔧</div>
          <div className="role-title">Other</div>
          <div className="role-desc">Custom role</div>
        </div>
      </div>

      <h3 style={{ marginBottom: '1rem', fontSize: '1rem' }}>Job Description Source</h3>

      <div className="toggle-group">
        <button
          className={`toggle-option ${jdSource === 'custom' ? 'active' : ''}`}
          onClick={() => setJdSource('custom')}
        >
          Paste JD Text
        </button>
        <button
          className={`toggle-option ${jdSource === 'curated' ? 'active' : ''}`}
          onClick={() => setJdSource('curated')}
        >
          Use Curated JDs
        </button>
        <button
          className={`toggle-option ${jdSource === 'linkedin' ? 'active' : ''}`}
          onClick={() => setJdSource('linkedin')}
        >
          LinkedIn URL
        </button>
      </div>

      {jdSource === 'custom' && (
        <div className="form-group">
          <textarea
            placeholder="Paste the job description here..."
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            style={{ minHeight: '150px' }}
          />
        </div>
      )}

      {jdSource === 'curated' && (
        <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', padding: '1rem', background: 'var(--bg-elevated)', borderRadius: '0.5rem' }}>
          <p>⚠️ Using curated JD library. Make sure JDs have been ingested via <code>/jd/ingest</code>.</p>
        </div>
      )}

      {jdSource === 'linkedin' && (
        <div className="form-group">
          <input
            type="url"
            placeholder="Paste LinkedIn job posting URL..."
            value={linkedinUrl}
            onChange={(e) => setLinkedinUrl(e.target.value)}
          />
        </div>
      )}

      {error && <div className="error">{error}</div>}

      <div className="btn-group">
        <button className="btn btn-secondary" onClick={() => setStep(1)}>
          ← Back
        </button>
        <button
          className="btn btn-primary"
          onClick={handleAnalyze}
          disabled={disableAnalyze}
        >
          {isAnalyzing ? 'Analyzing...' : 'Analyze Fit →'}
        </button>
      </div>
    </div>
  );
}
