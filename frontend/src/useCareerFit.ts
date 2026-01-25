/**
 * Custom hook containing all state management and handlers for the Career Fit Engine.
 */
import { useState, useEffect, useRef } from 'react';
import {
  uploadResumeText,
  uploadResumeFile,
  getResumeStatus,
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
  const pollIntervalRef = useRef<number | null>(null);

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

  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  // === Sticker Handlers ===
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

  // === Utility Functions ===
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

  // === File Handler ===
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setResumeFile(file);
      setUploadMode('file');
    }
  };

  // === Main Action Handlers ===
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

      pollIntervalRef.current = window.setInterval(() => {
        pollStatus(result.upload_id);
      }, 1000);

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
  };

  const handleClearBoard = () => {
    setStickers([]);
    setPastedResumeText('');
    setResumeFile(null);
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
          text: s.text,
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

    // Refs
    fileInputRef,

    // Handlers
    addSticker,
    handleAddStickerKeyDown,
    handleMultiLinePaste,
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
