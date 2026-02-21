import { useNavigate } from "react-router-dom";
import { MetricCard } from "@/components/MetricCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, Gift, DollarSign, Users, Plus } from "lucide-react";

const mockCampaigns = [
  { 
    id: 1, 
    name: "VIP Cashback Q4", 
    type: "Cash", 
    status: "Active", 
    issued: 1247, 
    redeemed: 892,
    redemptionRate: 71.5,
    roi: 2.3
  },
  { 
    id: 2, 
    name: "Welcome Free Bet", 
    type: "FreeBet", 
    status: "Active", 
    issued: 3421, 
    redeemed: 2156,
    redemptionRate: 63.0,
    roi: 1.8
  },
  { 
    id: 3, 
    name: "Casino Bonus Weekend", 
    type: "CasinoBonus", 
    status: "Paused", 
    issued: 892, 
    redeemed: 445,
    redemptionRate: 49.9,
    roi: 1.2
  },
];

export default function Dashboard() {
  const navigate = useNavigate();

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
          value={12}
          change={{ value: "2", positive: true }}
          icon={Gift}
        />
        <MetricCard
          title="Rewards Issued (7d)"
          value="8.2K"
          change={{ value: "12.3%", positive: true }}
          icon={TrendingUp}
        />
        <MetricCard
          title="Redemption Rate"
          value="68.4%"
          change={{ value: "3.2%", positive: true }}
          icon={Users}
        />
        <MetricCard
          title="Avg ROI"
          value="1.9x"
          change={{ value: "0.3x", positive: true }}
          icon={DollarSign}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Active Campaigns</CardTitle>
          <CardDescription>Overview of your current reward campaigns</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {mockCampaigns.map((campaign) => (
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
