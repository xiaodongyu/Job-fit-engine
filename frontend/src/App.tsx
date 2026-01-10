import { useState, useEffect, useRef } from 'react';
import {
  uploadResumeText,
  uploadResumeFile,
  getResumeStatus,
  analyzeFit,
  generateResume,
  exportDocx,
  AnalyzeFitResponse,
  ResumeGenerateResponse,
  ResumeStatusResponse,
  RoleType,
  UploadStatus
} from './api';

type Step = 1 | 2 | 3;
type JDSource = 'curated' | 'custom';
type UploadMode = 'stickers' | 'file';
type StickerLabel = 'work' | 'project' | 'internship' | 'skill' | 'metric' | 'education' | 'other';

interface Sticker {
  id: string;
  label: StickerLabel;
  text: string;
  active: boolean;
}

const LABEL_ICONS: Record<StickerLabel, string> = {
  work: '👔',
  project: '🛠️',
  internship: '💼',
  skill: '⚡',
  metric: '📊',
  education: '🎓',
  other: '📝'
};

const LABEL_COLORS: Record<StickerLabel, string> = {
  work: '#f97316',
  project: 'var(--accent-primary)',
  internship: 'var(--accent-secondary)',
  skill: 'var(--accent-success)',
  metric: 'var(--accent-warning)',
  education: '#ec4899',
  other: 'var(--text-muted)'
};

const STATUS_LABELS: Record<UploadStatus, string> = {
  uploading: '📤 Uploading...',
  parsing: '📄 Parsing document...',
  chunking: '✂️ Splitting into chunks...',
  embedding: '🧮 Generating embeddings...',
  indexing: '📚 Building search index...',
  ready: '✅ Ready!',
  error: '❌ Error'
};

export default function App() {
  // Session management
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [uploadId, setUploadId] = useState<string | null>(null);
  
  // Step state
  const [step, setStep] = useState<Step>(1);
  
  // === Stickers Board ===
  const [stickers, setStickers] = useState<Sticker[]>([]);
  const [newStickerText, setNewStickerText] = useState('');
  const [pastedResumeText, setPastedResumeText] = useState('');
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [uploadMode, setUploadMode] = useState<UploadMode>('stickers');
  
  // Upload state
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<ResumeStatusResponse | null>(null);
  
  // Step 2: Target role & JD
  const [targetRole, setTargetRole] = useState<RoleType>('SWE');
  const [jdSource, setJdSource] = useState<JDSource>('custom');
  const [jdText, setJdText] = useState('');
  
  // Step 3: Results
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [analysis, setAnalysis] = useState<AnalyzeFitResponse | null>(null);
  const [generatedResume, setGeneratedResume] = useState<ResumeGenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Evidence visibility
  const [showResumeEvidence, setShowResumeEvidence] = useState(false);
  const [showJDEvidence, setShowJDEvidence] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollIntervalRef = useRef<number | null>(null);

  // Load session + stickers from localStorage
  useEffect(() => {
    const savedSession = localStorage.getItem('career_fit_session');
    if (savedSession) setSessionId(savedSession);
    
    const savedStickers = localStorage.getItem('career_fit_stickers');
    if (savedStickers) {
      try {
        setStickers(JSON.parse(savedStickers));
      } catch (e) {
        console.error('Failed to parse saved stickers:', e);
      }
    }
    
    const savedPastedText = localStorage.getItem('career_fit_pasted_text');
    if (savedPastedText) setPastedResumeText(savedPastedText);
  }, []);

  // Save session to localStorage
  useEffect(() => {
    if (sessionId) localStorage.setItem('career_fit_session', sessionId);
  }, [sessionId]);

  // Save stickers to localStorage
  useEffect(() => {
    localStorage.setItem('career_fit_stickers', JSON.stringify(stickers));
  }, [stickers]);

  // Save pasted text to localStorage
  useEffect(() => {
    localStorage.setItem('career_fit_pasted_text', pastedResumeText);
  }, [pastedResumeText]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  // === Sticker Helpers ===
  const generateId = () => Math.random().toString(36).substring(2, 9);

  const addSticker = (text: string, label: StickerLabel = 'other') => {
    if (!text.trim()) return;
    const newSticker: Sticker = {
      id: generateId(),
      label,
      text: text.trim(),
      active: true
    };
    setStickers(prev => [...prev, newSticker]);
  };

  const handleAddStickerKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && newStickerText.trim()) {
      addSticker(newStickerText);
      setNewStickerText('');
    }
  };

  const handleMultiLinePaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    const text = e.clipboardData.getData('text');
    const lines = text.split('\n').filter(line => line.trim());
    
    if (lines.length > 1) {
      e.preventDefault();
      lines.forEach(line => addSticker(line));
    }
  };

  const updateSticker = (id: string, updates: Partial<Sticker>) => {
    setStickers(prev => prev.map(s => s.id === id ? { ...s, ...updates } : s));
  };

  const deleteSticker = (id: string) => {
    setStickers(prev => prev.filter(s => s.id !== id));
  };

  const toggleStickerActive = (id: string) => {
    setStickers(prev => prev.map(s => s.id === id ? { ...s, active: !s.active } : s));
  };

  // === Packing Logic ===
  const packStickersAndText = (): string => {
    const activeStickers = stickers.filter(s => s.active);
    let combined = '';
    
    if (activeStickers.length > 0) {
      combined += '[STICKERS]\n';
      combined += activeStickers.map(s => `- (${s.label}) ${s.text.trim()}`).join('\n');
    }
    
    if (pastedResumeText.trim()) {
      if (combined) combined += '\n\n';
      combined += '[PASTED_RESUME]\n' + pastedResumeText.trim();
    }
    
    return combined;
  };

  const hasContent = (): boolean => {
    if (uploadMode === 'file') {
      return !!resumeFile;
    }
    return stickers.some(s => s.active) || pastedResumeText.trim().length > 0;
  };

  // === Polling ===
  const pollStatus = async (uid: string) => {
    try {
      const status = await getResumeStatus(uid);
      setUploadStatus(status);
      
      if (status.status === 'ready') {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
        setIsUploading(false);
        setStep(2);
      } else if (status.status === 'error') {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
        setIsUploading(false);
        setError(status.detail || 'Processing failed');
      }
    } catch (err) {
      console.error('Status poll error:', err);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setResumeFile(file);
      setUploadMode('file');
    }
  };

  const handleResumeSubmit = async () => {
    setError(null);
    setIsUploading(true);
    setUploadStatus(null);
    
    try {
      let result;
      
      if (uploadMode === 'file' && resumeFile) {
        result = await uploadResumeFile(resumeFile);
      } else {
        const combinedText = packStickersAndText();
        if (!combinedText.trim()) {
          throw new Error('Please add some stickers or paste resume text');
        }
        result = await uploadResumeText(combinedText);
      }
      
      setSessionId(result.session_id);
      setUploadId(result.upload_id);
      
      // Start polling for status
      pollIntervalRef.current = window.setInterval(() => {
        pollStatus(result.upload_id);
      }, 1000);
      
      // Initial poll
      pollStatus(result.upload_id);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload resume');
      setIsUploading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!sessionId) return;
    
    setError(null);
    setIsAnalyzing(true);
    setAnalysis(null);
    setGeneratedResume(null);
    
    try {
      const useCurated = jdSource === 'curated';
      const jd = jdSource === 'custom' && jdText.trim() ? jdText : undefined;
      
      if (!useCurated && !jd) {
        throw new Error('Please provide a job description or use curated JDs');
      }
      
      const result = await analyzeFit(sessionId, targetRole, useCurated, jd);
      setAnalysis(result);
      setStep(3);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleGenerate = async () => {
    if (!sessionId) return;
    
    setError(null);
    setIsGenerating(true);
    
    try {
      const useCurated = jdSource === 'curated';
      const jd = jdSource === 'custom' && jdText.trim() ? jdText : undefined;
      const result = await generateResume(sessionId, targetRole, useCurated, jd);
      setGeneratedResume(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleExportDocx = async () => {
    if (!sessionId) return;
    
    setError(null);
    setIsExporting(true);
    
    try {
      const useCurated = jdSource === 'curated';
      const jd = jdSource === 'custom' && jdText.trim() ? jdText : undefined;
      const blob = await exportDocx(sessionId, targetRole, useCurated, jd);
      
      // Download the file
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'resume.docx';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
    } finally {
      setIsExporting(false);
    }
  };

  const handleStartOver = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    setStep(1);
    setSessionId(null);
    setUploadId(null);
    setUploadStatus(null);
    setJdText('');
    setAnalysis(null);
    setGeneratedResume(null);
    setError(null);
    localStorage.removeItem('career_fit_session');
    // Keep stickers and pasted text for reuse
  };

  const handleClearBoard = () => {
    setStickers([]);
    setPastedResumeText('');
    setResumeFile(null);
    localStorage.removeItem('career_fit_stickers');
    localStorage.removeItem('career_fit_pasted_text');
  };

  const getScoreClass = (score: number): string => {
    if (score >= 0.7) return 'score-high';
    if (score >= 0.4) return 'score-medium';
    return 'score-low';
  };

  const activeCount = stickers.filter(s => s.active).length;

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <h1>Tech Career Fit Engine</h1>
        <p>Build your resume with stickers • AI-powered analysis</p>
      </header>

      {/* Step Indicator */}
      <div className="steps">
        <div className={`step ${step === 1 ? 'active' : step > 1 ? 'completed' : ''}`}>
          <span className="step-number">{step > 1 ? '✓' : '1'}</span>
          <span>Sticker Board</span>
        </div>
        <div className={`step ${step === 2 ? 'active' : step > 2 ? 'completed' : ''}`}>
          <span className="step-number">{step > 2 ? '✓' : '2'}</span>
          <span>Target Role</span>
        </div>
        <div className={`step ${step === 3 ? 'active' : ''}`}>
          <span className="step-number">3</span>
          <span>Analysis</span>
        </div>
      </div>

      {/* Main Content */}
      <main className="main-content">
        {/* Step 1: Sticker Board */}
        {step === 1 && (
          <div className="card card-wide">
            <h2><span className="icon">📋</span> Sticker Board</h2>
            <p className="card-subtitle">Add your experiences as stickers. Toggle them on/off to include in your resume.</p>
            
            {/* Upload Mode Toggle */}
            <div className="toggle-group" style={{ marginBottom: '1.5rem' }}>
              <button
                className={`toggle-option ${uploadMode === 'stickers' ? 'active' : ''}`}
                onClick={() => setUploadMode('stickers')}
              >
                🎯 Stickers + Text
              </button>
              <button
                className={`toggle-option ${uploadMode === 'file' ? 'active' : ''}`}
                onClick={() => setUploadMode('file')}
              >
                📁 Upload File
              </button>
            </div>

            {uploadMode === 'stickers' ? (
              <>
                {/* Add Sticker Input */}
                <div className="sticker-input-section">
                  <div className="sticker-add-row">
                    <input
                      type="text"
                      className="sticker-input"
                      placeholder="Add a sticker... (press Enter)"
                      value={newStickerText}
                      onChange={(e) => setNewStickerText(e.target.value)}
                      onKeyDown={handleAddStickerKeyDown}
                    />
                    <button 
                      className="btn btn-secondary"
                      onClick={() => { addSticker(newStickerText); setNewStickerText(''); }}
                      disabled={!newStickerText.trim()}
                    >
                      + Add
                    </button>
                  </div>
                  
                  <div className="quick-add-hint">
                    💡 Tip: Paste multiple lines to create multiple stickers at once
                  </div>

                  {/* Multi-line paste area */}
                  <textarea
                    className="multi-paste-area"
                    placeholder="Paste multiple experiences here (one per line)..."
                    onPaste={handleMultiLinePaste}
                    rows={2}
                  />
                </div>

                {/* Stickers Grid */}
                {stickers.length > 0 ? (
                  <div className="stickers-grid">
                    {stickers.map((sticker) => (
                      <div 
                        key={sticker.id} 
                        className={`sticker-card ${!sticker.active ? 'inactive' : ''}`}
                        style={{ borderColor: sticker.active ? LABEL_COLORS[sticker.label] : undefined }}
                      >
                        <div className="sticker-header">
                          <select
                            className="sticker-label-select"
                            value={sticker.label}
                            onChange={(e) => updateSticker(sticker.id, { label: e.target.value as StickerLabel })}
                            style={{ color: LABEL_COLORS[sticker.label] }}
                          >
                            {Object.entries(LABEL_ICONS).map(([label, icon]) => (
                              <option key={label} value={label}>{icon} {label}</option>
                            ))}
                          </select>
                          <div className="sticker-actions">
                            <button 
                              className={`sticker-toggle ${sticker.active ? 'on' : 'off'}`}
                              onClick={() => toggleStickerActive(sticker.id)}
                              title={sticker.active ? 'Take down' : 'Stick on'}
                            >
                              {sticker.active ? '📌' : '📍'}
                            </button>
                            <button 
                              className="sticker-delete"
                              onClick={() => deleteSticker(sticker.id)}
                              title="Delete"
                            >
                              ✕
                            </button>
                          </div>
                        </div>
                        <textarea
                          className="sticker-text"
                          value={sticker.text}
                          onChange={(e) => updateSticker(sticker.id, { text: e.target.value })}
                          rows={3}
                        />
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="empty-board">
                    <span className="empty-icon">📝</span>
                    <p>No stickers yet. Add your first experience above!</p>
                  </div>
                )}

                <div className="divider">optional: paste full resume</div>

                {/* Pasted Resume Text */}
                <div className="form-group">
                  <textarea
                    placeholder="Paste your full resume text here (optional supplement to stickers)..."
                    value={pastedResumeText}
                    onChange={(e) => setPastedResumeText(e.target.value)}
                    style={{ minHeight: '120px' }}
                  />
                </div>

                <div className="board-stats">
                  <span className="stat">{activeCount} active sticker{activeCount !== 1 ? 's' : ''}</span>
                  {pastedResumeText && <span className="stat">+ pasted text</span>}
                </div>
              </>
            ) : (
              /* File Upload Mode */
              <div className="form-group">
                <label
                  className="file-upload"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <span className="icon">📁</span>
                  <span>Click to upload (.pdf, .docx, .txt)</span>
                  {resumeFile && <span className="filename">{resumeFile.name}</span>}
                </label>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".txt,.pdf,.doc,.docx"
                  onChange={handleFileChange}
                />
              </div>
            )}
            
            {/* Upload Status */}
            {isUploading && uploadStatus && (
              <div className="upload-status">
                <div className="status-indicator">
                  <div className="spinner-small" />
                  <span>{STATUS_LABELS[uploadStatus.status]}</span>
                </div>
                {uploadStatus.detail && (
                  <p className="status-detail">{uploadStatus.detail}</p>
                )}
              </div>
            )}
            
            {error && <div className="error">{error}</div>}
            
            <div className="btn-group">
              <button
                className="btn btn-secondary"
                onClick={handleClearBoard}
                disabled={isUploading || (stickers.length === 0 && !pastedResumeText && !resumeFile)}
              >
                🗑️ Clear Board
              </button>
              <button
                className="btn btn-primary"
                onClick={handleResumeSubmit}
                disabled={isUploading || !hasContent()}
              >
                {isUploading ? 'Processing...' : 'Upload & Analyze →'}
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Target Role */}
        {step === 2 && (
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
            
            {error && <div className="error">{error}</div>}
            
            <div className="btn-group">
              <button className="btn btn-secondary" onClick={() => setStep(1)}>
                ← Back
              </button>
              <button
                className="btn btn-primary"
                onClick={handleAnalyze}
                disabled={isAnalyzing || (jdSource === 'custom' && !jdText.trim())}
              >
                {isAnalyzing ? 'Analyzing...' : 'Analyze Fit →'}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Analysis & Results */}
        {step === 3 && (
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
                    <label style={{ color: 'var(--accent-primary)', marginBottom: '0.5rem' }}>Must Have</label>
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
        )}
      </main>
    </div>
  );
}
