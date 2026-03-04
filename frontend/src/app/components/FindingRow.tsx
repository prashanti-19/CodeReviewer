import { useState } from 'react';
import { ChevronDown, ChevronRight, AlertTriangle, AlertCircle, Info, AlertOctagon } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Finding } from '../types/analysis';

interface FindingRowProps {
  finding: Finding;
}

const severityConfig = {
  critical: { color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200', icon: AlertOctagon },
  high: { color: 'text-orange-600', bg: 'bg-orange-50', border: 'border-orange-200', icon: AlertTriangle },
  medium: { color: 'text-yellow-600', bg: 'bg-yellow-50', border: 'border-yellow-200', icon: AlertCircle },
  low: { color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-200', icon: Info },
};

const categoryConfig = {
  'security': { color: 'text-red-700', bg: 'bg-red-100', label: 'Security' },
  'code-smell': { color: 'text-purple-700', bg: 'bg-purple-100', label: 'Code Smell' },
  'maintainability': { color: 'text-orange-700', bg: 'bg-orange-100', label: 'Maintainability' },
  'readability': { color: 'text-blue-700', bg: 'bg-blue-100', label: 'Readability' },
};

export function FindingRow({ finding }: FindingRowProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const severityStyle = severityConfig[finding.severity];
  const categoryStyle = categoryConfig[finding.category];
  const SeverityIcon = severityStyle.icon;

  // Detect language from file extension
  const getLanguage = (filename: string): string => {
    const ext = filename.split('.').pop()?.toLowerCase();
    const langMap: Record<string, string> = {
      'py': 'python',
      'js': 'javascript',
      'jsx': 'jsx',
      'ts': 'typescript',
      'tsx': 'tsx',
      'java': 'java',
      'go': 'go',
      'rb': 'ruby',
      'php': 'php',
      'cs': 'csharp',
      'cpp': 'cpp',
      'c': 'c',
    };
    return langMap[ext || ''] || 'text';
  };

  return (
    <div className={`border rounded-lg overflow-hidden ${severityStyle.border} bg-white`}>
      {/* Header - Always Visible */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 text-left hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-start gap-4">
          {/* Expand Icon */}
          <div className="mt-1">
            {isExpanded ? (
              <ChevronDown className="h-5 w-5 text-gray-400" />
            ) : (
              <ChevronRight className="h-5 w-5 text-gray-400" />
            )}
          </div>

          {/* Severity Icon */}
          <div className={`mt-1 ${severityStyle.color}`}>
            <SeverityIcon className="h-5 w-5" />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <h3 className="font-semibold text-gray-900">{finding.title}</h3>
              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${categoryStyle.bg} ${categoryStyle.color}`}>
                {categoryStyle.label}
              </span>
              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${severityStyle.bg} ${severityStyle.color} capitalize`}>
                {finding.severity}
              </span>
            </div>

            <div className="flex items-center gap-4 text-sm text-gray-600 mb-1">
              <span className="font-mono">{finding.file}</span>
              <span>Lines {finding.line_start}–{finding.line_end}</span>
            </div>

            {!isExpanded && (
              <p className="text-sm text-gray-600 line-clamp-2">
                {finding.description}
              </p>
            )}
          </div>
        </div>
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-gray-200 p-4 bg-gray-50">
          {/* Description */}
          <div className="mb-4">
            <h4 className="text-sm font-semibold text-gray-900 mb-2">Description</h4>
            <p className="text-sm text-gray-700 leading-relaxed">{finding.description}</p>
          </div>

          {/* Code Snippet */}
          <div className="mb-4">
            <h4 className="text-sm font-semibold text-gray-900 mb-2">Code Snippet</h4>
            <div className="rounded-lg overflow-hidden border border-gray-300">
              <SyntaxHighlighter
                language={getLanguage(finding.file)}
                style={vscDarkPlus}
                showLineNumbers
                startingLineNumber={finding.line_start}
                customStyle={{
                  margin: 0,
                  fontSize: '0.875rem',
                }}
                wrapLines
                lineProps={(lineNumber) => {
                  const isHighlighted = lineNumber >= finding.line_start && lineNumber <= finding.line_end;
                  return {
                    style: {
                      backgroundColor: isHighlighted ? 'rgba(255, 200, 0, 0.15)' : 'transparent',
                      display: 'block',
                      width: '100%',
                    }
                  };
                }}
              >
                {finding.snippet}
              </SyntaxHighlighter>
            </div>
          </div>

          {/* Rule Info */}
          <div className="text-xs text-gray-500">
            <span className="font-semibold">Rule:</span> {finding.rule}
          </div>
        </div>
      )}
    </div>
  );
}
