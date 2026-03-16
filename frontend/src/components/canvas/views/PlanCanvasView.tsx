interface PlanCanvasViewProps {
  payload?: unknown
}

function asSteps(payload: unknown): string[] {
  if (Array.isArray(payload) && payload.every((item) => typeof item === 'string')) {
    return payload as string[]
  }
  if (payload && typeof payload === 'object' && Array.isArray((payload as { steps?: unknown }).steps)) {
    return ((payload as { steps?: unknown[] }).steps ?? [])
      .filter((step): step is string => typeof step === 'string')
  }
  return []
}

export default function PlanCanvasView({ payload }: PlanCanvasViewProps) {
  const steps = asSteps(payload)
  return (
    <div className="h-full overflow-auto p-4">
      <h3 className="mb-3 text-sm font-semibold">Plan View</h3>
      {steps.length > 0 ? (
        <ol className="list-decimal space-y-2 pl-5 text-sm">
          {steps.map((step) => (
            <li key={step} className="rounded-md border bg-card p-2">
              {step}
            </li>
          ))}
        </ol>
      ) : (
        <div className="rounded-md border bg-card p-3 text-sm text-muted-foreground">
          Plan payload is empty.
        </div>
      )}
    </div>
  )
}
