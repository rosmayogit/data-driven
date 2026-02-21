import { useCampaign } from '@/contexts/CampaignContext';
import { COUNTRIES, Country } from '@/types/campaign';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

export function CountryStep() {
  const { campaignData, updateCampaignData, validationErrors } = useCampaign();

  const handleSelect = (country: Country) => {
    const config = COUNTRIES.find((c) => c.code === country);
    if (config?.status === 'blocked') return;
    updateCampaignData('country', country);
  };

  const hasError = validationErrors.some((e) => e.field === 'country');

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Select the target country for this campaign. This will determine the currency used for all monetary values.
      </p>

      {hasError && (
        <p className="text-sm text-destructive">Please select a country to continue</p>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {COUNTRIES.map((country) => {
          const isBlocked = country.status === 'blocked';
          const isSelected = campaignData.country === country.code;

          return (
            <button
              key={country.code}
              onClick={() => handleSelect(country.code)}
              disabled={isBlocked}
              className={cn(
                'relative flex flex-col items-center gap-2 rounded-lg border p-4 transition-all',
                isBlocked
                  ? 'cursor-not-allowed border-border opacity-50'
                  : 'hover:border-primary',
                isSelected && !isBlocked
                  ? 'border-primary bg-primary/5 ring-2 ring-primary ring-offset-2'
                  : 'border-border'
              )}
            >
              {isBlocked && (
                <Badge variant="secondary" className="absolute -top-2 -right-2 text-[10px]">
                  Pending
                </Badge>
              )}
              <span className="text-3xl">{country.flag}</span>
              <span className="font-medium">{country.name}</span>
              <span className="text-xs text-muted-foreground">
                {country.currency.code} ({country.currency.symbol})
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}