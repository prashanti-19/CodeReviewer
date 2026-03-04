import { useEffect, useState, useMemo } from 'react';
import { useParams, Link } from 'react-router';
import { ArrowLeft, Loader2, Download, BarChart3 } from 'lucide-react';
import { getJobResults } from '../services/api';
import { AnalysisResults, Category, Severity, Finding } from '../types/analysis';
import { SummaryCards } from '../components/SummaryCards';
import { FilterBar } from '../components/FilterBar';
import { FindingRow } from '../components/FindingRow';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

export function Results() {
  const { jobId } = useParams<{ jobId: string }>();
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<Category | 'all'>('all');
  const [selectedSeverity, setSelectedSeverity] = useState<Severity | 'all'>('all');
  const [selectedFile, setSelectedFile] = useState('');
  const [showCharts, setShowCharts] = useState(false);

  useEffect(() => {
    if (!jobId) return;

    const fetchResults = async () => {
      try {
        const data = await getJobResults(jobId);
        setResults(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load results');
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, [jobId]);

  // Get unique files for filter dropdown
  const availableFiles = useMemo(() => {
    if (!results) return [];
    const files = new Set(results.findings.map(f => f.file));
    return Array.from(files).sort();
  }, [results]);

  // Apply filters
  const filteredFindings = useMemo(() => {
    if (!results) return [];

    return results.findings.filter((finding) => {
      // Search filter
      if (searchTerm) {
        const search = searchTerm.toLowerCase();
        const matchesSearch = 
          finding.title.toLowerCase().includes(search) ||
          finding.description.toLowerCase().includes(search) ||
          finding.file.toLowerCase().includes(search) ||
          finding.rule.toLowerCase().includes(search);
        
        if (!matchesSearch) return false;
      }

      // Category filter
      if (selectedCategory !== 'all' && finding.category !== selectedCategory) {
        return false;
      }

      // Severity filter
      if (selectedSeverity !== 'all' && finding.severity !== selectedSeverity) {
        return false;
      }

      // File filter
      if (selectedFile && finding.file !== selectedFile) {
        return false;
      }

      return true;
    });
  }, [results, searchTerm, selectedCategory, selectedSeverity, selectedFile]);

  // Chart data
  const severityChartData = useMemo(() => {
    if (!results) return [];
    return [
      { name: 'Critical', value: results.summary.by_severity.critical, fill: '#DC2626' },
      { name: 'High', value: results.summary.by_severity.high, fill: '#EA580C' },
      { name: 'Medium', value: results.summary.by_severity.medium, fill: '#CA8A04' },
      { name: 'Low', value: results.summary.by_severity.low, fill: '#2563EB' },
    ];
  }, [results]);

  const categoryChartData = useMemo(() => {
    if (!results) return [];
    return [
      { name: 'Security', value: results.summary.by_category.security },
      { name: 'Code Smell', value: results.summary.by_category['code-smell'] },
      { name: 'Maintainability', value: results.summary.by_category.maintainability },
      { name: 'Readability', value: results.summary.by_category.readability },
    ];
  }, [results]);

  const handleExport = () => {
    if (!results) return;
    
    const dataStr = JSON.stringify(results, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `code-analysis-${results.job_id}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (error || !results) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Failed to Load Results</h2>
          <p className="text-gray-600 mb-4">{error || 'No results found'}</p>
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Upload
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <Link
              to="/"
              className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
              New Analysis
            </Link>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Analysis Results</h1>
              <p className="text-sm text-gray-600 font-mono mt-1">Job: {results.job_id}</p>
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => setShowCharts(!showCharts)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <BarChart3 className="h-4 w-4" />
              {showCharts ? 'Hide Charts' : 'Show Charts'}
            </button>
            <button
              onClick={handleExport}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Download className="h-4 w-4" />
              Export JSON
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        <SummaryCards results={results} />

        {/* Charts */}
        {showCharts && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Issues by Category</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={categoryChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#3B82F6" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Issues by Severity</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={severityChartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}`}
                    outerRadius={80}
                    dataKey="value"
                  >
                    {severityChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Filters */}
        <FilterBar
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          selectedCategory={selectedCategory}
          onCategoryChange={setSelectedCategory}
          selectedSeverity={selectedSeverity}
          onSeverityChange={setSelectedSeverity}
          selectedFile={selectedFile}
          onFileChange={setSelectedFile}
          availableFiles={availableFiles}
        />

        {/* Results Count */}
        <div className="mb-4">
          <p className="text-sm text-gray-600">
            Showing {filteredFindings.length} of {results.findings.length} findings
          </p>
        </div>

        {/* Findings List */}
        <div className="space-y-3">
          {filteredFindings.length === 0 ? (
            <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
              <p className="text-gray-600">No findings match your filters</p>
            </div>
          ) : (
            filteredFindings.map((finding) => (
              <FindingRow key={finding.id} finding={finding} />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
