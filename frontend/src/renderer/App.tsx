import React, { useEffect, useState } from 'react';
import { Activity, Cpu, HardDrive } from 'lucide-react';

interface GPUInfo {
  id: number;
  name: string;
  vram_total_mb: number;
  vram_free_mb: number;
}

interface Diagnostics {
  ram_total_gb: number;
  ram_available_gb: number;
  gpus: GPUInfo[];
  recommendation: string;
  can_run_local_llm: boolean;
}

export default function App() {
  const [diagnostics, setDiagnostics] = useState<Diagnostics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/diagnostics')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch diagnostics');
        return res.json();
      })
      .then((data) => {
        setDiagnostics(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 p-8 font-sans">
      <div className="max-w-4xl mx-auto">
        <header className="mb-12 text-center">
          <h1 className="text-4xl font-bold text-slate-900 mb-4">Kairos Setup</h1>
          <p className="text-lg text-slate-600">Running system diagnostics to determine AI compatibility...</p>
        </header>

        {loading && (
          <div className="flex justify-center items-center p-12">
            <Activity className="animate-spin text-blue-500 w-12 h-12" />
          </div>
        )}

        {error && (
          <div className="bg-red-50 text-red-700 p-6 rounded-xl border border-red-200">
            <p className="font-semibold">Error connecting to backend:</p>
            <p>{error}</p>
            <p className="mt-4 text-sm">Make sure the FastAPI server is running on port 8000.</p>
          </div>
        )}

        {diagnostics && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
                <div className="flex items-center gap-3 mb-4 text-slate-700">
                  <HardDrive className="w-6 h-6" />
                  <h2 className="text-xl font-semibold">System Memory (RAM)</h2>
                </div>
                <p className="text-3xl font-bold text-slate-900">{diagnostics.ram_total_gb} GB</p>
                <p className="text-sm text-slate-500 mt-1">Total System RAM</p>
              </div>

              <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
                <div className="flex items-center gap-3 mb-4 text-slate-700">
                  <Cpu className="w-6 h-6" />
                  <h2 className="text-xl font-semibold">Graphics Processing (GPU)</h2>
                </div>
                {diagnostics.gpus.length > 0 ? (
                  diagnostics.gpus.map((gpu) => (
                    <div key={gpu.id} className="mb-4 last:mb-0">
                      <p className="text-lg font-medium text-slate-900">{gpu.name}</p>
                      <p className="text-sm text-slate-500">{(gpu.vram_total_mb / 1024).toFixed(1)} GB VRAM</p>
                    </div>
                  ))
                ) : (
                  <p className="text-lg font-medium text-slate-500">No Dedicated GPU Detected</p>
                )}
              </div>
            </div>

            <div className={`p-8 rounded-2xl border ${diagnostics.can_run_local_llm ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-blue-50 border-blue-200 text-blue-900'}`}>
              <h3 className="text-2xl font-bold mb-3">Recommendation</h3>
              <p className="text-lg">{diagnostics.recommendation}</p>
              <div className="mt-4 pt-4 border-t border-slate-200/50">
                <p className="text-sm opacity-80 font-medium">
                  System Requirements for Local AI (Llama 3 8B):
                </p>
                <p className="text-sm opacity-70 mt-1">
                  Requires &gt; 15GB of System RAM <strong>OR</strong> a Dedicated GPU with &gt; 6GB VRAM.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
