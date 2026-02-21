 import { useCampaign } from '@/contexts/CampaignContext';
 import { BetAndGetConfig, DEFAULT_VERTICAL_BET_CONFIG } from '@/types/campaign';
 import { BettingVerticalConfig } from '../shared/VerticalConfigComponents';
 
 const DEFAULT_CONFIG: BetAndGetConfig = {
   qualifyingBets: { ...DEFAULT_VERTICAL_BET_CONFIG },
 };
 
 export function CampaignConfigStep() {
   const { campaignData, updateCampaignData, getCurrency } = useCampaign();
   const config = campaignData.betAndGetConfig || DEFAULT_CONFIG;
   const currency = getCurrency();
 
   const updateConfig = (updates: Partial<BetAndGetConfig>) => {
     updateCampaignData('betAndGetConfig', { ...config, ...updates });
   };
 
   return (
     <div className="space-y-6 max-w-2xl">
       <p className="text-sm text-muted-foreground">
         Configure the qualifying bet requirements for this Bet &amp; Get campaign.
       </p>
 
       <BettingVerticalConfig
         title="Qualifying Bets"
         config={{ ...config.qualifyingBets, enabled: true }}
         onChange={(qualifyingBets) => updateConfig({ qualifyingBets })}
         currency={currency}
       />
     </div>
   );
 }