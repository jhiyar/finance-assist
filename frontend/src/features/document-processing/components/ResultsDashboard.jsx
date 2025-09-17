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
  BarChart3, 
  PieChart, 
  TrendingUp, 
  Clock, 
  FileText, 
  Award,
  Eye,
  Download
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

const ResultsDashboard = ({ processingJob, onViewChunks, onViewResults }) => {
  const [selectedMetric, setSelectedMetric] = useState('chunk_size_distribution');
  const [selectedMethods, setSelectedMethods] = useState([]);

  if (!processingJob || !processingJob.chunking_results) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">No results available</p>
      </div>
    );
  }

  const results = processingJob.chunking_results;
  const methods = results.map(result => result.chunking_method);

  // Prepare data for charts
  const prepareChartData = () => {
    const labels = methods.map(method => method.name);
    
    // Chunk size distribution
    const chunkSizes = results.map(result => result.avg_chunk_size);
    
    // Processing times
    const processingTimes = results.map(result => result.processing_time);
    
    // Total chunks
    const totalChunks = results.map(result => result.total_chunks);
    
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Results Dashboard</h2>
          <p className="text-gray-600">Analysis and comparison of chunking methods</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => onViewChunks(results)}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            <Eye className="h-4 w-4" />
            <span>View Chunks</span>
          </button>
          <button
            onClick={() => onViewResults(processingJob)}
            className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
          >
            <BarChart3 className="h-4 w-4" />
            <span>View Results</span>
          </button>
        </div>
      </div>

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
        {/* Chunk Size Distribution */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <Bar {...chunkSizeChartConfig} />
        </div>

        {/* Processing Time */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <Bar {...processingTimeChartConfig} />
        </div>

        {/* Evaluation Metrics */}
        <div className="bg-white p-6 rounded-lg border border-gray-200 lg:col-span-2">
          <Line {...metricsChartConfig} />
        </div>

        {/* Total Chunks */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <Doughnut {...totalChunksChartConfig} />
        </div>
      </div>

      {/* Detailed Results Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Detailed Results</h3>
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
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
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
                        {result.chunking_method.name}
                      </div>
                      <div className="text-sm text-gray-500">
                        {result.chunking_method.method_type}
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
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => onViewChunks([result])}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ResultsDashboard;
