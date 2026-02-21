 import React, { createContext, useContext, useState, useCallback, useMemo } from 'react';
 import {
   CampaignData,
   Country,
   CurrencyConfig,
   WizardStep,
   COUNTRIES,
   getInitialCampaignData,
 } from '@/types/campaign';
 
 interface ValidationError {
   field: string;
   message: string;
 }
 
 interface CampaignContextValue {
   campaignData: CampaignData;
   updateCampaignData: <K extends keyof CampaignData>(key: K, value: CampaignData[K]) => void;
   currentStep: string;
   setCurrentStep: (step: string) => void;
   steps: WizardStep[];
   goToNextStep: () => boolean;
   goToPreviousStep: () => void;
   validationErrors: ValidationError[];
   validateCurrentStep: () => boolean;
   getCurrency: () => CurrencyConfig | null;
   resetCampaign: () => void;
   canProceed: boolean;
 }
 
 const CampaignContext = createContext<CampaignContextValue | undefined>(undefined);
 
 const ALL_STEPS: WizardStep[] = [
   {
     id: 'country',
     title: 'Country',
     description: 'Select the target country for this campaign',
     isVisible: () => true,
   },
   {
     id: 'general',
     title: 'General',
     description: 'Configure basic campaign settings',
     isVisible: () => true,
   },
   {
     id: 'type',
     title: 'Campaign Type',
     description: 'Choose your campaign type',
     isVisible: () => true,
   },
   {
     id: 'triggers',
     title: 'Triggers',
     description: 'Configure trigger conditions',
     isVisible: (data) => data.campaignType === 'triggered',
   },
   {
     id: 'bet-config',
     title: 'Bet Config',
     description: 'Configure qualifying bets',
     isVisible: (data) => data.campaignType === 'bet-and-get',
   },
   {
     id: 'ftp-config',
     title: 'FTP Config',
     description: 'Configure free-to-play settings',
     isVisible: (data) => data.campaignType === 'free-to-play',
   },
   {
     id: 'ftp-mechanics',
     title: 'Mechanics',
     description: 'Configure game mechanics',
     isVisible: (data) => data.campaignType === 'free-to-play',
   },
   {
     id: 'challenge',
     title: 'Challenge',
     description: 'Configure challenge requirements',
     isVisible: (data) => {
       if (data.campaignType === 'bet-and-get') return true;
       if (data.campaignType === 'triggered' && data.triggeredConfig?.hasChallenge) return true;
       return false;
     },
   },
   {
     id: 'rewards',
     title: 'Rewards',
     description: 'Configure reward types and amounts',
     isVisible: () => true,
   },
   {
     id: 'review',
     title: 'Review',
     description: 'Review and submit your campaign',
     isVisible: () => true,
   },
 ];
 
 export function CampaignProvider({ children }: { children: React.ReactNode }) {
   const [campaignData, setCampaignData] = useState<CampaignData>(getInitialCampaignData());
   const [currentStep, setCurrentStep] = useState<string>('country');
   const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
 
   const steps = useMemo(() => {
     return ALL_STEPS.filter((step) => step.isVisible(campaignData));
   }, [campaignData]);
 
   const updateCampaignData = useCallback(<K extends keyof CampaignData>(key: K, value: CampaignData[K]) => {
     setCampaignData((prev) => ({ ...prev, [key]: value }));
     setValidationErrors([]);
   }, []);
 
   const getCurrency = useCallback((): CurrencyConfig | null => {
     if (!campaignData.country) return null;
     const country = COUNTRIES.find((c) => c.code === campaignData.country);
     return country?.currency || null;
   }, [campaignData.country]);
 
   const validateCurrentStep = useCallback((): boolean => {
     const errors: ValidationError[] = [];
 
     switch (currentStep) {
       case 'country':
         if (!campaignData.country) {
           errors.push({ field: 'country', message: 'Please select a country' });
         }
         break;
       case 'general':
         if (!campaignData.generalConfig.name.trim()) {
           errors.push({ field: 'name', message: 'Campaign name is required' });
         }
         if (!campaignData.generalConfig.isPermanent && !campaignData.generalConfig.startDateTime) {
           errors.push({ field: 'startDateTime', message: 'Start date is required' });
         }
         break;
       case 'type':
         if (!campaignData.campaignType) {
           errors.push({ field: 'campaignType', message: 'Please select a campaign type' });
         }
         break;
       case 'rewards':
         if (campaignData.selectedRewards.length === 0) {
           errors.push({ field: 'selectedRewards', message: 'Please select at least one reward' });
         }
         break;
     }
 
     setValidationErrors(errors);
     return errors.length === 0;
   }, [currentStep, campaignData]);
 
   const currentStepIndex = useMemo(() => {
     return steps.findIndex((s) => s.id === currentStep);
   }, [steps, currentStep]);
 
   const canProceed = useMemo(() => {
     switch (currentStep) {
       case 'country':
         return !!campaignData.country;
       case 'general':
         return !!campaignData.generalConfig.name.trim();
       case 'type':
         return !!campaignData.campaignType;
       case 'rewards':
         return campaignData.selectedRewards.length > 0;
       default:
         return true;
     }
   }, [currentStep, campaignData]);
 
   const goToNextStep = useCallback((): boolean => {
     if (!validateCurrentStep()) return false;
 
     const nextIndex = currentStepIndex + 1;
     if (nextIndex < steps.length) {
       setCurrentStep(steps[nextIndex].id);
       return true;
     }
     return false;
   }, [currentStepIndex, steps, validateCurrentStep]);
 
   const goToPreviousStep = useCallback(() => {
     const prevIndex = currentStepIndex - 1;
     if (prevIndex >= 0) {
       setCurrentStep(steps[prevIndex].id);
     }
   }, [currentStepIndex, steps]);
 
   const resetCampaign = useCallback(() => {
     setCampaignData(getInitialCampaignData());
     setCurrentStep('country');
     setValidationErrors([]);
   }, []);
 
   const value: CampaignContextValue = {
     campaignData,
     updateCampaignData,
     currentStep,
     setCurrentStep,
     steps,
     goToNextStep,
     goToPreviousStep,
     validationErrors,
     validateCurrentStep,
     getCurrency,
     resetCampaign,
     canProceed,
   };
 
   return <CampaignContext.Provider value={value}>{children}</CampaignContext.Provider>;
 }
 
 export function useCampaign() {
   const context = useContext(CampaignContext);
   if (!context) {
     throw new Error('useCampaign must be used within a CampaignProvider');
   }
   return context;
 }