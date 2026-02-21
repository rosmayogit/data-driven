 import { useCampaign } from '@/contexts/CampaignContext';
 import { Input } from '@/components/ui/input';
 import { Label } from '@/components/ui/label';
 import { Textarea } from '@/components/ui/textarea';
 import { Switch } from '@/components/ui/switch';
 import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
 import { Calendar } from '@/components/ui/calendar';
 import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
 import { Button } from '@/components/ui/button';
 import { CalendarIcon } from 'lucide-react';
 import { format } from 'date-fns';
 import { cn } from '@/lib/utils';
 import { CampaignGeneralConfig, WeekDay } from '@/types/campaign';
 
 const WEEK_DAYS: { value: WeekDay; label: string }[] = [
   { value: 'monday', label: 'Monday' },
   { value: 'tuesday', label: 'Tuesday' },
   { value: 'wednesday', label: 'Wednesday' },
   { value: 'thursday', label: 'Thursday' },
   { value: 'friday', label: 'Friday' },
   { value: 'saturday', label: 'Saturday' },
   { value: 'sunday', label: 'Sunday' },
 ];
 
 export function GeneralConfigStep() {
   const { campaignData, updateCampaignData, validationErrors } = useCampaign();
   const config = campaignData.generalConfig;
 
   const updateConfig = (updates: Partial<CampaignGeneralConfig>) => {
     updateCampaignData('generalConfig', { ...config, ...updates });
   };
 
   const hasNameError = validationErrors.some((e) => e.field === 'name');
 
   return (
     <div className="space-y-6 max-w-2xl">
       {/* Name & Description */}
       <div className="space-y-4">
         <div className="space-y-2">
           <Label htmlFor="name">Campaign Name *</Label>
           <Input
             id="name"
             value={config.name}
             onChange={(e) => updateConfig({ name: e.target.value })}
             placeholder="Enter campaign name"
             className={cn(hasNameError && 'border-destructive')}
           />
           {hasNameError && (
             <p className="text-sm text-destructive">Campaign name is required</p>
           )}
         </div>
 
         <div className="space-y-2">
           <Label htmlFor="description">Description</Label>
           <Textarea
             id="description"
             value={config.description}
             onChange={(e) => updateConfig({ description: e.target.value })}
             placeholder="Describe your campaign"
             rows={3}
           />
         </div>
       </div>
 
       {/* Scheduling */}
       <div className="space-y-4 rounded-lg border p-4">
         <h3 className="font-medium">Scheduling</h3>
 
         <div className="flex items-center justify-between">
           <div>
             <Label>Permanent Campaign</Label>
             <p className="text-sm text-muted-foreground">Campaign runs indefinitely</p>
           </div>
           <Switch
             checked={config.isPermanent}
             onCheckedChange={(isPermanent) => updateConfig({ isPermanent, endDateTime: null })}
           />
         </div>
 
         <div className="grid grid-cols-2 gap-4">
           <div className="space-y-2">
             <Label>Start Date</Label>
             <Popover>
               <PopoverTrigger asChild>
                 <Button
                   variant="outline"
                   className={cn(
                     'w-full justify-start text-left font-normal',
                     !config.startDateTime && 'text-muted-foreground'
                   )}
                 >
                   <CalendarIcon className="mr-2 h-4 w-4" />
                   {config.startDateTime ? format(config.startDateTime, 'PPP') : 'Pick a date'}
                 </Button>
               </PopoverTrigger>
               <PopoverContent className="w-auto p-0">
                 <Calendar
                   mode="single"
                   selected={config.startDateTime || undefined}
                   onSelect={(date) => updateConfig({ startDateTime: date || null })}
                   initialFocus
                 />
               </PopoverContent>
             </Popover>
           </div>
 
           {!config.isPermanent && (
             <div className="space-y-2">
               <Label>End Date</Label>
               <Popover>
                 <PopoverTrigger asChild>
                   <Button
                     variant="outline"
                     className={cn(
                       'w-full justify-start text-left font-normal',
                       !config.endDateTime && 'text-muted-foreground'
                     )}
                   >
                     <CalendarIcon className="mr-2 h-4 w-4" />
                     {config.endDateTime ? format(config.endDateTime, 'PPP') : 'Pick a date'}
                   </Button>
                 </PopoverTrigger>
                 <PopoverContent className="w-auto p-0">
                   <Calendar
                     mode="single"
                     selected={config.endDateTime || undefined}
                     onSelect={(date) => updateConfig({ endDateTime: date || null })}
                     initialFocus
                   />
                 </PopoverContent>
               </Popover>
             </div>
           )}
         </div>
       </div>
 
       {/* Audience */}
       <div className="space-y-4 rounded-lg border p-4">
         <h3 className="font-medium">Audience Targeting</h3>
 
         <div className="flex items-center justify-between">
           <div>
             <Label>Requires Opt-In</Label>
             <p className="text-sm text-muted-foreground">Users must opt-in to participate</p>
           </div>
           <Switch
             checked={config.requiresOptIn}
             onCheckedChange={(requiresOptIn) => updateConfig({ requiresOptIn })}
           />
         </div>
 
         <div className="space-y-2">
           <Label>Audience Type</Label>
           <Select
             value={config.audienceType}
             onValueChange={(value) => updateConfig({ audienceType: value as CampaignGeneralConfig['audienceType'] })}
           >
             <SelectTrigger>
               <SelectValue />
             </SelectTrigger>
             <SelectContent>
               <SelectItem value="open">Open to All</SelectItem>
               <SelectItem value="csv">CSV Upload</SelectItem>
               <SelectItem value="optimove">Optimove Segment</SelectItem>
             </SelectContent>
           </Select>
         </div>
 
         {config.audienceType === 'optimove' && (
           <div className="space-y-2">
             <Label>Optimove Segment</Label>
             <Input
               value={config.optimoveSegment || ''}
               onChange={(e) => updateConfig({ optimoveSegment: e.target.value })}
               placeholder="Enter segment name"
             />
           </div>
         )}
       </div>
 
       {/* Frequency */}
       <div className="space-y-4 rounded-lg border p-4">
         <div className="flex items-center justify-between">
           <div>
             <h3 className="font-medium">Frequency Limit</h3>
             <p className="text-sm text-muted-foreground">Limit how often users can qualify</p>
           </div>
           <Switch
             checked={config.frequency.enabled}
             onCheckedChange={(enabled) =>
               updateConfig({ frequency: { ...config.frequency, enabled } })
             }
           />
         </div>
 
         {config.frequency.enabled && (
           <div className="grid grid-cols-2 gap-4">
             <div className="space-y-2">
               <Label>Period</Label>
               <Select
                 value={config.frequency.period}
                 onValueChange={(value) =>
                   updateConfig({
                     frequency: { ...config.frequency, period: value as CampaignGeneralConfig['frequency']['period'] },
                   })
                 }
               >
                 <SelectTrigger>
                   <SelectValue />
                 </SelectTrigger>
                 <SelectContent>
                   <SelectItem value="daily">Daily</SelectItem>
                   <SelectItem value="weekly">Weekly</SelectItem>
                   <SelectItem value="monthly">Monthly</SelectItem>
                   <SelectItem value="campaign">Entire Campaign</SelectItem>
                 </SelectContent>
               </Select>
             </div>
             <div className="space-y-2">
               <Label>Max Qualifications</Label>
               <Input
                 type="number"
                 value={config.frequency.windowDays}
                 onChange={(e) =>
                   updateConfig({
                     frequency: { ...config.frequency, windowDays: Number(e.target.value) },
                   })
                 }
                 min={1}
               />
             </div>
           </div>
         )}
       </div>
 
       {/* Automated Execution */}
       <div className="space-y-4 rounded-lg border p-4">
         <div className="flex items-center justify-between">
           <div>
             <h3 className="font-medium">Automated Execution</h3>
             <p className="text-sm text-muted-foreground">Schedule automated campaign runs</p>
           </div>
           <Switch
             checked={config.automatedExecution.enabled}
             onCheckedChange={(enabled) =>
               updateConfig({ automatedExecution: { ...config.automatedExecution, enabled } })
             }
           />
         </div>
 
         {config.automatedExecution.enabled && (
           <div className="grid grid-cols-3 gap-4">
             <div className="space-y-2">
               <Label>Start Day</Label>
               <Select
                 value={config.automatedExecution.startDay}
                 onValueChange={(value) =>
                   updateConfig({
                     automatedExecution: { ...config.automatedExecution, startDay: value as WeekDay },
                   })
                 }
               >
                 <SelectTrigger>
                   <SelectValue />
                 </SelectTrigger>
                 <SelectContent>
                   {WEEK_DAYS.map((day) => (
                     <SelectItem key={day.value} value={day.value}>
                       {day.label}
                     </SelectItem>
                   ))}
                 </SelectContent>
               </Select>
             </div>
             <div className="space-y-2">
               <Label>Duration (weeks)</Label>
               <Input
                 type="number"
                 value={config.automatedExecution.durationWeeks}
                 onChange={(e) =>
                   updateConfig({
                     automatedExecution: { ...config.automatedExecution, durationWeeks: Number(e.target.value) },
                   })
                 }
                 min={1}
               />
             </div>
             <div className="space-y-2">
               <Label>Finish Time</Label>
               <Input
                 type="time"
                 value={config.automatedExecution.finishTime}
                 onChange={(e) =>
                   updateConfig({
                     automatedExecution: { ...config.automatedExecution, finishTime: e.target.value },
                   })
                 }
               />
             </div>
           </div>
         )}
       </div>
     </div>
   );
 }