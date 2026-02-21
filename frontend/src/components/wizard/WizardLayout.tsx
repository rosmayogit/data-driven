 import { useCampaign } from '@/contexts/CampaignContext';
 import { WizardSidebar } from './WizardSidebar';
 import { WizardHeader } from './WizardHeader';
 import { WizardContent } from './WizardContent';
 import { WizardFooter } from './WizardFooter';
 
 export function WizardLayout() {
   const { steps, currentStep } = useCampaign();
   const currentStepData = steps.find((s) => s.id === currentStep);
 
   return (
     <div className="flex min-h-[calc(100vh-8rem)] gap-6">
       <WizardSidebar />
       <div className="flex flex-1 flex-col">
         <WizardHeader
           title={currentStepData?.title || ''}
           description={currentStepData?.description || ''}
         />
         <div className="flex-1 py-6">
           <WizardContent />
         </div>
         <WizardFooter />
       </div>
     </div>
   );
 }