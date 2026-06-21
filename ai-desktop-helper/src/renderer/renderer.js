// ====== Utils ======
function $(sel) { return document.querySelector(sel); }
function $$(sel) { return document.querySelectorAll(sel); }

function escape(s) {
  var map = {
    '&': '&' + 'amp;',
    '<': '&' + 'lt;',
    '>': '&' + 'gt;',
    '"': '&' + 'quot;',
    "'": '&' + '#39;'
  };
  return String(s == null ? '' : s).replace(/[&<>"']/g, function(c) { return map[c]; });
}

function escapeAttr(s) { return escape(s); }

// ====== State ======
var state = {
  items: [],
  filter: 'all',
  typeFilter: 'all',
  reports: [],
  selectedReport: null,
  selectedCard: null
};

// ====== XSS-safe markdown renderer ======
function renderMarkdown(text) {
  text = text || '';
  // code blocks (先处理)
  text = text.replace(/```(\w*)\n([\s\S]*?)```/g, function(_, lang, code) {
    return '<pre><code>' + escape(code) + '</code></pre>';
  });
  // inline code
  text = text.replace(/`([^`]+)`/g, function(_, code) {
    return '<code>' + escape(code) + '</code>';
  });
  // headings
  text = text.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  text = text.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  text = text.replace(/^# (.+)$/gm, '<h1>$1</h1>');
  // bold
  text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  // italic
  text = text.replace(/\*(.+?)\*/g, '<em>$1</em>');
  // blockquote
  text = text.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');
  // lists
  text = text.replace(/^- (.+)$/gm, '<li>$1</li>');
  text = text.replace(/((?:<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>');
  // ordered lists
  text = text.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
  // links
  text = text.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  // paragraphs (double newlines)
  text = text.replace(/\n\n/g, '</p><p>');
  // single newlines preserved
  text = text.replace(/\n/g, '<br>');
  // wrap in paragraph
  text = '<p>' + text + '</p>';
  // fix nested <p><li> etc
  text = text.replace(/<p><(ul|ol|li|h[1-3]|pre|blockquote)/g, '<$1');
  text = text.replace(/<\/(ul|ol|li|h[1-3]|pre|blockquote)><\/p>/g, '</$1>');
  // clean empty paragraphs
  text = text.replace(/<p><\/p>/g, '');
  // split merged paragraphs from block elements
  text = text.replace(/<\/(ul|ol|pre|blockquote)><br><p>/g, '</$1><p>');
  return text;
}

// ====== Navigation ======
function bindNav() {
  $$('.nav-item').forEach(function(el) {
    el.addEventListener('click', function(e) {
      e.preventDefault();
      $$('.nav-item').forEach(function(n) { n.classList.remove('active'); });
      el.classList.add('active');
      $$('.view').forEach(function(v) { v.classList.remove('active'); });
      var view = el.dataset.view;
      $('#view-' + view).classList.add('active');
      if (view === 'today') refreshLocal();
      if (view === 'reports') refreshReports();
      if (view === 'about') renderAbout();
      if (view === 'console') scrollConsoleToBottom();
    });
  });
}

// ====== Date ======
function updateDate() {
  var d = new Date();
  var y = d.getFullYear();
  var m = String(d.getMonth() + 1).padStart(2, '0');
  var day = String(d.getDate()).padStart(2, '0');
  var w = ['日', '一', '二', '三', '四', '五', '六'][d.getDay()];
  $('#topbar-date').textContent = y + ' 年 ' + m + ' 月 ' + day + ' 日 星期' + w;
}

// ====== Console Logging ======
var logBuffer = '';

function appendLog(text) {
  logBuffer += text;
  var el = $('#console-output');
  // 移除 welcome 消息
  var welcome = el.querySelector('.console-welcome');
  if (welcome) welcome.remove();
  el.appendChild(document.createTextNode(text));
  scrollConsoleToBottom();
}

function scrollConsoleToBottom() {
  var el = $('#console-output');
  el.scrollTop = el.scrollHeight;
}

function bindConsole() {
  $('#btn-console-clear').addEventListener('click', function() {
    $('#console-output').innerHTML = '<div class="console-welcome"><div class="console-cat">🐱</div><div>等待操作...</div></div>';
    logBuffer = '';
  });
  $('#btn-console-scroll').addEventListener('click', scrollConsoleToBottom);
}

// ====== Status ======
function setStatus(text, type) {
  $('#status-text').textContent = text;
  var dot = $('#status-dot');
  dot.className = 'status-dot';
  if (type === 'busy') dot.classList.add('busy');
  else if (type === 'error') dot.classList.add('error');
}

// ====== Data Fetching ======
function refreshLocal() {
  setStatus('读取数据...', 'busy');
  window.api.readLocal().then(function(res) {
    try {
      if (res.ok && res.items) {
        state.items = res.items;
        renderStats();
        renderFilters();
        renderNews();
        // 只更新今日日报的 subtitle
        if (res.meta && res.meta.updated) {
          $('#today-subtitle').textContent = '共 ' + res.items.length + ' 条 · 更新于 ' + res.meta.updated;
        } else {
          $('#today-subtitle').textContent = '共 ' + res.items.length + ' 条';
        }
      } else {
        state.items = [];
        renderStats();
        renderFilters();
        renderNews();
        $('#today-subtitle').textContent = '暂无数据';
      }
      setStatus('就绪');
    } catch (e) {
      console.error('refreshLocal error:', e);
      setStatus('读取失败', 'error');
    }
  }).catch(function(e) {
    console.error('refreshLocal catch:', e);
    setStatus('读取失败', 'error');
  });
}

function refreshReports() {
  window.api.listReports().then(function(res) {
    if (res.ok) {
      state.reports = res.files;
      renderReports();
    }
  });
}

// ====== Stats ======
function renderStats() {
  try {
    var counts = {};
    state.items.forEach(function(it) {
      var t = it.type || '其他';
      counts[t] = (counts[t] || 0) + 1;
    });
    counts['all'] = state.items.length;

    var types = ['论文', '产品', '视频', '资讯', '开源项目'];
    types.forEach(function(t) {
      var el = $('#count-' + t);
      if (el) el.textContent = counts[t] || 0;
    });
    var allEl = $('#count-all');
    if (allEl) allEl.textContent = counts['all'] || 0;
  } catch (e) {
    console.error('renderStats error:', e);
  }

  // bind stat clicks
  $$('.stat-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      $$('.stat-btn').forEach(function(b) { b.classList.remove('active'); });
      btn.classList.add('active');
      state.typeFilter = btn.dataset.type;
      renderNews();
    });
  });
}

// ====== Filters ======
function renderFilters() {
  var cats = ['全部'];
  var catSet = {};
  state.items.forEach(function(it) {
    if (it.category && it.category !== '其他') {
      catSet[it.category] = true;
    }
  });
  Object.keys(catSet).forEach(function(c) { cats.push(c); });

  var container = $('#filter-chips');
  container.innerHTML = '';
  cats.forEach(function(c) {
    var btn = document.createElement('button');
    btn.className = 'chip' + (c === state.filter ? ' active' : '');
    btn.textContent = c === '全部' ? '全部' : c;
    btn.dataset.filter = c === '全部' ? 'all' : c;
    btn.addEventListener('click', function() {
      $$('.chip').forEach(function(ch) { ch.classList.remove('active'); });
      btn.classList.add('active');
      state.filter = btn.dataset.filter;
      renderNews();
    });
    container.appendChild(btn);
  });
}

// ====== News Cards ======
function renderNews() {
  var grid = $('#news-grid');
  var empty = $('#empty-state');
  grid.innerHTML = '';

  var filtered = state.items.filter(function(it) {
    // type filter
    if (state.typeFilter !== 'all' && it.type !== state.typeFilter) return false;
    // category filter
    if (state.filter !== 'all' && (it.category || '') !== state.filter) return false;
    return true;
  });

  if (filtered.length === 0) {
    grid.style.display = 'none';
    empty.style.display = 'flex';
    return;
  }

  grid.style.display = 'grid';
  empty.style.display = 'none';

  filtered.forEach(function(it) {
    var card = document.createElement('div');
    card.className = 'news-card';

    var tag = it.tag || it.type || '';
    var cat = it.category || '';
    var typeClass = 'type-' + (it.type || '其他');

    card.innerHTML =
      '<span class="news-card-tag ' + typeClass + '">' + escape(tag) + '</span>' +
      (cat ? '<span class="news-card-category">' + escape(cat) + '</span>' : '') +
      '<div class="news-card-title">' + escape(it.title_zh || it.title || '') + '</div>' +
      '<div class="news-card-summary">' + escape((it.summary_zh || it.summary || '').substring(0, 200)) + '</div>' +
      '<div class="news-card-meta">' +
        '<span class="news-card-source">' + escape(it.source || it.type || '') + '</span>' +
        '<span>' + (it.published || '') + '</span>' +
        '<span class="news-card-rightclick-hint">🖱️ 右键菜单</span>' +
      '</div>';

    card.addEventListener('click', function() {
      window.api.openExternal(it.url);
    });

    card.addEventListener('contextmenu', function(e) {
      e.preventDefault();
      var info = { url: it.url, title: it.title, title_zh: it.title_zh, summary: it.summary, summary_zh: it.summary_zh, type: it.type, category: it.category, tag: it.tag, source: it.source };
      state.selectedCard = info;
      window.api.cardContextMenu(info).then(function(r) {
        if (r.action === 'original') openOriginal(info);
        else if (r.action === 'interpret') openInterpret(info);
      });
    });

    grid.appendChild(card);
  });
}

// ====== Reports ======
function renderReports() {
  var list = $('#report-list');
  list.innerHTML = '';

  if (state.reports.length === 0) {
    list.innerHTML = '<div class="empty-text" style="padding:40px;text-align:center;color:var(--text-mute)">暂无报告</div>';
    return;
  }

  state.reports.forEach(function(r) {
    var item = document.createElement('div');
    item.className = 'report-item';
    var name = r.name;
    var date = name.replace(/report_|\.md/g, '');
    item.innerHTML = '<span class="report-item-name">📄 ' + escape(name) + '</span><span class="report-item-date">' + escape(date) + '</span>';
    item.addEventListener('click', function() {
      window.api.readReport(r.name).then(function(res) {
        if (res.ok) {
          showReportModal(res.content, res.name);
        }
      });
    });
    list.appendChild(item);
  });
}

function showReportModal(content, name) {
  var modal = $('#modal-mask');
  $('#modal-title').textContent = '📄 ' + name;
  $('#modal-body').innerHTML = '<div class="report-preview">' +
    escape(content).replace(/\n/g, '<br>').replace(/  /g, '&nbsp;&nbsp;') +
    '</div>';
  $('#modal-cancel').style.display = 'none';
  $('#modal-confirm').textContent = '关闭';
  modal.removeAttribute('hidden');
}

// ====== Slide Panel ======
function openSlidePanel() {
  $('#panel-mask').removeAttribute('hidden');
  $('#slide-panel').removeAttribute('hidden');
}

function closeSlidePanel() {
  $('#panel-mask').setAttribute('hidden', '');
  $('#slide-panel').setAttribute('hidden', '');
  // reset
  var iframe = $('#panel-original iframe');
  if (iframe) iframe.srcdoc = '';
  $('#interpret-content').innerHTML =
    '<div class="interpret-waiting"><div class="console-cat">🧠</div><div>等待解读...</div></div>';
}

function bindSlidePanel() {
  $('#panel-close').addEventListener('click', closeSlidePanel);
  $('#panel-mask').addEventListener('click', closeSlidePanel);

  $$('.panel-tab').forEach(function(tab) {
    tab.addEventListener('click', function() {
      $$('.panel-tab').forEach(function(t) { t.classList.remove('active'); });
      tab.classList.add('active');
      $$('.panel-view').forEach(function(v) { v.classList.remove('active'); });
      $('#panel-' + tab.dataset.panelView).classList.add('active');
    });
  });
}

// ====== Original ======
function openOriginal(info) {
  openSlidePanel();
  // switch to original tab
  $$('.panel-tab').forEach(function(t) { t.classList.remove('active'); });
  $$('.panel-view').forEach(function(v) { v.classList.remove('active'); });
  $('.panel-tab[data-panel-view="original"]').classList.add('active');
  $('#panel-original').classList.add('active');

  var iframe = $('#panel-original iframe');
  iframe.srcdoc = '<html><head><meta charset="utf-8"></head><body style="font-family:-apple-system,sans-serif;padding:20px;background:#f8f9fa;color:#333;"><div style="text-align:center;padding:40px;color:#888;"><p>⏳ 正在加载原文...</p><p><small>' + escape(info.url) + '</small></p></div></body></html>';

  window.api.cardFetchOriginal(info.url).then(function(res) {
    if (res.ok && res.html) {
      var styled = res.html.replace('<head>',
        '<head><base href="' + escapeAttr(info.url) + '"><style>body{font-family:-apple-system,sans-serif;max-width:800px;margin:0 auto;padding:20px;font-size:14px;line-height:1.7;color:#222;}img{max-width:100%;}pre{overflow-x:auto;background:#f5f5f5;padding:10px;border-radius:6px;}</style>'
      );
      iframe.srcdoc = styled;
    } else {
      iframe.srcdoc = '<html><head><meta charset="utf-8"></head><body style="font-family:-apple-system,sans-serif;padding:40px;background:#f8f9fa;color:#333;"><h2>⚠️ 原文加载失败</h2><p>无法获取: ' + escape(info.url) + '</p><p>' + escape(res.error || '未知错误') + '</p><p>请尝试直接在浏览器中打开。</p></body></html>';
    }
  });
}

// ====== Interpret ======
function openInterpret(info) {
  openSlidePanel();
  // switch to interpret tab
  $$('.panel-tab').forEach(function(t) { t.classList.remove('active'); });
  $$('.panel-view').forEach(function(v) { v.classList.remove('active'); });
  $('.panel-tab[data-panel-view="interpret"]').classList.add('active');
  $('#panel-interpret').classList.add('active');

  var content = $('#interpret-content');
  content.innerHTML = '<div class="interpret-waiting"><div class="console-cat">🧠</div><div>AI 解读中，请稍候...</div><div><small>' + escape(info.title_zh || info.title || '') + '</small></div></div>';

  window.api.cardInterpret(info).then(function(res) {
    if (res.ok && res.markdown) {
      content.innerHTML = renderMarkdown(res.markdown);
    } else if (res.markdown) {
      content.innerHTML = renderMarkdown(res.markdown);
    } else {
      content.innerHTML = '<div class="interpret-waiting"><div class="console-cat">⚠️</div><div>解读失败</div><div><small>' + escape(res.error || '未知错误') + '</small></div></div>';
    }
  });
}

// ====== Actions ======
function bindActions() {
  // Quick fetch
  $('#btn-quick-fetch').addEventListener('click', function() {
    setStatus('快速采集中...', 'busy');
    appendLog('[操作] ⚡ 开始快速采集 (arXiv + HuggingFace + ProductHunt)\n');
    // 切换到 console tab
    switchView('console');
    window.api.quickFetch().then(function(res) {
      appendLog('[操作] 快速采集完成\n');
      setStatus('就绪');
      refreshLocal();
    });
  });

  // Full collect
  $('#btn-full-collect').addEventListener('click', function() {
    setStatus('全量采集中...', 'busy');
    appendLog('[操作] 📡 开始全量采集 (所有数据源)\n');
    switchView('console');
    window.api.collect().then(function(res) {
      appendLog('[操作] 全量采集完成\n');
      setStatus('就绪');
      refreshLocal();
    });
  });

  // Generate report
  $('#btn-gen-report').addEventListener('click', function() {
    setStatus('生成报告中...', 'busy');
    appendLog('[操作] 📝 生成报告...\n');
    switchView('console');
    window.api.generateReport().then(function(res) {
      appendLog('[操作] 报告生成完成\n');
      setStatus('就绪');
    });
  });

  // Refresh
  $('#btn-refresh').addEventListener('click', function() {
    refreshLocal();
    refreshReports();
  });

  // Save config
  $('#btn-save-config').addEventListener('click', function() {
    var cfg = {
      baseUrl: $('#cfg-baseUrl').value.trim(),
      apiKey: $('#cfg-apiKey').value.trim(),
      modelName: $('#cfg-modelName').value.trim()
    };
    window.api.writeConfig(cfg).then(function(res) {
      if (res.ok) {
        $('#config-status').textContent = '✅ 已保存';
        setTimeout(function() { $('#config-status').textContent = ''; }, 3000);
      } else {
        $('#config-status').textContent = '❌ 保存失败';
      }
    });
  });
}

function switchView(view) {
  $$('.nav-item').forEach(function(n) { n.classList.remove('active'); });
  $$('.view').forEach(function(v) { v.classList.remove('active'); });
  $('.nav-item[data-view="' + view + '"]').classList.add('active');
  $('#view-' + view).classList.add('active');
}

// ====== Search ======
function bindSearch() {
  var input = $('#search-input');
  var clearBtn = $('#btn-search-clear');
  var goBtn = $('#btn-search-go');

  function toggleClear() {
    if (input.value.trim()) {
      clearBtn.classList.add('show');
    } else {
      clearBtn.classList.remove('show');
    }
  }

  input.addEventListener('input', toggleClear);

  clearBtn.addEventListener('click', function() {
    input.value = '';
    toggleClear();
    input.focus();
    // 重置为全部卡片
    state.filter = 'all';
    state.typeFilter = 'all';
    $$('.chip').forEach(function(c) {
      c.classList.toggle('active', c.dataset.filter === 'all');
    });
    $$('.stat-btn').forEach(function(b) {
      b.classList.toggle('active', b.dataset.type === 'all');
    });
    renderNews();
  });

  function doSearch() {
    var q = input.value.trim();
    if (!q) return;

    setStatus('搜索中...', 'busy');
    window.api.searchLocal(q).then(function(res) {
      if (res.ok && res.items && res.items.length > 0) {
        // 有本地结果
        state.items = res.items;
        state.filter = 'all';
        state.typeFilter = 'all';
        $('#today-subtitle').textContent = '🔍 "' + q + '" 搜索结果: ' + res.total + ' 条';
        renderStats();
        renderFilters();
        renderNews();
        switchView('today');
        setStatus('就绪');
      } else {
        // 无结果，弹出确认框在线抓取
        openConfirmFetch(q, function(confirmed) {
          if (!confirmed) {
            // 用户取消，保持当前列表不变
            setStatus('就绪');
          }
        });
      }
    }).catch(function(e) {
      setStatus('搜索失败', 'error');
    });
  }

  input.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') doSearch();
  });
  goBtn.addEventListener('click', doSearch);
}

// ====== Confirm Modal ======
var pendingKeyword = '';
var pendingCallback = null;

function openConfirmFetch(keyword, callback) {
  pendingKeyword = keyword;
  pendingCallback = callback || null;
  $('#modal-title').textContent = '🔍 联网搜索: ' + keyword;
  $('#modal-body').innerHTML = '<p>本地没有找到 "<strong>' + escape(keyword) + '</strong>" 的相关结果。</p><p>是否通过 arXiv API 在线抓取相关论文？</p><p style="font-size:12px;color:var(--text-mute);margin-top:8px;">抓取结果将自动合并到本地数据库中。</p>';
  $('#modal-cancel').style.display = '';
  $('#modal-confirm').textContent = '🔍 在线抓取';
  $('#modal-mask').removeAttribute('hidden');
}

function bindConfirmModal() {
  $('#modal-close').addEventListener('click', function() { closeModal(false); });
  $('#modal-cancel').addEventListener('click', function() { closeModal(false); });
  $('#modal-confirm').addEventListener('click', function() { closeModal(true); });
}

function closeModal(confirmed) {
  $('#modal-mask').setAttribute('hidden', '');
  $('#modal-cancel').style.display = '';
  if (pendingCallback) {
    var cb = pendingCallback;
    pendingCallback = null;
    cb(confirmed);
  }
  if (confirmed) {
    confirmFetch();
  }
}

function confirmFetch() {
  if (!pendingKeyword) return;
  var kw = pendingKeyword;
  pendingKeyword = '';

  setStatus('在线抓取中...', 'busy');
  appendLog('[操作] 🔍 在线抓取关键词: ' + kw + '\n');
  switchView('console');

  window.api.fetchByKeyword(kw).then(function(res) {
    if (res.ok && res.result && res.result.items && res.result.items.length > 0) {
      appendLog('[操作] 在线抓取完成，获取到 ' + res.result.items.length + ' 条结果\n');
      setStatus('就绪');
      refreshLocal();
      // 切换到今日日报
      switchView('today');
    } else {
      var err = (res.result && res.result.error) || res.error || '无结果';
      appendLog('[操作] 在线抓取完成，无结果或失败: ' + err + '\n');
      setStatus('无结果', 'error');
      // 给出友好提示
      $('#modal-title').textContent = '🔍 未找到结果';
      $('#modal-body').innerHTML = '<p>在线抓取也没有找到 "<strong>' + escape(kw) + '</strong>" 的相关内容。</p><p style="font-size:12px;color:var(--text-mute);margin-top:8px;">可以试试更通用的关键词，或者点击「快速采集」获取最新资讯。</p>';
      $('#modal-cancel').style.display = 'none';
      $('#modal-confirm').textContent = '知道了';
      pendingCallback = null;
      $('#modal-mask').removeAttribute('hidden');
    }
  }).catch(function(e) {
    appendLog('[操作] 在线抓取出错: ' + e.message + '\n');
    setStatus('抓取出错', 'error');
  });
}

// ====== Config ======
function loadConfig() {
  window.api.readConfig().then(function(cfg) {
    $('#cfg-baseUrl').value = cfg.baseUrl || '';
    $('#cfg-apiKey').value = cfg.apiKey || '';
    $('#cfg-modelName').value = cfg.modelName || '';
  });
}

// ====== About ======
function renderAbout() {
  window.api.getInfo().then(function(info) {
    var html =
      '<div class="about-section">' +
        '<h3>🐱 AI 桌面学习助手</h3>' +
        '<p>基于 Electron，深度融合 my-ai-daily-news 采集技能，打造一站式 AI 资讯桌面应用。</p>' +
        '<p>8 大数据源自动采集 · 本地智能搜索 · 在线关键词抓取 · 大模型 AI 解读</p>' +
      '</div>' +
      '<div class="about-section">' +
        '<h3>📡 数据源</h3>' +
        '<p>arXiv · HuggingFace · Product Hunt · YouTube · The Verge · GitHub Trending · PaperWeekly · 自定义 RSS</p>' +
      '</div>' +
      '<div class="about-section">' +
        '<h3>⚙️ 系统信息</h3>' +
        '<div class="about-info-grid">' +
          '<span class="about-info-label">Python</span><span class="about-info-value">' + escape(info.python) + '</span>' +
          '<span class="about-info-label">Platform</span><span class="about-info-value">' + escape(info.platform) + '</span>' +
          '<span class="about-info-label">Electron</span><span class="about-info-value">' + escape(info.electron) + '</span>' +
          '<span class="about-info-label">Node</span><span class="about-info-value">' + escape(info.node) + '</span>' +
          '<span class="about-info-label">数据目录</span><span class="about-info-value">' + escape(info.dataDir) + '</span>' +
        '</div>' +
      '</div>' +
      '<div class="about-section">' +
        '<h3>📝 使用提示</h3>' +
        '<p>💡 卡片左键点击 → 浏览器打开原文</p>' +
        '<p>💡 卡片右键点击 → 菜单选择「原文」或「解读」</p>' +
        '<p>💡 侧边栏配置 AI Key → 即可使用 AI 解读功能</p>' +
        '<p>💡 搜索无本地结果 → 自动提示在线抓取 arXiv</p>' +
      '</div>';
    $('#about-content').innerHTML = html;
  });
}

// ====== Log subscription ======
function bindLogging() {
  window.api.onLog(function(chunk) {
    appendLog(chunk);
  });
}

// ====== Init ======
function init() {
  updateDate();
  bindNav();
  bindActions();
  bindSearch();
  bindConfirmModal();
  bindSlidePanel();
  bindConsole();
  bindLogging();
  loadConfig();
  refreshLocal();
  refreshReports();
  renderAbout();
}

document.addEventListener('DOMContentLoaded', init);
