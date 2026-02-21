import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card } from "@/components/ui/card";

interface BasicInfoTabProps {
  formData: any;
  updateFormData: (field: string, value: any) => void;
}

export function BasicInfoTab({ formData, updateFormData }: BasicInfoTabProps) {
  return (
    <Card className="p-6 space-y-6">
      <div className="space-y-2">
        <Label htmlFor="name">Campaign Name *</Label>
        <Input
          id="name"
          placeholder="e.g., VIP Cashback Q4"
          value={formData.name}
          onChange={(e) => updateFormData("name", e.target.value)}
        />
        <p className="text-sm text-muted-foreground">
          Give your campaign a descriptive name
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="status">Status</Label>
        <Select value={formData.status} onValueChange={(value) => updateFormData("status", value)}>
          <SelectTrigger id="status">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="Draft">Draft</SelectItem>
            <SelectItem value="Active">Active</SelectItem>
            <SelectItem value="Paused">Paused</SelectItem>
            <SelectItem value="Archived">Archived</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="source">Source</Label>
        <Select value={formData.source} onValueChange={(value) => updateFormData("source", value)}>
          <SelectTrigger id="source">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="Campaign">Campaign</SelectItem>
            <SelectItem value="Manual">Manual</SelectItem>
            <SelectItem value="EventTriggered">Event Triggered</SelectItem>
          </SelectContent>
        </Select>
        <p className="text-sm text-muted-foreground">
          How rewards will be issued to users
        </p>
      </div>

      {formData.source === "EventTriggered" && (
        <div className="space-y-4 pt-4 border-t">
          <h4 className="font-semibold">Event Trigger Configuration</h4>
          
          <div className="space-y-2">
            <Label htmlFor="triggerEvent">Trigger Event *</Label>
            <Select value={formData.triggerEvent} onValueChange={(value) => updateFormData("triggerEvent", value)}>
              <SelectTrigger id="triggerEvent">
                <SelectValue placeholder="Select event" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Registration">Registration</SelectItem>
                <SelectItem value="Deposit">Deposit</SelectItem>
                <SelectItem value="BetActivity">Bet Activity</SelectItem>
                <SelectItem value="Claim">Claim</SelectItem>
                <SelectItem value="Login">Login</SelectItem>
                <SelectItem value="AppDownload">App Download</SelectItem>
                <SelectItem value="ProfileUpdate">Profile Update</SelectItem>
                <SelectItem value="AdHoc">Ad Hoc (KYC, Social, etc.)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {formData.triggerEvent === "Registration" && (
            <Card className="p-4 space-y-3 bg-muted/30">
              <p className="text-sm font-medium">Registration Parameters</p>
              <div className="space-y-2">
                <Label htmlFor="regDaysLimit">Days since registration ≤</Label>
                <Input
                  id="regDaysLimit"
                  type="number"
                  placeholder="e.g., 0 for today only"
                  value={formData.regDaysLimit}
                  onChange={(e) => updateFormData("regDaysLimit", e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="referralCode">Referral Code (optional)</Label>
                <Input
                  id="referralCode"
                  placeholder="e.g., WELCOME2024"
                  value={formData.referralCode}
                  onChange={(e) => updateFormData("referralCode", e.target.value)}
                />
              </div>
              <p className="text-xs text-muted-foreground italic">
                Example: Register today and get x2
              </p>
            </Card>
          )}

          {formData.triggerEvent === "Deposit" && (
            <Card className="p-4 space-y-3 bg-muted/30">
              <p className="text-sm font-medium">Deposit Parameters</p>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="isFirstDeposit"
                  checked={formData.isFirstDeposit}
                  onChange={(e) => updateFormData("isFirstDeposit", e.target.checked)}
                  className="rounded"
                />
                <Label htmlFor="isFirstDeposit">Is first deposit?</Label>
              </div>
              <div className="space-y-2">
                <Label htmlFor="minDepositAmount">Minimum deposit amount ≥</Label>
                <Input
                  id="minDepositAmount"
                  type="number"
                  placeholder="e.g., 1000"
                  value={formData.minDepositAmount}
                  onChange={(e) => updateFormData("minDepositAmount", e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="depositMethod">Deposit Method/Provider (optional)</Label>
                <Input
                  id="depositMethod"
                  placeholder="e.g., Card, Mobile Money"
                  value={formData.depositMethod}
                  onChange={(e) => updateFormData("depositMethod", e.target.value)}
                />
              </div>
            </Card>
          )}

          {formData.triggerEvent === "BetActivity" && (
            <Card className="p-4 space-y-3 bg-muted/30">
              <p className="text-sm font-medium">Bet Activity Parameters</p>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="isFirstBet"
                  checked={formData.isFirstBet}
                  onChange={(e) => updateFormData("isFirstBet", e.target.checked)}
                  className="rounded"
                />
                <Label htmlFor="isFirstBet">Is first bet?</Label>
              </div>
              <div className="space-y-2">
                <Label htmlFor="vertical">Vertical</Label>
                <Select value={formData.vertical} onValueChange={(value) => updateFormData("vertical", value)}>
                  <SelectTrigger id="vertical">
                    <SelectValue placeholder="Select vertical" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Sports">Sports</SelectItem>
                    <SelectItem value="Virtuals">Virtuals</SelectItem>
                    <SelectItem value="Casino">Casino</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {formData.vertical === "Sports" && (
                <div className="space-y-2">
                  <Label htmlFor="product">Product</Label>
                  <Select value={formData.product} onValueChange={(value) => updateFormData("product", value)}>
                    <SelectTrigger id="product">
                      <SelectValue placeholder="Select product" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Live">Live</SelectItem>
                      <SelectItem value="Prematch">Prematch</SelectItem>
                      <SelectItem value="Preschedule">Preschedule</SelectItem>
                      <SelectItem value="Instant">Instant</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}
              {formData.vertical === "Casino" && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="aggregator">Aggregator (optional)</Label>
                    <Input
                      id="aggregator"
                      placeholder="e.g., Evolution"
                      value={formData.aggregator}
                      onChange={(e) => updateFormData("aggregator", e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="gameProvider">Game Provider (optional)</Label>
                    <Input
                      id="gameProvider"
                      placeholder="e.g., Pragmatic Play"
                      value={formData.gameProvider}
                      onChange={(e) => updateFormData("gameProvider", e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="specificGames">Specific Games (optional)</Label>
                    <Input
                      id="specificGames"
                      placeholder="e.g., Sweet Bonanza"
                      value={formData.specificGames}
                      onChange={(e) => updateFormData("specificGames", e.target.value)}
                    />
                  </div>
                </>
              )}
              <div className="space-y-2">
                <Label htmlFor="betStakeAmount">Bet Stake Amount ≥</Label>
                <Input
                  id="betStakeAmount"
                  type="number"
                  placeholder="e.g., 500"
                  value={formData.betStakeAmount}
                  onChange={(e) => updateFormData("betStakeAmount", e.target.value)}
                />
              </div>
            </Card>
          )}

          {formData.triggerEvent === "Claim" && (
            <Card className="p-4 space-y-3 bg-muted/30">
              <p className="text-sm font-medium">Claim Parameters</p>
              <div className="space-y-2">
                <Label htmlFor="claimCode">Claim Code (optional)</Label>
                <Input
                  id="claimCode"
                  placeholder="e.g., FREEBONUS"
                  value={formData.claimCode}
                  onChange={(e) => updateFormData("claimCode", e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="claimLimit">Max Claims per User</Label>
                <Input
                  id="claimLimit"
                  type="number"
                  placeholder="e.g., 1"
                  value={formData.claimLimit}
                  onChange={(e) => updateFormData("claimLimit", e.target.value)}
                />
              </div>
              <p className="text-xs text-muted-foreground italic">
                User must manually claim this reward (one-click claim button)
              </p>
            </Card>
          )}

          {formData.triggerEvent === "Login" && (
            <Card className="p-4 bg-muted/30">
              <p className="text-sm text-muted-foreground">Login event will trigger reward automatically when user logs in.</p>
            </Card>
          )}

          {formData.triggerEvent === "AppDownload" && (
            <Card className="p-4 bg-muted/30">
              <p className="text-sm text-muted-foreground">App download event will trigger reward when user installs and opens the mobile app.</p>
            </Card>
          )}

          {formData.triggerEvent === "ProfileUpdate" && (
            <Card className="p-4 space-y-3 bg-muted/30">
              <p className="text-sm font-medium">Profile Update Parameters</p>
              <div className="space-y-2">
                <Label htmlFor="requiredFields">Required Fields (comma-separated)</Label>
                <Input
                  id="requiredFields"
                  placeholder="e.g., phone, email, address"
                  value={formData.requiredFields}
                  onChange={(e) => updateFormData("requiredFields", e.target.value)}
                />
              </div>
            </Card>
          )}

          {formData.triggerEvent === "AdHoc" && (
            <Card className="p-4 space-y-3 bg-muted/30">
              <p className="text-sm font-medium">Ad Hoc Event Parameters</p>
              <div className="space-y-2">
                <Label htmlFor="eventType">Event Type</Label>
                <Select value={formData.eventType} onValueChange={(value) => updateFormData("eventType", value)}>
                  <SelectTrigger id="eventType">
                    <SelectValue placeholder="Select event type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="KYC">KYC Completion</SelectItem>
                    <SelectItem value="Social">Social Profile Link</SelectItem>
                    <SelectItem value="Custom">Custom Event</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {formData.eventType === "Custom" && (
                <div className="space-y-2">
                  <Label htmlFor="customEventName">Custom Event Name</Label>
                  <Input
                    id="customEventName"
                    placeholder="e.g., birthday_bonus"
                    value={formData.customEventName}
                    onChange={(e) => updateFormData("customEventName", e.target.value)}
                  />
                </div>
              )}
            </Card>
          )}
        </div>
      )}

      <div className="space-y-4 pt-4 border-t">
        <h3 className="text-lg font-semibold">Campaign Duration & Frequency</h3>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="startDate">Campaign Start Date *</Label>
            <Input
              id="startDate"
              type="date"
              value={formData.startDate}
              onChange={(e) => updateFormData("startDate", e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="endDate">Campaign End Date *</Label>
            <Input
              id="endDate"
              type="date"
              value={formData.endDate}
              onChange={(e) => updateFormData("endDate", e.target.value)}
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="qualificationPeriod">Qualification Time Period</Label>
          <Select value={formData.qualificationPeriod} onValueChange={(value) => updateFormData("qualificationPeriod", value)}>
            <SelectTrigger id="qualificationPeriod">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Daily">Daily</SelectItem>
              <SelectItem value="Weekly">Weekly</SelectItem>
              <SelectItem value="Monthly">Monthly</SelectItem>
              <SelectItem value="Campaign">Entire Campaign Duration</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-sm text-muted-foreground">
            How often users qualify for rewards during the campaign
          </p>
        </div>
      </div>

    </Card>
  );
}
