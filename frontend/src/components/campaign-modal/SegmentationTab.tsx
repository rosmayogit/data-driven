import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { X } from "lucide-react";

interface SegmentationTabProps {
  formData: any;
  updateFormData: (field: string, value: any) => void;
}

const availableCountries = [
  { code: "NG", name: "Nigeria" },
  { code: "KE", name: "Kenya" },
  { code: "ZM", name: "Zambia" },
  { code: "ZA", name: "South Africa" },
  { code: "TZ", name: "Tanzania" },
];

export function SegmentationTab({ formData, updateFormData }: SegmentationTabProps) {
  const toggleCountry = (countryCode: string) => {
    const countries = formData.countries || [];
    if (countries.includes(countryCode)) {
      updateFormData("countries", countries.filter((c: string) => c !== countryCode));
    } else {
      updateFormData("countries", [...countries, countryCode]);
    }
  };

  return (
    <Card className="p-6 space-y-6">
      <div className="space-y-2">
        <Label htmlFor="segment">Target Segment</Label>
        <Select value={formData.segment} onValueChange={(value) => updateFormData("segment", value)}>
          <SelectTrigger id="segment">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="All">All Users</SelectItem>
            <SelectItem value="VIP">VIP Users</SelectItem>
            <SelectItem value="New">New Users</SelectItem>
            <SelectItem value="Returning">Returning Users</SelectItem>
            <SelectItem value="Custom">Custom Segment</SelectItem>
          </SelectContent>
        </Select>
        <p className="text-sm text-muted-foreground">
          Define which user segment can receive this reward
        </p>
      </div>

      <div className="space-y-3">
        <Label>Eligible Countries</Label>
        <div className="flex flex-wrap gap-2">
          {availableCountries.map((country) => {
            const isSelected = formData.countries?.includes(country.code);
            return (
              <Badge
                key={country.code}
                variant={isSelected ? "default" : "outline"}
                className="cursor-pointer"
                onClick={() => toggleCountry(country.code)}
              >
                {country.name} ({country.code})
                {isSelected && <X className="ml-1 h-3 w-3" />}
              </Badge>
            );
          })}
        </div>
        <p className="text-sm text-muted-foreground">
          Select countries where this reward is available
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="minDeposit">Minimum Deposit (30d)</Label>
          <Input
            id="minDeposit"
            type="number"
            placeholder="0"
            value={formData.minDeposit}
            onChange={(e) => updateFormData("minDeposit", parseInt(e.target.value) || 0)}
          />
          <p className="text-sm text-muted-foreground">
            Minimum deposit in last 30 days
          </p>
        </div>

        <div className="flex flex-col justify-between pt-8">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="kycRequired">KYC Required</Label>
              <p className="text-sm text-muted-foreground">
                User must complete KYC
              </p>
            </div>
            <Switch
              id="kycRequired"
              checked={formData.kycRequired}
              onCheckedChange={(checked) => updateFormData("kycRequired", checked)}
            />
          </div>
        </div>
      </div>

      <div className="bg-muted/50 p-4 rounded-lg space-y-2">
        <h4 className="font-medium text-sm">Eligibility Summary</h4>
        <div className="space-y-1 text-sm text-muted-foreground">
          <p>• Segment: <strong className="text-foreground">{formData.segment}</strong></p>
          <p>• Countries: <strong className="text-foreground">{formData.countries?.length || 0} selected</strong></p>
          <p>• Min. Deposit: <strong className="text-foreground">{formData.minDeposit} {formData.currency}</strong></p>
          <p>• KYC: <strong className="text-foreground">{formData.kycRequired ? "Required" : "Not required"}</strong></p>
        </div>
      </div>
    </Card>
  );
}
