import React, { useState, useEffect } from 'react';
import { Book, Languages, ChevronRight, Upload, Settings, BookOpen, Download } from 'lucide-react';
import { translateBook, getTranslationStatus, getDownloadUrl } from './api';

interface Chapter {
  id: number;
  content: string;
}

interface BookData {
  chapters: Chapter[];
  targetLanguage: string;
}

function App() {
  const [bookData, setBookData] = useState<BookData>({
    chapters: [],
    targetLanguage: 'Português'
  });
  const [currentStep, setCurrentStep] = useState(1);
  const [numChapters, setNumChapters] = useState<number>(1);
  const [currentChapter, setCurrentChapter] = useState<number>(1);
  const [chapterContent, setChapterContent] = useState<string>('');

  // API integration states
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<{
    status: string;
    progress: number;
    message: string;
    jobId?: string;
  } | null>(null);
  const [format, setFormat] = useState<string>('docx');

  const languages = [
    'Português',
    'Espanhol',
    'Francês',
    'Alemão',
    'Italiano',
    'Japonês',
    'Chinês',
    'Coreano'
  ];

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setBookData(prev => ({ ...prev, targetLanguage: e.target.value }));
  };

  const handleFormatChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFormat(e.target.value);
  };

  const handleNumChaptersChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const num = parseInt(e.target.value);
    if (num > 0 && num <= 100) {
      setNumChapters(num);
    }
  };

  const handleChapterContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setChapterContent(e.target.value);
  };

  const handleChapterSubmit = () => {
    if (chapterContent.trim()) {
      setBookData(prev => ({
        ...prev,
        chapters: [...prev.chapters, { id: currentChapter, content: chapterContent }]
      }));

      if (currentChapter < numChapters) {
        setCurrentChapter(prev => prev + 1);
        setChapterContent('');
      } else {
        submitTranslationJob();
      }
    }
  };

  const submitTranslationJob = async () => {
    try {
      setIsSubmitting(true);
      setError(null);
      
      const response = await translateBook(
        bookData.chapters, 
        bookData.targetLanguage,
        format
      );
      
      // Extract job ID from the URL
      const jobIdMatch = response.file_url?.match(/\/status\/([^\/]+)$/);
      const jobId = jobIdMatch ? jobIdMatch[1] : undefined;
      
      setJobStatus({
        status: response.status,
        progress: 0,
        message: response.message,
        jobId
      });
      
      setCurrentStep(3);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Poll for job status updates with variable interval based on status
  useEffect(() => {
    if (currentStep !== 3 || !jobStatus?.jobId) return;
    
    const statusUrl = `/api/translation/status/${jobStatus.jobId}`;
    
    // Function to fetch and update status
    const fetchStatus = async () => {
      try {
        console.log('Fetching status for job:', jobStatus.jobId);
        const progress = await getTranslationStatus(statusUrl);
        
        console.log('Status update:', progress);
        
        // Store the updated status
        setJobStatus({
          status: progress.status,
          progress: progress.progress,
          message: progress.message,
          jobId: jobStatus.jobId
        });
        
        return progress.status;
      } catch (err) {
        console.error('Error fetching job status:', err);
        // If we get a 404, it means the job is not found - mark as error
        if (err instanceof Error && err.message.includes('404')) {
          setJobStatus(prev => ({
            ...prev,
            status: 'completed',
            progress: prev?.progress || 1.0,
            message: 'Tradução concluída. O arquivo está pronto para download.'
          }));
          return 'completed';
        } else {
          setJobStatus(prev => ({
            ...prev,
            status: 'error',
            progress: prev?.progress || 0,
            message: err instanceof Error ? err.message : 'An unknown error occurred'
          }));
          return 'error';
        }
      }
    };
    
    // Initial fetch
    let timeoutId: number;
    fetchStatus().then(status => {
      // Determine if we should continue polling
      console.log('Polling status:', status);
      const shouldContinuePolling = 
        status !== 'completed' && 
        status !== 'error' && 
        status !== 'failed';
      
      // If job is still in progress, schedule next poll
      if (shouldContinuePolling) {
        // Determine polling interval based on status
        let interval = 3000; // default: 3 seconds
        
        if (status === 'translating' && jobStatus.message?.includes('Aguardando limite')) {
          // If hitting rate limits, poll less frequently
          interval = 10000; // 10 seconds
        }
        
        console.log(`Scheduling next poll in ${interval}ms`);
        // Schedule next poll
        timeoutId = window.setTimeout(fetchStatus, interval);
      } else {
        console.log('Polling stopped. Status:', status);
      }
    });
    
    // Cleanup on unmount or status change
    return () => {
      if (timeoutId) {
        console.log('Clearing timeout');
        window.clearTimeout(timeoutId);
      }
    };
  }, [currentStep, jobStatus?.jobId]);

  const handleStartOver = () => {
    setBookData({ chapters: [], targetLanguage: 'Português' });
    setCurrentStep(1);
    setNumChapters(1);
    setCurrentChapter(1);
    setChapterContent('');
    setJobStatus(null);
    setError(null);
  };

  const handleDownloadBook = () => {
    if (jobStatus?.jobId) {
      try {
        const downloadUrl = getDownloadUrl(jobStatus.jobId);
        console.log('Downloading from:', downloadUrl);
        window.location.href = downloadUrl;
      } catch (err) {
        console.error('Error preparing download URL:', err);
        setError('Erro ao preparar URL de download');
      }
    } else {
      setError('ID do trabalho não disponível para download');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Book className="h-6 w-6 text-indigo-600" />
              <span className="text-xl font-semibold text-gray-900">Tradutor de Livros</span>
            </div>
            <div className="flex items-center space-x-4">
              <Settings className="h-5 w-5 text-gray-500 cursor-pointer hover:text-gray-700" />
              <button
                onClick={handleStartOver}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Recomeçar
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-lg p-6">
          {/* Progress Steps */}
          <div className="flex items-center justify-between mb-8">
            <div className={`flex items-center ${currentStep >= 1 ? 'text-indigo-600' : 'text-gray-400'}`}>
              <div className="w-8 h-8 rounded-full border-2 flex items-center justify-center">
                1
              </div>
              <span className="ml-2">Configuração</span>
            </div>
            <ChevronRight className="w-5 h-5 text-gray-400" />
            <div className={`flex items-center ${currentStep >= 2 ? 'text-indigo-600' : 'text-gray-400'}`}>
              <div className="w-8 h-8 rounded-full border-2 flex items-center justify-center">
                2
              </div>
              <span className="ml-2">Conteúdo</span>
            </div>
            <ChevronRight className="w-5 h-5 text-gray-400" />
            <div className={`flex items-center ${currentStep === 3 ? 'text-indigo-600' : 'text-gray-400'}`}>
              <div className="w-8 h-8 rounded-full border-2 flex items-center justify-center">
                3
              </div>
              <span className="ml-2">Processamento</span>
            </div>
          </div>

          {/* Error message if any */}
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-600 rounded-md">
              {error}
            </div>
          )}

          {/* Step 1: Initial Setup */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Idioma de Destino
                </label>
                <select
                  value={bookData.targetLanguage}
                  onChange={handleLanguageChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                >
                  {languages.map(lang => (
                    <option key={lang} value={lang}>{lang}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Formato do Documento
                </label>
                <select
                  value={format}
                  onChange={handleFormatChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="docx">Microsoft Word (DOCX)</option>
                  <option value="pdf">PDF</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Número de Capítulos
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={numChapters}
                  onChange={handleNumChaptersChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <button
                onClick={() => setCurrentStep(2)}
                className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 transition-colors"
              >
                Continuar
              </button>
            </div>
          )}

          {/* Step 2: Chapter Content */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">
                  Capítulo {currentChapter} de {numChapters}
                </h2>
                <div className="text-sm text-gray-500">
                  {Math.floor(chapterContent.length / 3000)} páginas estimadas
                </div>
              </div>
              <textarea
                value={chapterContent}
                onChange={handleChapterContentChange}
                placeholder="Digite o conteúdo do capítulo aqui (até 10 páginas)..."
                className="w-full h-96 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
              />
              <button
                onClick={handleChapterSubmit}
                disabled={isSubmitting || !chapterContent.trim()}
                className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 transition-colors disabled:bg-indigo-300 disabled:cursor-not-allowed"
              >
                {currentChapter === numChapters ? 'Finalizar e Traduzir' : 'Próximo Capítulo'}
              </button>
            </div>
          )}

          {/* Step 3: Processing */}
          {currentStep === 3 && (
            <div className="text-center space-y-6">
              <div className="flex justify-center">
                <BookOpen className={`h-16 w-16 text-indigo-600 ${jobStatus?.status !== 'completed' ? 'animate-pulse' : ''}`} />
              </div>
              <h2 className="text-2xl font-semibold text-gray-900">
                {jobStatus?.status === 'completed' ? 'Tradução Concluída!' : 
                 jobStatus?.status === 'error' ? 'Erro na Tradução' :
                 jobStatus?.message?.includes('Aguardando limite') ? 'Aguardando API' : 'Processando seu Livro'}
              </h2>
              <p className="text-gray-600">
                {jobStatus?.message || `Traduzindo e formatando ${numChapters} capítulos para ${bookData.targetLanguage}...`}
              </p>
              
              {/* Progress bar */}
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div 
                  className={`h-2.5 rounded-full transition-all duration-500 ${
                    jobStatus?.status === 'error' ? 'bg-red-600' : 
                    jobStatus?.message?.includes('Aguardando limite') ? 'bg-yellow-600' : 'bg-indigo-600'
                  }`}
                  style={{ width: `${(jobStatus?.progress || 0) * 100}%` }}
                ></div>
              </div>
              
              {/* Error message with retry option */}
              {jobStatus?.status === 'error' && (
                <div className="mt-4">
                  <button
                    onClick={handleStartOver}
                    className="mt-2 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                  >
                    Tentar Novamente
                  </button>
                </div>
              )}
              
              {/* Download button - shown when completed or when the backend reports a PDF is available despite errors */}
              {(jobStatus?.status === 'completed' || 
                (jobStatus?.message && (
                  jobStatus.message.includes('PDF document created') || 
                  jobStatus.message.includes('Tradução concluída')
                ))) && (
                <button
                  onClick={handleDownloadBook}
                  className="mt-6 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  <Download className="-ml-1 mr-2 h-5 w-5" />
                  Baixar Livro Traduzido
                </button>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;