import { useCampaign } from '@/contexts/CampaignContext';
import { Button } from '@/components/ui/button';
import { ArrowLeft, ArrowRight, Check } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';

export function WizardFooter() {
  const { steps, currentStep, goToNextStep, goToPreviousStep, canProceed, campaignData } = useCampaign();
  const navigate = useNavigate();
  const { toast } = useToast();

  const currentStepIndex = steps.findIndex((s) => s.id === currentStep);
  const isFirstStep = currentStepIndex === 0;
  const isLastStep = currentStepIndex === steps.length - 1;

  const handleSubmit = async () => {
    try {
      const res = await fetch('/api/campaigns', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(campaignData),
      });
      if (!res.ok) throw new Error('Failed to create campaign');
      const created = await res.json();
      toast({
        title: 'Campaign Created',
        description: `"${created.name}" has been created successfully.`,
      });
      navigate('/campaigns');
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to create campaign. Is the backend running?',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="flex items-center justify-between border-t pt-4">
      <Button
        variant="outline"
        onClick={goToPreviousStep}
        disabled={isFirstStep}
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back
      </Button>

      {isLastStep ? (
        <Button onClick={handleSubmit} disabled={!canProceed}>
          <Check className="mr-2 h-4 w-4" />
          Create Campaign
        </Button>
      ) : (
        <Button onClick={goToNextStep} disabled={!canProceed}>
          Next
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      )}
    </div>
  );
}
