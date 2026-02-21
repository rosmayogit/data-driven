 import { useCampaign } from '@/contexts/CampaignContext';
 import { ChallengeConfig, DEFAULT_CHALLENGE_CONFIG } from '@/types/campaign';
 import { Label } from '@/components/ui/label';
 import { Switch } from '@/components/ui/switch';
 import { BettingVerticalConfig, CasinoVerticalConfig } from '../shared/VerticalConfigComponents';
 
 export function ChallengeConfigStep() {
   const { campaignData, updateCampaignData, getCurrency } = useCampaign();
   const config = campaignData.challengeConfig || DEFAULT_CHALLENGE_CONFIG;
   const currency = getCurrency();
 
   const updateConfig = (updates: Partial<ChallengeConfig>) => {
     updateCampaignData('challengeConfig', { ...config, ...updates });
   };
 
   return (
     <div className="space-y-6 max-w-2xl">
       <p className="text-sm text-muted-foreground">
         Configure the wagering challenge requirements users must complete to unlock their reward.
       </p>
 
       {/* Progress Counter */}
       <div className="flex items-center justify-between rounded-lg border p-4">
         <div>
           <Label>Show Progress Counter</Label>
           <p className="text-sm text-muted-foreground">
             Display progress toward challenge completion
           </p>
         </div>
         <Switch
           checked={config.progressCounter}
           onCheckedChange={(progressCounter) => updateConfig({ progressCounter })}
         />
       </div>
 
       {/* Vertical Configs */}
       <div className="space-y-4">
         <BettingVerticalConfig
           title="Sports Betting"
           config={config.sports}
           onChange={(sports) => updateConfig({ sports })}
           currency={currency}
         />
 
         <BettingVerticalConfig
           title="Virtuals"
           config={config.virtuals}
           onChange={(virtuals) => updateConfig({ virtuals })}
           currency={currency}
         />
 
         <CasinoVerticalConfig
           config={config.casino}
           onChange={(casino) => updateConfig({ casino })}
           currency={currency}
         />
       </div>
     </div>
   );
 }