import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { API_BASE_URL } from '../../../config/api.js';

export const useDocuments = () => {
  return useQuery({
    queryKey: ['documents'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE_URL}/document-processing/documents/`);
      return response.data;
    },
  });
};

export const useDocument = (documentId) => {
  return useQuery({
    queryKey: ['document', documentId],
    queryFn: async () => {
      const response = await axios.get(
        `${API_BASE_URL}/document-processing/documents/${documentId}/`
      );
      return response.data;
    },
    enabled: !!documentId,
  });
};

export const useDeleteDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (documentId) => {
      await axios.delete(`${API_BASE_URL}/document-processing/documents/${documentId}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
};
