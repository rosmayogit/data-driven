import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { MetricCard } from "@/components/MetricCard";
import { CampaignFunnel } from "@/components/CampaignFunnel";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Users, CheckCircle, Coins, TrendingUp, Target, CalendarDays, BarChart3, Gift } from "lucide-react";

const metricIcons = [Users, CheckCircle, Target, Gift, Coins, BarChart3, TrendingUp, CalendarDays];

const statusVariant = {
  Active: "default" as const,
  Paused: "secondary" as const,
  Archived: "outline" as const,
};

interface CampaignData {
  id: string;
  name: string;
  description: string;
  type: string;
  status: string;
  amount: string;
  startDate: string;
  endDate: string;
  metrics: { title: string; value: string }[];
  funnel: { label: string; count: number }[];
}

export default function CampaignDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [campaign, setCampaign] = useState<CampaignData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!id) return;
    fetch(`/api/campaigns/${id}`)
      .then((res) => {
        if (!res.ok) throw new Error("Not found");
        return res.json();
      })
      .then(setCampaign)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return <div className="flex items-center justify-center h-64 text-muted-foreground">Loading campaign...</div>;
  }

  if (error || !campaign) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" onClick={() => navigate(-1)}>
          <ArrowLeft className="mr-2 h-4 w-4" /> Back
        </Button>
        <p className="text-muted-foreground">Campaign not found.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight">{campaign.name}</h1>
            <Badge variant={statusVariant[campaign.status as keyof typeof statusVariant]}>
              {campaign.status}
            </Badge>
            <Badge variant="outline">{campaign.type}</Badge>
          </div>
          <p className="text-muted-foreground text-sm mt-1">
            {campaign.description} &middot; {campaign.startDate} to {campaign.endDate}
          </p>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        {campaign.metrics.map((m, i) => (
          <MetricCard
            key={m.title}
            title={m.title}
            value={m.value}
            icon={metricIcons[i % metricIcons.length]}
          />
        ))}
      </div>

      {/* Funnel */}
      <CampaignFunnel stages={campaign.funnel} />
    </div>
  );
}
