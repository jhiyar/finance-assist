import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { API_BASE_URL } from '../../../config/api.js';

export const useDocumentUpload = () => {
  const [uploadProgress, setUploadProgress] = useState(0);
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: async (formData) => {
      const response = await axios.post(
        `${API_BASE_URL}/document-processing/documents/upload/`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            const progress = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setUploadProgress(progress);
          },
        }
      );
      return response.data;
    },
    onSuccess: () => {
      // Invalidate and refetch documents list
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      setUploadProgress(0);
    },
    onError: (error) => {
      console.error('Upload failed:', error);
      setUploadProgress(0);
    },
  });

  const uploadDocument = (file, name) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name || file.name);
    
    return uploadMutation.mutateAsync(formData);
  };

  return {
    uploadDocument,
    isUploading: uploadMutation.isPending,
    uploadProgress,
    uploadError: uploadMutation.error,
    uploadSuccess: uploadMutation.isSuccess,
  };
};
