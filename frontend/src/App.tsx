/**
 * Tech Career Fit Engine - Main Application Shell
 * 
 * This is the main entry point that:
 * - Renders the app header and step indicator
 * - Routes to the appropriate step component based on current state
 * - Uses the useCareerFit hook for all state management
 */
import { useCareerFit } from './useCareerFit';
import type { CareerFitState } from './useCareerFit';
import { Landing, StickerBoard, RoleSelector, AnalysisResults, ClusterView } from './steps';
import { DotScreenShader } from "@/components/ui/dot-shader-background";
import { useEffect, useRef, useState } from "react";
import { TutorialTour, type TourStep } from "./components/TutorialTour";
import { ThemeToggle } from "./components/ThemeToggle";

export default function App() {
  const state: CareerFitState = useCareerFit();

  const appRef = useRef<HTMLDivElement>(null);
  const [eventSource, setEventSource] = useState<HTMLElement | undefined>(undefined);

  useEffect(() => {
    setEventSource(appRef.current ?? undefined);
  }, []);

  const [tourOpen, setTourOpen] = useState(false);
  const [tourStepIndex, setTourStepIndex] = useState(0);

  const tourSteps: TourStep[] = [
    {
      id: "steps-bar",
      selector: '[data-tour="steps-bar"]',
      title: "3-step workflow",
      body: "You’ll go from Sticker Board → Target Role → Analysis. The highlight shows where you are in the flow.",
      placement: "bottom",
      padding: 10,
    },
    {
      id: "step-1",
      selector: '[data-tour="step-1"]',
      title: "Step 1: Sticker Board",
      body: "Add experiences as quick bullets (or upload a file). Toggle anything you don’t want included.",
      placement: "bottom",
      padding: 10,
    },
    {
      id: "board",
      selector: '[data-tour="sticker-board"]',
      title: "Build your evidence",
      body: "Think of stickers as raw material. Short, specific bullets with numbers work best.",
      placement: "right",
      padding: 14,
    },
    {
      id: "sync-parse",
      selector: '[data-tour="sync-parse"]',
      title: "Sync & parse",
      body: "This processes your text/file so the next steps can match you against a job description.",
      placement: "top",
      padding: 12,
    },
    {
      id: "step-2",
      selector: '[data-tour="step-2"]',
      title: "Step 2: Target Role",
      body: "Paste a job description (or use curated ones) so the app knows what you’re aiming for.",
      placement: "bottom",
      padding: 10,
    },
    {
      id: "step-3",
      selector: '[data-tour="step-3"]',
      title: "Step 3: Analysis",
      body: "You’ll see matched vs missing requirements, plus evidence chunks and a resume draft.",
      placement: "bottom",
      padding: 10,
    },
  ];

  useEffect(() => {
    if (state.step !== 1) return;
    const seen = localStorage.getItem("career_fit_tour_seen");
    if (!seen) {
      setTourStepIndex(0);
      setTourOpen(true);
      localStorage.setItem("career_fit_tour_seen", "1");
    }
  }, [state.step]);

  return (
    <div ref={appRef} className="relative min-h-screen">
      {/* Dots background behind engine pages */}
      {state.step !== 'landing' && (
        <div className="fixed inset-0 z-0">
          <DotScreenShader eventSource={eventSource} />
        </div>
      )}

      {state.step === 'landing' ? (
        <Landing onStart={() => state.setStep(1)} />
      ) : (
        <div className="app-container relative z-10">
          {/* Header */}
          <header className="header">
            <div style={{ position: "absolute", top: "1rem", right: "1rem" }}>
              <ThemeToggle />
            </div>
            <h1>
              Tech Career <span className="brand-script">Fit</span> Engine
            </h1>
            <p>Build your resume with stickers • evidence-grounded analysis</p>
          </header>

          {/* Step Indicator */}
          <div className="steps" data-tour="steps-bar">
            <div
              className={`step ${state.step === 1 ? 'active' : (state.step === 2 || state.step === 3) ? 'completed' : ''}`}
              data-tour="step-1"
            >
              <span className="step-number">{(state.step === 2 || state.step === 3) ? '✓' : '1'}</span>
              <span>Sticker Board</span>
            </div>
            <div
              className={`step ${state.step === 2 ? 'active' : state.step === 3 ? 'completed' : ''}`}
              data-tour="step-2"
            >
              <span className="step-number">{state.step === 3 ? '✓' : '2'}</span>
              <span>Target Role</span>
            </div>
            <div className={`step ${state.step === 3 ? 'active' : ''}`} data-tour="step-3">
              <span className="step-number">3</span>
              <span>Analysis</span>
            </div>
            {state.step === 'cluster' && (
              <div className="step active">
                <span className="step-number">▦</span>
                <span>Clusters</span>
              </div>
            )}
          </div>

          {/* Main Content - Step Router */}
          <main className="main-content">
            {state.step === 1 && (
              <StickerBoard
                stickers={state.stickers}
                pastedResumeText={state.pastedResumeText}
                setPastedResumeText={state.setPastedResumeText}
                resumeFile={state.resumeFile}
                isUploading={state.isUploading}
                uploadStatus={state.uploadStatus}
                error={state.error}
                activeCount={state.activeCount}
                sessionId={state.sessionId}
                isClustering={state.isClustering}
                fileInputRef={state.fileInputRef}
                resumeBlocks={state.resumeBlocks}
                setStep={state.setStep}
                addSticker={state.addSticker}
                addResumeBlock={state.addResumeBlock}
                updateSticker={state.updateSticker}
                deleteSticker={state.deleteSticker}
                toggleStickerActive={state.toggleStickerActive}
                hasContent={state.hasContent}
                handleFileChange={state.handleFileChange}
                handleClearBoard={state.handleClearBoard}
                handleViewClusters={state.handleViewClusters}
                handleResumeSubmit={state.handleResumeSubmit}
              />
            )}

        {state.step === 2 && (
          <RoleSelector
            targetRole={state.targetRole}
            setTargetRole={state.setTargetRole}
            jdSource={state.jdSource}
            setJdSource={state.setJdSource}
            jdText={state.jdText}
            setJdText={state.setJdText}
            linkedinUrl={state.linkedinUrl}
            setLinkedinUrl={state.setLinkedinUrl}
            isAnalyzing={state.isAnalyzing}
            error={state.error}
            setStep={state.setStep}
            handleAnalyze={state.handleAnalyze}
          />
        )}

        {state.step === 3 && (
          <AnalysisResults
            isAnalyzing={state.isAnalyzing}
            isGenerating={state.isGenerating}
            isExporting={state.isExporting}
            analysis={state.analysis}
            generatedResume={state.generatedResume}
            error={state.error}
            showResumeEvidence={state.showResumeEvidence}
            setShowResumeEvidence={state.setShowResumeEvidence}
            showJDEvidence={state.showJDEvidence}
            setShowJDEvidence={state.setShowJDEvidence}
            setStep={state.setStep}
            handleGenerate={state.handleGenerate}
            handleExportDocx={state.handleExportDocx}
            handleStartOver={state.handleStartOver}
          />
        )}

        {state.step === 'cluster' && (
          <ClusterView
            clusterResult={state.clusterResult}
            error={state.error}
            setStep={state.setStep}
          />
        )}
          </main>
        </div>
      )}

      <TutorialTour
        open={tourOpen}
        steps={tourSteps}
        stepIndex={tourStepIndex}
        onStepIndexChange={setTourStepIndex}
        onSkip={() => setTourOpen(false)}
        onEnd={() => setTourOpen(false)}
      />
    </div>
  );
}
