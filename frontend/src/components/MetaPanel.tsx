import React from 'react';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';

interface MetaPanelProps {
  diagnostics: Record<string, unknown> | null;
  mode?: 'compact' | 'full';
}

interface TraceStep {
  id: string;
  title: string;
  payload: unknown;
  stamp: string;
}

function asRecord(value: unknown): Record<string, unknown> {
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return {};
}

function asTraceSteps(value: unknown): TraceStep[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter((item) => item && typeof item === 'object' && !Array.isArray(item))
    .map((item, idx) => {
      const row = item as Record<string, unknown>;
      const rawStep = row.step;
      const title = typeof rawStep === 'string' && rawStep.trim() ? rawStep : `step_${idx + 1}`;
      return {
        id: `trace-${idx + 1}`,
        title,
        payload: row,
        stamp: `T+${String(idx + 1).padStart(2, '0')}`,
      };
    });
}

const MetaPanel: React.FC<MetaPanelProps> = ({ diagnostics, mode = 'compact' }) => {
  const root = diagnostics ?? {};
  const optimization = asRecord(root.reasoning_optimization);
  const metaCognition = asRecord(root.meta_cognition);
  const runtimeMode = asRecord(root.runtime_mode);
  const actRuntime = asRecord(root.act_runtime);
  const traceSteps = asTraceSteps(root.reasoning_process);

  const hasOptimization = Object.keys(optimization).length > 0;
  const hasMetaCognition = Object.keys(metaCognition).length > 0;
  const hasRuntimeMode = Object.keys(runtimeMode).length > 0;
  const hasActRuntime = Object.keys(actRuntime).length > 0;
  const hasTraceSteps = traceSteps.length > 0;

  return (
    <div className="flex h-full min-h-0 flex-col gap-3 p-1">
      <h2 className="text-sm font-semibold tracking-tight">Meta / Self-Evolution</h2>

      {!hasOptimization && !hasMetaCognition && !hasRuntimeMode && !hasActRuntime && !hasTraceSteps && (
        <div className="rounded-md border border-dashed p-3 text-sm text-muted-foreground">
          No diagnostics yet. Send a query to populate optimization, meta-cognition, and runtime mode data.
        </div>
      )}

      <Card className="min-h-0">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">Reasoning Trace</CardTitle>
        </CardHeader>
        <CardContent>
          {hasTraceSteps ? (
            <ScrollArea className="max-h-56 rounded-md border bg-muted/20">
              <Accordion
                type="single"
                collapsible
                defaultValue={mode === 'full' ? traceSteps[0]?.id : undefined}
                className="px-3"
              >
                {traceSteps.map((step) => (
                  <AccordionItem key={step.id} value={step.id}>
                    <AccordionTrigger className="py-2 text-xs">
                      <span className="flex items-center gap-2">
                        <span className="rounded border px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                          {step.stamp}
                        </span>
                        <span>{step.title}</span>
                      </span>
                    </AccordionTrigger>
                    <AccordionContent>
                      <pre className="rounded-md border bg-background p-2 font-mono text-xs leading-5 whitespace-pre-wrap">
                        {JSON.stringify(step.payload, null, 2)}
                      </pre>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </ScrollArea>
          ) : (
            <p className="text-sm text-muted-foreground">No `diagnostics.reasoning_process` trace yet.</p>
          )}
        </CardContent>
      </Card>

      <Card className="min-h-0">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">Runtime Mode</CardTitle>
        </CardHeader>
        <CardContent>
          {hasRuntimeMode ? (
            <Accordion type="single" collapsible defaultValue={mode === 'full' ? 'open' : undefined}>
              <AccordionItem value="open">
                <AccordionTrigger className="py-1 text-xs">Show payload</AccordionTrigger>
                <AccordionContent>
                  <ScrollArea className="max-h-40 rounded-md border bg-muted/30">
                    <pre className="p-3 font-mono text-xs leading-5">{JSON.stringify(runtimeMode, null, 2)}</pre>
                  </ScrollArea>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          ) : (
            <p className="text-sm text-muted-foreground">No `diagnostics.runtime_mode` payload.</p>
          )}
        </CardContent>
      </Card>

      <Card className="min-h-0">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">Act Runtime</CardTitle>
        </CardHeader>
        <CardContent>
          {hasActRuntime ? (
            <Accordion type="single" collapsible>
              <AccordionItem value="open">
                <AccordionTrigger className="py-1 text-xs">Show payload</AccordionTrigger>
                <AccordionContent>
                  <ScrollArea className="max-h-40 rounded-md border bg-muted/30">
                    <pre className="p-3 font-mono text-xs leading-5">{JSON.stringify(actRuntime, null, 2)}</pre>
                  </ScrollArea>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          ) : (
            <p className="text-sm text-muted-foreground">No `diagnostics.act_runtime` payload.</p>
          )}
        </CardContent>
      </Card>

      <Card className="min-h-0">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">Reasoning Optimization</CardTitle>
        </CardHeader>
        <CardContent>
          {hasOptimization ? (
            <Accordion type="single" collapsible>
              <AccordionItem value="open">
                <AccordionTrigger className="py-1 text-xs">Show payload</AccordionTrigger>
                <AccordionContent>
                  <ScrollArea className="max-h-40 rounded-md border bg-muted/30">
                    <pre className="p-3 font-mono text-xs leading-5">{JSON.stringify(optimization, null, 2)}</pre>
                  </ScrollArea>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          ) : (
            <p className="text-sm text-muted-foreground">No `diagnostics.reasoning_optimization` payload.</p>
          )}
        </CardContent>
      </Card>

      <Card className="min-h-0">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">Meta Cognition</CardTitle>
        </CardHeader>
        <CardContent>
          {hasMetaCognition ? (
            <Accordion type="single" collapsible>
              <AccordionItem value="open">
                <AccordionTrigger className="py-1 text-xs">Show payload</AccordionTrigger>
                <AccordionContent>
                  <ScrollArea className="max-h-40 rounded-md border bg-muted/30">
                    <pre className="p-3 font-mono text-xs leading-5">{JSON.stringify(metaCognition, null, 2)}</pre>
                  </ScrollArea>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          ) : (
            <p className="text-sm text-muted-foreground">No `diagnostics.meta_cognition` payload.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default MetaPanel;
