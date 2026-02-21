import { useParams, useNavigate } from "react-router-dom";
import { MetricCard } from "@/components/MetricCard";
import { CampaignFunnel } from "@/components/CampaignFunnel";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Users, CheckCircle, Coins, TrendingUp, Target, CalendarDays, BarChart3 } from "lucide-react";

const campaignData: Record<string, {
  name: string;
  type: string;
  status: string;
  metrics: { title: string; value: string | number; icon: any; description?: string };
  funnel: { label: string; count: number }[];
}> = {
  "1": {
    name: "VIP Cashback Q4",
    type: "Cash",
    status: "Active",
    metrics: {} as any,
    funnel: [],
  },
  "2": {
    name: "Welcome Free Bet",
    type: "FreeBet",
    status: "Active",
    metrics: {} as any,
    funnel: [],
  },
  "3": {
    name: "Casino Bonus Weekend",
    type: "CasinoBonus",
    status: "Paused",
    metrics: {} as any,
    funnel: [],
  },
};

const mockMetrics: Record<string, { title: string; value: string | number; icon: any; description?: string }[]> = {
  "1": [
    { title: "Active Users in Promo", value: "1,247", icon: Users, description: "Users with ≥1 bet placed" },
    { title: "Users Completed", value: "892", icon: CheckCircle, description: "Fulfilled promo requirements" },
    { title: "Total Stakes", value: "NGN 45.2M", icon: Coins },
    { title: "Expected NGR Uplift/User", value: "NGN 1,250", icon: TrendingUp },
    { title: "Avg. Bet", value: "NGN 3,420", icon: Target },
    { title: "Avg. Active Days", value: "4.7", icon: CalendarDays, description: "Consecutive days" },
    { title: "ARPU Uplift", value: "+18.3%", icon: BarChart3, description: "vs non-participating users" },
  ],
  "2": [
    { title: "Active Users in Promo", value: "2,856", icon: Users, description: "Users with ≥1 bet placed" },
    { title: "Users Completed", value: "2,156", icon: CheckCircle, description: "Fulfilled promo requirements" },
    { title: "Total Stakes", value: "NGN 78.4M", icon: Coins },
    { title: "Expected NGR Uplift/User", value: "NGN 980", icon: TrendingUp },
    { title: "Avg. Bet", value: "NGN 2,150", icon: Target },
    { title: "Avg. Active Days", value: "3.2", icon: CalendarDays, description: "Consecutive days" },
    { title: "ARPU Uplift", value: "+12.7%", icon: BarChart3, description: "vs non-participating users" },
  ],
  "3": [
    { title: "Active Users in Promo", value: "423", icon: Users, description: "Users with ≥1 bet placed" },
    { title: "Users Completed", value: "445", icon: CheckCircle, description: "Fulfilled promo requirements" },
    { title: "Total Stakes", value: "NGN 12.8M", icon: Coins },
    { title: "Expected NGR Uplift/User", value: "NGN 750", icon: TrendingUp },
    { title: "Avg. Bet", value: "NGN 4,800", icon: Target },
    { title: "Avg. Active Days", value: "2.1", icon: CalendarDays, description: "Consecutive days" },
    { title: "ARPU Uplift", value: "+8.5%", icon: BarChart3, description: "vs non-participating users" },
  ],
};

const mockFunnels: Record<string, { label: string; count: number }[]> = {
  "1": [
    { label: "Assigned", count: 5000 },
    { label: "Opted In", count: 3200 },
    { label: "Participating", count: 2100 },
    { label: "Rewarded", count: 892 },
    { label: "Redeemed", count: 645 },
  ],
  "2": [
    { label: "Assigned", count: 8500 },
    { label: "Opted In", count: 5600 },
    { label: "Participating", count: 3800 },
    { label: "Rewarded", count: 2156 },
    { label: "Redeemed", count: 1820 },
  ],
  "3": [
    { label: "Assigned", count: 2000 },
    { label: "Opted In", count: 1200 },
    { label: "Participating", count: 680 },
    { label: "Rewarded", count: 445 },
    { label: "Redeemed", count: 312 },
  ],
};

const statusVariant = {
  Active: "default" as const,
  Paused: "secondary" as const,
  Archived: "outline" as const,
};

export default function CampaignDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const campaign = id ? campaignData[id] : null;
  const metrics = id ? mockMetrics[id] : null;
  const funnel = id ? mockFunnels[id] : null;

  if (!campaign || !metrics || !funnel) {
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
          <p className="text-muted-foreground text-sm mt-1">Campaign analytics & performance</p>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        {metrics.map((m) => (
          <MetricCard
            key={m.title}
            title={m.title}
            value={m.value}
            icon={m.icon}
            description={m.description}
          />
        ))}
      </div>

      {/* Funnel */}
      <CampaignFunnel stages={funnel} />
    </div>
  );
}
