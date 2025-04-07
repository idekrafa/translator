import React, { useState, useEffect, ChangeEvent } from 'react';
import './App.css';
import { translateBook, getTranslationStatus, getDownloadUrl, uploadPdfForTranslation } from './api';

// Basic interfaces
interface Chapter {
  id: number;
  content: string;
}

function App() {
  // State
  const [bookData, setBookData] = useState({
    chapters: [{ id: 1, content: '' }],
    targetLanguage: 'Português',
    format: 'docx',
  });
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isTranslating, setIsTranslating] = useState(false);
  const [translationProgress, setTranslationProgress] = useState(0);
  const [translationComplete, setTranslationComplete] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatusUrl, setJobStatusUrl] = useState<string | null>(null);
  const [currentChapter, setCurrentChapter] = useState(0);
  const [totalChapters, setTotalChapters] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  const [error, setError] = useState<string | null>(null);
  
  // Available languages
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

  // Event handlers
  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setBookData({ ...bookData, targetLanguage: e.target.value });
  };
  
  const handleFormatChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setBookData({ ...bookData, format: e.target.value });
  };
  
  const handleChapterChange = (id: number, content: string) => {
    setBookData({
      ...bookData,
      chapters: bookData.chapters.map(ch => 
        ch.id === id ? { ...ch, content } : ch
      ),
    });
  };
  
  const addChapter = () => {
    const newId = bookData.chapters.length > 0 
      ? Math.max(...bookData.chapters.map(ch => ch.id)) + 1 
      : 1;
    
    setBookData({
      ...bookData,
      chapters: [...bookData.chapters, { id: newId, content: '' }],
    });
  };
  
  const removeChapter = (id: number) => {
    if (bookData.chapters.length <= 1) return;
    
    setBookData({
      ...bookData,
      chapters: bookData.chapters.filter(ch => ch.id !== id),
    });
  };
  
  // File handlers
  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || !files[0]) return;
    
    const file = files[0];
    if (file.type !== 'application/pdf') {
      setError('Por favor, carregue apenas arquivos PDF');
      return;
    }
    
    setSelectedFile(file);
    setError(null);
  };
  
  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };
  
  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };
  
  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (!files || !files[0]) return;
    
    const file = files[0];
    if (file.type !== 'application/pdf') {
      setError('Por favor, carregue apenas arquivos PDF');
      return;
    }
    
    setSelectedFile(file);
    setError(null);
  };
  
  // Submit for translation
  const submitTranslation = async () => {
    try {
      setIsTranslating(true);
      setCurrentStep(3);
      setError(null);
      
      if (selectedFile) {
        // PDF translation
        const response = await uploadPdfForTranslation(
          selectedFile,
          bookData.targetLanguage,
          bookData.format
        );
        
        setJobStatusUrl(response.file_url);
        setJobId(response.job_id || null);
      } else {
        // Chapter translation
        if (bookData.chapters.some(ch => !ch.content.trim())) {
          setError('Por favor, preencha todos os capítulos');
          setIsTranslating(false);
          return;
        }
        
        const response = await translateBook(
          bookData.chapters,
          bookData.targetLanguage,
          bookData.format
        );
        
        setJobStatusUrl(response.file_url);
        setJobId(response.job_id || null);
      }
    } catch (err) {
      console.error('Translation error:', err);
      setIsTranslating(false);
      setError(err instanceof Error ? err.message : 'Erro ao iniciar tradução');
    }
  };
  
  // Reset everything
  const resetApp = () => {
    setBookData({
      chapters: [{ id: 1, content: '' }],
      targetLanguage: 'Português',
      format: 'docx',
    });
    setCurrentStep(1);
    setSelectedFile(null);
    setIsTranslating(false);
    setTranslationProgress(0);
    setTranslationComplete(false);
    setJobId(null);
    setJobStatusUrl(null);
    setCurrentChapter(0);
    setTotalChapters(0);
    setStatusMessage('');
    setError(null);
  };
  
  // Download translated document
  const downloadTranslation = () => {
    if (!jobId) return;
    
    const downloadUrl = getDownloadUrl(jobId);
    window.location.href = downloadUrl;
  };
  
  // Poll for status
  useEffect(() => {
    if (currentStep !== 3 || !jobStatusUrl) return;
    
    let timeoutId: number;
    
    const checkStatus = async () => {
      try {
        const status = await getTranslationStatus(jobStatusUrl);
        
        setTranslationProgress(status.progress);
        setStatusMessage(status.message);
        setCurrentChapter(status.current_chapter);
        setTotalChapters(status.total_chapters);
        
        if (status.status === 'completed') {
          setTranslationComplete(true);
        } else {
          timeoutId = window.setTimeout(checkStatus, 3000);
        }
      } catch (err) {
        console.error('Status check error:', err);
        setTranslationComplete(true);
      }
    };
    
    checkStatus();
    
    return () => {
      if (timeoutId) window.clearTimeout(timeoutId);
    };
  }, [currentStep, jobStatusUrl]);

  // Main component render
  return (
    <div className="container">
      <h1 className="title">Tradutor de Livros</h1>
      
      {/* Step 1: Configuration */}
      {currentStep === 1 && (
        <div className="step-container">
          <h2>Configurações</h2>
          
          <div className="form-group">
            <label>Idioma de destino</label>
            <select value={bookData.targetLanguage} onChange={handleLanguageChange}>
              {languages.map(lang => (
                <option key={lang} value={lang}>{lang}</option>
              ))}
            </select>
          </div>
          
          <div className="form-group">
            <label>Formato de saída</label>
            <select value={bookData.format} onChange={handleFormatChange}>
              <option value="docx">DOCX</option>
              <option value="pdf">PDF</option>
            </select>
          </div>
          
          <div className="button-group">
            <button className="button primary" onClick={() => setCurrentStep(2)}>
              Inserir capítulos manualmente
            </button>
            
            <button className="button secondary" onClick={() => setCurrentStep(4)}>
              Carregar PDF
            </button>
          </div>
        </div>
      )}
      
      {/* Step 2: Chapter Input */}
      {currentStep === 2 && (
        <div className="step-container">
          <div className="header">
            <h2>Digite os capítulos do livro</h2>
            <button className="button small" onClick={() => setCurrentStep(1)}>
              Voltar
            </button>
          </div>
          
          {bookData.chapters.map((chapter, idx) => (
            <div key={chapter.id} className="chapter-container">
              <div className="chapter-header">
                <span className="chapter-title">Capítulo {chapter.id}</span>
                {bookData.chapters.length > 1 && (
                  <button
                    className="button small danger"
                    onClick={() => removeChapter(chapter.id)}
                  >
                    Remover
                  </button>
                )}
              </div>
              
              <textarea
                value={chapter.content}
                onChange={(e) => handleChapterChange(chapter.id, e.target.value)}
                placeholder={`Digite o conteúdo do capítulo ${chapter.id}`}
                rows={8}
              />
              
              {idx < bookData.chapters.length - 1 && <hr />}
            </div>
          ))}
          
          <button className="button small" onClick={addChapter}>
            Adicionar Capítulo
          </button>
          
          {error && <div className="error-message">{error}</div>}
          
          <div className="button-group">
            <button className="button" onClick={() => setCurrentStep(1)}>Voltar</button>
            <button
              className="button primary"
              onClick={submitTranslation}
              disabled={isTranslating}
            >
              {isTranslating ? 'Iniciando...' : 'Traduzir Livro'}
            </button>
          </div>
        </div>
      )}
      
      {/* Step 3: Translation Progress */}
      {currentStep === 3 && (
        <div className="step-container">
          <h2>Progresso da Tradução</h2>
          
          <div className="progress-container">
            <div 
              className="progress-bar" 
              style={{ width: `${translationProgress * 100}%` }}
            />
          </div>
          
          <p className="status-message">{statusMessage || 'Inicializando tradução...'}</p>
          
          {currentChapter > 0 && totalChapters > 0 && (
            <p className="chapter-progress">Capítulo {currentChapter} de {totalChapters}</p>
          )}
          
          {translationComplete && (
            <button
              className="button primary large"
              onClick={downloadTranslation}
            >
              Baixar Tradução
            </button>
          )}
          
          <button className="button" onClick={resetApp}>Nova Tradução</button>
        </div>
      )}
      
      {/* Step 4: PDF Upload */}
      {currentStep === 4 && (
        <div className="step-container">
          <h2>Carregar arquivo PDF</h2>
          
          <input
            type="file"
            id="fileInput"
            onChange={handleFileChange}
            accept="application/pdf"
            style={{ display: 'none' }}
          />
          
          <div
            className={`dropzone ${isDragging ? 'dragging' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => document.getElementById('fileInput')?.click()}
          >
            <div className="dropzone-content">
              <div className="upload-icon"></div>
              
              {selectedFile ? (
                <div>
                  <p className="file-name">{selectedFile.name}</p>
                  <p className="file-size">({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)</p>
                </div>
              ) : (
                <p>Clique ou arraste um arquivo PDF para carregar</p>
              )}
            </div>
          </div>
          
          {selectedFile && (
            <div className="success-message">
              Arquivo selecionado: {selectedFile.name}
            </div>
          )}
          
          {error && <div className="error-message">{error}</div>}
          
          <div className="button-group">
            <button className="button" onClick={() => setCurrentStep(1)}>Voltar</button>
            <button
              className="button primary"
              disabled={!selectedFile || isTranslating}
              onClick={submitTranslation}
            >
              {isTranslating ? 'Iniciando...' : 'Traduzir PDF'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;