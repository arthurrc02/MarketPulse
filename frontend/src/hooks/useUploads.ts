import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  createUpload,
  deleteUpload,
  getUpload,
  listUploads,
  processUpload,
} from '@/lib/uploads/api'

export const UPLOADS_QUERY_KEY = ['uploads'] as const

// Processamento é síncrono nesta sprint (sem fila real — ver docs/decisions.md),
// então a resposta de `POST /process` já chega com o status final. O polling
// existe mesmo assim: é o que deixa esta página pronta para quando o
// processamento virar assíncrono (Sprint 4+), sem precisar reescrever nada
// aqui — só o backend passaria a responder "processing" por mais tempo.
const PROCESSING_POLL_INTERVAL_MS = 1500

export function useUploadsQuery() {
  return useQuery({ queryKey: UPLOADS_QUERY_KEY, queryFn: listUploads })
}

export function useUploadQuery(id: string) {
  return useQuery({
    queryKey: [...UPLOADS_QUERY_KEY, id],
    queryFn: () => getUpload(id),
    refetchInterval: (query) =>
      query.state.data?.status === 'processing' ? PROCESSING_POLL_INTERVAL_MS : false,
  })
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

export function useProcessUploadMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: processUpload,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: UPLOADS_QUERY_KEY })
    },
  })
}
