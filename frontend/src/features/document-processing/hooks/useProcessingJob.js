import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { API_BASE_URL } from '../../../config/api.js';

export const useProcessingJobs = () => {
  return useQuery({
    queryKey: ['processing-jobs'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE_URL}/document-processing/processing-jobs/`);
      return response.data;
    },
  });
};

export const useProcessingJob = (jobId) => {
  return useQuery({
    queryKey: ['processing-job', jobId],
    queryFn: async () => {
      const response = await axios.get(
        `${API_BASE_URL}/document-processing/processing-jobs/${jobId}/`
      );
      return response.data;
    },
    enabled: !!jobId,
    refetchInterval: (data) => {
      // Poll every 2 seconds if job is still processing
      return data?.status === 'processing' ? 2000 : false;
    },
  });
};

export const useProcessDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ documentId, chunkingMethodIds, configuration }) => {
      const response = await axios.post(
        `${API_BASE_URL}/document-processing/documents/${documentId}/process/`,
        {
          chunking_method_ids: chunkingMethodIds,
          configuration,
        }
      );
      return response.data;
    },
    onSuccess: () => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['processing-jobs'] });
      queryClient.invalidateQueries({ queryKey: ['chunking-results'] });
    },
  });
};

export const useCompareMethods = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (documentId) => {
      const response = await axios.post(
        `${API_BASE_URL}/document-processing/documents/${documentId}/compare/`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comparison-results'] });
    },
  });
};
