import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Calculator, Plus, Trash2, Gift } from "lucide-react";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

interface Reward {
  id: string;
  name: string;
  type: string;
  amountMode: string;
  amountValue: string;
  amountFormula: string;
  currency: string;
}

interface AmountTabProps {
  formData: any;
  updateFormData: (field: string, value: any) => void;
}

const rewardTypes = [
  { value: "FreeBet", label: "Free Bet" },
  { value: "FreeSpins", label: "Free Spins" },
  { value: "BonusCash", label: "Bonus Cash" },
  { value: "Cashback", label: "Cashback" },
  { value: "DepositMatch", label: "Deposit Match" },
  { value: "LoyaltyPoints", label: "Loyalty Points" },
];

const formulaExamples = [
  { name: "VIP Cashback", formula: "min(0.10 * losses_7d, 100000)", description: "10% of last 7 days losses, max 100k" },
  { name: "Deposit Match", formula: "min(1.0 * deposits_24h, 50000)", description: "100% match up to 50k" },
  { name: "Activity Tier", formula: "case(max_stakes_30d > 1000000, 20000, max_stakes_30d > 200000, 5000, 1000)", description: "Tiered based on max stakes" },
  { name: "Hybrid", formula: "0.05 * deposits_30d + 0.1 * losses_7d", description: "5% deposits + 10% losses" },
];

const formulaVariables = [
  { var: "deposits_24h", desc: "Deposits in last 24 hours" },
  { var: "deposits_7d", desc: "Deposits in last 7 days" },
  { var: "deposits_30d", desc: "Deposits in last 30 days" },
  { var: "stakes_7d", desc: "Total stakes in last 7 days" },
  { var: "stakes_30d", desc: "Total stakes in last 30 days" },
  { var: "max_stakes_30d", desc: "Max. stakes in last 30 days" },
  { var: "wins_7d", desc: "Total winnings in last 7 days" },
  { var: "losses_7d", desc: "Total losses in last 7 days" },
];

const generateId = () => Math.random().toString(36).substring(2, 9);

export function AmountTab({ formData, updateFormData }: AmountTabProps) {
  const rewards: Reward[] = formData.rewards || [
    {
      id: generateId(),
      name: "Primary Reward",
      type: "FreeBet",
      amountMode: "Fixed",
      amountValue: "",
      amountFormula: "",
      currency: "NGN",
    },
  ];

  const updateRewards = (newRewards: Reward[]) => {
    updateFormData("rewards", newRewards);
  };

  const addReward = () => {
    const newReward: Reward = {
      id: generateId(),
      name: `Reward ${rewards.length + 1}`,
      type: "FreeBet",
      amountMode: "Fixed",
      amountValue: "",
      amountFormula: "",
      currency: "NGN",
    };
    updateRewards([...rewards, newReward]);
  };

  const removeReward = (id: string) => {
    if (rewards.length <= 1) return;
    updateRewards(rewards.filter((r) => r.id !== id));
  };

  const updateReward = (id: string, field: keyof Reward, value: string) => {
    updateRewards(
      rewards.map((r) => (r.id === id ? { ...r, [field]: value } : r))
    );
  };

  const insertVariable = (rewardId: string, variable: string) => {
    const reward = rewards.find((r) => r.id === rewardId);
    if (!reward) return;
    const currentFormula = reward.amountFormula || "";
    updateReward(rewardId, "amountFormula", currentFormula + (currentFormula ? " + " : "") + variable);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Rewards Configuration</h3>
          <p className="text-sm text-muted-foreground">
            Configure one or more rewards for this campaign
          </p>
        </div>
        <Button onClick={addReward} variant="outline" size="sm">
          <Plus className="h-4 w-4 mr-2" />
          Add Reward
        </Button>
      </div>

      <Accordion type="multiple" defaultValue={[rewards[0]?.id]} className="space-y-3">
        {rewards.map((reward, index) => (
          <AccordionItem
            key={reward.id}
            value={reward.id}
            className="border rounded-lg px-4"
          >
            <AccordionTrigger className="hover:no-underline py-4">
              <div className="flex items-center gap-3 flex-1">
                <Gift className="h-4 w-4 text-primary" />
                <span className="font-medium">{reward.name || `Reward ${index + 1}`}</span>
                <Badge variant="secondary" className="ml-2">
                  {rewardTypes.find((t) => t.value === reward.type)?.label || reward.type}
                </Badge>
                {reward.amountMode === "Fixed" && reward.amountValue && (
                  <Badge variant="outline" className="ml-auto mr-4">
                    {reward.currency} {reward.amountValue}
                  </Badge>
                )}
              </div>
            </AccordionTrigger>
            <AccordionContent className="pb-4">
              <Card className="p-4 space-y-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1 grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Reward Name</Label>
                      <Input
                        placeholder="e.g., Welcome Bonus"
                        value={reward.name}
                        onChange={(e) => updateReward(reward.id, "name", e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Reward Type</Label>
                      <Select
                        value={reward.type}
                        onValueChange={(value) => updateReward(reward.id, "type", value)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {rewardTypes.map((type) => (
                            <SelectItem key={type.value} value={type.value}>
                              {type.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  {rewards.length > 1 && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="ml-4 text-destructive hover:text-destructive"
                      onClick={() => removeReward(reward.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>

                <div className="space-y-2">
                  <Label>Amount Mode</Label>
                  <Select
                    value={reward.amountMode}
                    onValueChange={(value) => updateReward(reward.id, "amountMode", value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Fixed">Fixed Amount</SelectItem>
                      <SelectItem value="Variable">Variable (Formula-Based)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {reward.amountMode === "Fixed" ? (
                  <div className="grid grid-cols-3 gap-4">
                    <div className="col-span-2 space-y-2">
                      <Label>Amount Value *</Label>
                      <Input
                        type="number"
                        placeholder="e.g., 5000"
                        value={reward.amountValue}
                        onChange={(e) => updateReward(reward.id, "amountValue", e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Currency</Label>
                      <Select
                        value={reward.currency}
                        onValueChange={(value) => updateReward(reward.id, "currency", value)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="NGN">NGN (₦)</SelectItem>
                          <SelectItem value="KES">KES (KSh)</SelectItem>
                          <SelectItem value="USD">USD ($)</SelectItem>
                          <SelectItem value="EUR">EUR (€)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label>Formula *</Label>
                        <Calculator className="h-4 w-4 text-muted-foreground" />
                      </div>
                      <Textarea
                        placeholder="e.g., 0.05 * deposits_30d + 0.1 * losses_7d"
                        value={reward.amountFormula}
                        onChange={(e) => updateReward(reward.id, "amountFormula", e.target.value)}
                        rows={3}
                        className="font-mono text-sm"
                      />
                      <p className="text-xs text-muted-foreground">
                        Use variables and operators (*, +, -, min, max, case)
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label>Quick Variables</Label>
                      <div className="flex flex-wrap gap-2">
                        {formulaVariables.map((item) => (
                          <Button
                            key={item.var}
                            variant="outline"
                            size="sm"
                            className="h-7 text-xs"
                            onClick={() => insertVariable(reward.id, item.var)}
                          >
                            <Plus className="h-3 w-3 mr-1" />
                            {item.var}
                          </Button>
                        ))}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Templates</Label>
                      <div className="grid grid-cols-2 gap-2">
                        {formulaExamples.map((example) => (
                          <div
                            key={example.name}
                            className="p-2 border rounded-md hover:bg-accent/50 cursor-pointer transition-colors text-xs"
                            onClick={() => updateReward(reward.id, "amountFormula", example.formula)}
                          >
                            <span className="font-medium">{example.name}</span>
                            <code className="block font-mono text-muted-foreground mt-1 truncate">
                              {example.formula}
                            </code>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4 pt-2 border-t">
                      <div className="col-span-2 space-y-2">
                        <Label>Preview</Label>
                        <div className="p-2 bg-muted rounded-md">
                          <p className="text-xs text-muted-foreground">Evaluated per user</p>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label>Currency</Label>
                        <Select
                          value={reward.currency}
                          onValueChange={(value) => updateReward(reward.id, "currency", value)}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="NGN">NGN (₦)</SelectItem>
                            <SelectItem value="KES">KES (KSh)</SelectItem>
                            <SelectItem value="USD">USD ($)</SelectItem>
                            <SelectItem value="EUR">EUR (€)</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </div>
                )}
              </Card>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>

      {rewards.length > 1 && (
        <p className="text-sm text-muted-foreground text-center pt-2">
          {rewards.length} rewards configured • All rewards will be issued together when campaign triggers
        </p>
      )}
    </div>
  );
}
