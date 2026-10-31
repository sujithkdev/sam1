// Session isolation regression checks; no browser or production data involved.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const elements = new Map();
function element(id) {
  if (!elements.has(id)) elements.set(id, {textContent:'',hidden:false,value:'',listeners:{},options:[],
    replaceChildren(...children){this.textContent='';this.children=children;},reset(){this.value='';},
    addEventListener(name,fn){this.listeners[name]=fn;},querySelector(){return element(id+'-button');}});
  return elements.get(id);
}
const pending=[];
const context=vm.createContext({document:{getElementById:element,querySelectorAll:()=>[]},
  Option:function(text,value){this.text=text;this.value=value;},DOMException,AbortController,AbortSignal,
  setTimeout:()=>1,clearTimeout:()=>{},fetch:(path,options)=>new Promise(resolve=>pending.push({path,options,resolve})),console,URLSearchParams});
vm.runInContext(fs.readFileSync('backend/server/static/dashboard.js','utf8'),context);
const run=code=>vm.runInContext(code,context);
(async()=>{
  run("user={role:'admin'};csrf='old-csrf';");
  for(const id of ['identity','enrolled','evidence','history','systems','alerts','commands','collector-raw'])element(id).textContent='SENSITIVE';
  const slow=run("api('/slow')");const response=pending.at(-1);
  run('clearSession()');
  response.resolve({ok:true,status:200,json:async()=>({secret:'late response'})});
  await assert.rejects(slow,{name:'AbortError'});
  for(const id of ['identity','enrolled','evidence','history','systems','alerts','commands','collector-raw'])assert.equal(element(id).textContent,'');
  assert.equal(run('csrf'),'');assert.equal(element('workspace').hidden,true);
  // A late response from an older session must not affect a new user's data.
  run("user={role:'viewer'};csrf='new-csrf';");
  assert.equal(run('csrf'),'new-csrf');
  const expiry=run("api('/expired')");pending.at(-1).resolve({ok:false,status:401,json:async()=>({error:'expired'})});
  await assert.rejects(expiry,/Session expired/);assert.equal(run('user'),null);
  // Logout clears the UI before its network response, while sending the original CSRF token.
  run("user={role:'admin'};csrf='logout-csrf';");element('enrolled').textContent='SECRET';
  const logout=element('logout').listeners.click();
  assert.equal(element('enrolled').textContent,'');assert.equal(run('user'),null);
  assert.equal(pending.at(-1).options.headers['X-CSRF-Token'],'logout-csrf');
  pending.at(-1).resolve({ok:true,status:200});await logout;
  console.log('PASS: logout cleanup, expired-session cleanup, late-response rejection, original CSRF preserved');
})().catch(error=>{console.error(error);process.exitCode=1;});
