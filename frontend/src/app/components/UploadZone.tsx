import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileCode, X } from 'lucide-react';

interface UploadZoneProps {
  files: File[];
  onFilesChange: (files: File[]) => void;
}

export function UploadZone({ files, onFilesChange }: UploadZoneProps) {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    onFilesChange([...files, ...acceptedFiles]);
  }, [files, onFilesChange]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/x-python': ['.py'],
      'text/javascript': ['.js'],
      'text/typescript': ['.ts', '.tsx'],
      'text/x-java': ['.java'],
      'text/x-go': ['.go'],
      'text/x-ruby': ['.rb'],
      'text/x-php': ['.php'],
      'text/x-csharp': ['.cs'],
      'text/x-c++': ['.cpp', '.cc', '.h'],
      'text/jsx': ['.jsx'],
    },
    maxSize: 50 * 1024 * 1024, // 50MB per file
  });

  const removeFile = (index: number) => {
    const newFiles = files.filter((_, i) => i !== index);
    onFilesChange(newFiles);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
          transition-colors duration-200
          ${isDragActive 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-gray-300 hover:border-gray-400 bg-gray-50'
          }
        `}
      >
        <input {...getInputProps()} />
        <Upload className={`mx-auto h-12 w-12 mb-4 ${isDragActive ? 'text-blue-500' : 'text-gray-400'}`} />
        <p className="text-lg mb-2">
          {isDragActive ? 'Drop your code files here' : 'Drag & drop code files here'}
        </p>
        <p className="text-sm text-gray-500">
          or click to browse • Supports .py, .js, .ts, .java, .go, .rb, .php, .cs and more
        </p>
        <p className="text-xs text-gray-400 mt-2">
          Maximum 50MB per file
        </p>
      </div>

      {files.length > 0 && (
        <div className="mt-6 space-y-2">
          <h3 className="font-medium text-sm text-gray-700 mb-3">
            Selected Files ({files.length})
          </h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {files.map((file, index) => (
              <div
                key={`${file.name}-${index}`}
                className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg"
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <FileCode className="h-5 w-5 text-blue-500 flex-shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {file.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatFileSize(file.size)}
                    </p>
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(index);
                  }}
                  className="ml-4 p-1 hover:bg-gray-100 rounded transition-colors"
                  aria-label="Remove file"
                >
                  <X className="h-4 w-4 text-gray-500" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
