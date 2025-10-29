import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { API_BASE_URL } from '../../../config/api.js';

export const useChunkingResults = () => {
  return useQuery({
    queryKey: ['chunking-results'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE_URL}/document-processing/chunking-results/`);
      return response.data;
    },
  });
};

export const useChunkingResult = (resultId) => {
  return useQuery({
    queryKey: ['chunking-result', resultId],
    queryFn: async () => {
      const response = await axios.get(
        `${API_BASE_URL}/document-processing/chunking-results/${resultId}/`
      );
      return response.data;
    },
    enabled: !!resultId,
  });
};
