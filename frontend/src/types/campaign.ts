 // ============================================
 // COUNTRY & CURRENCY TYPES
 // ============================================
 
export type Country = 'NG' | 'SA' | 'ZM' | 'KE';
export type Currency = 'NGN' | 'ZAR' | 'ZMW' | 'KES';
 
 export interface CurrencyConfig {
   code: Currency;
   symbol: string;
   name: string;
 }
 
export interface CountryConfig {
  code: Country;
  name: string;
  currency: CurrencyConfig;
  flag: string;
  status: 'active' | 'blocked';
}
 
 // ============================================
 // CAMPAIGN TYPE DEFINITIONS
 // ============================================
 
 export type CampaignType = 'simple' | 'triggered' | 'bet-and-get' | 'free-to-play';
 export type RewardType = 'free-bet' | 'free-spins' | 'cash' | 'bonus-wallet';
 export type WeekDay = 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday';
 
 // ============================================
 // GENERAL CONFIG
 // ============================================
 
 export interface CampaignGeneralConfig {
   name: string;
   description: string;
   isPermanent: boolean;
   startDateTime: Date | null;
   endDateTime: Date | null;
   requiresOptIn: boolean;
   audienceType: 'open' | 'csv' | 'optimove';
   csvFile?: File;
   optimoveSegment?: string;
   automatedExecution: {
     enabled: boolean;
     startDay: WeekDay;
     durationWeeks: number;
     finishTime: string;
   };
   frequency: {
     enabled: boolean;
     period: 'daily' | 'weekly' | 'monthly' | 'campaign';
     windowDays: number;
   };
 }
 
 // ============================================
 // VERTICAL CONFIGURATIONS (Betting/Casino)
 // ============================================
 
 export interface VerticalBetConfig {
   enabled: boolean;
   minStake: number;
   maxStake: number;
   minOdds?: number;
   minSelections?: number;
   betType: 'all' | 'single' | 'combined' | 'system';
   eligibleSports?: string[];
   eligibleMarkets?: string[];
 }
 
 export interface CasinoGame {
   id: string;
   name: string;
   vendor: string;
   type: string;
 }
 
 export interface CasinoConfig {
   enabled: boolean;
   minStake: number;
   maxStake: number;
   aggregator: string;
   vendor: string;
   selectedGames: CasinoGame[];
 }
 
 // ============================================
 // CHALLENGE CONFIGURATION
 // ============================================
 
 export interface ChallengeConfig {
   sports: VerticalBetConfig;
   virtuals: VerticalBetConfig;
   casino: CasinoConfig;
   progressCounter?: boolean;
 }
 
 // ============================================
 // TRIGGER CONFIGURATION
 // ============================================
 
 export type TriggerType = 'registration' | 'deposit' | 'bet';
 
 export interface TriggeredCampaignConfig {
   triggers: {
     sequence: TriggerType[];
     depositCondition?: {
       minAmount: number;
       currency: string;
     };
     betCondition?: {
       minStake: number;
       minOdds: number;
     };
   };
   hasChallenge: boolean;
 }
 
 // ============================================
 // BET-AND-GET CONFIGURATION
 // ============================================
 
 export interface BetAndGetConfig {
   qualifyingBets: VerticalBetConfig;
 }
 
 // ============================================
 // FREE-TO-PLAY CONFIGURATION
 // ============================================
 
 export type FTPFormat = 'prediction' | 'spin' | 'raffle';
 
 export interface FreeToPlayConfig {
   format: FTPFormat;
   entryRules: string;
 }
 
 export interface FreeToPlayMechanicsConfig {
   picksPerUser?: number;
   spinsPerUser?: number;
   attemptsPerUser?: number;
   scoringModel: 'exact' | 'partial' | 'binary';
   winnerSelectionLogic: 'highest-score' | 'random-draw' | 'first-correct';
 }
 
 // ============================================
 // REWARD CONFIGURATIONS
 // ============================================
 
 export interface FreeBetVoucher {
   id: string;
   amount: number;
   subcategory: 'prematch' | 'live';
   sports: ('all' | 'football' | 'tennis' | 'basketball' | 'cricket' | 'horse-racing')[];
   markets: string[];
 }
 
 export interface FreeBetRewardConfig {
   type: 'free-bet';
   daysOfValidity: number;
   sports: {
     enabled: boolean;
     vouchers: FreeBetVoucher[];
   };
   virtuals: {
     enabled: boolean;
     vouchers: FreeBetVoucher[];
   };
 }
 
 export interface FreeSpinsRewardConfig {
   type: 'free-spins';
   daysOfValidity: number;
   config: {
     enabled: boolean;
     amount: number;
     aggregator: string;
     vendor: string;
     selectedGames: CasinoGame[];
   };
 }
 
 export interface CashRewardConfig {
   type: 'cash';
   amount: number;
   withdrawable: boolean;
   maxRedemptions?: number;
 }
 
 export interface BonusWalletRewardConfig {
   type: 'bonus-wallet';
   amount: number;
   wageringChallenge: ChallengeConfig;
 }
 
 export type RewardConfig = FreeBetRewardConfig | FreeSpinsRewardConfig | CashRewardConfig | BonusWalletRewardConfig;
 
 // ============================================
 // MAIN CAMPAIGN DATA
 // ============================================
 
 export interface CampaignData {
   country: Country | null;
   generalConfig: CampaignGeneralConfig;
   campaignType: CampaignType | null;
   triggeredConfig?: TriggeredCampaignConfig;
   betAndGetConfig?: BetAndGetConfig;
   freeToPlayConfig?: FreeToPlayConfig;
   freeToPlayMechanicsConfig?: FreeToPlayMechanicsConfig;
   challengeConfig?: ChallengeConfig;
   selectedRewards: RewardType[];
   rewardConfigs: RewardConfig[];
 }
 
 // ============================================
 // WIZARD STEP DEFINITION
 // ============================================
 
 export interface WizardStep {
   id: string;
   title: string;
   description: string;
   isVisible: (data: CampaignData) => boolean;
 }
 
 // ============================================
 // CONSTANTS
 // ============================================
 
export const COUNTRIES: CountryConfig[] = [
  { code: 'NG', name: 'Nigeria', currency: { code: 'NGN', symbol: '₦', name: 'Nigerian Naira' }, flag: '🇳🇬', status: 'active' },
  { code: 'SA', name: 'South Africa', currency: { code: 'ZAR', symbol: 'R', name: 'South African Rand' }, flag: '🇿🇦', status: 'active' },
  { code: 'ZM', name: 'Zambia', currency: { code: 'ZMW', symbol: 'K', name: 'Zambian Kwacha' }, flag: '🇿🇲', status: 'active' },
  { code: 'KE', name: 'Kenya', currency: { code: 'KES', symbol: 'KSh', name: 'Kenyan Shilling' }, flag: '🇰🇪', status: 'blocked' },
];
 
 export const CAMPAIGN_TYPES: { type: CampaignType; title: string; description: string; allowedRewards: RewardType[] }[] = [
   {
     type: 'simple',
     title: 'Simple',
     description: 'Direct reward distribution to eligible users',
     allowedRewards: ['free-bet', 'free-spins', 'cash', 'bonus-wallet'],
   },
   {
     type: 'triggered',
     title: 'Triggered',
     description: 'Reward users based on specific actions (registration, deposit, bet)',
     allowedRewards: ['free-bet', 'free-spins', 'cash', 'bonus-wallet'],
   },
   {
     type: 'bet-and-get',
     title: 'Bet & Get',
     description: 'Users earn rewards from qualifying bets',
     allowedRewards: ['free-bet', 'free-spins', 'cash'],
   },
   {
     type: 'free-to-play',
     title: 'Free-to-Play',
     description: 'Prediction games, spins, and raffles',
     allowedRewards: ['free-bet', 'free-spins', 'cash', 'bonus-wallet'],
   },
 ];
 
 export const REWARD_TYPES: { type: RewardType; title: string; description: string }[] = [
   { type: 'free-bet', title: 'Free Bet', description: 'Vouchers for sports or virtuals betting' },
   { type: 'free-spins', title: 'Free Spins', description: 'Spins for casino games' },
   { type: 'cash', title: 'Cash', description: 'Direct cash reward' },
   { type: 'bonus-wallet', title: 'Bonus Wallet', description: 'Bonus funds with wagering requirements' },
 ];
 
 export const SPORTS_LIST = ['all', 'football', 'tennis', 'basketball', 'cricket', 'horse-racing'] as const;
 export const MARKETS_LIST = ['1X2', 'Over/Under', 'BTTS', 'Correct Score', 'First Goalscorer', 'Handicap'] as const;
 
 export const DEFAULT_VERTICAL_BET_CONFIG: VerticalBetConfig = {
   enabled: false,
   minStake: 0,
   maxStake: 0,
   minOdds: 1.5,
   minSelections: 1,
   betType: 'all',
   eligibleSports: [],
   eligibleMarkets: [],
 };
 
 export const DEFAULT_CASINO_CONFIG: CasinoConfig = {
   enabled: false,
   minStake: 0,
   maxStake: 0,
   aggregator: '',
   vendor: '',
   selectedGames: [],
 };
 
 export const DEFAULT_CHALLENGE_CONFIG: ChallengeConfig = {
   sports: { ...DEFAULT_VERTICAL_BET_CONFIG },
   virtuals: { ...DEFAULT_VERTICAL_BET_CONFIG },
   casino: { ...DEFAULT_CASINO_CONFIG },
   progressCounter: false,
 };
 
 export const DEFAULT_GENERAL_CONFIG: CampaignGeneralConfig = {
   name: '',
   description: '',
   isPermanent: false,
   startDateTime: null,
   endDateTime: null,
   requiresOptIn: false,
   audienceType: 'open',
   automatedExecution: {
     enabled: false,
     startDay: 'monday',
     durationWeeks: 1,
     finishTime: '23:59',
   },
   frequency: {
     enabled: false,
     period: 'daily',
     windowDays: 1,
   },
 };
 
 export const getInitialCampaignData = (): CampaignData => ({
   country: null,
   generalConfig: { ...DEFAULT_GENERAL_CONFIG },
   campaignType: null,
   selectedRewards: [],
   rewardConfigs: [],
 });