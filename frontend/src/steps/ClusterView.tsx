/**
 * Cluster View - Display clustered experience items.
 */
import type { ClusterResponse } from '../api';
import type { Step, StickerLabel } from '../types';
import { LABEL_ICONS, LABEL_COLORS } from '../types';

interface ClusterViewProps {
  clusterResult: ClusterResponse | null;
  error: string | null;
  setStep: (step: Step) => void;
}

export function ClusterView({
  clusterResult,
  error,
  setStep,
}: ClusterViewProps) {
  return (
    <div className="card" style={{ maxWidth: '900px' }}>
      <h2><span className="icon">🔬</span> Experience Clusters</h2>
      <p className="card-subtitle">
        Your experiences grouped by similarity.
        <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}> (Placeholder: all items in one cluster)</span>
      </p>

      {error && <div className="error">{error}</div>}

      {clusterResult && (
        <>
          <div className="cluster-stats" style={{
            display: 'flex',
            gap: '1rem',
            marginBottom: '1.5rem',
            padding: '1rem',
            background: 'var(--bg-elevated)',
            borderRadius: '0.5rem'
          }}>
            <span><strong>Total Items:</strong> {clusterResult.total_items}</span>
            <span><strong>Clusters:</strong> {clusterResult.clusters.length}</span>
            <span><strong>Session:</strong> <code>{clusterResult.session_id}</code></span>
          </div>

          {clusterResult.clusters.map((cluster) => (
            <div
              key={cluster.cluster_id}
              className="cluster-group"
              style={{
                marginBottom: '1.5rem',
                padding: '1.25rem',
                background: 'var(--bg-elevated)',
                borderRadius: '0.75rem',
                border: '1px solid var(--border-color)'
              }}
            >
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '1rem'
              }}>
                <h3 style={{ margin: 0, color: 'var(--accent-primary)' }}>
                  📁 {cluster.cluster_label}
                </h3>
                <span style={{
                  background: 'var(--accent-primary)',
                  color: 'white',
                  padding: '0.25rem 0.75rem',
                  borderRadius: '1rem',
                  fontSize: '0.8rem'
                }}>
                  {cluster.items.length} items
                </span>
              </div>

              {cluster.summary && (
                <p style={{
                  color: 'var(--text-secondary)',
                  fontSize: '0.875rem',
                  marginBottom: '1rem',
                  fontStyle: 'italic'
                }}>
                  {cluster.summary}
                </p>
              )}

              <div className="cluster-items" style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem'
              }}>
                {cluster.items.map((item) => (
                  <div
                    key={item.id}
                    style={{
                      display: 'flex',
                      gap: '0.75rem',
                      padding: '0.75rem',
                      background: 'var(--bg-secondary)',
                      borderRadius: '0.5rem',
                      borderLeft: `3px solid ${LABEL_COLORS[item.label as StickerLabel] || 'var(--text-muted)'}`
                    }}
                  >
                    <span style={{
                      fontSize: '1.25rem',
                      flexShrink: 0
                    }}>
                      {LABEL_ICONS[item.label as StickerLabel] || '📝'}
                    </span>
                    <div style={{ flex: 1 }}>
                      <div style={{
                        display: 'flex',
                        gap: '0.5rem',
                        marginBottom: '0.25rem',
                        fontSize: '0.75rem',
                        color: 'var(--text-muted)'
                      }}>
                        <span style={{
                          color: LABEL_COLORS[item.label as StickerLabel] || 'var(--text-muted)',
                          fontWeight: 500
                        }}>
                          {item.label}
                        </span>
                        <span>•</span>
                        <span>{item.source}</span>
                      </div>
                      <p style={{ margin: 0, fontSize: '0.9rem' }}>{item.text}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </>
      )}

      <div className="btn-group" style={{ marginTop: '2rem' }}>
        <button className="btn btn-secondary" onClick={() => setStep(1)}>
          ← Back to Sticker Board
        </button>
      </div>
    </div>
  );
}
