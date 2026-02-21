import { useState } from "react";
 import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plus, Search, Filter } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const mockCampaigns = [
  { 
    id: "RW-2024-001",
    name: "VIP Cashback Q4",
    type: "Cash",
    status: "Active",
    amount: { mode: "Variable", value: "0.10 * losses_7d" },
    issued: 1247,
    redeemed: 892,
    active: 203,
    expired: 152,
    createdAt: "2024-10-01"
  },
  { 
    id: "RW-2024-002",
    name: "Welcome Free Bet",
    type: "FreeBet",
    status: "Active",
    amount: { mode: "Fixed", value: "5000 NGN" },
    issued: 3421,
    redeemed: 2156,
    active: 891,
    expired: 374,
    createdAt: "2024-09-15"
  },
  { 
    id: "RW-2024-003",
    name: "Casino Bonus Weekend",
    type: "CasinoBonus",
    status: "Paused",
    amount: { mode: "Fixed", value: "10000 NGN" },
    issued: 892,
    redeemed: 445,
    active: 12,
    expired: 435,
    createdAt: "2024-10-05"
  },
  { 
    id: "RW-2024-004",
    name: "Sports Deposit Match",
    type: "SportsBonus",
    status: "Active",
    amount: { mode: "Variable", value: "1.0 * deposits_24h" },
    issued: 567,
    redeemed: 423,
    active: 89,
    expired: 55,
    createdAt: "2024-10-08"
  },
  { 
    id: "RW-2024-005",
    name: "Free Spins Friday",
    type: "FreeSpin",
    status: "Archived",
    amount: { mode: "Fixed", value: "50 spins" },
    issued: 2341,
    redeemed: 2003,
    active: 0,
    expired: 338,
    createdAt: "2024-09-01"
  },
];

const statusColors = {
  Active: "default",
  Paused: "secondary",
  Archived: "outline",
} as const;

const typeColors = {
  FreeBet: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  FreeSpin: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300",
  Cash: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
  SportsBonus: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300",
  CasinoBonus: "bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-300",
};

export default function Campaigns() {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
   const navigate = useNavigate();

  return (
    <>
      <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Campaigns</h1>
          <p className="text-muted-foreground">Manage and monitor your reward campaigns</p>
        </div>
         <Button onClick={() => navigate('/campaigns/create')}>
          <Plus className="mr-2 h-4 w-4" />
          Create Campaign
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>All Campaigns</CardTitle>
              <CardDescription>View and manage all reward campaigns</CardDescription>
            </div>
            <div className="flex gap-2">
              <div className="relative w-64">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search campaigns..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-32">
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="paused">Paused</SelectItem>
                  <SelectItem value="archived">Archived</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Campaign</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead className="text-right">Issued</TableHead>
                <TableHead className="text-right">Redeemed</TableHead>
                <TableHead className="text-right">Active</TableHead>
                <TableHead className="text-right">Expired</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockCampaigns.map((campaign) => (
                <TableRow key={campaign.id} className="cursor-pointer hover:bg-muted/50">
                  <TableCell>
                    <div>
                      <div className="font-medium">{campaign.name}</div>
                      <div className="text-sm text-muted-foreground">{campaign.id}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className={typeColors[campaign.type as keyof typeof typeColors]}>
                      {campaign.type}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={statusColors[campaign.status as keyof typeof statusColors]}>
                      {campaign.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">
                      <div className="font-medium">{campaign.amount.mode}</div>
                      <div className="text-muted-foreground">{campaign.amount.value}</div>
                    </div>
                  </TableCell>
                  <TableCell className="text-right font-medium">{campaign.issued.toLocaleString()}</TableCell>
                  <TableCell className="text-right">{campaign.redeemed.toLocaleString()}</TableCell>
                  <TableCell className="text-right text-primary">{campaign.active.toLocaleString()}</TableCell>
                  <TableCell className="text-right text-muted-foreground">{campaign.expired.toLocaleString()}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm" onClick={() => navigate(`/campaigns/${mockCampaigns.indexOf(campaign) + 1}`)}>View</Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
      </div>
    </>
  );
}
