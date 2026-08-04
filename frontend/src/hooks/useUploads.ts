import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { createUpload, deleteUpload, getUpload, listUploads } from '@/lib/uploads/api'

export const UPLOADS_QUERY_KEY = ['uploads'] as const

export function useUploadsQuery() {
  return useQuery({ queryKey: UPLOADS_QUERY_KEY, queryFn: listUploads })
}

export function useUploadQuery(id: string) {
  return useQuery({ queryKey: [...UPLOADS_QUERY_KEY, id], queryFn: () => getUpload(id) })
}

export function useCreateUploadMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createUpload,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: UPLOADS_QUERY_KEY })
    },
  })
}

export function useDeleteUploadMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteUpload,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: UPLOADS_QUERY_KEY })
    },
  })
}
