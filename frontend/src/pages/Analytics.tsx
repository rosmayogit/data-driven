import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

const issuanceData = [
  { date: "Oct 1", freeBets: 340, freeSpins: 450, cash: 120, sportsBonus: 80, casinoBonus: 95 },
  { date: "Oct 2", freeBets: 380, freeSpins: 520, cash: 145, sportsBonus: 92, casinoBonus: 110 },
  { date: "Oct 3", freeBets: 420, freeSpins: 480, cash: 132, sportsBonus: 105, casinoBonus: 88 },
  { date: "Oct 4", freeBets: 390, freeSpins: 510, cash: 158, sportsBonus: 98, casinoBonus: 102 },
  { date: "Oct 5", freeBets: 445, freeSpins: 550, cash: 171, sportsBonus: 112, casinoBonus: 125 },
  { date: "Oct 6", freeBets: 410, freeSpins: 490, cash: 149, sportsBonus: 89, casinoBonus: 95 },
  { date: "Oct 7", freeBets: 475, freeSpins: 580, cash: 185, sportsBonus: 125, casinoBonus: 138 },
];

const redemptionData = [
  { type: "Free Bet", issued: 3421, redeemed: 2156, rate: 63 },
  { type: "Free Spin", issued: 2890, redeemed: 2003, rate: 69 },
  { type: "Cash", issued: 1247, redeemed: 892, rate: 72 },
  { type: "Sports Bonus", issued: 567, redeemed: 423, rate: 75 },
  { type: "Casino Bonus", issued: 892, redeemed: 445, rate: 50 },
];

export default function Analytics() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
          <p className="text-muted-foreground">Campaign performance and insights</p>
        </div>
        <Select defaultValue="7d">
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

      <Card>
        <CardHeader>
          <CardTitle>Reward Issuance Trends</CardTitle>
          <CardDescription>Daily reward issuance by type</CardDescription>
        </CardHeader>
        <CardContent>
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
              <Line type="monotone" dataKey="sportsBonus" stroke="hsl(var(--chart-3))" name="Sports Bonus" strokeWidth={2} />
              <Line type="monotone" dataKey="casinoBonus" stroke="hsl(var(--chart-4))" name="Casino Bonus" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Redemption Performance</CardTitle>
          <CardDescription>Issued vs redeemed rewards by type</CardDescription>
        </CardHeader>
        <CardContent>
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
          <div className="grid grid-cols-5 gap-4 mt-6">
            {redemptionData.map((item) => (
              <div key={item.type} className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-primary">{item.rate}%</div>
                <div className="text-sm text-muted-foreground">{item.type}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
