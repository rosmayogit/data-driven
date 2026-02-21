import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { BasicInfoTab } from "./campaign-modal/BasicInfoTab";
import { AmountTab } from "./campaign-modal/AmountTab";
import { SegmentationTab } from "./campaign-modal/SegmentationTab";
import { RedemptionTab } from "./campaign-modal/RedemptionTab";
import { LifecycleTab } from "./campaign-modal/LifecycleTab";
import { toast } from "sonner";

interface CampaignModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  campaign?: any; // For editing existing campaigns
}

export function CampaignModal({ open, onOpenChange, campaign }: CampaignModalProps) {
  const [activeTab, setActiveTab] = useState("basic");
  const [formData, setFormData] = useState({
    name: campaign?.name || "",
    type: campaign?.type || "FreeBet",
    status: campaign?.status || "Draft",
    source: campaign?.source || "Campaign",
    startDate: campaign?.startDate || "",
    endDate: campaign?.endDate || "",
    qualificationPeriod: campaign?.qualificationPeriod || "Daily",
    // Event trigger fields
    triggerEvent: campaign?.trigger?.event || "",
    regDaysLimit: campaign?.trigger?.regDaysLimit || "",
    referralCode: campaign?.trigger?.referralCode || "",
    isFirstDeposit: campaign?.trigger?.isFirstDeposit || false,
    minDepositAmount: campaign?.trigger?.minDepositAmount || "",
    depositMethod: campaign?.trigger?.depositMethod || "",
    isFirstBet: campaign?.trigger?.isFirstBet || false,
    vertical: campaign?.trigger?.vertical || "",
    product: campaign?.trigger?.product || "",
    aggregator: campaign?.trigger?.aggregator || "",
    gameProvider: campaign?.trigger?.gameProvider || "",
    specificGames: campaign?.trigger?.specificGames || "",
    betStakeAmount: campaign?.trigger?.betStakeAmount || "",
    claimCode: campaign?.trigger?.claimCode || "",
    claimLimit: campaign?.trigger?.claimLimit || "1",
    requiredFields: campaign?.trigger?.requiredFields || "",
    eventType: campaign?.trigger?.eventType || "",
    customEventName: campaign?.trigger?.customEventName || "",
    rewards: campaign?.rewards || [
      {
        id: "default",
        name: "Primary Reward",
        type: campaign?.type || "FreeBet",
        amountMode: campaign?.amount?.mode || "Fixed",
        amountValue: campaign?.amount?.value || "",
        amountFormula: campaign?.amount?.formula || "",
        currency: campaign?.amount?.currency || "NGN",
      },
    ],
    segment: campaign?.eligibility?.segment || "All",
    countries: campaign?.eligibility?.country || ["NG"],
    kycRequired: campaign?.eligibility?.kyc_required || false,
    minDeposit: campaign?.eligibility?.min_deposit_30d || 0,
    redemptionContext: campaign?.redemption?.context || "Betslip",
    redemptionScope: campaign?.redemption?.scope || "Global",
    conditions: campaign?.redemption?.conditions || [],
    turnoverMultiplier: campaign?.turnover?.required_multiplier || 0,
    countingRules: campaign?.turnover?.counting_rules || [],
    expiryMode: campaign?.expiry?.mode || "AfterIssue",
    expiryDays: campaign?.expiry?.days || 7,
    creditDay: campaign?.creditDay || "RealTime",
    clawbackEnabled: campaign?.clawback?.enabled || true,
    clawbackRules: campaign?.clawback?.rules || [],
  });

  const updateFormData = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    // Validation
    if (!formData.name) {
      toast.error("Campaign name is required");
      return;
    }

    // Validate rewards
    const rewards = formData.rewards || [];
    for (const reward of rewards) {
      if (reward.amountMode === "Fixed" && !reward.amountValue) {
        toast.error(`Amount value is required for "${reward.name || 'reward'}"`);
        setActiveTab("amount");
        return;
      }
      if (reward.amountMode === "Variable" && !reward.amountFormula) {
        toast.error(`Formula is required for "${reward.name || 'reward'}"`);
        setActiveTab("amount");
        return;
      }
    }

    // Here you would call your API to save the campaign
    console.log("Saving campaign:", formData);
    
    toast.success(campaign ? "Campaign updated successfully" : "Campaign created successfully");
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{campaign ? "Edit Campaign" : "Create New Campaign"}</DialogTitle>
          <DialogDescription>
            Configure reward parameters, eligibility rules, and lifecycle settings
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-4">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="basic">Basic</TabsTrigger>
            <TabsTrigger value="segmentation">Segmentation</TabsTrigger>
            <TabsTrigger value="amount">Rewards</TabsTrigger>
            <TabsTrigger value="redemption">Redemption</TabsTrigger>
            <TabsTrigger value="lifecycle">Lifecycle</TabsTrigger>
          </TabsList>

          <TabsContent value="basic" className="space-y-4">
            <BasicInfoTab formData={formData} updateFormData={updateFormData} />
          </TabsContent>

          <TabsContent value="segmentation" className="space-y-4">
            <SegmentationTab formData={formData} updateFormData={updateFormData} />
          </TabsContent>

          <TabsContent value="amount" className="space-y-4">
            <AmountTab formData={formData} updateFormData={updateFormData} />
          </TabsContent>

          <TabsContent value="redemption" className="space-y-4">
            <RedemptionTab formData={formData} updateFormData={updateFormData} />
          </TabsContent>

          <TabsContent value="lifecycle" className="space-y-4">
            <LifecycleTab formData={formData} updateFormData={updateFormData} />
          </TabsContent>
        </Tabs>

        <div className="flex justify-end gap-3 mt-6 pt-6 border-t">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave}>
            {campaign ? "Update Campaign" : "Create Campaign"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
