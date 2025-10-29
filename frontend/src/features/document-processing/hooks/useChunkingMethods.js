import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { API_BASE_URL } from '../../../config/api.js';

export const useChunkingMethods = () => {
  return useQuery({
    queryKey: ['chunking-methods'],
    queryFn: async () => {
      console.log('Fetching chunking methods from:', `${API_BASE_URL}/document-processing/chunking-methods/`);
      const response = await axios.get(`${API_BASE_URL}/document-processing/chunking-methods/`);
      console.log('Chunking methods response:', response.data);
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 3,
    retryDelay: 1000,
  });
};

export const useChunkingMethodConfig = (methodId) => {
  return useQuery({
    queryKey: ['chunking-method-config', methodId],
    queryFn: async () => {
      const response = await axios.get(
        `${API_BASE_URL}/document-processing/chunking-methods/${methodId}/config/`
      );
      return response.data;
    },
    enabled: !!methodId,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};
