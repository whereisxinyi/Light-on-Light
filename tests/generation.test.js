import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import handler from '../api/translate.js';

const svg = '<svg viewBox="0 0 680 680"><path d="M1 1L2 2"/></svg>';
const response = (text) => ({ ok: true, json: async () => ({ candidates: [{content: {parts: [{text}]}}] }) });
function res() {
  return { headers: {}, setHeader(k,v) {this.headers[k]=v;}, status(n) {this.code=n;return this;}, json(v) {this.body=v;}, end() {} };
}
let requestId = 0;
const req = (text='A light in a room') => ({method:'POST',headers:{'x-forwarded-for':String(++requestId)},body:{text}});

test('API validates before contacting provider', async () => {
  const out=res();await handler(req('x'),out);assert.equal(out.code,400);
});

test('API advances after invalid output and temporary failures', async () => {
  const oldFetch=global.fetch, oldKey=process.env.GEMINI_API_KEY;
  process.env.GEMINI_API_KEY='test-placeholder';let calls=0;
  global.fetch=async () => ++calls === 1 ? response('No drawing') : calls === 2 ? {ok:false,status:503} : response(svg);
  try {const out=res();await handler(req(),out);assert.equal(calls,3);assert.equal(out.code,200);assert.equal(out.body.via,'gemini');assert.equal(out.headers['Cache-Control'],'no-store');}
  finally {global.fetch=oldFetch;if(oldKey===undefined)delete process.env.GEMINI_API_KEY;else process.env.GEMINI_API_KEY=oldKey;}
});

test('API reports complete failure without a fallback drawing', async () => {
  const oldFetch=global.fetch, oldKey=process.env.GEMINI_API_KEY;
  process.env.GEMINI_API_KEY='test-placeholder';global.fetch=async()=>({ok:false,status:503});
  try {const out=res();await handler(req(),out);assert.equal(out.code,503);assert.equal(out.body.svg,undefined);}
  finally {global.fetch=oldFetch;if(oldKey===undefined)delete process.env.GEMINI_API_KEY;else process.env.GEMINI_API_KEY=oldKey;}
});

const html=readFileSync(new URL('../make.html',import.meta.url),'utf8');
const flow=html.slice(html.indexOf('  var activeStudio = null;'),html.indexOf('  /* Same sentence, another knock'));
function browser(fetchImpl) {
  const elements=new Map();let submitted;
  const element=(id)=>{if(!elements.has(id))elements.set(id,{hidden:true,textContent:'',value:'A light in a room',focus(){},addEventListener(_,fn){this.click=fn;}});return elements.get(id);};
  const timers=[];let presented=null;
  const context={AbortController,fetch:fetchImpl,window:{location:{hostname:'light-on-light.vercel.app',origin:'https://light-on-light.vercel.app'}},$:element,body:{dataset:{state:'input'}},field:element('field'),go:element('go'),live:element('live'),form:{addEventListener(_,fn){submitted=fn;}},runId:0,setTimeout(fn,ms){timers.push({fn,ms});return timers.length;},clearTimeout(){},sanitizeSVG:s=>s,stamp:()=>'',setState(s){context.body.dataset.state=s;},sow(){},present(_,art){presented=art;context.body.dataset.state='gift';}};
  vm.createContext(context);vm.runInContext(flow,context);
  return {context,e:element,timers,presented:()=>presented,submit:()=>submitted({preventDefault(){}})};
}
const flush=()=>new Promise(resolve=>setImmediate(resolve));

test('visitor waits for live drawing, never calls bank or localhost, blocks duplicate submits',async()=>{
  let resolve;let calls=0;
  const page=browser((url)=>{assert.equal(url,'/api/translate');calls++;return new Promise(r=>resolve=r);});
  page.submit();page.submit();assert.equal(calls,1);assert.equal(page.context.body.dataset.state,'forming');assert.equal(page.presented(),null);
  assert.equal(page.timers[0].ms,165000);
  resolve({ok:true,json:async()=>({svg,via:'gemini'})});await flush();
  assert.equal(page.context.body.dataset.state,'wrapped');page.timers.find(t=>t.ms===2100).fn();assert.equal(page.presented().via,'gemini');
});

test('failure preserves sentence and offers retry',async()=>{
  const page=browser(async()=>({ok:false,status:503}));page.submit();await flush();
  assert.equal(page.context.body.dataset.state,'input');assert.equal(page.context.field.value,'A light in a room');assert.equal(page.e('go').textContent,'Try again');assert.equal(page.e('generationStatus').hidden,false);assert.equal(page.presented(),null);
});

test('cancel ignores a late response',async()=>{
  let resolve;const page=browser(()=>new Promise(r=>resolve=r));page.submit();page.e('cancel').click();resolve({ok:true,json:async()=>({svg,via:'gemini'})});await flush();assert.equal(page.context.body.dataset.state,'input');assert.equal(page.presented(),null);
});
