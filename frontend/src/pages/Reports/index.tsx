import React, { useState, useEffect } from 'react';
import { getReports, deleteReport, generateReport, getHistory } from '../../services/api/daranya';
import { FileText, Download, Trash2, FileJson, FileSpreadsheet, PlusCircle, Search } from 'lucide-react';

export default function ReportsView() {
  const [reports, setReports] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedVerif, setSelectedVerif] = useState<string>("");

  const fetchData = async () => {
    try {
      setLoading(true);
      const [repRes, histRes] = await Promise.all([getReports(), getHistory()]);
      if (repRes.success) setReports(repRes.data);
      if (histRes.success) {
        setHistory(histRes.data);
        if (histRes.data.length > 0) setSelectedVerif(histRes.data[0].verification_id);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleGenerate = async () => {
    if (!selectedVerif) return;
    try {
      setGenerating(true);
      await generateReport(selectedVerif, "pdf");
      const repRes = await getReports();
      if (repRes.success) setReports(repRes.data);
    } catch (e) {
      console.error(e);
    } finally {
      setGenerating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm("Delete this report?")) {
      await deleteReport(id);
      const repRes = await getReports();
      if (repRes.success) setReports(repRes.data);
    }
  };

  const getFormatIcon = (format: string) => {
    if (format === 'pdf') return <FileText className="h-6 w-6 text-rose-500" />;
    if (format === 'json') return <FileJson className="h-6 w-6 text-amber-500" />;
    return <FileSpreadsheet className="h-6 w-6 text-emerald-500" />;
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-center mb-8">
        <div className="flex items-center space-x-3 group">
          <div className="p-3 bg-white/40 backdrop-blur-md rounded-xl border border-white/60 shadow-lg shadow-sky-500/10 group-hover:shadow-sky-500/30 group-hover:-translate-y-1 transition-all duration-300">
            <FileText className="h-6 w-6 text-sky-600 animate-pulse" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Compliance Reports</h2>
            <p className="text-sky-700/80 font-medium text-sm mt-0.5">Generate and export structured verification data</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-3 bg-white/30 backdrop-blur-md p-2 rounded-2xl border border-white/50 shadow-sm">
          <div className="flex items-center space-x-2 px-3">
            <Search className="h-4 w-4 text-sky-600" />
            <select 
              value={selectedVerif}
              onChange={(e) => setSelectedVerif(e.target.value)}
              className="bg-transparent text-sm font-semibold text-slate-700 focus:outline-none w-48 truncate cursor-pointer"
            >
              <option value="" disabled>Select a Search</option>
              {history.map(h => (
                <option key={h.verification_id} value={h.verification_id}>
                  {new Date(h.timestamp).toLocaleDateString()} - {h.response_preview.substring(0, 30)}...
                </option>
              ))}
            </select>
          </div>
          
          <button 
            onClick={handleGenerate}
            disabled={generating || !selectedVerif}
            className="flex items-center space-x-2 px-5 py-2.5 bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white text-sm font-bold rounded-xl transition-all duration-300 shadow-lg shadow-sky-500/40 hover:shadow-xl hover:shadow-sky-500/50 hover:-translate-y-1 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {generating ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              <PlusCircle className="h-4 w-4" />
            )}
            <span>{generating ? 'Generating...' : 'New Report'}</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {reports.map((rep) => (
          <div key={rep.id} className="group bg-white/40 backdrop-blur-md border border-white/60 rounded-2xl p-6 shadow-lg shadow-sky-500/5 hover:shadow-2xl hover:shadow-sky-500/20 hover:border-sky-300/50 hover:-translate-y-2 transition-all duration-500 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-40 h-40 bg-gradient-to-bl from-sky-300/40 to-transparent rounded-bl-full -z-10 opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
            
            <div className="flex justify-between items-start mb-6 relative z-10">
              <div className="flex items-center space-x-4">
                <div className="p-3 bg-white/60 backdrop-blur-sm rounded-xl border border-white/80 group-hover:scale-110 group-hover:bg-white group-hover:shadow-lg shadow-sky-500/20 transition-all duration-500">
                  {getFormatIcon(rep.format)}
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wide group-hover:text-sky-700 transition-colors">{rep.format} Report</h3>
                  <p className="text-xs text-slate-600 capitalize font-medium">{rep.report_type}</p>
                </div>
              </div>
              <span className="text-[10px] uppercase font-bold px-2.5 py-1 rounded-full bg-emerald-50/80 text-emerald-700 border border-emerald-200 shadow-sm backdrop-blur-md">
                {rep.status}
              </span>
            </div>

            <div className="mb-5 relative z-10 text-xs text-slate-600 font-medium leading-relaxed bg-white/40 p-3 rounded-xl border border-white/40 shadow-inner">
              <span className="font-bold text-sky-700 block mb-1">Generated for: {rep.verification_id}</span>
              {rep.format === 'pdf' 
                ? "This report contains a comprehensive, human-readable audit of the selected claim including source evidence and confidence metrics." 
                : "A raw data extract containing complete verification metadata, evidence links, and JSON schemas for pipeline ingestion."}
            </div>
            
            <div className="space-y-3 mb-6 relative z-10 bg-white/30 backdrop-blur-sm rounded-xl p-4 border border-white/50 group-hover:bg-white/60 transition-colors duration-500">
              <div className="flex justify-between text-xs">
                <span className="text-slate-500 font-medium">Target ID</span>
                <span className="text-slate-700 font-mono font-semibold">{rep.verification_id}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-500 font-medium">Created On</span>
                <span className="text-slate-700 font-semibold">{new Date(rep.created_at).toLocaleDateString()}</span>
              </div>
            </div>
            
            <div className="flex items-center space-x-3 pt-4 border-t border-white/50 relative z-10">
              <button className="flex-1 flex justify-center items-center space-x-1.5 py-2.5 bg-sky-100/50 hover:bg-sky-500 text-sky-700 hover:text-white rounded-xl text-xs font-bold transition-all duration-300 shadow-sm hover:shadow-lg hover:shadow-sky-500/20">
                <Download className="h-4 w-4" />
                <span>Download</span>
              </button>
              <button 
                onClick={() => handleDelete(rep.id)}
                className="p-2.5 bg-rose-50 hover:bg-rose-600 text-rose-500 hover:text-white rounded-xl transition-all duration-300 shadow-sm hover:shadow-md"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
      
      {!loading && reports.length === 0 && (
        <div className="text-center py-20 border-2 border-dashed border-sky-200/50 bg-white/20 backdrop-blur-md rounded-3xl shadow-xl shadow-sky-500/5">
          <FileText className="h-12 w-12 text-sky-400 mx-auto mb-4 animate-pulse" />
          <h3 className="text-slate-800 font-bold mb-1">No reports generated</h3>
          <p className="text-slate-600 font-medium text-sm">Select a search and click "New Report" to generate compliance data.</p>
        </div>
      )}
    </div>
  );
}
