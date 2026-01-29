/**
 * Custom hook containing all state management and handlers for the Career Fit Engine.
 */
import { useState, useEffect, useRef } from 'react';
import {
  uploadResumeText,
  uploadResumeFile,
  addResumeMaterialsText,
  getResumeStructured,
  waitForResumeReady,
  analyzeFit,
  generateResume,
  exportDocx,
  clusterExperience,
  AnalyzeFitResponse,
  ResumeGenerateResponse,
  ResumeStatusResponse,
  ClusterResponse,
  ExperienceItem,
  RoleType,
} from './api';
import { Step, JDSource, UploadMode, Sticker, StickerLabel, generateId } from './types';
import type { ResumeBlock, ResumeBlockType } from './types';

export function useCareerFit() {
  // === Session Management ===
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [uploadId, setUploadId] = useState<string | null>(null);
  const [step, setStep] = useState<Step>(1);

  // === Sticker Board State ===
  const [stickers, setStickers] = useState<Sticker[]>([]);
  const [newStickerText, setNewStickerText] = useState('');
  const [pastedResumeText, setPastedResumeText] = useState('');
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [uploadMode, setUploadMode] = useState<UploadMode>('stickers');
  const [resumeBlocks, setResumeBlocks] = useState<ResumeBlock[]>([]);

  // === Upload State ===
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<ResumeStatusResponse | null>(null);

  // === Step 2: Target Role & JD ===
  const [targetRole, setTargetRole] = useState<RoleType>('SWE');
  const [jdSource, setJdSource] = useState<JDSource>('custom');
  const [jdText, setJdText] = useState('');

  // === Step 3: Results ===
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [analysis, setAnalysis] = useState<AnalyzeFitResponse | null>(null);
  const [generatedResume, setGeneratedResume] = useState<ResumeGenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // === Evidence Visibility ===
  const [showResumeEvidence, setShowResumeEvidence] = useState(false);
  const [showJDEvidence, setShowJDEvidence] = useState(false);

  // === Clustering ===
  const [isClustering, setIsClustering] = useState(false);
  const [clusterResult, setClusterResult] = useState<ClusterResponse | null>(null);

  // === Refs ===
  const fileInputRef = useRef<HTMLInputElement>(null);

  // === Computed Values ===
  const activeCount = stickers.filter(s => s.active).length;

  // === LocalStorage Effects ===
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

  useEffect(() => {
    if (sessionId) localStorage.setItem('career_fit_session', sessionId);
  }, [sessionId]);

  useEffect(() => {
    localStorage.setItem('career_fit_stickers', JSON.stringify(stickers));
  }, [stickers]);

  useEffect(() => {
    localStorage.setItem('career_fit_pasted_text', pastedResumeText);
  }, [pastedResumeText]);

  // === Sticker Handlers ===
  const addSticker = (
    text: string,
    label: StickerLabel = 'other',
    blockId?: string,
    blockType?: ResumeBlockType
  ) => {
    if (!text.trim()) return;
    const newSticker: Sticker = {
      id: generateId(),
      label,
      text: text.trim(),
      active: true,
      blockId,
      blockType
    };
    setStickers(prev => [...prev, newSticker]);
  };

  const handleAddStickerKeyDown = (
    e: React.KeyboardEvent<HTMLInputElement>,
    options?: { label?: StickerLabel; blockId?: string; blockType?: ResumeBlockType }
  ) => {
    if (e.key === 'Enter' && newStickerText.trim()) {
      addSticker(
        newStickerText,
        options?.label ?? 'other',
        options?.blockId,
        options?.blockType
      );
      setNewStickerText('');
    }
  };

  const handleMultiLinePaste = (
    e: React.ClipboardEvent<HTMLTextAreaElement>,
    options?: { label?: StickerLabel; blockId?: string; blockType?: ResumeBlockType }
  ) => {
    const text = e.clipboardData.getData('text');
    const lines = text.split('\n').filter(line => line.trim());
    if (lines.length > 1) {
      e.preventDefault();
      lines.forEach(line => addSticker(
        line,
        options?.label ?? 'other',
        options?.blockId,
        options?.blockType
      ));
    }
  };
  const formatBlockHeader = (block: ResumeBlock): string => {
    const datePart = block.startDate && block.endDate
      ? `${block.startDate}–${block.endDate}`
      : (block.startDate || block.endDate);

    if (block.type === 'experience') {
      return [block.company, block.title, block.location, datePart].filter(Boolean).join(' | ') || 'Experience';
    }
    if (block.type === 'project') {
      return [block.name, block.role, block.location, datePart].filter(Boolean).join(' | ') || 'Project';
    }
    return [block.school, block.degree, block.field, block.location, datePart].filter(Boolean).join(' | ') || 'Education';
  };

  const addResumeBlock = (block: Omit<ResumeBlock, 'id' | 'header'>): string => {
    const id = generateId();
    const fullBlock: ResumeBlock = {
      ...block,
      id,
      header: formatBlockHeader({ ...block, id, header: '' })
    };
    setResumeBlocks(prev => [...prev, fullBlock]);
    return id;
  };

  const applyStructuredBlocks = (structured: {
    experiences: Array<{ block_id: string; company?: string | null; title?: string | null; location?: string | null; start_date?: string | null; end_date?: string | null; bullets?: string[] | null; }>;
    projects: Array<{ block_id: string; name?: string | null; role?: string | null; location?: string | null; start_date?: string | null; end_date?: string | null; bullets?: string[] | null; }>;
    education: Array<{ block_id: string; school?: string | null; degree?: string | null; field?: string | null; location?: string | null; start_date?: string | null; end_date?: string | null; bullets?: string[] | null; }>;
  }) => {
    const blocks: ResumeBlock[] = [];
    const parsedStickers: Sticker[] = [];
    structured.experiences.forEach(exp => {
      const block: ResumeBlock = {
        id: exp.block_id,
        type: 'experience',
        company: exp.company || undefined,
        title: exp.title || undefined,
        location: exp.location || undefined,
        startDate: exp.start_date || undefined,
        endDate: exp.end_date || undefined,
        header: '',
        source: 'parsed'
      };
      block.header = formatBlockHeader(block);
      blocks.push(block);
      (exp.bullets || []).forEach(bullet => {
        if (!bullet?.trim()) return;
        parsedStickers.push({
          id: generateId(),
          label: 'work',
          text: bullet.trim(),
          active: true,
          blockId: block.id,
          blockType: block.type
        });
      });
    });
    structured.projects.forEach(proj => {
      const block: ResumeBlock = {
        id: proj.block_id,
        type: 'project',
        name: proj.name || undefined,
        role: proj.role || undefined,
        location: proj.location || undefined,
        startDate: proj.start_date || undefined,
        endDate: proj.end_date || undefined,
        header: '',
        source: 'parsed'
      };
      block.header = formatBlockHeader(block);
      blocks.push(block);
      (proj.bullets || []).forEach(bullet => {
        if (!bullet?.trim()) return;
        parsedStickers.push({
          id: generateId(),
          label: 'project',
          text: bullet.trim(),
          active: true,
          blockId: block.id,
          blockType: block.type
        });
      });
    });
    structured.education.forEach(edu => {
      const block: ResumeBlock = {
        id: edu.block_id,
        type: 'education',
        school: edu.school || undefined,
        degree: edu.degree || undefined,
        field: edu.field || undefined,
        location: edu.location || undefined,
        startDate: edu.start_date || undefined,
        endDate: edu.end_date || undefined,
        header: '',
        source: 'parsed'
      };
      block.header = formatBlockHeader(block);
      blocks.push(block);
      (edu.bullets || []).forEach(bullet => {
        if (!bullet?.trim()) return;
        parsedStickers.push({
          id: generateId(),
          label: 'education',
          text: bullet.trim(),
          active: true,
          blockId: block.id,
          blockType: block.type
        });
      });
    });
    setResumeBlocks(blocks);
    if (parsedStickers.length > 0) {
      setStickers(parsedStickers);
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

  // === Utility Functions ===
  const packStickersAndText = (): string => {
    const activeStickers = stickers.filter(s => s.active);
    let combined = '';

    if (activeStickers.length > 0) {
      combined += '[STICKERS]\n';
      combined += activeStickers.map(s => {
        const header = s.blockId
          ? resumeBlocks.find(b => b.id === s.blockId)?.header
          : undefined;
        const prefix = header ? `[${header}] ` : '';
        return `- (${s.label}) ${prefix}${s.text.trim()}`;
      }).join('\n');
    }

    if (pastedResumeText.trim()) {
      if (combined) combined += '\n\n';
      combined += '[PASTED_RESUME]\n' + pastedResumeText.trim();
    }

    return combined;
  };

  const hasContent = (): boolean => {
    return !!resumeFile || stickers.some(s => s.active) || pastedResumeText.trim().length > 0;
  };

  const fetchStructuredBlocks = async (sid: string) => {
    try {
      const structured = await getResumeStructured(sid);
      applyStructuredBlocks(structured.structured);
    } catch (err) {
      console.error('Failed to fetch structured resume:', err);
    }
  };

  const uploadAndParseFile = async (file: File) => {
    setError(null);
    setIsUploading(true);
    setUploadStatus(null);
    try {
      const result = await uploadResumeFile(file);
      setSessionId(result.session_id);
      setUploadId(result.upload_id);

      const status = await waitForResumeReady(result.upload_id, setUploadStatus);
      if (status.status === 'error') {
        throw new Error(status.detail || 'Processing failed');
      }

      await fetchStructuredBlocks(result.session_id);
      setIsUploading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload resume');
      setIsUploading(false);
    }
  };

  // === File Handler ===
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setResumeFile(file);
      setUploadMode('file');
      uploadAndParseFile(file);
    }
  };

  // === Main Action Handlers ===
  const handleResumeSubmit = async () => {
    setError(null);
    setIsUploading(true);
    setUploadStatus(null);

    try {
      const combinedText = packStickersAndText();
      const hasText = combinedText.trim().length > 0;
      const hasFile = !!resumeFile;

      if (!hasText && !hasFile) {
        throw new Error('Please add some stickers, paste resume text, or upload a file');
      }

      let result;
      if (hasFile && resumeFile && !sessionId) {
        result = await uploadResumeFile(resumeFile);
        setSessionId(result.session_id);
        setUploadId(result.upload_id);

        const firstStatus = await waitForResumeReady(result.upload_id, setUploadStatus);
        if (firstStatus.status === 'error') {
          throw new Error(firstStatus.detail || 'Processing failed');
        }
      } else if (!hasFile) {
        result = await uploadResumeText(combinedText);
        setSessionId(result.session_id);
        setUploadId(result.upload_id);

        const firstStatus = await waitForResumeReady(result.upload_id, setUploadStatus);
        if (firstStatus.status === 'error') {
          throw new Error(firstStatus.detail || 'Processing failed');
        }
      } else {
        result = { session_id: sessionId, upload_id: uploadId };
      }

      if (hasText && result?.session_id) {
        const addResult = await addResumeMaterialsText(result.session_id, combinedText);
        setUploadId(addResult.upload_id);
        const addStatus = await waitForResumeReady(addResult.upload_id, setUploadStatus);
        if (addStatus.status === 'error') {
          throw new Error(addStatus.detail || 'Processing failed');
        }
      }

      if (result?.session_id) {
        await fetchStructuredBlocks(result.session_id);
      }

      setIsUploading(false);
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
    setStep(1);
    setSessionId(null);
    setUploadId(null);
    setUploadStatus(null);
    setJdText('');
    setAnalysis(null);
    setGeneratedResume(null);
    setError(null);
    setResumeBlocks([]);
    localStorage.removeItem('career_fit_session');
  };

  const handleClearBoard = () => {
    setStickers([]);
    setPastedResumeText('');
    setResumeFile(null);
    setResumeBlocks([]);
    localStorage.removeItem('career_fit_stickers');
    localStorage.removeItem('career_fit_pasted_text');
  };

  const handleViewClusters = async () => {
    setError(null);
    setIsClustering(true);
    setClusterResult(null);

    try {
      const items: ExperienceItem[] = stickers
        .filter(s => s.active)
        .map(s => ({
          id: s.id,
          label: s.label,
          text: s.blockId
            ? `[${resumeBlocks.find(b => b.id === s.blockId)?.header || 'Section'}] ${s.text}`
            : s.text,
          source: 'sticker'
        }));

      const hasStickers = items.length > 0;
      const hasPastedText = pastedResumeText.trim().length > 0;
      const hasUploadedResume = !!sessionId;

      if (!hasStickers && !hasPastedText && !hasUploadedResume) {
        throw new Error('Add some stickers, paste resume text, or upload a resume first');
      }

      const result = await clusterExperience(items, pastedResumeText || undefined, sessionId || undefined);
      setClusterResult(result);
      setStep('cluster');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Clustering failed');
    } finally {
      setIsClustering(false);
    }
  };

  return {
    // State
    sessionId,
    uploadId,
    step,
    setStep,
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
    targetRole,
    setTargetRole,
    jdSource,
    setJdSource,
    jdText,
    setJdText,
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
    isClustering,
    clusterResult,
    activeCount,
    resumeBlocks,

    // Refs
    fileInputRef,

    // Handlers
    addSticker,
    handleAddStickerKeyDown,
    handleMultiLinePaste,
    addResumeBlock,
    updateSticker,
    deleteSticker,
    toggleStickerActive,
    hasContent,
    handleFileChange,
    handleResumeSubmit,
    handleAnalyze,
    handleGenerate,
    handleExportDocx,
    handleStartOver,
    handleClearBoard,
    handleViewClusters,
  };
}
