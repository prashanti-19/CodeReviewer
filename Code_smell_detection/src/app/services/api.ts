import { API_BASE_URL, API_ENDPOINTS, USE_MOCK_DATA } from '../config/api';
import { UploadResponse, JobStatus, AnalysisResults } from '../types/analysis';
import { generateMockResults } from './mockData';

// Real API calls - these will work once you deploy your backend
async function uploadFilesReal(files: File[]): Promise<UploadResponse> {
  const formData = new FormData();
  files.forEach(file => {
    formData.append('files', file);
  });

  const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.ANALYZE}`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.statusText}`);
  }

  return response.json();
}

async function getJobStatusReal(jobId: string): Promise<JobStatus> {
  const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.JOB_STATUS}/${jobId}/status`);

  if (!response.ok) {
    throw new Error(`Failed to get job status: ${response.statusText}`);
  }

  return response.json();
}

async function getJobResultsReal(jobId: string): Promise<AnalysisResults> {
  const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.JOB_RESULTS}/${jobId}/results`);

  if (!response.ok) {
    throw new Error(`Failed to get results: ${response.statusText}`);
  }

  return response.json();
}

// Mock API calls - for development/demo
function delay(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function uploadFilesMock(files: File[]): Promise<UploadResponse> {
  await delay(800);
  const jobId = `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  
  return {
    job_id: jobId,
    message: `Successfully queued ${files.length} files for analysis`
  };
}

async function getJobStatusMock(jobId: string): Promise<JobStatus> {
  await delay(500);
  
  // Simulate progressive status updates
  const elapsedTime = Date.now() - parseInt(jobId.split('_')[1]);
  
  if (elapsedTime < 3000) {
    return {
      job_id: jobId,
      status: 'processing',
      progress: Math.min(30, (elapsedTime / 3000) * 30),
      message: 'Parsing uploaded files...',
      files_processed: 3,
      total_files: 15
    };
  } else if (elapsedTime < 6000) {
    return {
      job_id: jobId,
      status: 'processing',
      progress: 30 + ((elapsedTime - 3000) / 3000) * 40,
      message: 'Running security analysis...',
      files_processed: 8,
      total_files: 15
    };
  } else if (elapsedTime < 9000) {
    return {
      job_id: jobId,
      status: 'processing',
      progress: 70 + ((elapsedTime - 6000) / 3000) * 25,
      message: 'Analyzing code quality...',
      files_processed: 13,
      total_files: 15
    };
  } else {
    return {
      job_id: jobId,
      status: 'completed',
      progress: 100,
      message: 'Analysis complete',
      files_processed: 15,
      total_files: 15
    };
  }
}

async function getJobResultsMock(jobId: string): Promise<AnalysisResults> {
  await delay(600);
  return generateMockResults(jobId);
}

// Exported functions - automatically switch between mock and real based on config
export async function uploadFiles(files: File[]): Promise<UploadResponse> {
  return USE_MOCK_DATA ? uploadFilesMock(files) : uploadFilesReal(files);
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  return USE_MOCK_DATA ? getJobStatusMock(jobId) : getJobStatusReal(jobId);
}

export async function getJobResults(jobId: string): Promise<AnalysisResults> {
  return USE_MOCK_DATA ? getJobResultsMock(jobId) : getJobResultsReal(jobId);
}
