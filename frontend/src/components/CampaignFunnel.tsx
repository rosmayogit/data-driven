import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface FunnelStage {
  label: string;
  count: number;
}

interface CampaignFunnelProps {
  stages: FunnelStage[];
}

export function CampaignFunnel({ stages }: CampaignFunnelProps) {
  const maxCount = stages[0]?.count || 1;

  const colors = [
    "bg-primary/20 text-primary",
    "bg-primary/35 text-primary",
    "bg-primary/50 text-primary-foreground",
    "bg-primary/70 text-primary-foreground",
    "bg-primary text-primary-foreground",
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>User Funnel</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {stages.map((stage, i) => {
            const pct = ((stage.count / maxCount) * 100).toFixed(1);
            const widthPct = Math.max((stage.count / maxCount) * 100, 12);
            const conversionFromPrev =
              i > 0
                ? ((stage.count / stages[i - 1].count) * 100).toFixed(1)
                : null;

            return (
              <div key={stage.label}>
                {conversionFromPrev && (
                  <div className="text-xs text-muted-foreground ml-2 mb-1">
                    ↓ {conversionFromPrev}% conversion
                  </div>
                )}
                <div className="flex items-center gap-4">
                  <div className="w-28 text-sm font-medium text-right shrink-0">
                    {stage.label}
                  </div>
                  <div className="flex-1">
                    <div
                      className={`h-10 rounded-md flex items-center px-3 transition-all ${colors[i]}`}
                      style={{ width: `${widthPct}%` }}
                    >
                      <span className="font-semibold text-sm whitespace-nowrap">
                        {stage.count.toLocaleString()}
                      </span>
                    </div>
                  </div>
                  <div className="w-14 text-sm text-muted-foreground shrink-0">
                    {pct}%
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
