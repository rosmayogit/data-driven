import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const mockUsers = [
  {
    id: "USR-001",
    name: "John Doe",
    email: "john.doe@example.com",
    segment: "VIP",
    activeRewards: 3,
    totalIssued: 12,
    totalRedeemed: 8,
    lifetimeValue: "₦2,450,000"
  },
  {
    id: "USR-002",
    name: "Jane Smith",
    email: "jane.smith@example.com",
    segment: "New",
    activeRewards: 1,
    totalIssued: 2,
    totalRedeemed: 1,
    lifetimeValue: "₦125,000"
  },
  {
    id: "USR-003",
    name: "Michael Johnson",
    email: "michael.j@example.com",
    segment: "Returning",
    activeRewards: 2,
    totalIssued: 8,
    totalRedeemed: 6,
    lifetimeValue: "₦890,000"
  },
];

export default function Users() {
  const [searchQuery, setSearchQuery] = useState("");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Users</h1>
        <p className="text-muted-foreground">Search and preview user rewards</p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>User Lookup</CardTitle>
              <CardDescription>Search by user ID, email, or name</CardDescription>
            </div>
            <div className="relative w-96">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search users..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>Segment</TableHead>
                <TableHead className="text-right">Active Rewards</TableHead>
                <TableHead className="text-right">Total Issued</TableHead>
                <TableHead className="text-right">Total Redeemed</TableHead>
                <TableHead className="text-right">Lifetime Value</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockUsers.map((user) => (
                <TableRow key={user.id} className="cursor-pointer hover:bg-muted/50">
                  <TableCell>
                    <div>
                      <div className="font-medium">{user.name}</div>
                      <div className="text-sm text-muted-foreground">{user.email}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={user.segment === "VIP" ? "default" : "secondary"}>
                      {user.segment}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <span className="font-medium text-primary">{user.activeRewards}</span>
                  </TableCell>
                  <TableCell className="text-right">{user.totalIssued}</TableCell>
                  <TableCell className="text-right">{user.totalRedeemed}</TableCell>
                  <TableCell className="text-right font-medium">{user.lifetimeValue}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm">View Details</Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
