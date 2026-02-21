 import { useCampaign } from '@/contexts/CampaignContext';
 import { FreeToPlayMechanicsConfig } from '@/types/campaign';
 import { Label } from '@/components/ui/label';
 import { Input } from '@/components/ui/input';
 import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
 
 const DEFAULT_CONFIG: FreeToPlayMechanicsConfig = {
   picksPerUser: 1,
   scoringModel: 'exact',
   winnerSelectionLogic: 'highest-score',
 };
 
 export function FTPMechanicsStep() {
   const { campaignData, updateCampaignData } = useCampaign();
   const ftpConfig = campaignData.freeToPlayConfig;
   const config = campaignData.freeToPlayMechanicsConfig || DEFAULT_CONFIG;
 
   const updateConfig = (updates: Partial<FreeToPlayMechanicsConfig>) => {
     updateCampaignData('freeToPlayMechanicsConfig', { ...config, ...updates });
   };
 
   const format = ftpConfig?.format || 'prediction';
 
   return (
     <div className="space-y-6 max-w-2xl">
       <p className="text-sm text-muted-foreground">
         Configure the game mechanics for your {format} game.
       </p>
 
       {/* Attempts/Picks per User */}
       <div className="space-y-4 rounded-lg border p-4">
         <h3 className="font-medium">User Limits</h3>
         <div className="grid grid-cols-2 gap-4">
           {format === 'prediction' && (
             <div className="space-y-2">
               <Label>Picks per User</Label>
               <Input
                 type="number"
                 value={config.picksPerUser || ''}
                 onChange={(e) => updateConfig({ picksPerUser: Number(e.target.value) })}
                 min={1}
                 placeholder="1"
               />
             </div>
           )}
           {format === 'spin' && (
             <div className="space-y-2">
               <Label>Spins per User</Label>
               <Input
                 type="number"
                 value={config.spinsPerUser || ''}
                 onChange={(e) => updateConfig({ spinsPerUser: Number(e.target.value) })}
                 min={1}
                 placeholder="1"
               />
             </div>
           )}
           {format === 'raffle' && (
             <div className="space-y-2">
               <Label>Entries per User</Label>
               <Input
                 type="number"
                 value={config.attemptsPerUser || ''}
                 onChange={(e) => updateConfig({ attemptsPerUser: Number(e.target.value) })}
                 min={1}
                 placeholder="1"
               />
             </div>
           )}
         </div>
       </div>
 
       {/* Scoring Model (for predictions) */}
       {format === 'prediction' && (
         <div className="space-y-4 rounded-lg border p-4">
           <h3 className="font-medium">Scoring Model</h3>
           <Select
             value={config.scoringModel}
             onValueChange={(value) =>
               updateConfig({ scoringModel: value as FreeToPlayMechanicsConfig['scoringModel'] })
             }
           >
             <SelectTrigger>
               <SelectValue />
             </SelectTrigger>
             <SelectContent>
               <SelectItem value="exact">Exact Match</SelectItem>
               <SelectItem value="partial">Partial Points</SelectItem>
               <SelectItem value="binary">Binary (Correct/Incorrect)</SelectItem>
             </SelectContent>
           </Select>
           <p className="text-xs text-muted-foreground">
             {config.scoringModel === 'exact' && 'Points awarded only for exact predictions'}
             {config.scoringModel === 'partial' && 'Partial points for close predictions'}
             {config.scoringModel === 'binary' && 'All-or-nothing scoring'}
           </p>
         </div>
       )}
 
       {/* Winner Selection */}
       <div className="space-y-4 rounded-lg border p-4">
         <h3 className="font-medium">Winner Selection</h3>
         <Select
           value={config.winnerSelectionLogic}
           onValueChange={(value) =>
             updateConfig({ winnerSelectionLogic: value as FreeToPlayMechanicsConfig['winnerSelectionLogic'] })
           }
         >
           <SelectTrigger>
             <SelectValue />
           </SelectTrigger>
           <SelectContent>
             <SelectItem value="highest-score">Highest Score</SelectItem>
             <SelectItem value="random-draw">Random Draw</SelectItem>
             <SelectItem value="first-correct">First Correct</SelectItem>
           </SelectContent>
         </Select>
         <p className="text-xs text-muted-foreground">
           {config.winnerSelectionLogic === 'highest-score' && 'Winner determined by highest score'}
           {config.winnerSelectionLogic === 'random-draw' && 'Winner randomly selected from eligible entries'}
           {config.winnerSelectionLogic === 'first-correct' && 'First user to answer correctly wins'}
         </p>
       </div>
     </div>
   );
 }