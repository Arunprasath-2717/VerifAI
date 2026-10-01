import React, { useState, useEffect } from 'react';
import { getAudit } from '../../services/api/daranya';
import { CheckCircle2, Clock, ShieldAlert, Activity, PlayCircle } from 'lucide-react';

export default function AuditView() {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchAudit() {
      try {
        const res = await getAudit();
        if (res.success) setEvents(res.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    fetchAudit();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  const getIcon = (status: string, stage: string) => {
    if (status === 'started') return <PlayCircle className="h-5 w-5 text-sky-500" />;
    if (status === 'error') return <ShieldAlert className="h-5 w-5 text-rose-500" />;
    if (stage === 'verification' && status === 'completed') return <CheckCircle2 className="h-5 w-5 text-emerald-500" />;
    return <CheckCircle2 className="h-5 w-5 text-indigo-500" />;
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center space-x-3 mb-8 group">
        <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-sm group-hover:shadow-md group-hover:-translate-y-0.5 transition-all duration-300">
          <Activity className="h-6 w-6 text-emerald-500" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">System Audit Log</h2>
          <p className="text-slate-500 text-sm mt-0.5">Chronological lifecycle trace of all engine actions</p>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl p-8 shadow-sm">
        <div className="relative border-l-2 border-slate-200 ml-4 space-y-8">
          {events.map((evt, idx) => (
            <div key={evt.id || idx} className="relative pl-8 group">
              <span className="absolute -left-[11px] top-1 bg-white border border-slate-200 rounded-full p-0.5 shadow-sm group-hover:scale-125 group-hover:shadow-md transition-all duration-300">
                {getIcon(evt.status, evt.stage)}
              </span>
              
              <div className="bg-slate-50 border border-slate-100 rounded-xl p-5 hover:bg-white hover:border-slate-300 hover:shadow-lg transition-all duration-300 shadow-sm relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/50 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
                
                <div className="flex justify-between items-start mb-3 relative z-10">
                  <div className="flex items-center space-x-3">
                    <span className="text-sm font-bold text-slate-800 capitalize tracking-wide group-hover:text-indigo-600 transition-colors">
                      {evt.stage.replace('_', ' ')}
                    </span>
                    <span className={`text-[10px] uppercase font-bold px-2.5 py-1 rounded-full border shadow-sm
                      ${evt.status === 'success' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 
                        evt.status === 'error' ? 'bg-rose-50 text-rose-700 border-rose-200' : 
                        evt.status === 'completed' ? 'bg-purple-50 text-purple-700 border-purple-200' :
                        'bg-sky-50 text-sky-700 border-sky-200'}`}>
                      {evt.status}
                    </span>
                  </div>
                  <div className="flex items-center space-x-1.5 text-xs text-slate-400 font-mono font-medium">
                    <Clock className="h-3.5 w-3.5" />
                    <span>{new Date(evt.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' })}</span>
                  </div>
                </div>
                
                {evt.metadata && (
                  <div className="mt-3 bg-white rounded-lg p-3 border border-slate-200 shadow-inner relative z-10 group-hover:border-indigo-100 transition-colors">
                    <pre className="text-xs text-slate-600 font-mono overflow-x-auto whitespace-pre-wrap">
                      {JSON.stringify(evt.metadata, null, 2)}
                    </pre>
                  </div>
                )}
                
                <div className="mt-4 pt-4 border-t border-slate-200/60 text-xs text-slate-400 font-mono relative z-10">
                  TxID: <span className="text-slate-500">{evt.id}</span> | Ref: <span className="text-slate-500">{evt.verification_id.split('-')[0]}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
