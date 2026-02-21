 import { useCampaign } from '@/contexts/CampaignContext';
 import { cn } from '@/lib/utils';
 import { Check } from 'lucide-react';
 
 export function WizardSidebar() {
   const { steps, currentStep, setCurrentStep, campaignData } = useCampaign();
 
   const getStepStatus = (stepId: string, index: number): 'complete' | 'current' | 'upcoming' => {
     const currentIndex = steps.findIndex((s) => s.id === currentStep);
     if (index < currentIndex) return 'complete';
     if (stepId === currentStep) return 'current';
     return 'upcoming';
   };
 
   const canNavigateToStep = (index: number): boolean => {
     const currentIndex = steps.findIndex((s) => s.id === currentStep);
     return index <= currentIndex;
   };
 
   return (
     <aside className="w-64 shrink-0">
       <div className="sticky top-24 rounded-lg border bg-card p-4">
         <h3 className="mb-4 text-sm font-semibold text-muted-foreground uppercase tracking-wider">
           Steps
         </h3>
         <nav className="space-y-1">
           {steps.map((step, index) => {
             const status = getStepStatus(step.id, index);
             const canNavigate = canNavigateToStep(index);
 
             return (
               <button
                 key={step.id}
                 onClick={() => canNavigate && setCurrentStep(step.id)}
                 disabled={!canNavigate}
                 className={cn(
                   'flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm transition-colors',
                   status === 'current' && 'bg-primary text-primary-foreground',
                   status === 'complete' && 'text-foreground hover:bg-muted',
                   status === 'upcoming' && 'text-muted-foreground cursor-not-allowed'
                 )}
               >
                 <span
                   className={cn(
                     'flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-medium',
                     status === 'current' && 'bg-primary-foreground text-primary',
                     status === 'complete' && 'bg-primary text-primary-foreground',
                     status === 'upcoming' && 'border border-muted-foreground/30'
                   )}
                 >
                   {status === 'complete' ? (
                     <Check className="h-3.5 w-3.5" />
                   ) : (
                     index + 1
                   )}
                 </span>
                 <span className="truncate">{step.title}</span>
               </button>
             );
           })}
         </nav>
       </div>
     </aside>
   );
 }