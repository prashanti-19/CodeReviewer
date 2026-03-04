export type Category = 'security' | 'code-smell' | 'maintainability' | 'readability';
export type Severity = 'critical' | 'high' | 'medium' | 'low';

export interface Finding {
  id: string;
  file: string;
  line_start: number;
  line_end: number;
  category: Category;
  severity: Severity;
  rule: string;
  title: string;
  description: string;
  snippet: string;
}

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  files_processed?: number;
  total_files?: number;
}

export interface AnalysisResults {
  job_id: string;
  findings: Finding[];
  summary: {
    total_issues: number;
    by_category: Record<Category, number>;
    by_severity: Record<Severity, number>;
    files_analyzed: number;
  };
}

export interface UploadResponse {
  job_id: string;
  message: string;
}
