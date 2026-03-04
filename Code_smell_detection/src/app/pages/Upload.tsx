import { useState } from 'react';
import { useNavigate } from 'react-router';
import { ArrowRight, Code2 } from 'lucide-react';
import { UploadZone } from '../components/UploadZone';
import { uploadFiles } from '../services/api';
import { toast } from 'sonner';

export function Upload() {
  const [files, setFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const navigate = useNavigate();

  const handleAnalyze = async () => {
    if (files.length === 0) {
      toast.error('Please select at least one file to analyze');
      return;
    }

    setIsUploading(true);
    try {
      const response = await uploadFiles(files);
      toast.success('Files uploaded successfully!');
      navigate(`/processing/${response.job_id}`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Upload failed');
      setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-4">
            <div className="bg-blue-600 p-3 rounded-xl">
              <Code2 className="h-8 w-8 text-white" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-3">
            Code Quality Analysis Platform
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Upload your code files to receive detailed insights on security vulnerabilities,
            code smells, maintainability issues, and readability improvements.
          </p>
        </div>

        {/* Upload Zone */}
        <div className="mb-8">
          <UploadZone files={files} onFilesChange={setFiles} />
        </div>

        {/* Action Button */}
        {files.length > 0 && (
          <div className="flex justify-center">
            <button
              onClick={handleAnalyze}
              disabled={isUploading}
              className="inline-flex items-center gap-2 px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isUploading ? 'Uploading...' : 'Analyze Code'}
              <ArrowRight className="h-5 w-5" />
            </button>
          </div>
        )}

        {/* Info Cards */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <div className="text-red-600 font-semibold mb-2">Security</div>
            <p className="text-sm text-gray-600">
              Detect SQL injection, XSS, hardcoded credentials, and crypto weaknesses
            </p>
          </div>
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <div className="text-purple-600 font-semibold mb-2">Code Smells</div>
            <p className="text-sm text-gray-600">
              Identify duplicated code, god classes, long methods, and anti-patterns
            </p>
          </div>
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <div className="text-orange-600 font-semibold mb-2">Maintainability</div>
            <p className="text-sm text-gray-600">
              Find high complexity, deep nesting, magic numbers, and unused code
            </p>
          </div>
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <div className="text-blue-600 font-semibold mb-2">Readability</div>
            <p className="text-sm text-gray-600">
              Spot unclear naming, missing docs, long lines, and inconsistent style
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
