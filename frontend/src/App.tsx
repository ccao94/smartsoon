import { useState } from 'react'
import './App.css'

// ─────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────

type DocType = 'native_pdf' | 'scanned_pdf' | 'image'
type OcrEngine = 'tesseract' | 'surya' | 'none'

interface PageResult {
  page_number: number
  text: string
  confidence: number
}

interface DocumentResult {
  doc_id: string
  filename: string
  doc_type: DocType
  ocr_engine: OcrEngine
  ocr_confidence: number
  page_count: number
  pages: PageResult[]
}

interface ExtractResponse {
  status: string
  document: DocumentResult
}

interface AnonResponse {
  original: string
  anonymized: string
  chunks: number
  document_id: string
}

interface RagFullResponse {
  [key: string]: unknown
}

interface StepState<T> {
  status: 'idle' | 'running' | 'success' | 'error'
  data?: T
  error?: string
}

// ─────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────

const LIASSE_ID = 'Demo_Soutenance_Finale'
const DEFAULT_QUERY = 'Résume les informations principales de ce document médical.'

// ─────────────────────────────────────────────────────────────
// Icons (inline SVG)
// ─────────────────────────────────────────────────────────────

const IconUpload = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="17 8 12 3 7 8" />
    <line x1="12" y1="3" x2="12" y2="15" />
  </svg>
)

const IconOCR = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="9" y1="13" x2="15" y2="13" />
    <line x1="9" y1="17" x2="15" y2="17" />
  </svg>
)

const IconShield = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
)

const IconSparkles = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3z" />
    <path d="M5 18l.75 2.25L8 21l-2.25.75L5 24l-.75-2.25L2 21l2.25-.75L5 18z" />
    <path d="M19 15l.75 2.25L22 18l-2.25.75L19 21l-.75-2.25L16 18l2.25-.75L19 15z" />
  </svg>
)

const IconCheck = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12" />
  </svg>
)

const IconError = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="8" x2="12" y2="12" />
    <line x1="12" y1="16" x2="12.01" y2="16" />
  </svg>
)

const IconChevron = ({ open }: { open: boolean }) => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    style={{ transform: open ? 'rotate(180deg)' : 'rotate(0)', transition: 'transform 0.2s' }}
  >
    <polyline points="6 9 12 15 18 9" />
  </svg>
)

// ─────────────────────────────────────────────────────────────
// Main App
// ─────────────────────────────────────────────────────────────

function App() {
  const [file, setFile] = useState<File | null>(null)
  const [query, setQuery] = useState<string>(DEFAULT_QUERY)
  const [dossierType, setDossierType] = useState<string>('Accident de la route')
  const [motifExpertise, setMotifExpertise] = useState<string>(
    'Chiffrage des préjudices corporels'
  )

  const [extract, setExtract] = useState<StepState<ExtractResponse>>({ status: 'idle' })
  const [anon, setAnon] = useState<StepState<AnonResponse[]>>({ status: 'idle' })
  const [rag, setRag] = useState<StepState<RagFullResponse>>({ status: 'idle' })

  const isRunning =
    extract.status === 'running' || anon.status === 'running' || rag.status === 'running'

  function reset() {
    setExtract({ status: 'idle' })
    setAnon({ status: 'idle' })
    setRag({ status: 'idle' })
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!file) return
    reset()

    setExtract({ status: 'running' })
    let extractData: ExtractResponse
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await fetch('/api/extract', { method: 'POST', body: formData })
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`)
      extractData = (await res.json()) as ExtractResponse
      setExtract({ status: 'success', data: extractData })
    } catch (err) {
      setExtract({ status: 'error', error: (err as Error).message })
      return
    }

    setAnon({ status: 'running' })
    const anonResults: AnonResponse[] = []
    try {
      for (const page of extractData.document.pages) {
        const payload = {
          raw_text: page.text,
          metadata: {
            document_id: extractData.document.doc_id,
            page_number: page.page_number,
          },
        }
        const res = await fetch(`/api/rag/process?liasse_id=${LIASSE_ID}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
        if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`)
        anonResults.push((await res.json()) as AnonResponse)
      }
      setAnon({ status: 'success', data: anonResults })
    } catch (err) {
      setAnon({ status: 'error', error: (err as Error).message })
      return
    }

    setRag({ status: 'running' })
    try {
      const payload = {
        document_id: extractData.document.doc_id,
        query: query.trim() || DEFAULT_QUERY,
        dossier_type: dossierType,
        motif_expertise: motifExpertise,
      }
      const res = await fetch(`/api/rag/process/full?liasse_id=${LIASSE_ID}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`)
      setRag({ status: 'success', data: (await res.json()) as RagFullResponse })
    } catch (err) {
      setRag({ status: 'error', error: (err as Error).message })
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <div className="logo-mark">S</div>
            <div>
              <h1>SmartSoon</h1>
              <p className="subtitle">Assistant IA · Expertise médicale</p>
            </div>
          </div>
        </div>
      </header>

      <main className="main">
        <aside className="sidebar">
          <form onSubmit={handleSubmit} className="upload-form">
            <div className="form-section">
              <h2 className="form-title">Document à analyser</h2>
              <p className="form-hint">PDF ou image (jpg, png)</p>

              <label htmlFor="file" className={`file-drop ${file ? 'has-file' : ''}`}>
                <input
                  id="file"
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg"
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                  disabled={isRunning}
                />
                <div className="file-drop-inner">
                  <IconUpload />
                  {file ? (
                    <>
                      <span className="file-name">{file.name}</span>
                      <span className="file-size">{(file.size / 1024).toFixed(1)} Ko</span>
                    </>
                  ) : (
                    <>
                      <span className="file-name">Choisir un fichier</span>
                      <span className="file-size">ou glisser-déposer</span>
                    </>
                  )}
                </div>
              </label>
            </div>

            <div className="form-section">
              <h2 className="form-title">Paramètres d'expertise</h2>

              <div className="form-group">
                <label htmlFor="dossier">Type de dossier</label>
                <input
                  id="dossier"
                  type="text"
                  value={dossierType}
                  onChange={(e) => setDossierType(e.target.value)}
                  disabled={isRunning}
                />
              </div>

              <div className="form-group">
                <label htmlFor="motif">Motif d'expertise</label>
                <input
                  id="motif"
                  type="text"
                  value={motifExpertise}
                  onChange={(e) => setMotifExpertise(e.target.value)}
                  disabled={isRunning}
                />
              </div>

              <div className="form-group">
                <label htmlFor="query">Question pour l'IA</label>
                <textarea
                  id="query"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  disabled={isRunning}
                  rows={3}
                />
              </div>
            </div>

            <button type="submit" className="submit-btn" disabled={!file || isRunning}>
              {isRunning ? (
                <>
                  <span className="spinner" />
                  <span>Traitement en cours…</span>
                </>
              ) : (
                <>
                  <IconSparkles />
                  <span>Lancer le pipeline</span>
                </>
              )}
            </button>
          </form>
        </aside>

        <section className="results">
          <div className="results-header">
            <h2>Pipeline de traitement</h2>
            <p className="results-subtitle">
              Suivez chaque étape en temps réel. Chaque bloc peut être déplié pour voir la réponse JSON complète.
            </p>
          </div>

          <StepBlock
            step={1}
            title="Extraction OCR"
            description="Tesseract extrait le texte du document (fallback Surya si confiance faible)"
            icon={<IconOCR />}
            state={extract}
          >
            {extract.status === 'success' && extract.data && (
              <div className="step-summary">
                <SummaryItem label="Moteur" value={extract.data.document.ocr_engine} />
                <SummaryItem
                  label="Type"
                  value={extract.data.document.doc_type.replace('_', ' ')}
                />
                <SummaryItem
                  label="Confiance"
                  value={`${(extract.data.document.ocr_confidence * 100).toFixed(1)} %`}
                />
                <SummaryItem
                  label="Pages"
                  value={extract.data.document.page_count.toString()}
                />
              </div>
            )}
          </StepBlock>

          <StepBlock
            step={2}
            title="Anonymisation"
            description="Presidio remplace les données sensibles (noms, dates, NIR, etc.)"
            icon={<IconShield />}
            state={anon}
          >
            {anon.status === 'success' && anon.data && (
              <div className="step-summary">
                <SummaryItem label="Pages traitées" value={anon.data.length.toString()} />
                <SummaryItem
                  label="Chunks indexés"
                  value={anon.data.reduce((sum, r) => sum + r.chunks, 0).toString()}
                />
              </div>
            )}
          </StepBlock>

          <StepBlock
            step={3}
            title="Synthèse Mistral"
            description="Génération du rapport d'expertise via RAG"
            icon={<IconSparkles />}
            state={rag}
          />

          {extract.status === 'idle' && (
            <div className="empty-state">
              <p>Sélectionnez un document et lancez le pipeline pour commencer.</p>
            </div>
          )}
        </section>
      </main>

      <footer className="footer">
        <span>EFREI ING2 · 2025-2026 · Partenaire SOON Expertise</span>
      </footer>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────

function SummaryItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="summary-item">
      <span className="summary-label">{label}</span>
      <span className="summary-value">{value}</span>
    </div>
  )
}

interface StepBlockProps<T> {
  step: number
  title: string
  description: string
  icon: React.ReactNode
  state: StepState<T>
  children?: React.ReactNode
}

function StepBlock<T>({ step, title, description, icon, state, children }: StepBlockProps<T>) {
  const [expanded, setExpanded] = useState(false)

  const statusIcon =
    state.status === 'success' ? (
      <IconCheck />
    ) : state.status === 'error' ? (
      <IconError />
    ) : state.status === 'running' ? (
      <span className="spinner" />
    ) : null

  const statusText = {
    idle: 'En attente',
    running: 'En cours',
    success: 'Terminé',
    error: 'Erreur',
  }[state.status]

  return (
    <div className={`step-block step-${state.status}`}>
      <div className="step-main">
        <div className="step-number">{String(step).padStart(2, '0')}</div>

        <div className="step-icon">{icon}</div>

        <div className="step-content">
          <div className="step-header">
            <div>
              <h3 className="step-title">{title}</h3>
              <p className="step-description">{description}</p>
            </div>
            <div className={`step-status status-${state.status}`}>
              {statusIcon}
              <span>{statusText}</span>
            </div>
          </div>

          {state.status === 'error' && (
            <div className="error-box">
              <IconError />
              <div>
                <strong>Une erreur est survenue</strong>
                <p>{state.error}</p>
              </div>
            </div>
          )}

          {state.status === 'success' && children}

          {state.status === 'success' && state.data && (
            <>
              <button
                className="toggle-btn"
                onClick={() => setExpanded(!expanded)}
                type="button"
              >
                <IconChevron open={expanded} />
                <span>{expanded ? 'Masquer la réponse JSON' : 'Voir la réponse JSON'}</span>
              </button>
              {expanded && (
                <pre className="json-output">
                  {JSON.stringify(state.data, null, 2)}
                </pre>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default App