/**
 * Chamadas HTTP de upload, tipadas em camelCase para o resto da app.
 *
 * O backend responde em snake_case (convenção Python); `mapUpload` é o único
 * lugar onde esse formato de wire aparece.
 */

import { apiRequest } from '@/lib/apiClient'

export type UploadStatus = 'uploaded' | 'queued' | 'processing' | 'processed' | 'failed'

export interface UploadRecord {
  id: string
  originalFilename: string
  fileSize: number
  mimeType: string
  status: UploadStatus
  uploadedAt: string
}

interface UploadResponseBody {
  id: string
  original_filename: string
  file_size: number
  mime_type: string
  status: UploadStatus
  uploaded_at: string
}

function mapUpload(body: UploadResponseBody): UploadRecord {
  return {
    id: body.id,
    originalFilename: body.original_filename,
    fileSize: body.file_size,
    mimeType: body.mime_type,
    status: body.status,
    uploadedAt: body.uploaded_at,
  }
}

export async function listUploads(): Promise<UploadRecord[]> {
  const body = await apiRequest<UploadResponseBody[]>('/api/v1/uploads')
  return body.map(mapUpload)
}

export async function getUpload(id: string): Promise<UploadRecord> {
  const body = await apiRequest<UploadResponseBody>(`/api/v1/uploads/${id}`)
  return mapUpload(body)
}

export async function createUpload(file: File): Promise<UploadRecord> {
  const formData = new FormData()
  formData.set('file', file)
  const body = await apiRequest<UploadResponseBody>('/api/v1/uploads', {
    method: 'POST',
    body: formData,
  })
  return mapUpload(body)
}

export async function deleteUpload(id: string): Promise<void> {
  await apiRequest(`/api/v1/uploads/${id}`, { method: 'DELETE' })
}
