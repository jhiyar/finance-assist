import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/document-processing';

export const useChunkingResults = () => {
  return useQuery({
    queryKey: ['chunking-results'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE_URL}/chunking-results/`);
      return response.data;
    },
  });
};

export const useChunkingResult = (resultId) => {
  return useQuery({
    queryKey: ['chunking-result', resultId],
    queryFn: async () => {
      const response = await axios.get(
        `${API_BASE_URL}/chunking-results/${resultId}/`
      );
      return response.data;
    },
    enabled: !!resultId,
  });
};
