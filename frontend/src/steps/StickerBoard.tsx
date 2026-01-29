/**
 * Step 1: Sticker Board - Add experiences as stickers or upload resume file.
 */
import { useState } from 'react';
import { LABEL_ICONS, LABEL_COLORS, STATUS_LABELS, StickerLabel, Sticker, ResumeBlock, ResumeBlockType, Step } from '../types';
import type { ResumeStatusResponse } from '../api';

interface StickerBoardProps {
  stickers: Sticker[];
  pastedResumeText: string;
  setPastedResumeText: (text: string) => void;
  resumeFile: File | null;
  isUploading: boolean;
  uploadStatus: ResumeStatusResponse | null;
  error: string | null;
  activeCount: number;
  sessionId: string | null;
  isClustering: boolean;
  fileInputRef: React.RefObject<HTMLInputElement>;
  resumeBlocks: ResumeBlock[];
  setStep: (step: Step) => void;
  // Handlers
  addSticker: (text: string, label?: StickerLabel, blockId?: string, blockType?: ResumeBlockType) => void;
  addResumeBlock: (block: Omit<ResumeBlock, 'id' | 'header'>) => string;
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
  pastedResumeText,
  setPastedResumeText,
  resumeFile,
  isUploading,
  uploadStatus,
  error,
  activeCount,
  sessionId,
  isClustering,
  fileInputRef,
  resumeBlocks,
  setStep,
  addSticker,
  addResumeBlock,
  updateSticker,
  deleteSticker,
  toggleStickerActive,
  hasContent,
  handleFileChange,
  handleClearBoard,
  handleViewClusters,
  handleResumeSubmit,
}: StickerBoardProps) {
  const [blockInputs, setBlockInputs] = useState<Record<string, string>>({});
  const [otherInput, setOtherInput] = useState('');
  const [newBlockType, setNewBlockType] = useState<ResumeBlockType>('experience');
  const [newBlockFields, setNewBlockFields] = useState({
    company: '',
    title: '',
    name: '',
    role: '',
    school: '',
    degree: '',
    field: '',
    location: '',
    startDate: '',
    endDate: ''
  });

  const mapTypeToLabel = (type?: ResumeBlockType): StickerLabel => {
    if (type === 'project') return 'project';
    if (type === 'education') return 'education';
    return 'work';
  };

  const canCreateBlock = (): boolean => {
    if (newBlockType === 'experience') {
      return !!newBlockFields.company.trim()
        && !!newBlockFields.title.trim()
        && !!newBlockFields.startDate.trim()
        && !!newBlockFields.endDate.trim();
    }
    if (newBlockType === 'project') {
      return !!newBlockFields.name.trim()
        && !!newBlockFields.role.trim()
        && !!newBlockFields.startDate.trim()
        && !!newBlockFields.endDate.trim();
    }
    return !!newBlockFields.school.trim()
      && !!newBlockFields.degree.trim()
      && !!newBlockFields.startDate.trim()
      && !!newBlockFields.endDate.trim();
  };

  const handleCreateBlock = () => {
    if (!canCreateBlock()) return;
    addResumeBlock({
      type: newBlockType,
      company: newBlockType === 'experience' ? newBlockFields.company.trim() : undefined,
      title: newBlockType === 'experience' ? newBlockFields.title.trim() : undefined,
      name: newBlockType === 'project' ? newBlockFields.name.trim() : undefined,
      role: newBlockType === 'project' ? newBlockFields.role.trim() : undefined,
      school: newBlockType === 'education' ? newBlockFields.school.trim() : undefined,
      degree: newBlockType === 'education' ? newBlockFields.degree.trim() : undefined,
      field: newBlockType === 'education' ? newBlockFields.field.trim() : undefined,
      location: newBlockFields.location.trim() || undefined,
      startDate: newBlockFields.startDate.trim(),
      endDate: newBlockFields.endDate.trim(),
      source: 'manual'
    });
    setNewBlockFields({
      company: '',
      title: '',
      name: '',
      role: '',
      school: '',
      degree: '',
      field: '',
      location: '',
      startDate: '',
      endDate: ''
    });
  };

  const formatBlockDetails = (block: ResumeBlock): string => {
    const datePart = block.startDate && block.endDate
      ? `${block.startDate}–${block.endDate}`
      : (block.startDate || block.endDate);
    if (block.type === 'experience') {
      return [block.company, block.title, block.location, datePart].filter(Boolean).join(' | ');
    }
    if (block.type === 'project') {
      return [block.name, block.role, block.location, datePart].filter(Boolean).join(' | ');
    }
    return [block.school, block.degree, block.field, block.location, datePart].filter(Boolean).join(' | ');
  };

  const formatBlockLabel = (block: ResumeBlock): string => {
    const details = formatBlockDetails(block);
    return details || (block.type === 'experience' ? 'Experience' : block.type === 'project' ? 'Project' : 'Education');
  };

  const handleBlockInputChange = (blockId: string, value: string) => {
    setBlockInputs(prev => ({ ...prev, [blockId]: value }));
  };

  const handleAddBlockSticker = (block: ResumeBlock) => {
    const text = blockInputs[block.id]?.trim();
    if (!text) return;
    const label = mapTypeToLabel(block.type);
    addSticker(text, label, block.id, block.type);
    setBlockInputs(prev => ({ ...prev, [block.id]: '' }));
  };
  return (
    <div className="card card-wide">
      <h2><span className="icon">📋</span> Sticker Board</h2>
      <p className="card-subtitle">Add your experiences as stickers. Toggle them on/off to include in your resume.</p>

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

      {resumeBlocks.length > 0 ? (
        <div className="parsed-blocks">
          <div className="parsed-title">Parsed Resume Sections</div>
          <div className="parsed-grid">
            {resumeBlocks.map(block => (
              <div key={block.id} className="parsed-item">
                <span className="parsed-type">{block.type}</span>
                <span className="parsed-header">{formatBlockLabel(block)}</span>
                <div className="sticker-add-row">
                  <input
                    type="text"
                    className="sticker-input"
                    placeholder="Add a bullet under this section..."
                    value={blockInputs[block.id] || ''}
                    onChange={(e) => handleBlockInputChange(block.id, e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleAddBlockSticker(block);
                      }
                    }}
                  />
                  <button
                    className="btn btn-secondary"
                    onClick={() => handleAddBlockSticker(block)}
                    disabled={!blockInputs[block.id]?.trim()}
                  >
                    + Add
                  </button>
                </div>
                {stickers.filter(s => s.blockId === block.id).length > 0 && (
                  <div className="block-stickers">
                    {stickers.filter(s => s.blockId === block.id).map(sticker => (
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
                )}
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="empty-board">
          <span className="empty-icon">📄</span>
          <p>Create your first fixed section to start building your resume.</p>
        </div>
      )}

      {resumeBlocks.length === 0 && (
        <div className="parsed-blocks">
          <div className="parsed-title">Create a fixed section</div>
          <div className="sticker-target">
            <label>Section type</label>
            <select
              value={newBlockType}
              onChange={(e) => setNewBlockType(e.target.value as ResumeBlockType)}
            >
              <option value="experience">Experience</option>
              <option value="project">Project</option>
              <option value="education">Education</option>
            </select>
          </div>
          <div className="new-block-fields">
            {newBlockType === 'experience' && (
              <>
                <input
                  type="text"
                  placeholder="Company"
                  value={newBlockFields.company}
                  onChange={(e) => setNewBlockFields(prev => ({ ...prev, company: e.target.value }))}
                />
                <input
                  type="text"
                  placeholder="Title"
                  value={newBlockFields.title}
                  onChange={(e) => setNewBlockFields(prev => ({ ...prev, title: e.target.value }))}
                />
              </>
            )}
            {newBlockType === 'project' && (
              <>
                <input
                  type="text"
                  placeholder="Project Name"
                  value={newBlockFields.name}
                  onChange={(e) => setNewBlockFields(prev => ({ ...prev, name: e.target.value }))}
                />
                <input
                  type="text"
                  placeholder="Role / Title"
                  value={newBlockFields.role}
                  onChange={(e) => setNewBlockFields(prev => ({ ...prev, role: e.target.value }))}
                />
              </>
            )}
            {newBlockType === 'education' && (
              <>
                <input
                  type="text"
                  placeholder="School"
                  value={newBlockFields.school}
                  onChange={(e) => setNewBlockFields(prev => ({ ...prev, school: e.target.value }))}
                />
                <input
                  type="text"
                  placeholder="Degree"
                  value={newBlockFields.degree}
                  onChange={(e) => setNewBlockFields(prev => ({ ...prev, degree: e.target.value }))}
                />
              </>
            )}
            {newBlockType === 'education' && (
              <input
                type="text"
                placeholder="Field (optional)"
                value={newBlockFields.field}
                onChange={(e) => setNewBlockFields(prev => ({ ...prev, field: e.target.value }))}
              />
            )}
            <input
              type="text"
              placeholder="Start Date (e.g. 2021-01)"
              value={newBlockFields.startDate}
              onChange={(e) => setNewBlockFields(prev => ({ ...prev, startDate: e.target.value }))}
            />
            <input
              type="text"
              placeholder="End Date (e.g. 2023-06 or Present)"
              value={newBlockFields.endDate}
              onChange={(e) => setNewBlockFields(prev => ({ ...prev, endDate: e.target.value }))}
            />
            <input
              type="text"
              placeholder="Location (optional)"
              value={newBlockFields.location}
              onChange={(e) => setNewBlockFields(prev => ({ ...prev, location: e.target.value }))}
            />
          </div>
          <button
            className="btn btn-secondary"
            onClick={handleCreateBlock}
            disabled={!canCreateBlock()}
          >
            + Add Section
          </button>
        </div>
      )}

      <div className="parsed-blocks">
        <div className="parsed-title">Other (Skill)</div>
        <div className="sticker-add-row">
          <input
            type="text"
            className="sticker-input"
            placeholder="Add a skill or other note..."
            value={otherInput}
            onChange={(e) => setOtherInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                if (otherInput.trim()) {
                  addSticker(otherInput.trim(), 'skill');
                  setOtherInput('');
                }
              }
            }}
          />
          <button
            className="btn btn-secondary"
            onClick={() => {
              if (!otherInput.trim()) return;
              addSticker(otherInput.trim(), 'skill');
              setOtherInput('');
            }}
            disabled={!otherInput.trim()}
          >
            + Add
          </button>
        </div>
      </div>

      <div className="divider">optional: paste full resume</div>

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
        {resumeFile && <span className="stat">+ file attached</span>}
      </div>

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
        {sessionId && (
          <button
            className="btn btn-secondary"
            onClick={() => setStep(2)}
            disabled={isUploading}
          >
            Continue →
          </button>
        )}
        <button
          className="btn btn-primary"
          onClick={handleResumeSubmit}
          disabled={isUploading || !hasContent()}
        >
          {isUploading ? 'Processing...' : 'Sync & Parse →'}
        </button>
      </div>
    </div>
  );
}
