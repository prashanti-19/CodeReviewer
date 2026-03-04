import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { getJobStatus } from '../services/api';
import { JobStatus } from '../types/analysis';

interface ProcessingStatusProps {
  jobId: string;
}

export function ProcessingStatus({ jobId }: ProcessingStatusProps) {
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    let pollInterval: number;

    const pollStatus = async () => {
      try {
        const statusData = await getJobStatus(jobId);
        setStatus(statusData);

        if (statusData.status === 'completed') {
          clearInterval(pollInterval);
          // Navigate to results after a brief delay
          setTimeout(() => {
            navigate(`/results/${jobId}`);
          }, 1000);
        } else if (statusData.status === 'failed') {
          clearInterval(pollInterval);
          setError('Analysis failed. Please try again.');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to get status');
        clearInterval(pollInterval);
      }
    };

    // Poll immediately, then every 2 seconds
    pollStatus();
    pollInterval = window.setInterval(pollStatus, 2000);

    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [jobId, navigate]);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
        <AlertCircle className="h-16 w-16 text-red-500 mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Analysis Failed</h2>
        <p className="text-gray-600">{error}</p>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  const isComplete = status.status === 'completed';

  return (
    <div className="max-w-2xl mx-auto p-8">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="flex flex-col items-center">
          {isComplete ? (
            <CheckCircle2 className="h-16 w-16 text-green-500 mb-4" />
          ) : (
            <Loader2 className="h-16 w-16 text-blue-500 mb-4 animate-spin" />
          )}

          <h2 className="text-2xl font-semibold text-gray-900 mb-2">
            {isComplete ? 'Analysis Complete!' : 'Analyzing Your Code'}
          </h2>
          <p className="text-gray-600 mb-6">{status.message}</p>

          {/* Progress Bar */}
          <div className="w-full mb-6">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>Progress</span>
              <span>{Math.round(status.progress)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="bg-blue-500 h-3 rounded-full transition-all duration-500"
                style={{ width: `${status.progress}%` }}
              />
            </div>
          </div>

          {/* File Processing Status */}
          {status.files_processed !== undefined && status.total_files !== undefined && (
            <div className="text-sm text-gray-600">
              Processing file {status.files_processed} of {status.total_files}
            </div>
          )}

          {/* Job ID */}
          <div className="mt-6 text-xs text-gray-400 font-mono">
            Job ID: {status.job_id}
          </div>
        </div>
      </div>
    </div>
  );
}
