 interface WizardHeaderProps {
   title: string;
   description: string;
 }
 
 export function WizardHeader({ title, description }: WizardHeaderProps) {
   return (
     <div className="border-b pb-4">
       <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
       <p className="text-muted-foreground">{description}</p>
     </div>
   );
 }