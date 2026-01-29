/**
 * Shared types, interfaces, and constants for the Career Fit Engine.
 */

// === Step & Mode Types ===
export type Step = 1 | 2 | 3 | 'cluster';
export type JDSource = 'curated' | 'custom';
export type UploadMode = 'stickers' | 'file';
export type StickerLabel = 'work' | 'project' | 'internship' | 'skill' | 'metric' | 'education' | 'other';
export type ResumeBlockType = 'experience' | 'project' | 'education';

// === Sticker Interface ===
export interface Sticker {
  id: string;
  label: StickerLabel;
  text: string;
  active: boolean;
  blockId?: string;
  blockType?: ResumeBlockType;
}

export interface ResumeBlock {
  id: string;
  type: ResumeBlockType;
  header: string;
  company?: string;
  title?: string;
  name?: string;
  role?: string;
  school?: string;
  degree?: string;
  field?: string;
  location?: string;
  startDate?: string;
  endDate?: string;
  source?: string;
}

// === Constants ===
export const LABEL_ICONS: Record<StickerLabel, string> = {
  work: '👔',
  project: '🛠️',
  internship: '💼',
  skill: '⚡',
  metric: '📊',
  education: '🎓',
  other: '📝'
};

export const LABEL_COLORS: Record<StickerLabel, string> = {
  work: '#f97316',
  project: 'var(--accent-primary)',
  internship: 'var(--accent-secondary)',
  skill: 'var(--accent-success)',
  metric: 'var(--accent-warning)',
  education: '#ec4899',
  other: 'var(--text-muted)'
};

import type { UploadStatus } from './api';

export const STATUS_LABELS: Record<UploadStatus, string> = {
  uploading: '📤 Uploading...',
  parsing: '📄 Parsing document...',
  chunking: '✂️ Splitting into chunks...',
  embedding: '🧮 Generating embeddings...',
  indexing: '📚 Building search index...',
  ready: '✅ Ready!',
  error: '❌ Error'
};

// === Utility Functions ===
export const generateId = () => Math.random().toString(36).substring(2, 9);

export const getScoreClass = (score: number): string => {
  if (score >= 0.7) return 'score-high';
  if (score >= 0.4) return 'score-medium';
  return 'score-low';
};
