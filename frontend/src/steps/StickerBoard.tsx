/**
 * Step 1: Sticker Board - Add experiences as stickers or upload resume file.
 */
import { LABEL_ICONS, LABEL_COLORS, STATUS_LABELS, StickerLabel, Sticker } from '../types';
import type { ResumeStatusResponse } from '../api';

interface StickerBoardProps {
  stickers: Sticker[];
  newStickerText: string;
  setNewStickerText: (text: string) => void;
  pastedResumeText: string;
  setPastedResumeText: (text: string) => void;
  resumeFile: File | null;
  uploadMode: 'stickers' | 'file';
  setUploadMode: (mode: 'stickers' | 'file') => void;
  isUploading: boolean;
  uploadStatus: ResumeStatusResponse | null;
  error: string | null;
  activeCount: number;
  sessionId: string | null;
  isClustering: boolean;
  fileInputRef: React.RefObject<HTMLInputElement>;
  // Handlers
  addSticker: (text: string, label?: StickerLabel) => void;
  handleAddStickerKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  handleMultiLinePaste: (e: React.ClipboardEvent<HTMLTextAreaElement>) => void;
  updateSticker: (id: string, updates: Partial<Sticker>) => void;
  deleteSticker: (id: string) => void;
  toggleStickerActive: (id: string) => void;
  hasContent: () => boolean;
  handleFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleClearBoard: () => void;
  handleViewClusters: () => void;
  handleResumeSubmit: () => void;
}

export function StickerBoard({
  stickers,
  newStickerText,
  setNewStickerText,
  pastedResumeText,
  setPastedResumeText,
  resumeFile,
  uploadMode,
  setUploadMode,
  isUploading,
  uploadStatus,
  error,
  activeCount,
  sessionId,
  isClustering,
  fileInputRef,
  addSticker,
  handleAddStickerKeyDown,
  handleMultiLinePaste,
  updateSticker,
  deleteSticker,
  toggleStickerActive,
  hasContent,
  handleFileChange,
  handleClearBoard,
  handleViewClusters,
  handleResumeSubmit,
}: StickerBoardProps) {
  return (
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
          className="btn btn-secondary"
          onClick={handleViewClusters}
          disabled={isClustering || isUploading || (!hasContent() && !sessionId)}
        >
          {isClustering ? 'Clustering...' : '🔬 View Clusters'}
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
  );
}
