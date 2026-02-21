 import { useCampaign } from '@/contexts/CampaignContext';
 import {
   RewardType,
   REWARD_TYPES,
   CAMPAIGN_TYPES,
   FreeBetRewardConfig,
   FreeSpinsRewardConfig,
   CashRewardConfig,
   BonusWalletRewardConfig,
   RewardConfig,
   DEFAULT_CHALLENGE_CONFIG,
 } from '@/types/campaign';
 import { Label } from '@/components/ui/label';
 import { Input } from '@/components/ui/input';
 import { Switch } from '@/components/ui/switch';
 import { Badge } from '@/components/ui/badge';
 import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
 import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
 import { ChevronDown, Gift, Sparkles, Banknote, Wallet } from 'lucide-react';
 import { cn } from '@/lib/utils';
 import { CasinoVerticalConfig, BettingVerticalConfig } from '../shared/VerticalConfigComponents';
 
 const REWARD_ICONS: Record<RewardType, React.ReactNode> = {
   'free-bet': <Gift className="h-5 w-5" />,
   'free-spins': <Sparkles className="h-5 w-5" />,
   cash: <Banknote className="h-5 w-5" />,
   'bonus-wallet': <Wallet className="h-5 w-5" />,
 };
 
 export function RewardStep() {
   const { campaignData, updateCampaignData, getCurrency, validationErrors } = useCampaign();
   const currency = getCurrency();
 
   const campaignType = CAMPAIGN_TYPES.find((t) => t.type === campaignData.campaignType);
   const allowedRewards = campaignType?.allowedRewards || [];
 
   const toggleReward = (rewardType: RewardType) => {
     const current = campaignData.selectedRewards;
     const isSelected = current.includes(rewardType);
 
     if (isSelected) {
       updateCampaignData(
         'selectedRewards',
         current.filter((r) => r !== rewardType)
       );
       updateCampaignData(
         'rewardConfigs',
         campaignData.rewardConfigs.filter((c) => c.type !== rewardType)
       );
     } else {
       updateCampaignData('selectedRewards', [...current, rewardType]);
       // Add default config for new reward
       const defaultConfig = getDefaultRewardConfig(rewardType);
       updateCampaignData('rewardConfigs', [...campaignData.rewardConfigs, defaultConfig]);
     }
   };
 
   const updateRewardConfig = (rewardType: RewardType, updates: Record<string, unknown>) => {
     updateCampaignData(
       'rewardConfigs',
       campaignData.rewardConfigs.map((config) =>
         config.type === rewardType ? ({ ...config, ...updates } as RewardConfig) : config
       )
     );
   };
 
   const getRewardConfig = (rewardType: RewardType): RewardConfig | undefined => {
     return campaignData.rewardConfigs.find((c) => c.type === rewardType);
   };
 
   const hasError = validationErrors.some((e) => e.field === 'selectedRewards');
 
   return (
     <div className="space-y-6">
       <p className="text-sm text-muted-foreground">
         Select and configure the rewards for this campaign. You can add multiple reward types.
       </p>
 
       {hasError && (
         <p className="text-sm text-destructive">Please select at least one reward type</p>
       )}
 
       {/* Reward Selection */}
       <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
         {REWARD_TYPES.map((reward) => {
           const isAllowed = allowedRewards.includes(reward.type);
           const isSelected = campaignData.selectedRewards.includes(reward.type);
 
           return (
             <button
               key={reward.type}
               onClick={() => isAllowed && toggleReward(reward.type)}
               disabled={!isAllowed}
               className={cn(
                 'flex flex-col items-center gap-2 rounded-lg border p-4 transition-all',
                 isSelected && 'border-primary bg-primary/5 ring-2 ring-primary ring-offset-2',
                 !isSelected && isAllowed && 'hover:border-primary',
                 !isAllowed && 'opacity-50 cursor-not-allowed'
               )}
             >
               <div
                 className={cn(
                   'rounded-lg p-2',
                   isSelected ? 'bg-primary text-primary-foreground' : 'bg-muted'
                 )}
               >
                 {REWARD_ICONS[reward.type]}
               </div>
               <span className="font-medium text-sm">{reward.title}</span>
               {!isAllowed && (
                 <Badge variant="outline" className="text-xs">
                   Not Available
                 </Badge>
               )}
             </button>
           );
         })}
       </div>
 
       {/* Reward Configurations */}
       <div className="space-y-4">
         {campaignData.selectedRewards.map((rewardType) => {
           const config = getRewardConfig(rewardType);
           if (!config) return null;
 
           return (
             <RewardConfigSection
               key={rewardType}
               rewardType={rewardType}
               config={config}
               onUpdate={(updates) => updateRewardConfig(rewardType, updates)}
               currency={currency}
             />
           );
         })}
       </div>
     </div>
   );
 }
 
 interface RewardConfigSectionProps {
   rewardType: RewardType;
   config: RewardConfig;
   onUpdate: (updates: Partial<RewardConfig>) => void;
   currency: ReturnType<typeof useCampaign>['getCurrency'] extends () => infer R ? R : never;
 }
 
 function RewardConfigSection({ rewardType, config, onUpdate, currency }: RewardConfigSectionProps) {
   const rewardInfo = REWARD_TYPES.find((r) => r.type === rewardType);
 
   return (
     <Collapsible defaultOpen>
       <Card>
         <CollapsibleTrigger className="w-full">
           <CardHeader className="flex flex-row items-center justify-between py-3">
             <div className="flex items-center gap-3">
               <div className="rounded-lg p-2 bg-primary text-primary-foreground">
                 {REWARD_ICONS[rewardType]}
               </div>
               <CardTitle className="text-base">{rewardInfo?.title} Configuration</CardTitle>
             </div>
             <ChevronDown className="h-5 w-5 text-muted-foreground" />
           </CardHeader>
         </CollapsibleTrigger>
         <CollapsibleContent>
           <CardContent className="space-y-4 pt-0">
             {rewardType === 'free-bet' && (
               <FreeBetConfig
                 config={config as FreeBetRewardConfig}
                 onUpdate={onUpdate}
                 currency={currency}
               />
             )}
             {rewardType === 'free-spins' && (
               <FreeSpinsConfig
                 config={config as FreeSpinsRewardConfig}
                 onUpdate={onUpdate}
                 currency={currency}
               />
             )}
             {rewardType === 'cash' && (
               <CashConfig
                 config={config as CashRewardConfig}
                 onUpdate={onUpdate}
                 currency={currency}
               />
             )}
             {rewardType === 'bonus-wallet' && (
               <BonusWalletConfig
                 config={config as BonusWalletRewardConfig}
                 onUpdate={onUpdate}
                 currency={currency}
               />
             )}
           </CardContent>
         </CollapsibleContent>
       </Card>
     </Collapsible>
   );
 }
 
 function FreeBetConfig({
   config,
   onUpdate,
   currency,
 }: {
   config: FreeBetRewardConfig;
   onUpdate: (updates: Partial<FreeBetRewardConfig>) => void;
   currency: ReturnType<typeof useCampaign>['getCurrency'] extends () => infer R ? R : never;
 }) {
   return (
     <div className="space-y-4">
       <div className="space-y-2">
         <Label>Days of Validity</Label>
         <Input
           type="number"
           value={config.daysOfValidity}
           onChange={(e) => onUpdate({ daysOfValidity: Number(e.target.value) })}
           min={1}
           placeholder="7"
         />
       </div>
 
       <div className="flex items-center justify-between rounded-lg border p-3">
         <Label>Sports Vouchers</Label>
         <Switch
           checked={config.sports.enabled}
           onCheckedChange={(enabled) => onUpdate({ sports: { ...config.sports, enabled } })}
         />
       </div>
 
       {config.sports.enabled && (
         <div className="space-y-2 pl-4 border-l-2 border-primary/20">
           <Label>Voucher Amount ({currency?.symbol})</Label>
           <Input
             type="number"
             value={config.sports.vouchers[0]?.amount || ''}
             onChange={(e) =>
               onUpdate({
                 sports: {
                   ...config.sports,
                   vouchers: [
                     {
                       id: '1',
                       amount: Number(e.target.value),
                       subcategory: 'prematch',
                       sports: ['all'],
                       markets: [],
                     },
                   ],
                 },
               })
             }
             placeholder="Enter amount"
           />
         </div>
       )}
 
       <div className="flex items-center justify-between rounded-lg border p-3">
         <Label>Virtuals Vouchers</Label>
         <Switch
           checked={config.virtuals.enabled}
           onCheckedChange={(enabled) => onUpdate({ virtuals: { ...config.virtuals, enabled } })}
         />
       </div>
 
       {config.virtuals.enabled && (
         <div className="space-y-2 pl-4 border-l-2 border-primary/20">
           <Label>Voucher Amount ({currency?.symbol})</Label>
           <Input
             type="number"
             value={config.virtuals.vouchers[0]?.amount || ''}
             onChange={(e) =>
               onUpdate({
                 virtuals: {
                   ...config.virtuals,
                   vouchers: [
                     {
                       id: '1',
                       amount: Number(e.target.value),
                       subcategory: 'prematch',
                       sports: ['all'],
                       markets: [],
                     },
                   ],
                 },
               })
             }
             placeholder="Enter amount"
           />
         </div>
       )}
     </div>
   );
 }
 
 function FreeSpinsConfig({
   config,
   onUpdate,
   currency,
 }: {
   config: FreeSpinsRewardConfig;
   onUpdate: (updates: Partial<FreeSpinsRewardConfig>) => void;
   currency: ReturnType<typeof useCampaign>['getCurrency'] extends () => infer R ? R : never;
 }) {
   return (
     <div className="space-y-4">
       <div className="grid grid-cols-2 gap-4">
         <div className="space-y-2">
           <Label>Days of Validity</Label>
           <Input
             type="number"
             value={config.daysOfValidity}
             onChange={(e) => onUpdate({ daysOfValidity: Number(e.target.value) })}
             min={1}
             placeholder="7"
           />
         </div>
         <div className="space-y-2">
           <Label>Number of Spins</Label>
           <Input
             type="number"
             value={config.config.amount}
             onChange={(e) =>
               onUpdate({ config: { ...config.config, amount: Number(e.target.value) } })
             }
             min={1}
             placeholder="10"
           />
         </div>
       </div>
 
       <CasinoVerticalConfig
         config={{
           enabled: config.config.enabled,
           minStake: 0,
           maxStake: 0,
           aggregator: config.config.aggregator,
           vendor: config.config.vendor,
           selectedGames: config.config.selectedGames,
         }}
         onChange={(casinoConfig) =>
           onUpdate({
             config: {
               ...config.config,
               enabled: casinoConfig.enabled,
               aggregator: casinoConfig.aggregator,
               vendor: casinoConfig.vendor,
               selectedGames: casinoConfig.selectedGames,
             },
           })
         }
         currency={currency}
       />
     </div>
   );
 }
 
 function CashConfig({
   config,
   onUpdate,
   currency,
 }: {
   config: CashRewardConfig;
   onUpdate: (updates: Partial<CashRewardConfig>) => void;
   currency: ReturnType<typeof useCampaign>['getCurrency'] extends () => infer R ? R : never;
 }) {
   return (
     <div className="space-y-4">
       <div className="space-y-2">
         <Label>Amount ({currency?.symbol})</Label>
         <Input
           type="number"
           value={config.amount}
           onChange={(e) => onUpdate({ amount: Number(e.target.value) })}
           placeholder="Enter amount"
         />
       </div>
 
       <div className="flex items-center justify-between rounded-lg border p-3">
         <div>
           <Label>Withdrawable</Label>
           <p className="text-xs text-muted-foreground">Allow immediate withdrawal</p>
         </div>
         <Switch
           checked={config.withdrawable}
           onCheckedChange={(withdrawable) => onUpdate({ withdrawable })}
         />
       </div>
 
       <div className="space-y-2">
         <Label>Max Redemptions (optional)</Label>
         <Input
           type="number"
           value={config.maxRedemptions || ''}
           onChange={(e) =>
             onUpdate({ maxRedemptions: e.target.value ? Number(e.target.value) : undefined })
           }
           placeholder="Unlimited"
         />
       </div>
     </div>
   );
 }
 
 function BonusWalletConfig({
   config,
   onUpdate,
   currency,
 }: {
   config: BonusWalletRewardConfig;
   onUpdate: (updates: Partial<BonusWalletRewardConfig>) => void;
   currency: ReturnType<typeof useCampaign>['getCurrency'] extends () => infer R ? R : never;
 }) {
   return (
     <div className="space-y-4">
       <div className="space-y-2">
         <Label>Bonus Amount ({currency?.symbol})</Label>
         <Input
           type="number"
           value={config.amount}
           onChange={(e) => onUpdate({ amount: Number(e.target.value) })}
           placeholder="Enter amount"
         />
       </div>
 
       <div className="rounded-lg border p-4 space-y-4">
         <h4 className="font-medium">Wagering Challenge</h4>
         <p className="text-sm text-muted-foreground">
           Configure turnover requirements to unlock bonus funds
         </p>
 
         <BettingVerticalConfig
           title="Sports Turnover"
           config={config.wageringChallenge.sports}
           onChange={(sports) =>
             onUpdate({ wageringChallenge: { ...config.wageringChallenge, sports } })
           }
           currency={currency}
         />
 
         <CasinoVerticalConfig
           config={config.wageringChallenge.casino}
           onChange={(casino) =>
             onUpdate({ wageringChallenge: { ...config.wageringChallenge, casino } })
           }
           currency={currency}
         />
       </div>
     </div>
   );
 }
 
 function getDefaultRewardConfig(rewardType: RewardType): RewardConfig {
   switch (rewardType) {
     case 'free-bet':
       return {
         type: 'free-bet',
         daysOfValidity: 7,
         sports: { enabled: false, vouchers: [] },
         virtuals: { enabled: false, vouchers: [] },
       };
     case 'free-spins':
       return {
         type: 'free-spins',
         daysOfValidity: 7,
         config: {
           enabled: true,
           amount: 10,
           aggregator: '',
           vendor: '',
           selectedGames: [],
         },
       };
     case 'cash':
       return {
         type: 'cash',
         amount: 0,
         withdrawable: false,
       };
     case 'bonus-wallet':
       return {
         type: 'bonus-wallet',
         amount: 0,
         wageringChallenge: { ...DEFAULT_CHALLENGE_CONFIG },
       };
   }
 }