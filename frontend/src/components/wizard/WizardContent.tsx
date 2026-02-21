 import { useCampaign } from '@/contexts/CampaignContext';
 import { CountryStep } from './steps/CountryStep';
 import { GeneralConfigStep } from './steps/GeneralConfigStep';
 import { CampaignTypeStep } from './steps/CampaignTypeStep';
 import { TriggerConfigStep } from './steps/TriggerConfigStep';
 import { CampaignConfigStep } from './steps/CampaignConfigStep';
 import { FTPConfigStep } from './steps/FTPConfigStep';
 import { FTPMechanicsStep } from './steps/FTPMechanicsStep';
 import { ChallengeConfigStep } from './steps/ChallengeConfigStep';
 import { RewardStep } from './steps/RewardStep';
 import { ReviewStep } from './steps/ReviewStep';
 
 export function WizardContent() {
   const { currentStep } = useCampaign();
 
   switch (currentStep) {
     case 'country':
       return <CountryStep />;
     case 'general':
       return <GeneralConfigStep />;
     case 'type':
       return <CampaignTypeStep />;
     case 'triggers':
       return <TriggerConfigStep />;
     case 'bet-config':
       return <CampaignConfigStep />;
     case 'ftp-config':
       return <FTPConfigStep />;
     case 'ftp-mechanics':
       return <FTPMechanicsStep />;
     case 'challenge':
       return <ChallengeConfigStep />;
     case 'rewards':
       return <RewardStep />;
     case 'review':
       return <ReviewStep />;
     default:
       return <div>Unknown step</div>;
   }
 }