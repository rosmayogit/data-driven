import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

interface IssuanceEntry {
  date: string;
  freeBets: number;
  freeSpins: number;
  cash: number;
  casinoBonus: number;
}

interface RedemptionEntry {
  type: string;
  issued: number;
  redeemed: number;
  rate: number;
}

interface AnalyticsData {
  issuanceData: IssuanceEntry[];
  redemptionData: RedemptionEntry[];
}

export default function Analytics() {
  const [period, setPeriod] = useState("30d");
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/analytics?period=${period}`)
      .then((res) => res.json())
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [period]);

  const issuanceData = data?.issuanceData ?? [];
  const redemptionData = data?.redemptionData ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
          <p className="text-muted-foreground">Campaign performance and insights</p>
        </div>
        <Select value={period} onValueChange={setPeriod}>
          <SelectTrigger className="w-32">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7d">Last 7 days</SelectItem>
            <SelectItem value="30d">Last 30 days</SelectItem>
            <SelectItem value="90d">Last 90 days</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {loading ? (
        <div className="text-center py-8 text-muted-foreground">Loading analytics...</div>
      ) : (
      <>
      <Card>
        <CardHeader>
          <CardTitle>Reward Issuance Trends</CardTitle>
          <CardDescription>Daily reward issuance by type</CardDescription>
        </CardHeader>
        <CardContent>
          {issuanceData.length > 0 ? (
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={issuanceData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis dataKey="date" className="text-xs" />
              <YAxis className="text-xs" />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--background))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "var(--radius)"
                }}
              />
              <Legend />
              <Line type="monotone" dataKey="freeBets" stroke="hsl(var(--chart-1))" name="Free Bets" strokeWidth={2} />
              <Line type="monotone" dataKey="freeSpins" stroke="hsl(var(--chart-5))" name="Free Spins" strokeWidth={2} />
              <Line type="monotone" dataKey="cash" stroke="hsl(var(--chart-2))" name="Cash" strokeWidth={2} />
              <Line type="monotone" dataKey="casinoBonus" stroke="hsl(var(--chart-4))" name="Casino Bonus" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
          ) : (
            <div className="text-center py-8 text-muted-foreground">No issuance data for this period</div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Redemption Performance</CardTitle>
          <CardDescription>Issued vs redeemed rewards by type</CardDescription>
        </CardHeader>
        <CardContent>
          {redemptionData.length > 0 ? (
          <>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={redemptionData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis dataKey="type" className="text-xs" />
              <YAxis className="text-xs" />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--background))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "var(--radius)"
                }}
              />
              <Legend />
              <Bar dataKey="issued" fill="hsl(var(--chart-1))" name="Issued" radius={[4, 4, 0, 0]} />
              <Bar dataKey="redeemed" fill="hsl(var(--chart-2))" name="Redeemed" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
            {redemptionData.map((item) => (
              <div key={item.type} className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-primary">{item.rate}%</div>
                <div className="text-sm text-muted-foreground">{item.type}</div>
              </div>
            ))}
          </div>
          </>
          ) : (
            <div className="text-center py-8 text-muted-foreground">No redemption data available</div>
          )}
        </CardContent>
      </Card>
      </>
      )}
    </div>
  );
}
