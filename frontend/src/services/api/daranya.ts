// Mock Data for Daranya's Module
const MOCK_DELAY = 600; // Simulate network latency

const mockHistory = [
  {
    verification_id: "ver-001",
    model: "gemini-1.5-pro",
    response_preview: "Climate change is significantly accelerating sea level rise in coastal regions...",
    timestamp: "2026-09-14T10:30:00Z",
    verdict: "SUPPORTED",
    confidence: 0.94,
    claim_count: 3,
    source_count: 5
  },
  {
    verification_id: "ver-002",
    model: "gpt-4o",
    response_preview: "Drinking 8 glasses of water a day will cure all modern diseases...",
    timestamp: "2026-09-13T14:15:00Z",
    verdict: "CONTRADICTED",
    confidence: 0.88,
    claim_count: 1,
    source_count: 2
  },
  {
    verification_id: "ver-003",
    model: "claude-3-opus",
    response_preview: "The global economy is projected to grow by 2.4% next year according to the IMF.",
    timestamp: "2026-09-12T09:45:00Z",
    verdict: "NEUTRAL",
    confidence: 0.72,
    claim_count: 2,
    source_count: 4
  }
];

const mockAuditEvents = [
  { id: "evt-01", verification_id: "ver-001", stage: "verification", status: "started", timestamp: "2026-09-14T10:29:50Z", metadata: { claim: "Climate change is significantly..." } },
  { id: "evt-02", verification_id: "ver-001", stage: "engine_processing", status: "started", timestamp: "2026-09-14T10:29:51Z" },
  { id: "evt-03", verification_id: "ver-001", stage: "claim_extraction", status: "success", timestamp: "2026-09-14T10:29:54Z", metadata: { claims_found: 3 } },
  { id: "evt-04", verification_id: "ver-001", stage: "source_retrieval", status: "success", timestamp: "2026-09-14T10:29:57Z", metadata: { sources_found: 5 } },
  { id: "evt-05", verification_id: "ver-001", stage: "engine_processing", status: "success", timestamp: "2026-09-14T10:30:00Z" },
  { id: "evt-06", verification_id: "ver-001", stage: "verification", status: "completed", timestamp: "2026-09-14T10:30:00Z" }
];

const mockProvenance = {
  claim_id: "clm-101",
  claim_text: "Climate change is significantly accelerating sea level rise.",
  verdict: "SUPPORTED",
  confidence: 0.94,
  decision_basis: "Multiple highly credible sources explicitly confirm that global warming contributes directly to rising sea levels via ice melt and thermal expansion.",
  evidence: [
    {
      source_title: "NASA Global Climate Change",
      source_url: "https://climate.nasa.gov/vital-signs/sea-level/",
      source_quality: 0.98,
      relevance: 0.95,
      verdict: "SUPPORTED",
      confidence: 0.99,
      decision_basis: "Directly states that sea levels are rising as a result of human-caused global warming."
    },
    {
      source_title: "NOAA Climate.gov",
      source_url: "https://www.climate.gov/news-features/understanding-climate/climate-change-global-sea-level",
      source_quality: 0.97,
      relevance: 0.92,
      verdict: "SUPPORTED",
      confidence: 0.96,
      decision_basis: "Confirms acceleration of sea level rise over the past century."
    }
  ]
};

const mockReports = [
  { id: "rep-001", verification_id: "ver-001", format: "pdf", report_type: "compliance", status: "generated", created_at: "2026-09-14T10:35:00Z" },
  { id: "rep-002", verification_id: "ver-002", format: "json", report_type: "standard", status: "generated", created_at: "2026-09-13T14:20:00Z" }
];

// Helper to simulate API delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// ==========================================
// HISTORY API (Mocked)
// ==========================================

export async function getHistory(page = 1, limit = 20, filters?: any) {
  await delay(MOCK_DELAY);
  return { success: true, data: mockHistory };
}

export async function searchHistory(query: string, page = 1, limit = 20) {
  await delay(MOCK_DELAY);
  const lowerQ = query.toLowerCase();
  const filtered = mockHistory.filter(h => h.response_preview.toLowerCase().includes(lowerQ));
  return { success: true, data: filtered };
}

export async function deleteHistoryItem(verificationId: string) {
  await delay(MOCK_DELAY);
  return { success: true, data: { deleted: true } };
}

export async function clearHistory() {
  await delay(MOCK_DELAY);
  return { success: true, data: { deleted: true } };
}

// ==========================================
// AUDIT API (Mocked)
// ==========================================

export async function getAudit() {
  await delay(MOCK_DELAY);
  return { success: true, data: mockAuditEvents };
}

// ==========================================
// PROVENANCE API (Mocked)
// ==========================================

export async function getClaimProvenance(claimId: string, verificationId: string) {
  await delay(MOCK_DELAY);
  return { success: true, data: mockProvenance };
}

// ==========================================
// REPORTS API (Mocked)
// ==========================================

export async function getReports() {
  await delay(MOCK_DELAY);
  return { success: true, data: mockReports };
}

export async function generateReport(verificationId: string, format: string) {
  await delay(MOCK_DELAY);
  return { success: true, data: { report_id: "rep-new", status: "generated" } };
}

export async function deleteReport(reportId: string) {
  await delay(MOCK_DELAY);
  return { success: true, data: { deleted: true } };
}
