// Sprinter SEOSprint Real-Time Autonomous Scanner (v2.0)
// Compatible with Kiwi Browser on Android - Runs on https://seosprint.run/earn-task/2
(async function() {
  const HUD_ID = 'sprinter-live-hud';
  const existing = document.getElementById(HUD_ID);
  if (existing) existing.remove();

  // 1. Account Scanning
  let accountId = (typeof ss_id !== 'undefined' && ss_id) ? String(ss_id) : 'Unknown';
  let accountBal = '0.00';
  const balEl = document.querySelector('.user-balance, .balance, [class*="balance"]');
  if (balEl) accountBal = balEl.textContent.trim().replace(/[^\d\.,]/g, '');

  // Sync account info to Termux if server is active
  fetch('http://127.0.0.1:8080/api/account', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: accountId,
      username: 'SEOSprint Member #' + accountId,
      balance_usd: parseFloat(accountBal.replace(',', '.')) || 0.0,
      rating: 0.0,
      status: 'Active'
    })
  }).catch(() => {});

  // 2. Build Mobile-Optimized HUD
  const hud = document.createElement('div');
  hud.id = HUD_ID;
  hud.style.cssText = `
    position: fixed; top: 8px; left: 8px; right: 8px; max-height: 92vh;
    background: #0f172a; color: #f8fafc; border: 2px solid #10b981;
    border-radius: 12px; box-shadow: 0 16px 45px rgba(0,0,0,0.9);
    z-index: 2147483647; font-family: -apple-system, Roboto, sans-serif; font-size: 13px;
    display: flex; flex-direction: column; overflow: hidden;
  `;

  hud.innerHTML = `
    <div style="background:#1e293b; padding:10px 14px; border-bottom:1px solid #334155; display:flex; justify-content:space-between; align-items:center;">
      <div>
        <div style="font-weight:700; font-size:13px; color:#38bdf8;">[SPRINTER] $100 Goal Task Scanner</div>
        <div style="font-size:11px; color:#94a3b8;">User: #${accountId} | Email Only | Android Only | No KYC | &lt; 5m</div>
      </div>
      <div style="display:flex; gap:5px;">
        <button id="scan-stop-btn" style="background:#ef4444; color:#fff; border:none; padding:5px 9px; border-radius:5px; font-weight:700; cursor:pointer; font-size:11px;">Stop</button>
        <button id="scan-close-btn" style="background:#475569; color:#fff; border:none; padding:5px 9px; border-radius:5px; cursor:pointer; font-size:11px;">X</button>
      </div>
    </div>
    <div style="padding:10px 14px; background:#182234; border-bottom:1px solid #334155;">
      <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:5px;">
        <span id="scan-status-text" style="color:#38bdf8; font-weight:600;">Starting scan...</span>
        <span id="scan-goal-counter" style="color:#10b981; font-weight:700;">$0.00 / $100.00 (0%)</span>
      </div>
      <div style="background:#334155; border-radius:8px; height:8px; width:100%; overflow:hidden;">
        <div id="scan-prog-bar" style="background:linear-gradient(90deg, #38bdf8, #10b981); width:0%; height:100%;"></div>
      </div>
      <div style="display:flex; justify-content:space-between; font-size:11px; color:#94a3b8; margin-top:5px;">
        <span id="scan-pages-info">Target: /earn-task/2</span>
        <span id="scan-matched-info">Matched: 0 tasks (Synced: 0)</span>
      </div>
    </div>
    <div id="scan-log-box" style="padding:10px; overflow-y:auto; flex:1; max-height:48vh; background:#0b1120;"></div>
    <div style="padding:10px; background:#1e293b; border-top:1px solid #334155; display:flex; gap:6px;">
      <button id="scan-guide-btn" style="flex:1; background:#f59e0b; color:#0f172a; font-weight:700; border:none; padding:8px; border-radius:5px; cursor:pointer; font-size:11px;">Task #1 Guide</button>
      <button id="scan-export-btn" disabled style="flex:1; background:#10b981; color:#0f172a; font-weight:700; border:none; padding:8px; border-radius:5px; cursor:pointer; font-size:11px;">Export JSON</button>
      <button id="scan-export-txt-btn" disabled style="flex:1; background:#38bdf8; color:#0f172a; font-weight:700; border:none; padding:8px; border-radius:5px; cursor:pointer; font-size:11px;">Export TXT</button>
    </div>
  `;

  document.body.appendChild(hud);

  const statusEl = hud.querySelector('#scan-status-text');
  const goalCounterEl = hud.querySelector('#scan-goal-counter');
  const progBar = hud.querySelector('#scan-prog-bar');
  const pagesInfo = hud.querySelector('#scan-pages-info');
  const matchedInfo = hud.querySelector('#scan-matched-info');
  const logBox = hud.querySelector('#scan-log-box');
  const btnStop = hud.querySelector('#scan-stop-btn');
  const btnClose = hud.querySelector('#scan-close-btn');
  const btnExport = hud.querySelector('#scan-export-btn');
  const btnExportTxt = hud.querySelector('#scan-export-txt-btn');
  const btnGuide = hud.querySelector('#scan-guide-btn');

  let isScanning = true;
  let targetGoalUSD = 100.0;
  let accumulatedUSD = 0.0;
  let qualifiedTasks = [];
  let seenTaskIds = new Set();
  let syncedCount = 0;

  btnClose.onclick = () => { isScanning = false; hud.remove(); };
  btnStop.onclick = () => { isScanning = false; statusEl.textContent = 'Scan paused.'; };

  function parsePrice(text) {
    if (!text) return 0.0;
    const usd = text.match(/([\d\.,]+)\s*(\$|usd)/i) || text.match(/(\$)\s*([\d\.,]+)/i);
    if (usd) return parseFloat((usd[1] === '$' ? usd[2] : usd[1]).replace(',', '.')) || 0.0;
    const rub = text.match(/([\d\.,]+)\s*(руб|₽|rub)/i);
    if (rub) return (parseFloat(rub[1].replace(',', '.')) || 0.0) / 95.0;
    const num = text.match(/[\d\.,]+/);
    return num ? parseFloat(num[0].replace(',', '.')) || 0.0 : 0.0;
  }

  function estimateTime(title, desc) {
    const text = (title + ' ' + desc).toLowerCase();
    if (['клик', 'переход', 'быстрый', 'секунд', '1 мин', 'быстро'].some(t => text.includes(t))) return 1.5;
    if (['только регистрация', 'без активности', 'простая рега'].some(t => text.includes(t))) return 2.0;
    if (['скачать', 'установить', 'apk', 'приложение', 'app'].some(t => text.includes(t))) return 3.5;
    return 2.5;
  }

  function matchesUserCriteria(title, desc) {
    const text = (title + ' ' + desc).toLowerCase();

    // 1. Strictly Reject KYC, Face, Passport, ID
    const kyc = ['паспорт', 'вериф', 'kyc', 'паспортные', 'passport', 'id card', 'селфи', 'selfie', 'документ', 'личность', 'госуслуги'];
    for (const k of kyc) {
      if (text.includes(k)) {
        const idx = text.indexOf(k);
        const prefix = text.substring(Math.max(0, idx - 25), idx);
        if (!/(?:no|without|без|не\s+нужно|не\s+требуется)/i.test(prefix)) return false;
      }
    }

    // 2. Strictly Reject Phone Number, SMS, OTP
    const phone = ['номер телефона', 'смс', 'sms', 'код из смс', 'подтвердить номер', 'привязать телефон', 'звонок', 'phone number', 'otp', 'привязка номера'];
    for (const p of phone) {
      if (text.includes(p)) {
        const idx = text.indexOf(p);
        const prefix = text.substring(Math.max(0, idx - 25), idx);
        if (!/(?:no|without|без|не\s+нужно|не\s+требуется)/i.test(prefix)) return false;
      }
    }

    // 3. Strictly Reject Deposits, Payments, Casinos
    if (['депозит', 'deposit', 'вложить', 'вложения', 'пополнить', 'купить', 'оплата', 'казино', 'casino', 'ставки'].some(t => text.includes(t))) return false;

    // 4. Reject multi-day grinds or > 5 min tasks
    if (['дней', 'неделю', 'уровень', 'прокачать', 'lvl', 'level', '10 минут', '15 минут', '20 минут', '30 минут', '1 час'].some(t => text.includes(t))) return false;

    // 5. Must match Email Signup or Android app installation
    return ['регистрация', 'рега', 'email', 'почта', 'почт', 'подтвердить почту', 'sign up', 'signup', 'register', 'аккаунт', 'активация', 'скачать', 'приложение', 'app', 'android', 'apk', 'установка', 'телефон'].some(t => text.includes(t));
  }

  function translateSimple(text) {
    return text
      .replace(/Только регистрация/gi, 'Registration Only')
      .replace(/без активности/gi, 'No activity required')
      .replace(/Быстрая регистрация/gi, 'Fast Registration')
      .replace(/Подтвердить почту/gi, 'Confirm Email')
      .replace(/В отчёт/gi, 'Report: ')
      .replace(/Логин/gi, 'Login/Username')
      .replace(/Установить приложение/gi, 'Install App')
      .replace(/Простая/gi, 'Simple');
  }

  let page = 1;
  const maxPages = 60;

  while (isScanning && page <= maxPages && accumulatedUSD < targetGoalUSD) {
    statusEl.textContent = `Scanning Page ${page}...`;
    pagesInfo.textContent = `Page ${page} / ${maxPages}`;

    const url = new URL('/earn-task/2', location.origin);
    url.searchParams.set('page', page);

    try {
      const resp = await fetch(url.toString(), { credentials: 'include' });
      if (!resp.ok) { page++; continue; }
      const text = await resp.text();
      if (text.includes('Oops ... Sorry generously') || text.includes('Denied')) {
        statusEl.textContent = 'Error: Session not logged in.';
        break;
      }

      const doc = new DOMParser().parseFromString(text, 'text/html');
      const rows = doc.querySelectorAll('.table-rtask tr, .table-rtask-main, tr[data-task-id], .work-task-cell');
      if (!rows.length) {
        statusEl.textContent = 'End of task catalog reached.';
        break;
      }

      const newBatch = [];
      rows.forEach(el => {
        const row = el.closest('tr') || el;
        const linkEl = row.querySelector('a[href*="/taskread/"], a[href*="earn-task/"]');
        if (!linkEl) return;
        const href = linkEl.href;
        const taskId = href.match(/\/taskread\/(\d+)/)?.[1] || href;
        if (seenTaskIds.has(taskId)) return;
        seenTaskIds.add(taskId);

        const title = linkEl.textContent.trim();
        const priceEl = row.querySelector('.watch-price, .price-click, .ticon-pricetag') || row;
        const priceUSD = parsePrice(priceEl ? priceEl.textContent : '');
        const estMin = estimateTime(title, row.textContent);

        if (matchesUserCriteria(title, row.textContent)) {
          const taskObj = {
            taskId: taskId,
            title: title,
            priceUSD: priceUSD,
            url: href,
            page: page,
            est_minutes: estMin
          };
          qualifiedTasks.push(taskObj);
          newBatch.push(taskObj);
          accumulatedUSD += priceUSD;

          // Re-sort qualified tasks by lowest time-taking first
          qualifiedTasks.sort((a, b) => a.est_minutes - b.est_minutes || b.priceUSD - a.priceUSD);

          const item = document.createElement('div');
          item.style.cssText = 'background:#1e293b; border-left:3px solid #10b981; padding:6px 8px; margin-bottom:6px; border-radius:4px;';
          item.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span style="background:#334155; color:#38bdf8; font-size:10px; padding:2px 5px; border-radius:3px; font-weight:700;">~${estMin.toFixed(1)}m</span>
              <span style="color:#10b981; font-weight:700; font-size:12px;">+$${priceUSD.toFixed(3)}</span>
            </div>
            <div style="margin-top:3px;">
              <a href="${href}" target="_blank" style="color:#f8fafc; font-size:12px; font-weight:600; text-decoration:none;">${translateSimple(title)}</a>
            </div>
          `;
          logBox.prepend(item);

          const pct = Math.min(100, Math.round((accumulatedUSD / targetGoalUSD) * 100));
          progBar.style.width = `${pct}%`;
          goalCounterEl.textContent = `$${accumulatedUSD.toFixed(2)} / $${targetGoalUSD.toFixed(2)} (${pct}%)`;
        }
      });

      // Sync batch to Termux Sprinter server (port 8080)
      if (newBatch.length > 0) {
        fetch('http://127.0.0.1:8080/api/bulk-shortlist', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newBatch)
        }).then(r => r.json()).then(res => {
          if (res.status === 'ok') syncedCount += res.saved_count;
          matchedInfo.textContent = `Matched: ${qualifiedTasks.length} tasks (Synced: ${syncedCount})`;
        }).catch(() => {
          matchedInfo.textContent = `Matched: ${qualifiedTasks.length} tasks (Termux sync offline)`;
        });
      }

      btnExport.disabled = qualifiedTasks.length === 0;
      btnExportTxt.disabled = qualifiedTasks.length === 0;

      if (accumulatedUSD >= targetGoalUSD) {
        statusEl.textContent = `Goal Reached ($${accumulatedUSD.toFixed(2)})!`;
        break;
      }
      await new Promise(r => setTimeout(r, 1200));
      page++;
    } catch (e) {
      page++;
      await new Promise(r => setTimeout(r, 2000));
    }
  }

  btnGuide.onclick = () => {
    if (qualifiedTasks.length === 0) {
      alert("No qualified tasks scanned yet. Wait for scan to find tasks.");
      return;
    }
    const t = qualifiedTasks[0];
    const guideMsg = `TASK #1 EXECUTION GUIDE (Fastest ~${t.est_minutes} min):\n\n` +
      `Title: ${translateSimple(t.title)}\n` +
      `Payout: +$${t.priceUSD.toFixed(3)}\n` +
      `Link: ${t.url}\n\n` +
      `FAST 3-STEP GUIDE:\n` +
      `1. Open task link & click 'Start Execution'.\n` +
      `2. Quick register with your email (no phone/KYC needed).\n` +
      `3. Confirm email link, copy username & paste into report box!\n\n` +
      `Open task now?`;
    if (confirm(guideMsg)) {
      window.open(t.url, '_blank');
    }
  };

  btnExport.onclick = () => {
    const dataStr = JSON.stringify(qualifiedTasks, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `seosprint_earn_task2_${Date.now()}.json`;
    a.click();
    navigator.clipboard.writeText(dataStr);
    alert(`Exported ${qualifiedTasks.length} tasks to JSON and copied to clipboard.`);
  };

  btnExportTxt.onclick = () => {
    let txt = `SEOSPRINT /earn-task/2 SHORTLIST (${qualifiedTasks.length} tasks - $${accumulatedUSD.toFixed(2)})\n`;
    txt += `Sorted Lowest Time to Highest Time\n\n`;
    qualifiedTasks.forEach((t, i) => {
      txt += `${i + 1}. [~${t.est_minutes.toFixed(1)} min] [+$${t.priceUSD.toFixed(3)}] ${translateSimple(t.title)}\n   ${t.url}\n\n`;
    });
    const blob = new Blob([txt], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `seosprint_tasks_${Date.now()}.txt`;
    a.click();
    navigator.clipboard.writeText(txt);
    alert(`Exported ${qualifiedTasks.length} links to TXT and copied to clipboard.`);
  };
})();
