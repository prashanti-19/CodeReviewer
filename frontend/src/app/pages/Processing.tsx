import { useParams } from 'react-router';
import { ProcessingStatus } from '../components/ProcessingStatus';

export function Processing() {
  const { jobId } = useParams<{ jobId: string }>();

  if (!jobId) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Invalid Job ID</h2>
          <p className="text-gray-600">Please start a new analysis.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 py-12 px-4">
      <ProcessingStatus jobId={jobId} />
    </div>
  );
}
