 import { useCampaign } from '@/contexts/CampaignContext';
 import { COUNTRIES, CAMPAIGN_TYPES, REWARD_TYPES } from '@/types/campaign';
 import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
 import { Badge } from '@/components/ui/badge';
 import { Button } from '@/components/ui/button';
 import { Pencil, MapPin, Settings, Target, Gift } from 'lucide-react';
 import { format } from 'date-fns';
 
 export function ReviewStep() {
   const { campaignData, setCurrentStep, getCurrency } = useCampaign();
   const currency = getCurrency();
 
   const country = COUNTRIES.find((c) => c.code === campaignData.country);
   const campaignType = CAMPAIGN_TYPES.find((t) => t.type === campaignData.campaignType);
 
   return (
     <div className="space-y-6">
       <p className="text-sm text-muted-foreground">
         Review your campaign configuration before creating it.
       </p>
 
       {/* Country */}
       <ReviewCard
         title="Country"
         icon={<MapPin className="h-4 w-4" />}
         onEdit={() => setCurrentStep('country')}
       >
         <div className="flex items-center gap-2">
           <span className="text-2xl">{country?.flag}</span>
           <div>
             <div className="font-medium">{country?.name}</div>
             <div className="text-sm text-muted-foreground">
               Currency: {currency?.code} ({currency?.symbol})
             </div>
           </div>
         </div>
       </ReviewCard>
 
       {/* General Config */}
       <ReviewCard
         title="General Configuration"
         icon={<Settings className="h-4 w-4" />}
         onEdit={() => setCurrentStep('general')}
       >
         <div className="space-y-2">
           <div>
             <span className="text-muted-foreground">Name: </span>
             <span className="font-medium">{campaignData.generalConfig.name || 'Not set'}</span>
           </div>
           {campaignData.generalConfig.description && (
             <div>
               <span className="text-muted-foreground">Description: </span>
               <span>{campaignData.generalConfig.description}</span>
             </div>
           )}
           <div className="flex flex-wrap gap-2 mt-2">
             {campaignData.generalConfig.isPermanent ? (
               <Badge variant="secondary">Permanent</Badge>
             ) : (
               <>
                 {campaignData.generalConfig.startDateTime && (
                   <Badge variant="outline">
                     Start: {format(campaignData.generalConfig.startDateTime, 'PP')}
                   </Badge>
                 )}
                 {campaignData.generalConfig.endDateTime && (
                   <Badge variant="outline">
                     End: {format(campaignData.generalConfig.endDateTime, 'PP')}
                   </Badge>
                 )}
               </>
             )}
             {campaignData.generalConfig.requiresOptIn && (
               <Badge variant="secondary">Opt-In Required</Badge>
             )}
             <Badge variant="outline">
               Audience: {campaignData.generalConfig.audienceType}
             </Badge>
           </div>
         </div>
       </ReviewCard>
 
       {/* Campaign Type */}
       <ReviewCard
         title="Campaign Type"
         icon={<Target className="h-4 w-4" />}
         onEdit={() => setCurrentStep('type')}
       >
         <div>
           <div className="font-medium">{campaignType?.title}</div>
           <div className="text-sm text-muted-foreground">{campaignType?.description}</div>
         </div>
       </ReviewCard>
 
       {/* Rewards */}
       <ReviewCard
         title="Rewards"
         icon={<Gift className="h-4 w-4" />}
         onEdit={() => setCurrentStep('rewards')}
       >
         {campaignData.selectedRewards.length === 0 ? (
           <p className="text-muted-foreground">No rewards configured</p>
         ) : (
           <div className="space-y-3">
             {campaignData.rewardConfigs.map((config) => {
               const rewardInfo = REWARD_TYPES.find((r) => r.type === config.type);
               return (
                 <div key={config.type} className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
                   <Badge>{rewardInfo?.title}</Badge>
                   <div className="text-sm">
                     {config.type === 'cash' && (
                       <span>
                         {currency?.symbol}
                         {config.amount} {config.withdrawable ? '(withdrawable)' : '(non-withdrawable)'}
                       </span>
                     )}
                     {config.type === 'free-spins' && (
                       <span>
                         {config.config.amount} spins, valid for {config.daysOfValidity} days
                       </span>
                     )}
                     {config.type === 'free-bet' && (
                       <span>
                         Valid for {config.daysOfValidity} days
                         {config.sports.enabled && ' • Sports enabled'}
                         {config.virtuals.enabled && ' • Virtuals enabled'}
                       </span>
                     )}
                     {config.type === 'bonus-wallet' && (
                       <span>
                         {currency?.symbol}
                         {config.amount} with wagering requirements
                       </span>
                     )}
                   </div>
                 </div>
               );
             })}
           </div>
         )}
       </ReviewCard>
     </div>
   );
 }
 
 function ReviewCard({
   title,
   icon,
   children,
   onEdit,
 }: {
   title: string;
   icon: React.ReactNode;
   children: React.ReactNode;
   onEdit: () => void;
 }) {
   return (
     <Card>
       <CardHeader className="flex flex-row items-center justify-between py-3">
         <CardTitle className="text-base flex items-center gap-2">
           {icon}
           {title}
         </CardTitle>
         <Button variant="ghost" size="sm" onClick={onEdit}>
           <Pencil className="h-4 w-4 mr-1" />
           Edit
         </Button>
       </CardHeader>
       <CardContent>{children}</CardContent>
     </Card>
   );
 }