import type { ChangeEvent, FormEvent } from 'react'
import type { DocumentItem } from '../../contracts/api'
import DocumentsPanel from '../right-panel/DocumentsPanel'

interface FilesTabProps {
  documents: DocumentItem[]
  documentsLoading: boolean
  error: string
  selectedFile: File | null
  onFileSelected: (event: ChangeEvent<HTMLInputElement>) => void
  onUpload: (event: FormEvent) => void
  onDelete: (id: string) => void
}

export default function FilesTab(props: FilesTabProps) {
  return <DocumentsPanel {...props} />
}
