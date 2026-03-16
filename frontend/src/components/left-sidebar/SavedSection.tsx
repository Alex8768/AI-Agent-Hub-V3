import { Bookmark } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function SavedSection() {
  return (
    <div className="space-y-3 p-3">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Bookmark className="h-4 w-4" />
            Saved
          </CardTitle>
        </CardHeader>
        <CardContent className="text-xs text-muted-foreground">
          Saved views and prompts will appear here.
        </CardContent>
      </Card>
    </div>
  )
}
