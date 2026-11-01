export type Mode = 'Compare' | 'Verify' | 'Summarize';
export const modeRoutes: Record<Mode,string> = {Compare:'/chat',Verify:'/verify',Summarize:'/chat'};
export const examples = [
  {id:'comparison', category:'Models', title:'One question. More than one perspective.', eyebrow:'01 / MULTI-MODEL', color:'pine', text:'Compare responses from selected AI providers in a single workspace.'},
  {id:'verification', category:'Evidence', title:'Ask for the evidence, not just an answer.', eyebrow:'02 / CLAIM CHECK', color:'ink', text:'Investigate specific statements and examine sources with context.'},
  {id:'synthesis', category:'Workflow', title:'Make sense of different points of view.', eyebrow:'03 / SYNTHESIS', color:'clay', text:'Review where answers overlap, disagree or need additional checking.'},
  {id:'uncertainty', category:'Evidence', title:'Leave room for what we don’t know.', eyebrow:'04 / UNCERTAINTY', color:'paper', text:'Keep qualification and missing information visible in your review.'},
  {id:'models', category:'Models', title:'Work with your selected models.', eyebrow:'05 / YOUR STACK', color:'slate', text:'Connect supported model providers through your own credentials.'},
  {id:'history', category:'Workflow', title:'A record worth returning to.', eyebrow:'06 / TRACEABILITY', color:'olive', text:'Revisit earlier conversations and verification activity in your workspace.'}
] as const;
export const faq = [
  ['What is VerifAI?','VerifAI is a workspace for comparing AI model responses, investigating claims and keeping supporting evidence and uncertainty visible.'],
  ['Does VerifAI guarantee every answer is true?','No. AI outputs and retrieved evidence require interpretation. VerifAI helps you inspect and cross-check information; it does not guarantee correctness.'],
  ['Can I use more than one AI model?','VerifAI has a multi-model chat workflow. Model access depends on your connected providers and supported API credentials.'],
  ['Is the preview on this page connected to AI models?','No. The landing-page composer saves a draft locally in the page, then directs you to the authenticated workspace. It does not generate or verify answers here.'],
  ['Where can I review the privacy policy?','Read the Privacy and Terms pages linked in the navigation and footer.']
] as const;
export const methodSteps = [
  {n:'01',name:'Ask',headline:'Start with the question.',copy:'Give your question a place to begin. Keep the original intent clear before exploring possible answers.',label:'QUESTION IN',detail:'“What should I check before trusting this claim?”'},
  {n:'02',name:'Compare',headline:'Look across perspectives.',copy:'Different model responses can reveal agreement, disagreement, and areas that need closer examination.',label:'MODEL PERSPECTIVES',detail:'Response A  /  Response B  /  Response C'},
  {n:'03',name:'Investigate',headline:'Follow the evidence.',copy:'Break broad statements into claims and examine available sources, limitations, and contradictions.',label:'CLAIM REVIEW',detail:'Support  /  Contradiction  /  Insufficient evidence'},
  {n:'04',name:'Understand',headline:'Leave with context.',copy:'Use a considered synthesis and an honest view of uncertainty as your starting point for the next decision.',label:'REVIEW NOTES',detail:'Conclusions are provisional until validated'}
] as const;
