import type { ReactNode } from 'react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'

type RuntimeCardVariant = 'execution' | 'file' | 'tool' | 'approval' | 'result' | 'reasoning' | 'plan' | 'warning'

interface RuntimeCardProps {
  variant: RuntimeCardVariant
  title: string
  subtitle?: string
  badge?: string
  children?: ReactNode
  footer?: ReactNode
}

const variantClass: Record<RuntimeCardVariant, string> = {
  execution: 'border-border/80 bg-background',
  file: 'border-cyan-300/40 bg-cyan-50/20 dark:bg-cyan-900/10',
  tool: 'border-violet-300/40 bg-violet-50/20 dark:bg-violet-900/10',
  approval: 'border-orange-300/70 bg-orange-50/30 dark:bg-orange-900/15',
  result: 'border-emerald-300/40 bg-emerald-50/20 dark:bg-emerald-900/10',
  reasoning: 'border-amber-300/50 bg-amber-50/30 dark:bg-amber-900/10',
  plan: 'border-primary/20 bg-primary/5',
  warning: 'border-destructive/60 bg-destructive/10',
}

export default function RuntimeCard({ variant, title, subtitle, badge, children, footer }: RuntimeCardProps) {
  return (
    <Card className={variantClass[variant]}>
      <CardContent className="space-y-2 p-3.5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-sm font-medium">{title}</div>
            {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
          </div>
          {badge && (
            <Badge variant="outline" className="text-[10px]">
              {badge}
            </Badge>
          )}
        </div>
        {children}
        {footer}
      </CardContent>
    </Card>
  )
}
