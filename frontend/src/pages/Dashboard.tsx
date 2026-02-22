import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { MetricCard } from "@/components/MetricCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, Gift, DollarSign, Users, Plus } from "lucide-react";

interface Campaign {
  id: string;
  name: string;
  type: string;
  status: string;
  issued: number;
  redeemed: number;
  redemptionRate: number;
  roi: number;
}

interface DashboardData {
  metrics: {
    activeCampaigns: number;
    rewardsIssued7d: string;
    redemptionRate: string;
    avgROI: string;
  };
  topCampaigns: Campaign[];
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/dashboard")
      .then((res) => res.json())
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-64 text-muted-foreground">Loading dashboard...</div>;
  }

  const metrics = data?.metrics ?? { activeCampaigns: 0, rewardsIssued7d: "0", redemptionRate: "0%", avgROI: "0x" };
  const campaigns = data?.topCampaigns ?? [];

  return (
      <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">Monitor reward campaigns and performance</p>
        </div>
        <Button onClick={() => navigate("/campaigns/create")}>
          <Plus className="mr-2 h-4 w-4" />
          Create Campaign
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Active Campaigns"
          value={metrics.activeCampaigns}
          icon={Gift}
        />
        <MetricCard
          title="Rewards Issued (7d)"
          value={metrics.rewardsIssued7d}
          icon={TrendingUp}
        />
        <MetricCard
          title="Redemption Rate"
          value={metrics.redemptionRate}
          icon={Users}
        />
        <MetricCard
          title="Avg ROI"
          value={metrics.avgROI}
          icon={DollarSign}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Top Campaigns</CardTitle>
          <CardDescription>Your best performing reward campaigns</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {campaigns.map((campaign) => (
              <div
                key={campaign.id}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 transition-colors cursor-pointer"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="font-semibold">{campaign.name}</h3>
                    <Badge variant={campaign.status === "Active" ? "default" : "secondary"}>
                      {campaign.status}
                    </Badge>
                    <Badge variant="outline">{campaign.type}</Badge>
                  </div>
                  <div className="flex gap-6 text-sm text-muted-foreground">
                    <span>Issued: <strong className="text-foreground">{campaign.issued.toLocaleString()}</strong></span>
                    <span>Redeemed: <strong className="text-foreground">{campaign.redeemed.toLocaleString()}</strong></span>
                    <span>Rate: <strong className="text-foreground">{campaign.redemptionRate}%</strong></span>
                    <span>ROI: <strong className="text-success">{campaign.roi}x</strong></span>
                  </div>
                </div>
                <Button variant="ghost" size="sm" onClick={() => navigate(`/campaigns/${campaign.id}`)}>View Details</Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      </div>
  );
}
