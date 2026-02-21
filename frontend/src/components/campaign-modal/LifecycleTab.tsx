import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface LifecycleTabProps {
  formData: any;
  updateFormData: (field: string, value: any) => void;
}

export function LifecycleTab({ formData, updateFormData }: LifecycleTabProps) {
  const toggleClawbackRule = (rule: string) => {
    const rules = formData.clawbackRules || [];
    if (rules.includes(rule)) {
      updateFormData("clawbackRules", rules.filter((r: string) => r !== rule));
    } else {
      updateFormData("clawbackRules", [...rules, rule]);
    }
  };

  return (
    <Card className="p-6 space-y-6">
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Expiry Settings</h3>
        
        <div className="space-y-2">
          <Label htmlFor="expiryMode">Expiry Mode</Label>
          <Select 
            value={formData.expiryMode} 
            onValueChange={(value) => updateFormData("expiryMode", value)}
          >
            <SelectTrigger id="expiryMode">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="AfterIssue">Days After Issue</SelectItem>
              <SelectItem value="FixedDate">Fixed Date</SelectItem>
              <SelectItem value="FirstBet">After First Bet</SelectItem>
              <SelectItem value="Never">Never Expires</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="creditDay">Credit Day</Label>
          <Select 
            value={formData.creditDay} 
            onValueChange={(value) => updateFormData("creditDay", value)}
          >
            <SelectTrigger id="creditDay">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="RealTime">Real-time once challenge is on</SelectItem>
              <SelectItem value="SelectedDate">Selected date / Specific</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-sm text-muted-foreground">
            When the reward will be credited to user's account
          </p>
        </div>

        {formData.expiryMode === "AfterIssue" && (
          <div className="space-y-2">
            <Label htmlFor="expiryDays">Expiry Days</Label>
            <Input
              id="expiryDays"
              type="number"
              placeholder="e.g., 7"
              value={formData.expiryDays}
              onChange={(e) => updateFormData("expiryDays", parseInt(e.target.value) || 0)}
            />
            <p className="text-sm text-muted-foreground">
              Number of days until reward expires after issue
            </p>
          </div>
        )}

        <div className="bg-muted/50 p-4 rounded-lg">
          <p className="text-sm">
            <strong>Expiry Behavior:</strong> When a reward expires, it will be automatically removed from the user's account. 
            If clawback is enabled, any related funds may also be reversed.
          </p>
        </div>
      </div>

      <div className="space-y-4 pt-4 border-t">
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label htmlFor="clawbackEnabled">Enable Clawback</Label>
            <p className="text-sm text-muted-foreground">
              Reverse rewards under certain conditions
            </p>
          </div>
          <Switch
            id="clawbackEnabled"
            checked={formData.clawbackEnabled}
            onCheckedChange={(checked) => updateFormData("clawbackEnabled", checked)}
          />
        </div>

        {formData.clawbackEnabled && (
          <div className="space-y-3">
            <Label>Clawback Rules</Label>
            <div className="space-y-2">
              {[
                { id: "unused_on_expiry", label: "Unused on Expiry", desc: "Clawback if reward expires without being used" },
                { id: "withdrawal_within_24h", label: "Fast Withdrawal", desc: "Clawback if user withdraws within 24h of receiving reward" },
                { id: "breach_of_tos", label: "ToS Breach", desc: "Clawback if user violates terms of service" },
                { id: "duplicate_account", label: "Duplicate Account", desc: "Clawback if duplicate account detected" },
              ].map((rule) => (
                <div
                  key={rule.id}
                  className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                    formData.clawbackRules?.includes(rule.id) ? "bg-primary/10 border-primary" : "hover:bg-accent/50"
                  }`}
                  onClick={() => toggleClawbackRule(rule.id)}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium">{rule.label}</span>
                    {formData.clawbackRules?.includes(rule.id) && (
                      <Badge variant="default">Active</Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">{rule.desc}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="bg-amber-500/10 border border-amber-500/20 p-4 rounded-lg">
        <h4 className="font-medium text-sm mb-2 flex items-center gap-2">
          <span className="text-warning">⚠️</span> Important
        </h4>
        <p className="text-sm text-muted-foreground">
          Clawback operations are permanent and will be logged in the audit trail. 
          Make sure your clawback rules comply with local regulations and your terms of service.
        </p>
      </div>
    </Card>
  );
}
