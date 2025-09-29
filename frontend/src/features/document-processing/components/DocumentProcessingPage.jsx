import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import DocumentUploader from './DocumentUploader';
import ChunkingMethodSelector from './ChunkingMethodSelector';
import ProcessingProgress from './ProcessingProgress';
import ResultsDashboard from './ResultsDashboard';
import ChunkViewerModal from './ChunkViewerModal';
import ResultsViewerModal from './ResultsViewerModal';
import ContextPruningPanel from './ContextPruningPanel';
import { useDocuments } from '../hooks/useDocuments';
import { useProcessingJobs, useProcessDocument, useProcessingJob } from '../hooks/useProcessingJob';
import { 
  Upload, 
  Settings, 
  BarChart3, 
  FileText, 
  Play,
  ArrowRight,
  CheckCircle
} from 'lucide-react';

const DocumentProcessingPage = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [selectedMethods, setSelectedMethods] = useState([]);
  const [configuration, setConfiguration] = useState({});
  const [currentJob, setCurrentJob] = useState(null);
  const [showChunkModal, setShowChunkModal] = useState(false);
  const [showResultsModal, setShowResultsModal] = useState(false);
  const [modalData, setModalData] = useState(null);
  const [pruningResult, setPruningResult] = useState(null);

  const { data: documents, isLoading: documentsLoading } = useDocuments();
  const { data: processingJobs } = useProcessingJobs();
  const { data: currentJobData } = useProcessingJob(currentJob?.id);
  const processDocument = useProcessDocument();

  // Debug logging
  console.log('DocumentProcessingPage state:', {
    currentStep,
    currentJob,
    currentJobData,
    selectedDocument,
    selectedMethods
  });

  const steps = [
    { id: 1, name: 'Upload Document', icon: Upload },
    { id: 2, name: 'Select Methods', icon: Settings },
    { id: 3, name: 'Process', icon: Play },
    { id: 4, name: 'View Results', icon: BarChart3 },
    { id: 5, name: 'Context Pruning', icon: FileText },
  ];

  const handleDocumentUpload = (document) => {
    setSelectedDocument(document);
    setCurrentStep(2);
  };

  const handleMethodsChange = (methods) => {
    setSelectedMethods(methods);
  };

  const handleConfigurationChange = (config) => {
    setConfiguration(config);
  };

  const handleStartProcessing = async () => {
    if (!selectedDocument || selectedMethods.length === 0) return;

    try {
      console.log('Starting processing with:', {
        documentId: selectedDocument.id,
        chunkingMethodIds: selectedMethods.map(m => m.id),
        configuration,
      });
      
      const result = await processDocument.mutateAsync({
        documentId: selectedDocument.id,
        chunkingMethodIds: selectedMethods.map(m => m.id),
        configuration,
      });
      
      console.log('Processing result:', result);
      setCurrentJob(result);
      setCurrentStep(3);
    } catch (error) {
      console.error('Processing failed:', error);
    }
  };

  const handleViewChunks = (results) => {
    setModalData(results);
    setShowChunkModal(true);
  };

  const handleViewResults = (processingJob) => {
    setModalData(processingJob);
    setShowResultsModal(true);
  };

  const getChunksAsDocuments = (processingJob) => {
    if (!processingJob || !processingJob.chunking_results) {
      return [];
    }

    const documents = [];
    processingJob.chunking_results.forEach(result => {
      if (result.chunks) {
        result.chunks.forEach(chunk => {
          documents.push({
            content: chunk.content,
            metadata: {
              ...chunk.metadata,
              chunk_id: chunk.id,
              chunking_method: result.chunking_method?.name,
              chunk_type: chunk.chunk_type,
              chunk_index: chunk.chunk_index,
              token_count: chunk.token_count
            }
          });
        });
      }
    });
    return documents;
  };

  const isStepCompleted = (stepId) => {
    switch (stepId) {
      case 1:
        return !!selectedDocument;
      case 2:
        return selectedMethods.length > 0;
      case 3:
        return (currentJobData || currentJob)?.status === 'completed';
      case 4:
        return (currentJobData || currentJob)?.status === 'completed';
      default:
        return false;
    }
  };

  const canProceedToStep = (stepId) => {
    switch (stepId) {
      case 2:
        return !!selectedDocument;
      case 3:
        return selectedMethods.length > 0;
      case 4:
        return (currentJobData || currentJob)?.status === 'completed';
      default:
        return false;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Document Processing & Chunking Comparison</h1>
            <p className="mt-2 text-gray-600">
              Upload documents and compare different chunking strategies for RAG systems
            </p>
          </div>

          {/* Progress Steps */}
          <div className="mb-8">
            <nav aria-label="Progress">
              <ol className="flex items-center justify-center space-x-8">
                {steps.map((step, stepIdx) => {
                  const isCompleted = isStepCompleted(step.id);
                  const isCurrent = currentStep === step.id;
                  const canProceed = canProceedToStep(step.id);
                  const Icon = step.icon;

                  return (
                    <li key={step.name} className="flex items-center">
                      <div className="flex items-center">
                        <div
                          className={`
                            flex items-center justify-center w-10 h-10 rounded-full border-2
                            ${isCompleted
                              ? 'bg-green-600 border-green-600 text-white'
                              : isCurrent
                              ? 'bg-blue-600 border-blue-600 text-white'
                              : canProceed
                              ? 'border-gray-300 text-gray-500 hover:border-gray-400'
                              : 'border-gray-200 text-gray-300'
                            }
                          `}
                        >
                          {isCompleted ? (
                            <CheckCircle className="w-6 h-6" />
                          ) : (
                            <Icon className="w-6 h-6" />
                          )}
                        </div>
                        <div className="ml-4">
                          <p
                            className={`
                              text-sm font-medium
                              ${isCompleted || isCurrent
                                ? 'text-gray-900'
                                : canProceed
                                ? 'text-gray-500'
                                : 'text-gray-300'
                              }
                            `}
                          >
                            {step.name}
                          </p>
                        </div>
                      </div>
                      {stepIdx < steps.length - 1 && (
                        <div className="ml-8 flex items-center">
                          <ArrowRight className="w-5 h-5 text-gray-400" />
                        </div>
                      )}
                    </li>
                  );
                })}
              </ol>
            </nav>
          </div>

          {/* Step Content */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            {currentStep === 1 && (
              <div className="p-8">
                <div className="text-center mb-8">
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">Upload Document</h2>
                  <p className="text-gray-600">
                    Upload a PDF, DOCX, or text document to begin the chunking comparison process
                  </p>
                </div>
                <DocumentUploader onUploadSuccess={handleDocumentUpload} />
              </div>
            )}

            {currentStep === 2 && (
              <div className="p-8">
                <div className="mb-6">
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">Select Chunking Methods</h2>
                  <p className="text-gray-600">
                    Choose one or more chunking methods to compare. Each method will process your document
                    and generate chunks that can be analyzed and compared.
                  </p>
                </div>
                <ChunkingMethodSelector
                  selectedMethods={selectedMethods}
                  onMethodsChange={handleMethodsChange}
                  onConfigurationChange={handleConfigurationChange}
                />
                <div className="mt-8 flex justify-end space-x-4">
                  <button
                    onClick={() => setCurrentStep(1)}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    Back
                  </button>
                  <button
                    onClick={handleStartProcessing}
                    disabled={selectedMethods.length === 0 || processDocument.isPending}
                    className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
                  >
                    <Play className="w-4 h-4" />
                    <span>Start Processing</span>
                  </button>
                </div>
              </div>
            )}


            {currentStep === 3 && (
              <div className="p-8">
                <div className="mb-6">
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    {(currentJobData || currentJob)?.status === 'processing' ? 'Processing Document...' : 
                     (currentJobData || currentJob)?.status === 'completed' ? 'Processing Complete!' :
                     (currentJobData || currentJob)?.status === 'failed' ? 'Processing Failed' :
                     'Processing Document'}
                  </h2>
                  <p className="text-gray-600">
                    {(currentJobData || currentJob)?.status === 'processing' ? 
                      'Your document is being processed with the selected chunking methods. This may take a few minutes.' :
                      (currentJobData || currentJob)?.status === 'completed' ?
                      'Document processing completed successfully! You can now view and analyze the results.' :
                      (currentJobData || currentJob)?.status === 'failed' ?
                      'Document processing failed. Please check the error details below and try again.' :
                      'Preparing to process your document...'}
                  </p>
                </div>
                {(currentJobData || currentJob) && (
                  <ProcessingProgress job={currentJobData || currentJob} />
                )}
                {(currentJobData || currentJob)?.status === 'completed' && (
                  <div className="mt-6 flex justify-end">
                    <button
                      onClick={() => setCurrentStep(4)}
                      className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center space-x-2"
                    >
                      <BarChart3 className="w-4 h-4" />
                      <span>View Results</span>
                    </button>
                  </div>
                )}
                {(currentJobData || currentJob)?.status === 'failed' && (
                  <div className="mt-6 flex justify-end space-x-3">
                    <button
                      onClick={() => setCurrentStep(2)}
                      className="px-6 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
                    >
                      Try Again
                    </button>
                    <button
                      onClick={() => setCurrentStep(1)}
                      className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                    >
                      Upload New Document
                    </button>
                  </div>
                )}
              </div>
            )}

            {currentStep === 4 && (
              <div className="p-8">
                <div className="mb-6">
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">Results & Analysis</h2>
                  <p className="text-gray-600">
                    Compare the performance of different chunking methods and analyze the results.
                  </p>
                </div>
                {currentJobData && (
                  <ResultsDashboard
                    processingJob={currentJobData}
                    onViewChunks={handleViewChunks}
                    onViewResults={handleViewResults}
                  />
                )}
                <div className="mt-8 flex justify-end">
                  <button
                    onClick={() => setCurrentStep(5)}
                    className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors flex items-center space-x-2"
                  >
                    <FileText className="w-4 h-4" />
                    <span>Context Pruning Analysis</span>
                  </button>
                </div>
              </div>
            )}

            {currentStep === 5 && (
              <div className="p-8">
                <div className="mb-6">
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">Context Pruning Analysis</h2>
                  <p className="text-gray-600">
                    Apply context pruning to the generated chunks to see how it affects their relevance and quality.
                    This helps analyze the impact of pruning on your document chunks.
                  </p>
                </div>
                {currentJobData && (
                  <ContextPruningPanel
                    documents={getChunksAsDocuments(currentJobData)}
                    onPruningComplete={setPruningResult}
                  />
                )}
                <div className="mt-8 flex justify-end space-x-4">
                  <button
                    onClick={() => setCurrentStep(4)}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    Back to Results
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Recent Documents */}
          {documents && documents.length > 0 && (
            <div className="mt-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Documents</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {documents.slice(0, 6).map((document) => (
                  <div
                    key={document.id}
                    className="bg-white p-4 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors cursor-pointer"
                    onClick={() => {
                      setSelectedDocument(document);
                      setCurrentStep(2);
                    }}
                  >
                    <div className="flex items-center space-x-3">
                      <FileText className="h-8 w-8 text-blue-500" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {document.name}
                        </p>
                        <p className="text-sm text-gray-500">
                          {document.file_type.toUpperCase()} • {document.file_size_mb} MB
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Modals */}
        <ChunkViewerModal
          isOpen={showChunkModal}
          onClose={() => setShowChunkModal(false)}
          results={modalData}
          title="Chunk Analysis"
        />
        
        <ResultsViewerModal
          isOpen={showResultsModal}
          onClose={() => setShowResultsModal(false)}
          processingJob={modalData}
          title="Processing Results"
        />
      </div>
  );
};

export default DocumentProcessingPage;
