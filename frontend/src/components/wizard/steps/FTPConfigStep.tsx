 import { useCampaign } from '@/contexts/CampaignContext';
 import { FreeToPlayConfig, FTPFormat } from '@/types/campaign';
 import { Label } from '@/components/ui/label';
 import { Textarea } from '@/components/ui/textarea';
 import { cn } from '@/lib/utils';
 import { Trophy, RotateCw, Ticket } from 'lucide-react';
 
 const FTP_FORMATS: { type: FTPFormat; title: string; description: string; icon: React.ReactNode }[] = [
   { type: 'prediction', title: 'Prediction', description: 'Users predict outcomes to win', icon: <Trophy className="h-6 w-6" /> },
   { type: 'spin', title: 'Spin', description: 'Spin-to-win wheel or slots', icon: <RotateCw className="h-6 w-6" /> },
   { type: 'raffle', title: 'Raffle', description: 'Random draw from entries', icon: <Ticket className="h-6 w-6" /> },
 ];
 
 const DEFAULT_CONFIG: FreeToPlayConfig = {
   format: 'prediction',
   entryRules: '',
 };
 
 export function FTPConfigStep() {
   const { campaignData, updateCampaignData } = useCampaign();
   const config = campaignData.freeToPlayConfig || DEFAULT_CONFIG;
 
   const updateConfig = (updates: Partial<FreeToPlayConfig>) => {
     updateCampaignData('freeToPlayConfig', { ...config, ...updates });
   };
 
   return (
     <div className="space-y-6 max-w-2xl">
       <p className="text-sm text-muted-foreground">
         Configure the free-to-play game format and entry rules.
       </p>
 
       {/* Format Selection */}
       <div className="space-y-3">
         <Label>Game Format</Label>
         <div className="grid grid-cols-3 gap-4">
           {FTP_FORMATS.map((format) => (
             <button
               key={format.type}
               onClick={() => updateConfig({ format: format.type })}
               className={cn(
                 'flex flex-col items-center gap-3 rounded-lg border p-5 transition-all hover:border-primary',
                 config.format === format.type
                   ? 'border-primary bg-primary/5 ring-2 ring-primary ring-offset-2'
                   : 'border-border'
               )}
             >
               <div className={cn(
                 'rounded-lg p-3',
                 config.format === format.type
                   ? 'bg-primary text-primary-foreground'
                   : 'bg-muted'
               )}>
                 {format.icon}
               </div>
               <div className="text-center">
                 <div className="font-medium">{format.title}</div>
                 <div className="text-xs text-muted-foreground">{format.description}</div>
               </div>
             </button>
           ))}
         </div>
       </div>
 
       {/* Entry Rules */}
       <div className="space-y-2">
         <Label htmlFor="entryRules">Entry Rules</Label>
         <Textarea
           id="entryRules"
           value={config.entryRules}
           onChange={(e) => updateConfig({ entryRules: e.target.value })}
           placeholder="Describe how users can enter this game..."
           rows={4}
         />
         <p className="text-xs text-muted-foreground">
           Describe requirements or conditions for entry (e.g., "Place a bet of ₦500 or more")
         </p>
       </div>
     </div>
   );
 }