import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  BookOpen,
  Upload,
  Search,
  FileText,
  Download,
  Trash2,
  X,
  CheckCircle2,
  Clock,
  AlertCircle
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { KnowledgeDocument } from '../types';
import { knowledgeApi } from '../api';
import { BorderGlowButton } from '../components/ui/BorderGlowButton';
import { useTheme } from '../context/ThemeContext';

interface KnowledgeBasePageProps {
  documents: KnowledgeDocument[];
  onAddDocument: (doc: KnowledgeDocument) => void;
  onDeleteDocument: (docId: string) => void;
  theme?: 'light' | 'dark';
}

export const KnowledgeBasePage: React.FC<KnowledgeBasePageProps> = ({
  documents,
  onAddDocument,
  onDeleteDocument,
  theme: propTheme,
}) => {
  const context = useTheme();
  const isDark = (propTheme || context.theme) === 'dark';
  const { documentId } = useParams<{ documentId?: string }>();
  const navigate = useNavigate();

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [newDocName, setNewDocName] = useState('');
  const [newDocCategory, setNewDocCategory] = useState('Internal Governance');
  const [selectedDocForDetails, setSelectedDocForDetails] = useState<KnowledgeDocument | null>(
    documentId ? documents.find(d => d.id === documentId) || null : null
  );

  // Direct /knowledge-base/:documentId links may mount before documents load.
  // Update the open detail panel as soon as the backend list arrives.
  useEffect(() => {
    if (!documentId) return;
    setSelectedDocForDetails(documents.find(d => d.id === documentId) || null);
  }, [documentId, documents]);

  const filteredDocs = documents.filter(doc => {
    const matchesSearch = doc.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (doc.description && doc.description.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesType = selectedType === 'ALL' || doc.type === selectedType;
    const matchesStatus = selectedStatus === 'ALL' || doc.status.toLowerCase() === selectedStatus.toLowerCase();
    return matchesSearch && matchesType && matchesStatus;
  });

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [deletingDocumentId, setDeletingDocumentId] = useState<string | null>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setUploadError(null);
    if (!selectedFile) {
      setUploadError('Choose a file to upload. A title alone cannot be indexed as evidence.');
      return;
    }

    setIsUploading(true);
    try {
      const createdDoc = await knowledgeApi.uploadFile(
        selectedFile, newDocName.trim() || selectedFile.name, newDocCategory
      );
      onAddDocument(createdDoc);
      setNewDocName('');
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      setShowUploadModal(false);
    } catch (err) {
      // Failed uploads must never create invented "Indexed" documents.
      setUploadError(err instanceof Error ? err.message : 'Unable to upload document.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteWithBackend = async (docId: string) => {
    setDeleteError(null);
    setDeletingDocumentId(docId);
    try {
      await knowledgeApi.deleteDocument(docId);
      onDeleteDocument(docId);
      if (selectedDocForDetails?.id === docId) setSelectedDocForDetails(null);
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Unable to delete document.');
    } finally {
      setDeletingDocumentId(null);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6 pb-16"
    >
      {/* Header with high-contrast text for both light and dark themes */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-2xl flex items-center justify-center bg-[#D8F3DC] text-[#1B4332] border border-[#74C69D] dark:bg-[#181A20] dark:text-[#B6FF2E] dark:border-[#333742] dark:shadow-[0_0_15px_rgba(182,255,46,0.15)] shadow-xs transition-colors">
            <BookOpen size={24} />
          </div>
          <div>
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-[#1B4332] dark:text-white transition-colors">
              Knowledge Base
            </h1>
            <p className="text-xs md:text-sm font-medium text-[#356B52] dark:text-slate-300 transition-colors">
              Manage your private documents for verification.
            </p>
          </div>
        </div>

        <BorderGlowButton
          size="md"
          variant="primary"
          onClick={() => setShowUploadModal(true)}
          theme={isDark ? 'dark' : 'light'}
        >
          <Upload size={16} />
          <span>Upload Document</span>
        </BorderGlowButton>
      </div>

      {deleteError && (
        <p role="alert" className="p-3 rounded-xl border border-rose-300 bg-rose-50 text-rose-700 dark:bg-rose-950/30 dark:text-rose-300 text-xs">
          Could not delete document: {deleteError}
        </p>
      )}

      {/* Filter and Search Bar - Fully Dark/Light Styled */}
      <div className="p-4 rounded-2xl border flex flex-col sm:flex-row items-center justify-between gap-3 shadow-xs transition-colors bg-[#FFFFFF] border-[#74C69D] dark:bg-[#23262F] dark:border-[#333742]">
        <div className="relative w-full sm:max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#356B52] dark:text-slate-400" size={16} />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search documents by name or category..."
            className="w-full rounded-xl py-2 pl-9 pr-4 text-xs md:text-sm transition-all outline-none bg-[#D8F3DC] border border-[#74C69D] text-[#1B4332] placeholder-[#356B52] focus:ring-2 focus:ring-[#1B4332]/20 focus:border-[#1B4332] dark:bg-[#181A20] dark:border-[#333742] dark:text-slate-100 dark:placeholder-slate-500 dark:focus:ring-[#B6FF2E]/30 dark:focus:border-[#B6FF2E]"
          />
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="text-xs font-semibold rounded-xl px-3 py-2 outline-none border transition-colors bg-[#D8F3DC] border-[#74C69D] text-[#1B4332] dark:bg-[#181A20] dark:border-[#333742] dark:text-slate-200 cursor-pointer"
          >
            <option value="ALL">All Types</option>
            <option value="PDF">PDF</option>
            <option value="DOCX">DOCX</option>
            <option value="CSV">CSV</option>
          </select>

          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="text-xs font-semibold rounded-xl px-3 py-2 outline-none border transition-colors bg-[#D8F3DC] border-[#74C69D] text-[#1B4332] dark:bg-[#181A20] dark:border-[#333742] dark:text-slate-200 cursor-pointer"
          >
            <option value="ALL">All Status</option>
            <option value="Indexed">Indexed</option>
            <option value="Processing">Processing</option>
            <option value="Failed">Failed</option>
          </select>
        </div>
      </div>

      {/* Document Table Card - Dark/Light Redesigned */}
      <div className="rounded-2xl border shadow-xs overflow-hidden transition-colors bg-[#FFFFFF] border-[#74C69D] dark:bg-[#1E2129] dark:border-[#2E3340]">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b uppercase text-[10px] font-bold tracking-wider border-[#74C69D] dark:border-[#2E3340] bg-[#D8F3DC] dark:bg-[#14161C] text-[#356B52] dark:text-slate-400">
                <th className="py-3 px-5">Name</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Size</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Uploaded</th>
                <th className="py-3 px-5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#D8F3DC] dark:divide-[#2E3340]">
              {filteredDocs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 px-4 text-center">
                    <div className="max-w-sm mx-auto space-y-3">
                      <div className={`w-10 h-10 rounded-xl mx-auto flex items-center justify-center ${
                        isDark ? 'bg-[#14161C] text-slate-400 border border-[#2E3340]' : 'bg-[#D8F3DC] text-[#1B4332] border border-[#74C69D]'
                      }`}>
                        <BookOpen size={20} strokeWidth={2.2} />
                      </div>
                      <div className="space-y-1">
                        <h4 className={`text-sm font-bold ${isDark ? 'text-white' : 'text-[#1B4332]'}`}>
                          No documents in knowledge vault
                        </h4>
                        <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-[#356B52]'}`}>
                          {searchTerm ? 'No documents match your search query.' : 'Upload PDF, DOCX, or text files to ingest verified ground-truth documents.'}
                        </p>
                      </div>
                      {!searchTerm && (
                        <button
                          onClick={() => setShowUploadModal(true)}
                          className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold cursor-pointer transition-all active:scale-95 shadow-xs ${
                            isDark ? 'bg-[#B6FF2E] text-[#12141A] hover:bg-[#A3E823]' : 'bg-[#74C69D] text-[#102D21] hover:bg-[#8FD9B4]'
                          }`}
                        >
                          <Upload size={13} />
                          <span>Upload Document</span>
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ) : (
                filteredDocs.map((doc, idx) => (
                  <motion.tr
                    key={doc.id}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.04 }}
                    onClick={() => setSelectedDocForDetails(doc)}
                    className="transition-colors cursor-pointer group hover:bg-[#D8F3DC] dark:hover:bg-[#14161C]"
                  >
                    <td className="py-3 px-5 font-bold flex items-center gap-3 text-[#1B4332] dark:text-white">
                      <div className="w-8 h-8 rounded-lg flex items-center justify-center transition-colors bg-[#D8F3DC] text-[#1B4332] group-hover:bg-[#1B4332]/10 group-hover:text-[#1B4332] dark:bg-[#14161C] dark:text-slate-400 dark:group-hover:text-[#B6FF2E] dark:group-hover:bg-[#B6FF2E]/10">
                        <FileText size={15} />
                      </div>
                      <span className="truncate max-w-[220px] transition-colors group-hover:text-[#1B4332] dark:group-hover:text-[#B6FF2E]">{doc.name}</span>
                    </td>
                    <td className="py-3 px-4 font-semibold text-[#356B52] dark:text-slate-300">{doc.type}</td>
                    <td className="py-3 px-4 font-mono text-[#356B52] dark:text-slate-400">{doc.size}</td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                        doc.status === 'Indexed'
                          ? 'bg-[#74C69D]/30 text-[#1B4332] border border-[#74C69D] dark:bg-[#B6FF2E]/15 dark:text-[#B6FF2E] dark:border-[#B6FF2E]/30'
                          : doc.status === 'Processing'
                          ? 'bg-amber-50 text-amber-800 border border-amber-200 dark:bg-amber-500/15 dark:text-amber-300 dark:border-amber-500/30'
                          : 'bg-rose-50 text-rose-800 border border-rose-200 dark:bg-rose-500/15 dark:text-rose-300 dark:border-rose-500/30'
                      }`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${
                          doc.status === 'Indexed'
                            ? 'bg-emerald-500 dark:bg-[#B6FF2E]'
                            : doc.status === 'Processing'
                            ? 'bg-amber-500 animate-pulse'
                            : 'bg-rose-500'
                        }`} />
                        <span>{doc.status}</span>
                      </span>
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-500 dark:text-slate-400">{doc.uploadedDate}</td>
                    <td className="py-3 px-5 text-right">
                      <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                        <button
                          title="Download"
                          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 dark:hover:text-[#B6FF2E] dark:hover:bg-[#14161C] transition-colors"
                        >
                          <Download size={14} />
                        </button>
                        <button
                          title="Delete"
                          onClick={() => handleDeleteWithBackend(doc.id)}
                          disabled={deletingDocumentId === doc.id}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:text-rose-400 dark:hover:bg-rose-500/10 transition-colors cursor-pointer"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </motion.tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Strip */}
        {filteredDocs.length > 0 && (
          <div className="p-3.5 border-t flex items-center justify-between text-xs border-[#74C69D] dark:border-[#2E3340] text-[#356B52] dark:text-slate-400 bg-[#D8F3DC]/60 dark:bg-[#14161C]/40">
            <span>Showing {filteredDocs.length} of {documents.length} documents</span>
            <div className="flex items-center gap-1.5">
              {[1].map((page) => (
                <button
                  key={page}
                  className="w-7 h-7 rounded-lg text-xs font-bold transition-all cursor-pointer bg-[#1B4332] text-[#D8F3DC] dark:bg-[#B6FF2E] dark:text-[#181A20] shadow-xs"
                >
                  {page}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Document Detail Inspector Drawer */}
      <AnimatePresence>
        {selectedDocForDetails && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex justify-end">
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 240 }}
              className="w-full max-w-md h-full shadow-2xl p-6 flex flex-col justify-between border-l overflow-y-auto bg-[#FFFFFF] border-[#74C69D] dark:bg-[#23262F] dark:border-[#333742] text-[#1B4332] dark:text-white"
            >
              <div className="space-y-5">
                <div className="flex items-center justify-between pb-3 border-b border-[#74C69D] dark:border-[#333742]">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-[#D8F3DC] text-[#1B4332] border border-[#74C69D] dark:bg-[#181A20] dark:text-[#B6FF2E] dark:border dark:border-[#B6FF2E]/30">
                      <FileText size={18} />
                    </div>
                    <div>
                      <h3 className="font-extrabold text-sm truncate max-w-[240px] text-[#1B4332] dark:text-white">
                        {selectedDocForDetails.name}
                      </h3>
                      <span className="text-[10px] text-[#356B52]">Document Inspector</span>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedDocForDetails(null)}
                    className="w-8 h-8 rounded-lg flex items-center justify-center bg-[#D8F3DC] hover:bg-[#D8F3DC] text-[#356B52] dark:bg-[#181A20] dark:hover:bg-[#2A2E38] dark:text-slate-300"
                  >
                    <X size={16} />
                  </button>
                </div>

                <div className="space-y-3">
                  <div className="p-4 rounded-2xl border space-y-2 text-xs bg-[#D8F3DC] border-[#74C69D] dark:bg-[#181A20] dark:border-[#333742]">
                    <div className="flex justify-between">
                      <span className="text-[#356B52]">Indexing Status</span>
                      <span className="font-bold text-[#1B4332] dark:text-[#B6FF2E]">{selectedDocForDetails.status}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#356B52]">Vector Chunks</span>
                      <span className="font-bold font-mono text-[#1B4332] dark:text-white">{selectedDocForDetails.chunksCount ?? 0} chunks</span>
                    </div>
                    {selectedDocForDetails.reliabilityScore != null && (
                      <div className="flex justify-between">
                        <span className="text-[#356B52]">Reliability Weight</span>
                        <span className="font-bold font-mono text-[#1B4332] dark:text-[#B6FF2E]">{selectedDocForDetails.reliabilityScore}%</span>
                      </div>
                    )}
                  </div>

                  <div>
                    <label className="text-[11px] font-bold uppercase tracking-wider block mb-1 text-[#356B52] dark:text-slate-400">
                      Description & Provenance
                    </label>
                    <p className="text-xs leading-relaxed p-3.5 rounded-xl border bg-[#D8F3DC] border-[#74C69D] text-[#1B4332] dark:bg-[#181A20] dark:border-[#333742] dark:text-slate-200">
                      {selectedDocForDetails.description || 'No description provided.'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-[#74C69D] dark:border-[#333742] flex gap-2">
                <button
                  onClick={() => setSelectedDocForDetails(null)}
                  className="w-full py-2.5 rounded-xl text-xs font-bold transition-colors cursor-pointer bg-[#D8F3DC] hover:bg-[#D8F3DC] text-[#1B4332] dark:bg-[#181A20] dark:hover:bg-[#2A2E38] dark:text-slate-200"
                >
                  Close Inspector
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Upload Document Modal */}
      <AnimatePresence>
        {showUploadModal && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="rounded-2xl w-full max-w-lg p-5 sm:p-6 border shadow-2xl space-y-4 bg-[#FFFFFF] border-[#74C69D] dark:bg-[#1E2129] dark:border-[#2E3340] text-[#1B4332] dark:text-white"
            >
              <div className="flex items-center justify-between pb-3 border-b border-[#74C69D] dark:border-[#333742]">
                <h3 className="font-extrabold text-base text-[#1B4332] dark:text-white">Upload Ground-Truth Document</h3>
                <button
                  onClick={() => setShowUploadModal(false)}
                  className="w-8 h-8 rounded-lg flex items-center justify-center bg-[#D8F3DC] text-[#356B52] hover:text-[#1B4332] dark:bg-[#181A20] dark:text-slate-400 dark:hover:text-white"
                >
                  <X size={16} />
                </button>
              </div>

              <form onSubmit={handleUploadSubmit} className="space-y-4 text-xs">
                {uploadError && (
                  <p role="alert" className="p-3 rounded-lg border border-rose-300 bg-rose-50 text-rose-700 dark:bg-rose-950/30 dark:text-rose-300">
                    Upload failed: {uploadError}
                  </p>
                )}
                <div>
                  <label className="font-bold block mb-1 text-[#1B4332] dark:text-slate-300">Document Title / File Name</label>
                  <input
                    type="text"
                    required
                    value={newDocName}
                    onChange={(e) => setNewDocName(e.target.value)}
                    placeholder="e.g. Clinical Trial Evaluation 2026.pdf"
                    className="w-full rounded-xl px-3 py-2.5 text-xs outline-none border transition-all bg-[#D8F3DC] border-[#74C69D] text-[#1B4332] focus:ring-1 focus:ring-[#1B4332] dark:bg-[#181A20] dark:border-[#333742] dark:text-white dark:focus:border-[#B6FF2E]"
                  />
                </div>

                <div>
                  <label className="font-bold block mb-1 text-[#1B4332] dark:text-slate-300">Category Classification</label>
                  <select
                    value={newDocCategory}
                    onChange={(e) => setNewDocCategory(e.target.value)}
                    className="w-full rounded-xl px-3 py-2.5 text-xs font-semibold outline-none border transition-all bg-[#D8F3DC] border-[#74C69D] text-[#1B4332] dark:bg-[#181A20] dark:border-[#333742] dark:text-white cursor-pointer"
                  >
                    <option value="Internal Governance">Internal Governance</option>
                    <option value="Academic Research">Academic Research</option>
                    <option value="Technical Specs">Technical Specs</option>
                    <option value="Raw Empirical Data">Raw Empirical Data</option>
                  </select>
                </div>

                <input
                  type="file"
                  ref={fileInputRef}
                  className="hidden"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      const f = e.target.files[0];
                      setSelectedFile(f);
                      if (!newDocName) setNewDocName(f.name);
                    }
                  }}
                />

                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="p-6 border-2 border-dashed rounded-2xl text-center space-y-1 bg-[#D8F3DC]/50 border-[#74C69D] dark:bg-[#181A20]/50 dark:border-[#333742] cursor-pointer hover:border-[#1B4332] dark:hover:border-[#B6FF2E] transition-colors"
                >
                  <Upload size={24} className="mx-auto text-[#356B52] dark:text-slate-400" />
                  <p className="font-bold text-[#1B4332] dark:text-slate-200">
                    {selectedFile ? `Selected: ${selectedFile.name}` : 'Drag and drop file here, or browse'}
                  </p>
                  <p className="text-[11px] text-[#356B52] dark:text-slate-400">PDF, DOCX, CSV, or TXT up to 25MB</p>
                </div>

                <div className="flex justify-end gap-2.5 pt-2 border-t border-[#74C69D] dark:border-[#333742]">
                  <button
                    type="button"
                    onClick={() => setShowUploadModal(false)}
                    className="px-4 py-2 rounded-xl font-bold transition-colors cursor-pointer text-[#356B52] hover:bg-[#D8F3DC] dark:text-slate-300 dark:hover:bg-[#181A20]"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isUploading}
                    className="px-5 py-2 rounded-xl font-bold shadow-xs cursor-pointer transition-all active:scale-95 bg-[#1B4332] hover:bg-[#163E2D] text-[#D8F3DC] dark:bg-[#B6FF2E] dark:hover:bg-[#A3E823] dark:text-[#181A20] dark:font-black disabled:opacity-50"
                  >
                    {isUploading ? 'Uploading...' : 'Upload & Index'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};
export default KnowledgeBasePage;
