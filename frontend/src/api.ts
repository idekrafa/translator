// Define the Chapter interface locally instead of importing it
interface Chapter {
  id: number;
  content: string;
}

// API base URL - adjust this based on your deployment environment
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://translator-1-5392.onrender.com';

interface BookTranslationRequest {
  chapters: Chapter[];
  target_language: string;
}

interface TranslationResponse {
  status: string;
  message: string;
  file_url: string | null;
  job_id?: string;
}

interface TranslationProgress {
  status: string;
  progress: number;
  current_chapter: number;
  total_chapters: number;
  message: string;
}

/**
 * Send a book translation request to the backend
 */
export async function translateBook(
  chapters: Chapter[],
  targetLanguage: string,
  outputFormat: string = 'docx'
): Promise<TranslationResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/translation/translate?output_format=${outputFormat}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        chapters,
        target_language: targetLanguage,
      } as BookTranslationRequest),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to start translation job');
    }

    return await response.json();
  } catch (error) {
    console.error('Translation request error:', error);
    throw error;
  }
}

/**
 * Get the status of a translation job
 */
export async function getTranslationStatus(jobUrl: string): Promise<TranslationProgress> {
  try {
    const response = await fetch(`${API_BASE_URL}${jobUrl}`);
    
    if (!response.ok) {
      // If status is 404, the job is likely completed but the server was restarted
      // or the job data was cleaned up
      if (response.status === 404) {
        return {
          status: 'completed',
          progress: 1.0,
          current_chapter: 1,
          total_chapters: 1,
          message: 'Tradução concluída. O arquivo está pronto para download.'
        };
      }
      
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to get translation status');
    }

    return await response.json();
  } catch (error) {
    console.error('Translation status error:', error);
    
    // If error message includes 404, treat as completed job
    if (error instanceof Error && error.message.includes('404')) {
      return {
        status: 'completed',
        progress: 1.0,
        current_chapter: 1,
        total_chapters: 1,
        message: 'Tradução concluída. O arquivo está pronto para download.'
      };
    }
    
    throw error;
  }
}

/**
 * Download a completed translation job
 */
export function getDownloadUrl(jobId: string): string {
  return `${API_BASE_URL}/api/translation/download/${jobId}`;
}

/**
 * Upload a PDF file for translation
 */
export async function uploadPdfForTranslation(
  file: File,
  targetLanguage: string,
  outputFormat: string = 'docx'
): Promise<TranslationResponse> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('target_language', targetLanguage);
    formData.append('output_format', outputFormat);

    const response = await fetch(`${API_BASE_URL}/api/upload/pdf`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to upload PDF for translation');
    }

    return await response.json();
  } catch (error) {
    console.error('PDF upload error:', error);
    throw error;
  }
} 
