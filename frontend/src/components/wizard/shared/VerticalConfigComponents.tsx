 import { Input } from '@/components/ui/input';
 import { Label } from '@/components/ui/label';
 import { Switch } from '@/components/ui/switch';
 import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
 import { Badge } from '@/components/ui/badge';
 import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
 import { Checkbox } from '@/components/ui/checkbox';
 import { VerticalBetConfig, CasinoConfig, CasinoGame, CurrencyConfig } from '@/types/campaign';
 
 // Sample data constants
 export const AGGREGATORS = ['EveryMatrix Aggregator', 'SoftSwiss', 'Pragmatic'];
 
 export const VENDORS: Record<string, string[]> = {
   'EveryMatrix Aggregator': ['NetEnt', 'Microgaming', 'Play\'n GO', 'Yggdrasil'],
   'SoftSwiss': ['BGaming', 'Endorphina', 'Belatra'],
   'Pragmatic': ['Pragmatic Play'],
 };
 
 export const SAMPLE_GAMES: Record<string, CasinoGame[]> = {
   'NetEnt': [
     { id: 'starburst', name: 'Starburst', vendor: 'NetEnt', type: 'Slots' },
     { id: 'gonzo', name: 'Gonzo\'s Quest', vendor: 'NetEnt', type: 'Slots' },
     { id: 'dead-alive', name: 'Dead or Alive', vendor: 'NetEnt', type: 'Slots' },
   ],
   'Microgaming': [
     { id: 'mega-moolah', name: 'Mega Moolah', vendor: 'Microgaming', type: 'Jackpot' },
     { id: 'immortal-romance', name: 'Immortal Romance', vendor: 'Microgaming', type: 'Slots' },
   ],
   'Play\'n GO': [
     { id: 'book-dead', name: 'Book of Dead', vendor: 'Play\'n GO', type: 'Slots' },
     { id: 'reactoonz', name: 'Reactoonz', vendor: 'Play\'n GO', type: 'Slots' },
   ],
   'Yggdrasil': [
     { id: 'vikings', name: 'Vikings Go Berzerk', vendor: 'Yggdrasil', type: 'Slots' },
   ],
   'BGaming': [
     { id: 'elvis-frog', name: 'Elvis Frog in Vegas', vendor: 'BGaming', type: 'Slots' },
   ],
   'Endorphina': [
     { id: 'lucky-streak', name: 'Lucky Streak 3', vendor: 'Endorphina', type: 'Slots' },
   ],
   'Belatra': [
     { id: 'piggy-bank', name: 'Piggy Bank', vendor: 'Belatra', type: 'Slots' },
   ],
   'Pragmatic Play': [
     { id: 'wolf-gold', name: 'Wolf Gold', vendor: 'Pragmatic Play', type: 'Slots' },
     { id: 'gates-olympus', name: 'Gates of Olympus', vendor: 'Pragmatic Play', type: 'Slots' },
     { id: 'sweet-bonanza', name: 'Sweet Bonanza', vendor: 'Pragmatic Play', type: 'Slots' },
   ],
 };
 
 const SPORTS_OPTIONS = ['Football', 'Tennis', 'Basketball', 'Cricket', 'Horse Racing'];
 const MARKETS_OPTIONS = ['1X2', 'Over/Under', 'BTTS', 'Correct Score', 'Handicap'];
 const BET_TYPES = [
   { value: 'all', label: 'All' },
   { value: 'single', label: 'Single' },
   { value: 'combined', label: 'Combined/Accumulator' },
   { value: 'system', label: 'System' },
 ];
 
 interface BettingVerticalConfigProps {
   title: string;
   config: VerticalBetConfig;
   onChange: (config: VerticalBetConfig) => void;
   currency: CurrencyConfig | null;
 }
 
 export function BettingVerticalConfig({ title, config, onChange, currency }: BettingVerticalConfigProps) {
   const currencySymbol = currency?.symbol || '';
 
   const toggleSport = (sport: string) => {
     const current = config.eligibleSports || [];
     const updated = current.includes(sport)
       ? current.filter((s) => s !== sport)
       : [...current, sport];
     onChange({ ...config, eligibleSports: updated });
   };
 
   const toggleMarket = (market: string) => {
     const current = config.eligibleMarkets || [];
     const updated = current.includes(market)
       ? current.filter((m) => m !== market)
       : [...current, market];
     onChange({ ...config, eligibleMarkets: updated });
   };
 
   return (
     <Card>
       <CardHeader className="pb-3">
         <div className="flex items-center justify-between">
           <CardTitle className="text-base">{title}</CardTitle>
           <Switch
             checked={config.enabled}
             onCheckedChange={(enabled) => onChange({ ...config, enabled })}
           />
         </div>
       </CardHeader>
       {config.enabled && (
         <CardContent className="space-y-4">
           <div className="grid grid-cols-2 gap-4">
             <div className="space-y-2">
               <Label>Min Stake ({currencySymbol})</Label>
               <Input
                 type="number"
                 value={config.minStake || ''}
                 onChange={(e) => onChange({ ...config, minStake: Number(e.target.value) })}
                 placeholder="0"
               />
             </div>
             <div className="space-y-2">
               <Label>Max Stake ({currencySymbol})</Label>
               <Input
                 type="number"
                 value={config.maxStake || ''}
                 onChange={(e) => onChange({ ...config, maxStake: Number(e.target.value) })}
                 placeholder="0"
               />
             </div>
           </div>
 
           <div className="grid grid-cols-2 gap-4">
             <div className="space-y-2">
               <Label>Min Odds</Label>
               <Input
                 type="number"
                 step="0.1"
                 value={config.minOdds || ''}
                 onChange={(e) => onChange({ ...config, minOdds: Number(e.target.value) })}
                 placeholder="1.5"
               />
             </div>
             <div className="space-y-2">
               <Label>Min Selections</Label>
               <Input
                 type="number"
                 value={config.minSelections || ''}
                 onChange={(e) => onChange({ ...config, minSelections: Number(e.target.value) })}
                 placeholder="1"
               />
             </div>
           </div>
 
           <div className="space-y-2">
             <Label>Bet Type</Label>
             <Select
               value={config.betType}
               onValueChange={(value) => onChange({ ...config, betType: value as VerticalBetConfig['betType'] })}
             >
               <SelectTrigger>
                 <SelectValue />
               </SelectTrigger>
               <SelectContent>
                 {BET_TYPES.map((type) => (
                   <SelectItem key={type.value} value={type.value}>
                     {type.label}
                   </SelectItem>
                 ))}
               </SelectContent>
             </Select>
           </div>
 
           <div className="space-y-2">
             <Label>Eligible Sports</Label>
             <div className="flex flex-wrap gap-2">
               {SPORTS_OPTIONS.map((sport) => (
                 <Badge
                   key={sport}
                   variant={config.eligibleSports?.includes(sport) ? 'default' : 'outline'}
                   className="cursor-pointer"
                   onClick={() => toggleSport(sport)}
                 >
                   {sport}
                 </Badge>
               ))}
             </div>
           </div>
 
           <div className="space-y-2">
             <Label>Eligible Markets</Label>
             <div className="flex flex-wrap gap-2">
               {MARKETS_OPTIONS.map((market) => (
                 <Badge
                   key={market}
                   variant={config.eligibleMarkets?.includes(market) ? 'default' : 'outline'}
                   className="cursor-pointer"
                   onClick={() => toggleMarket(market)}
                 >
                   {market}
                 </Badge>
               ))}
             </div>
           </div>
         </CardContent>
       )}
     </Card>
   );
 }
 
 interface CasinoVerticalConfigProps {
   config: CasinoConfig;
   onChange: (config: CasinoConfig) => void;
   currency: CurrencyConfig | null;
 }
 
 export function CasinoVerticalConfig({ config, onChange, currency }: CasinoVerticalConfigProps) {
   const currencySymbol = currency?.symbol || '';
   const availableVendors = config.aggregator ? VENDORS[config.aggregator] || [] : [];
   const availableGames = config.vendor ? SAMPLE_GAMES[config.vendor] || [] : [];
 
   const toggleGame = (game: CasinoGame) => {
     const isSelected = config.selectedGames.some((g) => g.id === game.id);
     const updated = isSelected
       ? config.selectedGames.filter((g) => g.id !== game.id)
       : [...config.selectedGames, game];
     onChange({ ...config, selectedGames: updated });
   };
 
   return (
     <Card>
       <CardHeader className="pb-3">
         <div className="flex items-center justify-between">
           <CardTitle className="text-base">Casino</CardTitle>
           <Switch
             checked={config.enabled}
             onCheckedChange={(enabled) => onChange({ ...config, enabled })}
           />
         </div>
       </CardHeader>
       {config.enabled && (
         <CardContent className="space-y-4">
           <div className="grid grid-cols-2 gap-4">
             <div className="space-y-2">
               <Label>Min Stake ({currencySymbol})</Label>
               <Input
                 type="number"
                 value={config.minStake || ''}
                 onChange={(e) => onChange({ ...config, minStake: Number(e.target.value) })}
                 placeholder="0"
               />
             </div>
             <div className="space-y-2">
               <Label>Max Stake ({currencySymbol})</Label>
               <Input
                 type="number"
                 value={config.maxStake || ''}
                 onChange={(e) => onChange({ ...config, maxStake: Number(e.target.value) })}
                 placeholder="0"
               />
             </div>
           </div>
 
           <div className="space-y-2">
             <Label>Aggregator</Label>
             <Select
               value={config.aggregator}
               onValueChange={(value) => onChange({ ...config, aggregator: value, vendor: '', selectedGames: [] })}
             >
               <SelectTrigger>
                 <SelectValue placeholder="Select aggregator" />
               </SelectTrigger>
               <SelectContent>
                 {AGGREGATORS.map((agg) => (
                   <SelectItem key={agg} value={agg}>
                     {agg}
                   </SelectItem>
                 ))}
               </SelectContent>
             </Select>
           </div>
 
           {config.aggregator && (
             <div className="space-y-2">
               <Label>Vendor</Label>
               <Select
                 value={config.vendor}
                 onValueChange={(value) => onChange({ ...config, vendor: value, selectedGames: [] })}
               >
                 <SelectTrigger>
                   <SelectValue placeholder="Select vendor" />
                 </SelectTrigger>
                 <SelectContent>
                   {availableVendors.map((vendor) => (
                     <SelectItem key={vendor} value={vendor}>
                       {vendor}
                     </SelectItem>
                   ))}
                 </SelectContent>
               </Select>
             </div>
           )}
 
           {config.vendor && (
             <div className="space-y-2">
               <Label>Select Games</Label>
               <div className="rounded-md border max-h-48 overflow-y-auto">
                 {availableGames.map((game) => (
                   <div
                     key={game.id}
                     className="flex items-center gap-3 p-2 hover:bg-muted border-b last:border-b-0"
                   >
                     <Checkbox
                       checked={config.selectedGames.some((g) => g.id === game.id)}
                       onCheckedChange={() => toggleGame(game)}
                     />
                     <div className="flex-1">
                       <div className="text-sm font-medium">{game.name}</div>
                       <div className="text-xs text-muted-foreground">{game.type}</div>
                     </div>
                   </div>
                 ))}
               </div>
             </div>
           )}
 
           {config.selectedGames.length > 0 && (
             <div className="space-y-2">
               <Label>Selected Games ({config.selectedGames.length})</Label>
               <div className="flex flex-wrap gap-1">
                 {config.selectedGames.map((game) => (
                   <Badge key={game.id} variant="secondary" className="text-xs">
                     {game.name}
                   </Badge>
                 ))}
               </div>
             </div>
           )}
         </CardContent>
       )}
     </Card>
   );
 }