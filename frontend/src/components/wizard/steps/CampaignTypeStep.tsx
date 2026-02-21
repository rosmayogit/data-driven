 import { useCampaign } from '@/contexts/CampaignContext';
 import { CAMPAIGN_TYPES, CampaignType, REWARD_TYPES } from '@/types/campaign';
 import { Badge } from '@/components/ui/badge';
 import { cn } from '@/lib/utils';
 import { Gift, Zap, Target, Gamepad2 } from 'lucide-react';
 
 const ICONS: Record<CampaignType, React.ReactNode> = {
   simple: <Gift className="h-6 w-6" />,
   triggered: <Zap className="h-6 w-6" />,
   'bet-and-get': <Target className="h-6 w-6" />,
   'free-to-play': <Gamepad2 className="h-6 w-6" />,
 };
 
 export function CampaignTypeStep() {
   const { campaignData, updateCampaignData, validationErrors } = useCampaign();
 
   const handleSelect = (type: CampaignType) => {
     updateCampaignData('campaignType', type);
     // Clear type-specific configs when changing type
     updateCampaignData('triggeredConfig', undefined);
     updateCampaignData('betAndGetConfig', undefined);
     updateCampaignData('freeToPlayConfig', undefined);
     updateCampaignData('freeToPlayMechanicsConfig', undefined);
     updateCampaignData('challengeConfig', undefined);
   };
 
   const hasError = validationErrors.some((e) => e.field === 'campaignType');
 
   return (
     <div className="space-y-4">
       <p className="text-sm text-muted-foreground">
         Select the type of campaign you want to create. Each type has different configuration options and allowed rewards.
       </p>
 
       {hasError && (
         <p className="text-sm text-destructive">Please select a campaign type to continue</p>
       )}
 
       <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
         {CAMPAIGN_TYPES.map((campaign) => (
           <button
             key={campaign.type}
             onClick={() => handleSelect(campaign.type)}
             className={cn(
               'flex flex-col items-start gap-3 rounded-lg border p-5 text-left transition-all hover:border-primary',
               campaignData.campaignType === campaign.type
                 ? 'border-primary bg-primary/5 ring-2 ring-primary ring-offset-2'
                 : 'border-border'
             )}
           >
             <div className="flex items-center gap-3">
               <div className={cn(
                 'rounded-lg p-2',
                 campaignData.campaignType === campaign.type
                   ? 'bg-primary text-primary-foreground'
                   : 'bg-muted'
               )}>
                 {ICONS[campaign.type]}
               </div>
               <h3 className="font-semibold text-lg">{campaign.title}</h3>
             </div>
             <p className="text-sm text-muted-foreground">{campaign.description}</p>
             <div className="flex flex-wrap gap-1 mt-2">
               {campaign.allowedRewards.map((rewardType) => {
                 const reward = REWARD_TYPES.find((r) => r.type === rewardType);
                 return (
                   <Badge key={rewardType} variant="outline" className="text-xs">
                     {reward?.title}
                   </Badge>
                 );
               })}
             </div>
           </button>
         ))}
       </div>
     </div>
   );
 }