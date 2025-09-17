import React, { useState } from 'react';
import { Bar, Line, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { 
  X, 
  Download, 
  BarChart3, 
  TrendingUp, 
  Award,
  Clock,
  FileText,
  Target,
  Zap,
  Eye,
  Copy
} from 'lucide-react';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const ResultsViewerModal = ({ isOpen, onClose, processingJob, title = "Processing Results" }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedMetric, setSelectedMetric] = useState('all');

  if (!isOpen || !processingJob) return null;

  const results = processingJob.chunking_results || [];
  const methods = results.map(result => result.chunking_method);

  // Prepare data for charts
  const prepareChartData = () => {
    const labels = methods.map(method => method.name);
    
    // Chunk size distribution
    const chunkSizes = results.map(result => result.avg_chunk_size || 0);
    
    // Processing times
    const processingTimes = results.map(result => result.processing_time || 0);
    
    // Total chunks
    const totalChunks = results.map(result => result.total_chunks || 0);
    
    // Evaluation metrics
    const metrics = {
      chunk_size_distribution: results.map(result => 
        result.evaluation_metrics?.find(m => m.metric_type === 'chunk_size_distribution')?.metric_value || 0
      ),
      overlap_analysis: results.map(result => 
        result.evaluation_metrics?.find(m => m.metric_type === 'overlap_analysis')?.metric_value || 0
      ),
      context_preservation: results.map(result => 
        result.evaluation_metrics?.find(m => m.metric_type === 'context_preservation')?.metric_value || 0
      ),
      structure_retention: results.map(result => 
        result.evaluation_metrics?.find(m => m.metric_type === 'structure_retention')?.metric_value || 0
      ),
      semantic_coherence: results.map(result => 
        result.evaluation_metrics?.find(m => m.metric_type === 'semantic_coherence')?.metric_value || 0
      ),
      processing_efficiency: results.map(result => 
        result.evaluation_metrics?.find(m => m.metric_type === 'processing_efficiency')?.metric_value || 0
      ),
    };

    return {
      labels,
      chunkSizes,
      processingTimes,
      totalChunks,
      metrics
    };
  };

  const chartData = prepareChartData();

  // Chart configurations
  const chunkSizeChartConfig = {
    type: 'bar',
    data: {
      labels: chartData.labels,
      datasets: [{
        label: 'Average Chunk Size (tokens)',
        data: chartData.chunkSizes,
        backgroundColor: 'rgba(59, 130, 246, 0.5)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 1,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: 'Chunk Size Distribution'
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Tokens'
          }
        }
      }
    }
  };

  const processingTimeChartConfig = {
    type: 'bar',
    data: {
      labels: chartData.labels,
      datasets: [{
        label: 'Processing Time (seconds)',
        data: chartData.processingTimes,
        backgroundColor: 'rgba(16, 185, 129, 0.5)',
        borderColor: 'rgba(16, 185, 129, 1)',
        borderWidth: 1,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: 'Processing Time Comparison'
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Seconds'
          }
        }
      }
    }
  };

  const metricsChartConfig = {
    type: 'line',
    data: {
      labels: chartData.labels,
      datasets: Object.entries(chartData.metrics).map(([metric, values], index) => ({
        label: metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        data: values,
        borderColor: `hsl(${index * 60}, 70%, 50%)`,
        backgroundColor: `hsla(${index * 60}, 70%, 50%, 0.1)`,
        tension: 0.1,
      }))
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: 'Evaluation Metrics Comparison'
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 1,
          title: {
            display: true,
            text: 'Score (0-1)'
          }
        }
      }
    }
  };

  const totalChunksChartConfig = {
    type: 'doughnut',
    data: {
      labels: chartData.labels,
      datasets: [{
        data: chartData.totalChunks,
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(139, 92, 246, 0.8)',
        ],
        borderWidth: 2,
        borderColor: '#fff',
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: 'Total Chunks Generated'
        },
        legend: {
          position: 'bottom',
        }
      }
    }
  };

  const exportResults = (format = 'json') => {
    const data = {
      processing_job: {
        id: processingJob.id,
        document: processingJob.document?.name,
        status: processingJob.status,
        started_at: processingJob.started_at,
        completed_at: processingJob.completed_at,
        duration: processingJob.duration
      },
      results: results.map(result => ({
        method: result.chunking_method?.name,
        method_type: result.chunking_method?.method_type,
        total_chunks: result.total_chunks,
        processing_time: result.processing_time,
        avg_chunk_size: result.avg_chunk_size,
        evaluation_metrics: result.evaluation_metrics?.map(metric => ({
          type: metric.metric_type,
          value: metric.metric_value,
          details: metric.metric_details
        }))
      }))
    };

    if (format === 'json') {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `processing_results_${new Date().toISOString().split('T')[0]}.json`;
      a.click();
    }
  };

  const getMetricIcon = (metricType) => {
    switch (metricType) {
      case 'chunk_size_distribution': return <BarChart3 className="h-4 w-4" />;
      case 'overlap_analysis': return <Target className="h-4 w-4" />;
      case 'context_preservation': return <FileText className="h-4 w-4" />;
      case 'structure_retention': return <TrendingUp className="h-4 w-4" />;
      case 'semantic_coherence': return <Eye className="h-4 w-4" />;
      case 'processing_efficiency': return <Zap className="h-4 w-4" />;
      default: return <BarChart3 className="h-4 w-4" />;
    }
  };

  const getMetricColor = (value) => {
    if (value >= 0.8) return 'text-green-600';
    if (value >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'metrics', label: 'Metrics', icon: TrendingUp },
    { id: 'comparison', label: 'Comparison', icon: Award },
    { id: 'details', label: 'Details', icon: FileText }
  ];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="fixed inset-0 bg-black bg-opacity-50" onClick={onClose} />
        
        <div className="relative bg-white rounded-lg shadow-xl w-full max-w-7xl max-h-[90vh] flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
              <p className="text-gray-600 mt-1">
                {processingJob.document?.name} • {results.length} method{results.length > 1 ? 's' : ''} compared
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => exportResults('json')}
                className="flex items-center space-x-2 px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                <Download className="h-4 w-4" />
                <span>Export Results</span>
              </button>
              <button
                onClick={onClose}
                className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {activeTab === 'overview' && (
              <div className="space-y-6">
                {/* Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="bg-white p-6 rounded-lg border border-gray-200">
                    <div className="flex items-center">
                      <BarChart3 className="h-8 w-8 text-blue-600" />
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Methods Compared</p>
                        <p className="text-2xl font-bold text-gray-900">{methods.length}</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-white p-6 rounded-lg border border-gray-200">
                    <div className="flex items-center">
                      <FileText className="h-8 w-8 text-green-600" />
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Total Chunks</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {chartData.totalChunks.reduce((sum, count) => sum + count, 0)}
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-white p-6 rounded-lg border border-gray-200">
                    <div className="flex items-center">
                      <Clock className="h-8 w-8 text-yellow-600" />
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Avg Processing Time</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {(chartData.processingTimes.reduce((sum, time) => sum + time, 0) / chartData.processingTimes.length).toFixed(2)}s
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-white p-6 rounded-lg border border-gray-200">
                    <div className="flex items-center">
                      <Award className="h-8 w-8 text-purple-600" />
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Best Method</p>
                        <p className="text-lg font-bold text-gray-900">
                          {methods[0]?.name || 'N/A'}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Charts */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-white p-6 rounded-lg border border-gray-200">
                    <Bar {...chunkSizeChartConfig} />
                  </div>
                  <div className="bg-white p-6 rounded-lg border border-gray-200">
                    <Bar {...processingTimeChartConfig} />
                  </div>
                  <div className="bg-white p-6 rounded-lg border border-gray-200 lg:col-span-2">
                    <Line {...metricsChartConfig} />
                  </div>
                  <div className="bg-white p-6 rounded-lg border border-gray-200">
                    <Doughnut {...totalChunksChartConfig} />
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'metrics' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {results.map((result, index) => {
                    const overallScore = result.evaluation_metrics?.reduce((sum, metric) => sum + metric.metric_value, 0) / (result.evaluation_metrics?.length || 1);
                    
                    return (
                      <div key={result.id} className="bg-white p-6 rounded-lg border border-gray-200">
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="text-lg font-semibold text-gray-900">
                            {result.chunking_method?.name}
                          </h3>
                          <div className="flex items-center space-x-2">
                            <div className="w-16 bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-blue-600 h-2 rounded-full"
                                style={{ width: `${(overallScore * 100).toFixed(0)}%` }}
                              />
                            </div>
                            <span className="text-sm font-medium text-gray-900">
                              {(overallScore * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                        
                        <div className="space-y-3">
                          {result.evaluation_metrics?.map((metric) => (
                            <div key={metric.id} className="flex items-center justify-between">
                              <div className="flex items-center space-x-2">
                                {getMetricIcon(metric.metric_type)}
                                <span className="text-sm text-gray-700">
                                  {metric.metric_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                </span>
                              </div>
                              <span className={`text-sm font-medium ${getMetricColor(metric.metric_value)}`}>
                                {(metric.metric_value * 100).toFixed(0)}%
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {activeTab === 'comparison' && (
              <div className="space-y-6">
                <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                  <div className="px-6 py-4 border-b border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900">Method Comparison</h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Method
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Chunks
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Avg Size
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Time
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Score
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {results.map((result, index) => {
                          const overallScore = result.evaluation_metrics?.reduce((sum, metric) => sum + metric.metric_value, 0) / (result.evaluation_metrics?.length || 1);
                          
                          return (
                            <tr key={result.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="text-sm font-medium text-gray-900">
                                  {result.chunking_method?.name}
                                </div>
                                <div className="text-sm text-gray-500">
                                  {result.chunking_method?.method_type}
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {result.total_chunks}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {result.avg_chunk_size?.toFixed(0) || 'N/A'} tokens
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {result.processing_time_formatted}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="flex items-center">
                                  <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                                    <div
                                      className="bg-blue-600 h-2 rounded-full"
                                      style={{ width: `${(overallScore * 100).toFixed(0)}%` }}
                                    />
                                  </div>
                                  <span className="text-sm text-gray-900">
                                    {(overallScore * 100).toFixed(0)}%
                                  </span>
                                </div>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'details' && (
              <div className="space-y-6">
                {results.map((result) => (
                  <div key={result.id} className="bg-white p-6 rounded-lg border border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      {result.chunking_method?.name} - Detailed Results
                    </h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Basic Information</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Total Chunks:</span>
                            <span className="font-medium">{result.total_chunks}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Average Chunk Size:</span>
                            <span className="font-medium">{result.avg_chunk_size?.toFixed(0) || 'N/A'} tokens</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Processing Time:</span>
                            <span className="font-medium">{result.processing_time_formatted}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Created:</span>
                            <span className="font-medium">{new Date(result.created_at).toLocaleString()}</span>
                          </div>
                        </div>
                      </div>
                      
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Evaluation Metrics</h4>
                        <div className="space-y-2 text-sm">
                          {result.evaluation_metrics?.map((metric) => (
                            <div key={metric.id} className="flex justify-between">
                              <span className="text-gray-600">
                                {metric.metric_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                              </span>
                              <span className={`font-medium ${getMetricColor(metric.metric_value)}`}>
                                {(metric.metric_value * 100).toFixed(0)}%
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-6 border-t border-gray-200 bg-gray-50">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600">
                Processing completed on {new Date(processingJob.completed_at).toLocaleString()}
              </div>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResultsViewerModal;
