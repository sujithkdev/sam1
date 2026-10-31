'use strict';
const $ = id => document.getElementById(id);
let csrf = '', user = null, epoch = 0, timer, revision = 0, page = 1, view = 'overview';
let selectedAlert = null, selectedEndpoint = null, endpoints = [], detailVersion = 0, lastSuccess = 0;
const requests = new Set();
const workerLabel = worker => !worker.enabled ? 'disabled — no background analysis' : worker.healthy ? 'reporting healthy' : 'unhealthy / stopped';
const date = value => value ? new Date(typeof value === 'number' ? value * 1000 : value).toLocaleString() : 'Not observed';
function node(tag, text, className) { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (className) n.className = className; return n; }
function message(text) { $('message').textContent = text; $('message').hidden = !text; }
function clearSession() {
  epoch++; revision++; detailVersion++; clearTimeout(timer); requests.forEach(c => c.abort()); requests.clear();
  csrf = ''; user = null; selectedAlert = null; selectedEndpoint = null; endpoints = []; lastSuccess = 0; page = 1;
  $('workspace').hidden = true; $('login').hidden = false;
  for (const id of ['identity','enrolled','evidence','history','systems','alerts','commands','collectors','collector-raw','endpoint-fields','evidence-fields','timeline','rules-list','audit','health-summary','health-raw','alert-reason','ancestry','endpoint-title','coverage','updated','page-info']) $(id).replaceChildren();
  for (const id of ['online-count','events-count','alerts-count','backlog']) $(id).textContent = '—';
  for (const id of ['login-form','filters','enroll-form','rotate-form','triage-form','command-form']) $(id).reset();
  $('filter-endpoint').replaceChildren(new Option('All endpoints','')); $('rotate-system').replaceChildren();
  $('alert-detail').hidden = true; $('endpoint-detail').hidden = true; message('');
}
async function api(path, options = {}) {
  const ticket = epoch, controller = new AbortController(); requests.add(controller);
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(path, {credentials:'same-origin', ...options, signal:controller.signal,
      headers:{'Content-Type':'application/json','X-CSRF-Token':csrf,...options.headers}});
    const data = await response.json();
    if (ticket !== epoch) throw new DOMException('Stale session','AbortError');
    if (response.status === 401) { clearSession(); throw new Error('Session expired or credentials invalid. Sign in again.'); }
    if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
    return data;
  } catch(e) { if(e.name==='AbortError' && ticket===epoch) throw new Error('Request timed out. Use Refresh to retry.'); throw e; } finally { clearTimeout(timeout); requests.delete(controller); }
}
function attempt(fn) { return async event => { if(event) event.preventDefault(); const ticket=epoch; const form=event?.currentTarget; const submit=form?.tagName==='FORM' ? form.querySelector('button:not([type=button])') : null; if(submit?.disabled)return; if(submit)submit.disabled=true; try { await fn(event); } catch(e) { if(e.name !== 'AbortError' && (ticket===epoch || !user)) message(e.message); } finally { if(submit)submit.disabled=false; } }; }
function facts(id, values) { const target=$(id); target.replaceChildren(); for(const [key,value] of Object.entries(values)) target.append(node('dt',key),node('dd',value ?? 'Not observed')); }
function empty(target, columns, text) { const tr=node('tr'),td=node('td',text);td.colSpan=columns;tr.append(td);target.append(tr); }
function badge(value) { return node('span',value || 'unknown',`badge ${['critical','high','medium','low','online','offline'].includes(String(value).toLowerCase()) ? String(value).toLowerCase() : ''}`); }
function button(text, fn) { const b=node('button',text,'secondary');b.type='button';b.addEventListener('click',attempt(fn));return b; }
function switchView(next) {
  view=next; revision++;
  document.querySelectorAll('[data-page]').forEach(n=>n.hidden=n.dataset.page!==view);
  document.querySelectorAll('nav [data-view]').forEach(n=>{ if(n.dataset.view===view)n.setAttribute('aria-current','page');else n.removeAttribute('aria-current'); });
  $('page-title').textContent={overview:'Overview',alerts:'Alert investigations',endpoints:'Endpoint inventory',rules:'Detection rules',health:'System health'}[view];
  if(user) refresh();
}
function choices(id, includeAll) { const select=$(id),old=select.value;select.replaceChildren();if(includeAll)select.add(new Option('All endpoints',''));endpoints.forEach(e=>select.add(new Option(e.system_id,e.system_id)));if([...select.options].some(o=>o.value===old))select.value=old; }
function renderEndpoints() {
  const target=$('systems');target.replaceChildren();
  for(const item of endpoints) { const tr=node('tr'),name=node('td',item.system_id);name.append(node('small',item.hostname || 'Not registered'));tr.append(name);const status=node('td');status.append(badge(item.status));tr.append(status,node('td',date(item.last_seen)),node('td',date(item.last_event)),node('td',item.agent_ver || 'Unknown'));const action=node('td');action.append(button('Inspect',()=>openEndpoint(item.system_id)));tr.append(action);target.append(tr); }
  if(!endpoints.length)empty(target,6,'No enrolled endpoints. An administrator can enroll an agent below.');
  choices('filter-endpoint',true);choices('rotate-system',false);
  if(selectedEndpoint)renderEndpoint(endpoints.find(e=>e.system_id===selectedEndpoint));
}
function renderEndpoint(item) {
  if(!item){$('endpoint-detail').hidden=true;selectedEndpoint=null;return;}
  $('endpoint-detail').hidden=false;$('endpoint-title').textContent=item.hostname || item.system_id;
  facts('endpoint-fields',{'Identity':item.system_id,'Connection':item.status,'Platform':item.platform,'Agent version':item.agent_ver,'Last heartbeat / registration':date(item.last_seen),'Last telemetry received':date(item.last_event),'Retained telemetry':item.event_count || 0,'Collection gap':!item.last_event?'No telemetry observed':`No telemetry received for ${Math.max(0,Math.floor((Date.now()/1000-item.last_event)/60))} minutes; idle endpoints may be quiet`,'Last reported transport state':item.health?.transport?.state || 'Unknown','Transport observation time':date(item.health?.transport?.observed_at),'Last telemetry acknowledgment':date(item.health?.transport?.last_ack_at),'Queued outbound records':item.health?.outbox?.queued ?? 'Unknown','Oldest known queue age (seconds at report)':item.health?.outbox?.oldest_known_age_seconds ?? 'Unknown / empty','Queue records with unknown enqueue time':item.health?.outbox?.unknown_enqueue_count ?? 'Unknown','Server analysis pending':item.pending ?? 0,'Server analysis failed':item.failed ?? 0,'Oldest pending analysis age (seconds)':item.analysis_pending_age_seconds ?? 'No pending record','Sysmon reported state':item.health?.sysmon?.state || 'Unknown','Sysmon last poll':date(item.health?.sysmon?.last_poll),'Recorded collector gaps':item.health?.sysmon?.gaps ?? 'Unknown','Rejected outbound records':item.health?.outbox?.rejected ?? 'Unknown','Collector report':item.health_stale?'Missing or stale; current health unknown':`Reported ${date(item.health_received)} (agent-reported, not independently verified)`});
  $('collectors').replaceChildren();
  for(const [name,value] of Object.entries(item.health || {})) $('collectors').append(node('div',`${name}: ${JSON.stringify(value)}`,'entry'));
  if(!item.health)$('collectors').append(node('p','No collector report received. Sysmon status is unknown.'));
  $('collector-raw').textContent=JSON.stringify(item.health,null,2);
  $('command-panel').hidden=user.role==='viewer';
}
async function openEndpoint(id) { selectedEndpoint=id;renderEndpoint(endpoints.find(e=>e.system_id===id));if(user.role!=='viewer')await commands(); }
function renderAlerts(data) {
  const target=$('alerts');target.replaceChildren();
  for(const row of data.alerts){const tr=node('tr');tr.append(node('td',date(row.timestamp)));const sev=node('td');sev.append(badge(row.risk_level));const host=node('td',row.system_id);host.append(node('small',row.process));tr.append(sev,host,node('td',row.reason),node('td',row.triage_status.replaceAll('_',' ')));const action=node('td');action.append(button('Review',()=>openAlert(row.id)));tr.append(action);target.append(tr);}
  if(!data.alerts.length)empty(target,6,'No matching alerts in this window. Check filters and endpoint collection health; this does not establish safety.');
  $('page-info').textContent=`${data.total} matching · Page ${page} of ${Math.max(1,Math.ceil(data.total/data.size))}`;
  $('previous').disabled=page<=1;$('next').disabled=page*data.size>=data.total;
}
async function openAlert(id, focus=true) {
  const ticket=++detailVersion;selectedAlert=null;
  const data=await api(`/api/console/alerts/${id}`);if(ticket!==detailVersion)return;
  selectedAlert=data;const e=data.evidence || {},a=data.alert;
  $('alert-detail').hidden=false;$('alert-reason').textContent=a.reason;
  facts('evidence-fields',{'Alert ID':a.id,'Endpoint':a.system_id,'Severity':a.risk_level,'Rule matches':(data.assessment?.sigma?.matches || []).map(r=>`${r.title} (${r.id})`).join('; ') || 'See recorded reason / assessment','Process':e.exe_path || a.exe_path || a.process,'PID':e.pid ?? a.pid,'Command line':e.cmdline || 'Not captured','User':e.user,'Source':e.source || e.collector || 'Not recorded','Source event ID':a.event_id,'Evidence availability':data.evidence?'Recorded source event available':'Unavailable; may not have been retained'});
  $('ancestry').textContent=e.parent || e.parent_exe_path ? `${e.parent_exe_path || e.parent} (parent PID ${e.ppid ?? 'unknown'}) → ${e.child || a.process} (PID ${e.pid ?? a.pid}). This is the recorded direct parent, not a verified complete chain.` : 'Parent identity was not captured. No ancestry inferred.';
  if(data.ancestry?.length) $('ancestry').textContent=data.ancestry.map(n=>`${n.label} (PID ${n.pid})`).join(' → ') + '. ' + data.ancestry_scope;
  $('timeline').replaceChildren();for(const [label,value] of [['Source event',e.time],['Server receipt',data.received],['Alert recorded',a.timestamp]])$('timeline').append(node('li',`${label}: ${date(value)}`));
  $('triage-form').hidden=user.role==='viewer';$('triage-status').value=data.triage.status;$('triage-note').value='';
  $('history').replaceChildren();for(const row of data.history)$('history').append(node('div',`${date(row.timestamp)} · ${row.username} · ${row.status} — ${row.note || 'No note'}`,'entry'));
  if(!data.history.length)$('history').append(node('p','No investigation decisions recorded.'));
  $('evidence').textContent=JSON.stringify(data,null,2);if(focus)$('alert-detail').focus();
}
async function commands() {
  const sid=selectedEndpoint;if(!sid)return;
  const data=await api(`/api/commands?system_id=${encodeURIComponent(sid)}&limit=30`);if(sid!==selectedEndpoint)return;
  $('commands').replaceChildren();
  for(const row of data.commands){let result;try{result=JSON.parse(row.result);}catch{result=row.result;}
    let state=row.status==='pending'?'queued':row.status==='leased'?'leased — execution unconfirmed':row.status==='executed'?'completed — inspect result':row.status;
    if(['pending','leased'].includes(row.status)&&row.expires_at<Date.now()/1000)state='expired';
    if(result && (result.error || result.status==='error' || result.success===false))state='failed';
    const entry=node('details');entry.append(node('summary',`${row.action} · ${state} · ${date(row.created_at)}`),node('pre',JSON.stringify(result ?? 'No result received',null,2)));$('commands').append(entry);
  }
  if(!data.commands.length)$('commands').append(node('p','No information requests for this endpoint.'));
}
async function refresh() {
  if(!user)return;clearTimeout(timer);const ticket=++revision;$('refresh').disabled=true;$('updated').textContent=lastSuccess?`Refreshing · Last successful update ${new Date(lastSuccess).toLocaleTimeString()}`:'Loading observed data…';
  try{
    const [summary,inventory]=await Promise.all([api(`/api/console/summary?hours=${$('hours').value}`),api('/api/console/endpoints')]);if(ticket!==revision)return;
    endpoints=inventory.endpoints;renderEndpoints();
    $('online-count').textContent=`${summary.online} / ${summary.enrolled}`;$('events-count').textContent=summary.received_events;$('alerts-count').textContent=summary.recorded_alerts;$('backlog').textContent=`${summary.backlog.pending || 0} / ${summary.backlog.failed || 0}`;
    const gaps=endpoints.filter(e=>e.status!=='online'||e.health_stale||!e.last_event||e.health?.sysmon?.state!=='available'||(e.health?.sysmon?.gaps || 0)>0||(e.health?.outbox?.rejected || 0)>0).length;
    $('coverage').textContent=!summary.enrolled?'No active enrollment. Connect an endpoint to begin observing activity.':`${gaps} endpoint(s) have offline, collector-coverage or telemetry-gap indicators. Last receipt in window: ${date(summary.last_received)}. Analysis worker: ${workerLabel(summary.worker)}. No alerts does not mean safe.`;
    if(view==='alerts'){const params=new URLSearchParams({hours:$('hours').value,page,size:25,q:$('search').value,severity:$('severity').value,status:$('filter-status').value,system_id:$('filter-endpoint').value});const data=await api('/api/console/alerts?'+params);if(ticket!==revision)return;renderAlerts(data);}
    if(view==='rules'){const data=await api('/api/console/rules');if(ticket!==revision)return;$('rules-list').replaceChildren();for(const r of data.rules){const card=node('article',undefined,'card');card.append(badge(r.level),node('h2',r.title),node('p',r.description),node('p',`ID ${r.id} · ${r.author} · ${r.license}`),node('small',`SHA256 ${r.sha256}`));const details=node('details');details.append(node('summary','Rule predicates and known false positives'),node('pre',JSON.stringify({detection:r.detection,falsepositives:r.falsepositives},null,2)));card.append(details);$('rules-list').append(card);}}
    if(view==='health'){
      $('audit-panel').hidden=user.role!=='admin';
      if(user.role==='admin'){const [ops,audit]=await Promise.all([api('/api/operations'),api('/api/audit?limit=100')]);if(ticket!==revision)return;
        $('health-summary').textContent=`Worker: ${workerLabel(ops.worker)} · Storage admission: ${ops.storage.available?'available':'blocked'} · Pending: ${ops.backlog.pending || 0} · Failed: ${ops.backlog.failed || 0}`;
        $('health-raw').textContent=JSON.stringify(ops,null,2);$('audit').replaceChildren();for(const row of audit.audit)$('audit').append(node('div',`${date(row.timestamp)} · ${row.username} · ${row.action} · ${row.detail}`,'entry'));
      }else{$('health-summary').textContent=`Worker: ${workerLabel(summary.worker)}. Detailed storage and audit information requires an administrator.`;$('health-raw').textContent=JSON.stringify(summary.backlog,null,2);}
    }
    if(ticket!==revision)return;lastSuccess=Date.now();$('updated').textContent=`Updated ${new Date(lastSuccess).toLocaleTimeString()} · ${$('hours').selectedOptions[0].text} · Auto-refresh 10 seconds`;message('');
  }catch(e){if(ticket===revision&&e.name!=='AbortError'){message(e.message);$('updated').textContent=`Refresh failed. Displayed data may be stale. Last success: ${lastSuccess?new Date(lastSuccess).toLocaleString():'never'}. Use Refresh to retry.`;}}
  finally{if(ticket===revision){$('refresh').disabled=false;if(user)timer=setTimeout(refresh,10000);}}
}
async function signedIn(data){epoch++;requests.forEach(c=>c.abort());requests.clear();user=data;csrf=data.csrf;$('identity').textContent=`${data.username} · ${data.role}`;$('login').hidden=true;$('workspace').hidden=false;$('enrollment').hidden=data.role!=='admin';$('password').value='';switchView('overview');}
$('login-form').addEventListener('submit',attempt(async()=>{const data=await api('/auth/login',{method:'POST',body:JSON.stringify({username:$('username').value,password:$('password').value})});await signedIn(data);}));
$('logout').addEventListener('click',async()=>{
  const token=csrf;clearSession();$('refresh').disabled=false;
  const submit=$('login-form').querySelector('button');submit.disabled=true;
  try{const response=await fetch('/auth/logout',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRF-Token':token},body:'{}',signal:AbortSignal.timeout(15000)});if(!response.ok&&response.status!==401)throw new Error('Server sign-out failed');}
  catch(e){message('Local data cleared, but server session revocation was not confirmed. Retry signing in and signing out when the server is reachable.');}
  finally{submit.disabled=false;}
});
$('refresh').addEventListener('click',()=>refresh());$('hours').addEventListener('change',()=>{page=1;refresh();});
 document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>switchView(b.dataset.view)));
$('filters').addEventListener('submit',e=>{e.preventDefault();page=1;refresh();});$('previous').addEventListener('click',()=>{page--;refresh();});$('next').addEventListener('click',()=>{page++;refresh();});
$('close-alert').addEventListener('click',()=>{detailVersion++;selectedAlert=null;$('alert-detail').hidden=true;});
$('triage-form').addEventListener('submit',attempt(async()=>{if(!selectedAlert)return;const id=selectedAlert.alert.id;await api(`/api/console/alerts/${id}/triage`,{method:'POST',body:JSON.stringify({status:$('triage-status').value,note:$('triage-note').value,version:selectedAlert.triage.version})});await openAlert(id,false);refresh();}));
$('command-form').addEventListener('submit',attempt(async()=>{if(!selectedEndpoint)return;await api('/api/command',{method:'POST',body:JSON.stringify({system_id:selectedEndpoint,action:$('action').value,params:{}})});await commands();}));$('load-results').addEventListener('click',attempt(commands));
async function credential(mode){const sid=mode==='enroll'?$('system-id').value:$('rotate-system').value;const data=await api('/api/console/credentials',{method:'POST',body:JSON.stringify({mode,system_id:sid,confirm:$('rotate-confirm').value})});$('enrolled').textContent=`Save securely; hidden on logout or when you select Hide credential.\nEDR_SYSTEM_ID=${data.system_id}\nEDR_API_KEY=${data.token}`;$('rotate-confirm').value='';refresh();}
$('enroll-form').addEventListener('submit',attempt(()=>credential('enroll')));$('rotate-form').addEventListener('submit',attempt(()=>credential('rotate')));$('clear-token').addEventListener('click',()=>$('enrolled').replaceChildren());
api('/auth/me').then(signedIn).catch(()=>clearSession());
