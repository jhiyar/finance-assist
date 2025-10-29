import React, { useState } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { useChunkingMethods, useChunkingMethodConfig } from '../hooks/useChunkingMethods';
import { Check, ChevronDown, ChevronUp, Settings, Info } from 'lucide-react';

const ChunkingMethodSelector = ({ selectedMethods, onMethodsChange, onConfigurationChange }) => {
  const { data: methods, isLoading, error } = useChunkingMethods();
  const [expandedMethod, setExpandedMethod] = useState(null);
  const [configurations, setConfigurations] = useState({});

  const { control, watch, setValue } = useForm({
    defaultValues: {
      methods: selectedMethods || []
    }
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'methods'
  });

  const handleMethodToggle = (method) => {
    const isSelected = selectedMethods?.some(m => m.id === method.id);
    
    if (isSelected) {
      // Remove method
      const newMethods = selectedMethods.filter(m => m.id !== method.id);
      onMethodsChange(newMethods);
      
      // Remove configuration
      const newConfigs = { ...configurations };
      delete newConfigs[method.method_type];
      setConfigurations(newConfigs);
      onConfigurationChange(newConfigs);
    } else {
      // Add method
      const newMethods = [...(selectedMethods || []), method];
      onMethodsChange(newMethods);
      
      // Set default configuration
      const newConfigs = { ...configurations };
      newConfigs[method.method_type] = method.parameters;
      setConfigurations(newConfigs);
      onConfigurationChange(newConfigs);
    }
  };

  const handleConfigChange = (methodType, config) => {
    const newConfigs = { ...configurations };
    newConfigs[methodType] = { ...newConfigs[methodType], ...config };
    setConfigurations(newConfigs);
    onConfigurationChange(newConfigs);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading chunking methods...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-lg font-medium text-red-800 mb-2">Error Loading Chunking Methods</h3>
        <p className="text-red-700 mb-4">
          Failed to load chunking methods from the server. Please check:
        </p>
        <ul className="list-disc list-inside text-red-700 space-y-1">
          <li>Backend server is running</li>
          <li>Database migrations have been run</li>
          <li>Chunking methods have been populated</li>
        </ul>
        <p className="text-sm text-red-600 mt-4">
          Error: {error.message}
        </p>
        <button
          onClick={() => window.location.reload()}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!methods || methods.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <h3 className="text-lg font-medium text-yellow-800 mb-2">No Chunking Methods Available</h3>
        <p className="text-yellow-700 mb-4">
          No chunking methods found. Please run the following command to populate the database:
        </p>
        <code className="block bg-yellow-100 p-3 rounded text-sm text-yellow-800 mb-4">
          python manage.py populate_chunking_methods
        </code>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 transition-colors"
        >
          Refresh
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Select Chunking Methods</h3>
      <p className="text-sm text-gray-600">
        Choose one or more chunking methods to compare. Each method will process your document
        and generate chunks that can be analyzed and compared.
      </p>

      <div className="grid gap-4">
        {methods?.map((method) => {
          const isSelected = selectedMethods?.some(m => m.id === method.id);
          const isExpanded = expandedMethod === method.id;

          return (
            <div
              key={method.id}
              className={`border rounded-lg transition-all ${
                isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              {/* Method Header */}
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <button
                      onClick={() => handleMethodToggle(method)}
                      className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                        isSelected
                          ? 'bg-blue-600 border-blue-600 text-white'
                          : 'border-gray-300 hover:border-gray-400'
                      }`}
                    >
                      {isSelected && <Check className="h-3 w-3" />}
                    </button>
                    <div>
                      <h4 className="font-medium text-gray-900">{method.name}</h4>
                      <p className="text-sm text-gray-600">{method.description}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {isSelected && (
                      <button
                        onClick={() => setExpandedMethod(isExpanded ? null : method.id)}
                        className="p-1 text-gray-400 hover:text-gray-600"
                      >
                        {isExpanded ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Method Configuration */}
              {isSelected && isExpanded && (
                <div className="border-t bg-gray-50 p-4">
                  <MethodConfiguration
                    method={method}
                    configuration={configurations[method.method_type] || method.parameters}
                    onConfigurationChange={(config) => handleConfigChange(method.method_type, config)}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {selectedMethods?.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center space-x-2 text-blue-800">
            <Info className="h-5 w-5" />
            <span className="font-medium">
              {selectedMethods.length} method{selectedMethods.length > 1 ? 's' : ''} selected
            </span>
          </div>
          <p className="text-sm text-blue-700 mt-1">
            Processing will run all selected methods and generate comparison results.
          </p>
        </div>
      )}
    </div>
  );
};

const MethodConfiguration = ({ method, configuration, onConfigurationChange }) => {
  const { register, watch, setValue } = useForm({
    defaultValues: configuration
  });

  const watchedValues = watch();

  React.useEffect(() => {
    onConfigurationChange(watchedValues);
  }, [watchedValues, onConfigurationChange]);

  const renderConfigField = (key, config) => {
    const value = configuration[key] || config.default;

    switch (config.type) {
      case 'integer':
        return (
          <input
            {...register(key)}
            type="number"
            min={config.min}
            max={config.max}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        );
      case 'float':
        return (
          <input
            {...register(key, { valueAsNumber: true })}
            type="number"
            step="0.1"
            min={config.min}
            max={config.max}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        );
      case 'boolean':
        return (
          <input
            {...register(key)}
            type="checkbox"
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
        );
      default:
        return (
          <input
            {...register(key)}
            type="text"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        );
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-2 text-gray-700">
        <Settings className="h-4 w-4" />
        <span className="font-medium">Configuration</span>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(method.parameters).map(([key, config]) => (
          <div key={key}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </label>
            {renderConfigField(key, config)}
            {config.min !== undefined && config.max !== undefined && (
              <p className="text-xs text-gray-500 mt-1">
                Range: {config.min} - {config.max}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ChunkingMethodSelector;
