// Sprinter Real-Time In-Browser Scanner (Zero Emojis)
// Run this directly in Kiwi Browser Console on https://seosprint.net/earn
(async function() {
  const HUD_ID = 'sprinter-live-hud';
  const existing = document.getElementById(HUD_ID);
  if (existing) existing.remove();

  const hud = document.createElement('div');
  hud.id = HUD_ID;
  hud.style.cssText = `
    position: fixed; top: 10px; left: 10px; right: 10px; max-height: 90vh;
    background: #0f172a; color: #f8fafc; border: 2px solid #10b981;
    border-radius: 12px; box-shadow: 0 16px 40px rgba(0,0,0,0.85);
    z-index: 2147483647; font-family: -apple-system, sans-serif; font-size: 13px;
    display: flex; flex-direction: column; overflow: hidden;
  `;

  hud.innerHTML = `
    <div style="background:#1e293b; padding:12px; border-bottom:1px solid #334155; display:flex; justify-content:space-between; align-items:center;">
      <div>
        <div style="font-weight:700; font-size:14px; color:#38bdf8;">[SPRINTER] $100 Goal Task Scanner</div>
        <div style="font-size:11px; color:#94a3b8;">Email Signup | Phone Only | No KYC | No Phone# | 2-3 Min</div>
      </div>
      <div>
        <button id="scan-stop-btn" style="background:#ef4444; color:#fff; border:none; padding:4px 8px; border-radius:4px; font-weight:700; cursor:pointer;">Stop</button>
        <button id="scan-close-btn" style="background:#475569; color:#fff; border:none; padding:4px 8px; border-radius:4px; margin-left:4px; cursor:pointer;">X</button>
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
        <span id="scan-pages-info">Pages: 0</span>
        <span id="scan-matched-info">Matched: 0 tasks (Synced to Termux: 0)</span>
      </div>
    </div>
    <div id="scan-log-box" style="padding:10px; overflow-y:auto; flex:1; max-height:48vh; background:#0b1120;"></div>
    <div style="padding:10px; background:#1e293b; border-top:1px solid #334155; display:flex; gap:6px;">
      <button id="scan-export-btn" disabled style="flex:1; background:#10b981; color:#0f172a; font-weight:700; border:none; padding:8px; border-radius:5px; cursor:pointer; font-size:11px;">Export JSON</button>
      <button id="scan-export-txt-btn" disabled style="flex:1; background:#38bdf8; color:#0f172a; font-weight:700; border:none; padding:8px; border-radius:5px; cursor:pointer; font-size:11px;">Export Links (TXT)</button>
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

  function matchesUserCriteria(title, desc) {
    const text = (title + ' ' + desc).toLowerCase();
    const kyc = ['паспорт', 'вериф', 'kyc', 'паспортные', 'passport', 'id card', 'селфи', 'selfie', 'документ', 'личность', 'госуслуги'];
    for (const kw of kyc) {
      const idx = text.indexOf(kw);
      if (idx !== -1 && !/(?:no|without|без|не\s+нужно|не\s+требуется)/i.test(text.substring(Math.max(0, idx - 25), idx))) return false;
    }
    const phone = ['номер телефона', 'смс', 'sms', 'код из смс', 'подтвердить номер', 'привязать телефон', 'звонок', 'phone number', 'otp'];
    for (const kw of phone) {
      const idx = text.indexOf(kw);
      if (idx !== -1 && !/(?:no|without|без|не\s+нужно|не\s+требуется)/i.test(text.substring(Math.max(0, idx - 25), idx))) return false;
    }
    const money = ['депозит', 'deposit', 'вложить', 'вложения', 'пополнить баланс', 'купить', 'оплата', 'инвестиц', 'казино'];
    for (const kw of money) {
      const idx = text.indexOf(kw);
      if (idx !== -1 && !/(?:no|without|без|не\s+нужно|не\s+требуется)/i.test(text.substring(Math.max(0, idx - 25), idx))) return false;
    }
    if (['дней', 'неделю', 'уровень', 'прокачать', 'lvl', 'level'].some(t => text.includes(t))) return false;
    return ['регистрация', 'рега', 'email', 'почта', 'почт', 'подтвердить почту', 'sign up', 'signup', 'register', 'аккаунт', 'активация', 'скачать', 'приложение', 'app', 'android', 'apk', 'установка', 'телефон'].some(t => text.includes(t));
  }

  const baseUrl = new URL('/earn', location.origin);
  let page = 1;
  const maxPages = 60;

  while (isScanning && page <= maxPages && accumulatedUSD < targetGoalUSD) {
    statusEl.textContent = `Scanning Page ${page}...`;
    pagesInfo.textContent = `Page ${page} / ${maxPages}`;
    baseUrl.searchParams.set('page', page);

    try {
      const resp = await fetch(baseUrl.toString(), { credentials: 'include' });
      if (!resp.ok) { page++; continue; }
      const doc = new DOMParser().parseFromString(await resp.text(), 'text/html');
      const rows = doc.querySelectorAll('.table-rtask tr, .table-rtask-main, tr[data-task-id], .work-task-cell');
      if (!rows.length) break;

      const newBatch = [];
      rows.forEach(el => {
        const row = el.closest('tr') || el;
        const linkEl = row.querySelector('a[href*="/taskread/"], a[href*="earn-task/"]');
        if (!linkEl) return;
        const url = linkEl.href;
        const taskId = url.match(/\/taskread\/(\d+)/)?.[1] || url;
        if (seenTaskIds.has(taskId)) return;
        seenTaskIds.add(taskId);

        const title = linkEl.textContent.trim();
        const priceEl = row.querySelector('.watch-price, .price-click, .ticon-pricetag') || row;
        const priceUSD = parsePrice(priceEl ? priceEl.textContent : '');

        if (matchesUserCriteria(title, row.textContent)) {
          const taskObj = { taskId, title, priceUSD, url, page };
          qualifiedTasks.push(taskObj);
          newBatch.push(taskObj);
          accumulatedUSD += priceUSD;

          const item = document.createElement('div');
          item.style.cssText = 'background:#1e293b; border-left:3px solid #10b981; padding:6px 8px; margin-bottom:6px; border-radius:4px;';
          item.innerHTML = `<div style="display:flex; justify-content:space-between;"><a href="${url}" target="_blank" style="color:#38bdf8; font-size:12px; font-weight:600; text-decoration:none;">${title}</a><span style="color:#10b981; font-weight:700;">+$${priceUSD.toFixed(3)}</span></div>`;
          logBox.prepend(item);

          const pct = Math.min(100, Math.round((accumulatedUSD / targetGoalUSD) * 100));
          progBar.style.width = `${pct}%`;
          goalCounterEl.textContent = `$${accumulatedUSD.toFixed(2)} / $${targetGoalUSD.toFixed(2)} (${pct}%)`;
        }
      });

      // Sync batch to Termux Sprinter server if running
      if (newBatch.length > 0) {
        fetch('http://127.0.0.1:8080/api/bulk-shortlist', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newBatch)
        }).then(r => r.json()).then(res => {
          if (res.status === 'ok') syncedCount += res.saved_count;
          matchedInfo.textContent = `Matched: ${qualifiedTasks.length} tasks (Synced to Termux: ${syncedCount})`;
        }).catch(() => {
          matchedInfo.textContent = `Matched: ${qualifiedTasks.length} tasks (Termux offline)`;
        });
      }

      btnExport.disabled = qualifiedTasks.length === 0;
      btnExportTxt.disabled = qualifiedTasks.length === 0;

      if (accumulatedUSD >= targetGoalUSD) {
        statusEl.textContent = `Goal Achieved ($${accumulatedUSD.toFixed(2)})!`;
        break;
      }
      await new Promise(r => setTimeout(r, 1200));
      page++;
    } catch (e) {
      page++;
      await new Promise(r => setTimeout(r, 2000));
    }
  }

  btnExport.onclick = () => {
    const dataStr = JSON.stringify(qualifiedTasks, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `sprinter_100usd_${Date.now()}.json`;
    a.click();
    navigator.clipboard.writeText(dataStr);
    alert(`Exported ${qualifiedTasks.length} tasks to JSON and copied to clipboard.`);
  };

  btnExportTxt.onclick = () => {
    let txt = `SPRINTER $100 GOAL LIST (${qualifiedTasks.length} tasks - $${accumulatedUSD.toFixed(2)})\n\n`;
    qualifiedTasks.forEach((t, i) => { txt += `${i + 1}. [+$${t.priceUSD.toFixed(3)}] ${t.title}\n   ${t.url}\n\n`; });
    const blob = new Blob([txt], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `sprinter_links_${Date.now()}.txt`;
    a.click();
    navigator.clipboard.writeText(txt);
    alert(`Exported ${qualifiedTasks.length} links to TXT and copied to clipboard.`);
  };
})();
