import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Plus, X } from "lucide-react";
import { useState } from "react";

interface RedemptionTabProps {
  formData: any;
  updateFormData: (field: string, value: any) => void;
}

export function RedemptionTab({ formData, updateFormData }: RedemptionTabProps) {
  const [newCondition, setNewCondition] = useState("");

  const addCondition = () => {
    if (newCondition.trim()) {
      updateFormData("conditions", [...(formData.conditions || []), newCondition]);
      setNewCondition("");
    }
  };

  const removeCondition = (index: number) => {
    const updated = formData.conditions.filter((_: any, i: number) => i !== index);
    updateFormData("conditions", updated);
  };

  const toggleCountingRule = (rule: string) => {
    const rules = formData.countingRules || [];
    if (rules.includes(rule)) {
      updateFormData("countingRules", rules.filter((r: string) => r !== rule));
    } else {
      updateFormData("countingRules", [...rules, rule]);
    }
  };

  const getContextOptions = () => {
    switch (formData.type) {
      case "FreeBet":
      case "SportsBonus":
        return ["Betslip"];
      case "FreeSpin":
      case "CasinoBonus":
        return ["Game"];
      case "Cash":
        return ["Wallet"];
      default:
        return ["Betslip", "Game", "Wallet"];
    }
  };

  return (
    <Card className="p-6 space-y-6">
      <div className="space-y-2">
        <Label htmlFor="redemptionContext">Redemption Context</Label>
        <Select 
          value={formData.redemptionContext} 
          onValueChange={(value) => updateFormData("redemptionContext", value)}
        >
          <SelectTrigger id="redemptionContext">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {getContextOptions().map((option) => (
              <SelectItem key={option} value={option}>{option}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <p className="text-sm text-muted-foreground">
          Where this reward can be redeemed
        </p>
      </div>

      {(formData.type === "FreeBet" || formData.type === "SportsBonus") && (
        <div className="space-y-2">
          <Label htmlFor="redemptionScope">Redemption Scope</Label>
          <Select 
            value={formData.redemptionScope} 
            onValueChange={(value) => updateFormData("redemptionScope", value)}
          >
            <SelectTrigger id="redemptionScope">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Global">All Sports</SelectItem>
              <SelectItem value="Sport">Specific Sport</SelectItem>
              <SelectItem value="Virtuals">Virtuals</SelectItem>
              <SelectItem value="Competition">Specific Competition</SelectItem>
              <SelectItem value="Team">Specific Team</SelectItem>
              <SelectItem value="Market">Specific Market</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-sm text-muted-foreground">
            Limit where this reward can be used
          </p>
        </div>
      )}

      <div className="space-y-3">
        <Label>Redemption Conditions</Label>
        <div className="flex gap-2">
          <Input
            placeholder="e.g., min_odds >= 1.5"
            value={newCondition}
            onChange={(e) => setNewCondition(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && addCondition()}
          />
          <Button type="button" onClick={addCondition} size="icon">
            <Plus className="h-4 w-4" />
          </Button>
        </div>
        <div className="flex flex-wrap gap-2">
          {formData.conditions?.map((condition: string, index: number) => (
            <Badge key={index} variant="secondary" className="pl-3 pr-2">
              {condition}
              <X
                className="ml-2 h-3 w-3 cursor-pointer"
                onClick={() => removeCondition(index)}
              />
            </Badge>
          ))}
        </div>
        <p className="text-sm text-muted-foreground">
          Add conditions like minimum odds, bet types, or selection counts
        </p>
      </div>

      {(formData.type === "SportsBonus" || formData.type === "CasinoBonus") && (
        <>
          <div className="space-y-2">
            <Label htmlFor="turnoverMultiplier">Turnover Multiplier</Label>
            <Input
              id="turnoverMultiplier"
              type="number"
              step="0.1"
              placeholder="e.g., 3.0"
              value={formData.turnoverMultiplier}
              onChange={(e) => updateFormData("turnoverMultiplier", parseFloat(e.target.value) || 0)}
            />
            <p className="text-sm text-muted-foreground">
              Required turnover multiplier before bonus converts to cash (e.g., 3x means user must wager 3x the bonus amount)
            </p>
          </div>

          <div className="space-y-3">
            <Label>Counting Rules</Label>
            <div className="space-y-2">
              {["stakes_only", "exclude_free_bets", "exclude_jackpots", "winning_bets_only"].map((rule) => (
                <div
                  key={rule}
                  className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                    formData.countingRules?.includes(rule) ? "bg-primary/10 border-primary" : "hover:bg-accent/50"
                  }`}
                  onClick={() => toggleCountingRule(rule)}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">
                      {rule.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                    </span>
                    {formData.countingRules?.includes(rule) && (
                      <Badge variant="default">Selected</Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </Card>
  );
}
