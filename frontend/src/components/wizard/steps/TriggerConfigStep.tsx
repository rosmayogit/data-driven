 import { useCampaign } from '@/contexts/CampaignContext';
 import { TriggeredCampaignConfig, TriggerType } from '@/types/campaign';
 import { Label } from '@/components/ui/label';
 import { Input } from '@/components/ui/input';
 import { Switch } from '@/components/ui/switch';
 import { Badge } from '@/components/ui/badge';
 import { cn } from '@/lib/utils';
 import { UserPlus, Wallet, DollarSign } from 'lucide-react';
 
 const TRIGGER_OPTIONS: { type: TriggerType; title: string; description: string; icon: React.ReactNode }[] = [
   { type: 'registration', title: 'Registration', description: 'When user registers', icon: <UserPlus className="h-5 w-5" /> },
   { type: 'deposit', title: 'Deposit', description: 'When user makes a deposit', icon: <Wallet className="h-5 w-5" /> },
   { type: 'bet', title: 'Bet', description: 'When user places a bet', icon: <DollarSign className="h-5 w-5" /> },
 ];
 
 const DEFAULT_CONFIG: TriggeredCampaignConfig = {
   triggers: {
     sequence: [],
   },
   hasChallenge: false,
 };
 
 export function TriggerConfigStep() {
   const { campaignData, updateCampaignData, getCurrency } = useCampaign();
   const config = campaignData.triggeredConfig || DEFAULT_CONFIG;
   const currency = getCurrency();
 
   const updateConfig = (updates: Partial<TriggeredCampaignConfig>) => {
     updateCampaignData('triggeredConfig', { ...config, ...updates });
   };
 
   const toggleTrigger = (trigger: TriggerType) => {
     const current = config.triggers.sequence;
     const updated = current.includes(trigger)
       ? current.filter((t) => t !== trigger)
       : [...current, trigger];
     updateConfig({ triggers: { ...config.triggers, sequence: updated } });
   };
 
   const hasDeposit = config.triggers.sequence.includes('deposit');
   const hasBet = config.triggers.sequence.includes('bet');
 
   return (
     <div className="space-y-6 max-w-2xl">
       <p className="text-sm text-muted-foreground">
         Configure what actions will trigger rewards for users. You can select multiple triggers in sequence.
       </p>
 
       {/* Trigger Selection */}
       <div className="space-y-3">
         <Label>Select Triggers</Label>
         <div className="grid grid-cols-3 gap-3">
           {TRIGGER_OPTIONS.map((trigger) => (
             <button
               key={trigger.type}
               onClick={() => toggleTrigger(trigger.type)}
               className={cn(
                 'flex flex-col items-center gap-2 rounded-lg border p-4 transition-all hover:border-primary',
                 config.triggers.sequence.includes(trigger.type)
                   ? 'border-primary bg-primary/5 ring-2 ring-primary ring-offset-2'
                   : 'border-border'
               )}
             >
               <div className={cn(
                 'rounded-lg p-2',
                 config.triggers.sequence.includes(trigger.type)
                   ? 'bg-primary text-primary-foreground'
                   : 'bg-muted'
               )}>
                 {trigger.icon}
               </div>
               <span className="font-medium text-sm">{trigger.title}</span>
             </button>
           ))}
         </div>
       </div>
 
       {config.triggers.sequence.length > 0 && (
         <div className="space-y-2">
           <Label>Trigger Sequence</Label>
           <div className="flex items-center gap-2">
             {config.triggers.sequence.map((trigger, index) => (
               <div key={trigger} className="flex items-center gap-2">
                 {index > 0 && <span className="text-muted-foreground">→</span>}
                 <Badge variant="secondary">{trigger}</Badge>
               </div>
             ))}
           </div>
         </div>
       )}
 
       {/* Deposit Condition */}
       {hasDeposit && (
         <div className="space-y-4 rounded-lg border p-4">
           <h3 className="font-medium">Deposit Condition</h3>
           <div className="space-y-2">
             <Label>Minimum Amount ({currency?.symbol})</Label>
             <Input
               type="number"
               value={config.triggers.depositCondition?.minAmount || ''}
               onChange={(e) =>
                 updateConfig({
                   triggers: {
                     ...config.triggers,
                     depositCondition: {
                       minAmount: Number(e.target.value),
                       currency: currency?.code || 'NGN',
                     },
                   },
                 })
               }
               placeholder="Enter minimum deposit"
             />
           </div>
         </div>
       )}
 
       {/* Bet Condition */}
       {hasBet && (
         <div className="space-y-4 rounded-lg border p-4">
           <h3 className="font-medium">Bet Condition</h3>
           <div className="grid grid-cols-2 gap-4">
             <div className="space-y-2">
               <Label>Minimum Stake ({currency?.symbol})</Label>
               <Input
                 type="number"
                 value={config.triggers.betCondition?.minStake || ''}
                 onChange={(e) =>
                   updateConfig({
                     triggers: {
                       ...config.triggers,
                       betCondition: {
                         minStake: Number(e.target.value),
                         minOdds: config.triggers.betCondition?.minOdds || 1.5,
                       },
                     },
                   })
                 }
                 placeholder="Enter minimum stake"
               />
             </div>
             <div className="space-y-2">
               <Label>Minimum Odds</Label>
               <Input
                 type="number"
                 step="0.1"
                 value={config.triggers.betCondition?.minOdds || ''}
                 onChange={(e) =>
                   updateConfig({
                     triggers: {
                       ...config.triggers,
                       betCondition: {
                         minStake: config.triggers.betCondition?.minStake || 0,
                         minOdds: Number(e.target.value),
                       },
                     },
                   })
                 }
                 placeholder="1.5"
               />
             </div>
           </div>
         </div>
       )}
 
       {/* Challenge Toggle */}
       {config.triggers.sequence.length > 0 && !config.triggers.sequence.every((t) => t === 'registration') && (
         <div className="flex items-center justify-between rounded-lg border p-4">
           <div>
             <Label>Require Challenge</Label>
             <p className="text-sm text-muted-foreground">
               Add wagering requirements before reward
             </p>
           </div>
           <Switch
             checked={config.hasChallenge}
             onCheckedChange={(hasChallenge) => updateConfig({ hasChallenge })}
           />
         </div>
       )}
     </div>
   );
 }