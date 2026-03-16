import { FolderKanban } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface ProjectsSectionProps {
  workspaceId: string
}

export default function ProjectsSection({ workspaceId }: ProjectsSectionProps) {
  return (
    <div className="space-y-3 p-3">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-sm">
            <FolderKanban className="h-4 w-4" />
            Projects
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-xs">
          <div className="rounded-md border bg-muted/40 p-2">
            <div className="text-muted-foreground">Active project</div>
            <div className="mt-1 font-medium">{workspaceId}</div>
          </div>
          <Badge variant="outline">Default workspace</Badge>
        </CardContent>
      </Card>
    </div>
  )
}
