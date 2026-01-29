/**
 * Tech Career Fit Engine - Main Application Shell
 * 
 * This is the main entry point that:
 * - Renders the app header and step indicator
 * - Routes to the appropriate step component based on current state
 * - Uses the useCareerFit hook for all state management
 */
import { useCareerFit } from './useCareerFit';
import { StickerBoard, RoleSelector, AnalysisResults, ClusterView } from './steps';

export default function App() {
  const state = useCareerFit();

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <h1>Tech Career Fit Engine</h1>
        <p>Build your resume with stickers • AI-powered analysis</p>
      </header>

      {/* Step Indicator */}
      <div className="steps">
        <div className={`step ${state.step === 1 ? 'active' : (state.step === 2 || state.step === 3) ? 'completed' : ''}`}>
          <span className="step-number">{(state.step === 2 || state.step === 3) ? '✓' : '1'}</span>
          <span>Sticker Board</span>
        </div>
        <div className={`step ${state.step === 2 ? 'active' : state.step === 3 ? 'completed' : ''}`}>
          <span className="step-number">{state.step === 3 ? '✓' : '2'}</span>
          <span>Target Role</span>
        </div>
        <div className={`step ${state.step === 3 ? 'active' : ''}`}>
          <span className="step-number">3</span>
          <span>Analysis</span>
        </div>
        {state.step === 'cluster' && (
          <div className="step active">
            <span className="step-number">🔬</span>
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
  );
}
