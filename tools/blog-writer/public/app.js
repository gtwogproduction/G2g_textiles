const state = {
  urls: [],
  coverFile: null,
  coverPublicId: '',
  coverSecureUrl: '',
  article: null,
};

let allPosts = [];
let categories = [];

async function init() {
  await Promise.all([loadCategories(), loadPosts()]);
}

async function loadCategories() {
  try {
    const res = await fetch('/api/categories');
    categories = await res.json();
    populateCategorySelects();
  } catch (e) {
    console.error('Failed to load categories', e);
  }
}

function populateCategorySelects() {
  const selects = [document.getElementById('category'), document.getElementById('meta-category')];
  selects.forEach(sel => {
    while (sel.options.length > 1) sel.remove(1);
    categories.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.id;
      opt.textContent = c.name;
      sel.appendChild(opt);
    });
  });
}

async function loadPosts() {
  try {
    const res = await fetch('/api/posts');
    allPosts = await res.json();
    renderRefTable(allPosts);
  } catch (e) {
    console.error('Failed to load posts', e);
  }
}

function switchMode(mode) {
  document.querySelectorAll('.mode-section').forEach(el => el.classList.remove('active'));
  document.getElementById(`mode-${mode}`).classList.add('active');
  document.querySelectorAll('.mode-tab').forEach(el => {
    el.classList.toggle('active', el.textContent.toLowerCase().includes(mode === 'write' ? 'write' : 'reference'));
  });
}

function addUrl() {
  const input = document.getElementById('url-input');
  const url = input.value.trim();
  if (!url || !url.startsWith('http')) return;
  if (state.urls.includes(url)) { input.value = ''; return; }
  state.urls.push(url);
  input.value = '';
  renderUrlTags();
}

document.getElementById('url-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') { e.preventDefault(); addUrl(); }
});

function removeUrl(idx) {
  state.urls.splice(idx, 1);
  renderUrlTags();
}

function renderUrlTags() {
  const list = document.getElementById('url-list');
  list.innerHTML = '';
  state.urls.forEach((url, i) => {
    const tag = document.createElement('div');
    tag.className = 'tag';
    tag.innerHTML = `<span title="${url}">${url}</span><button onclick="removeUrl(${i})" title="Remove">×</button>`;
    list.appendChild(tag);
  });
}

function handleCoverSelect(input) {
  const file = input.files[0];
  if (!file) return;
  state.coverFile = file;
  state.coverPublicId = '';
  state.coverSecureUrl = '';

  const reader = new FileReader();
  reader.onload = e => {
    document.getElementById('upload-placeholder').style.display = 'none';
    document.getElementById('upload-preview').style.display = 'block';
    document.getElementById('cover-preview-img').src = e.target.result;
    document.getElementById('upload-area').classList.add('has-file');
  };
  reader.readAsDataURL(file);
}

async function uploadCoverImage() {
  if (!state.coverFile) return;
  const fd = new FormData();
  fd.append('image', state.coverFile);
  const res = await fetch('/api/upload-image', { method: 'POST', body: fd });
  if (!res.ok) throw new Error('Image upload failed');
  const data = await res.json();
  state.coverPublicId = data.public_id;
  state.coverSecureUrl = data.secure_url;
}

function removeCover() {
  state.coverFile = null;
  state.coverPublicId = '';
  state.coverSecureUrl = '';
  document.getElementById('cover-meta-wrap').style.display = 'none';
  document.getElementById('meta-cover-img').src = '';
}

async function startGeneration() {
  const topic = document.getElementById('topic').value.trim();
  if (!topic) { alert('Please enter a topic.'); return; }

  document.getElementById('btn-generate').disabled = true;

  if (state.coverFile) {
    try {
      await uploadCoverImage();
    } catch (e) {
      alert('Cover image upload failed: ' + e.message);
      document.getElementById('btn-generate').disabled = false;
      return;
    }
  }

  showPanel(2);
  resetPhaseCards();
  setStatus('Starting pipeline...', '');

  const postType = document.getElementById('post-type').value;
  const catSel = document.getElementById('category');
  const categoryName = catSel.value ? (catSel.options[catSel.selectedIndex]?.text || '') : '';

  const fd = new FormData();
  fd.append('topic', topic);
  fd.append('post_type', postType);
  fd.append('category_name', categoryName);
  fd.append('urls', JSON.stringify(state.urls));

  const es = await fetch('/api/generate', { method: 'POST', body: fd });
  const reader = es.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop();
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      try { handleEvent(JSON.parse(line.slice(6))); } catch {}
    }
  }
}

const phaseProgress = { seo: 25, writing: 55, qa: 80, translation: 100 };

function handleEvent(evt) {
  switch (evt.type) {
    case 'status':
      setStatus(evt.text, '');
      break;
    case 'phase': {
      const id = `phase-${evt.phase}`;
      setPhaseState(id, 'running', 'Running');
      openPhase(id);
      setStatus(`Running: ${evt.label}...`, 'running');
      setProgress(phaseProgress[evt.phase] - 15 || 10);
      break;
    }
    case 'seo_delta':      appendStream('stream-seo', evt.text); break;
    case 'writing_delta':  appendStream('stream-writing', evt.text); break;
    case 'qa_delta':       appendStream('stream-qa', evt.text); break;
    case 'translation_delta': appendStream('stream-translation', evt.text); break;
    case 'seo_done':
      setPhaseState('phase-seo', 'done', 'Done');
      setProgress(25);
      break;
    case 'done':    handleDone(evt.article); break;
    case 'warning': setStatus('Warning: ' + evt.text, ''); break;
    case 'error':   setStatus('Error: ' + evt.text, 'error'); break;
  }
}

function handleDone(article) {
  ['phase-seo', 'phase-writing', 'phase-qa', 'phase-translation'].forEach(id => setPhaseState(id, 'done', 'Done'));
  setProgress(100);
  setStatus('Done! Review your article below.', 'done');

  state.article = article;

  document.getElementById('edit-title').textContent = article.title || '';
  document.getElementById('edit-excerpt').textContent = article.excerpt || '';
  document.getElementById('edit-body').innerHTML = article.body || '';
  document.getElementById('edit-title-de').textContent = article.title_de || '';
  document.getElementById('edit-excerpt-de').textContent = article.excerpt_de || '';
  document.getElementById('edit-body-de').innerHTML = article.body_de || '';

  document.getElementById('meta-slug').value = article.slug || '';
  document.getElementById('meta-title').value = article.meta_title || '';
  document.getElementById('meta-desc').value = article.meta_description || '';

  updateCounter('meta-title', 'meta-title-counter', 60);
  updateCounter('meta-desc', 'meta-desc-counter', 160);
  watchCharCounter('edit-excerpt', 'excerpt-counter', 300);
  watchCharCounter('edit-excerpt-de', 'excerpt-de-counter', 300);

  document.getElementById('meta-post-type').value = document.getElementById('post-type').value;
  document.getElementById('meta-category').value = document.getElementById('category').value;

  if (article.fixes && article.fixes.length) {
    document.getElementById('fixes-list').innerHTML = article.fixes.map(f => `<li>${f}</li>`).join('');
    document.getElementById('fixes-wrap').classList.remove('hidden');
  }

  if (state.coverSecureUrl) {
    document.getElementById('meta-cover-img').src = state.coverSecureUrl;
    document.getElementById('cover-meta-wrap').style.display = 'block';
  }

  setTimeout(() => showPanel(3), 600);
}

async function saveDraft() {
  const btn = document.getElementById('btn-save');
  btn.disabled = true;
  btn.textContent = 'Saving...';

  const catSel = document.getElementById('meta-category');

  const payload = {
    title: document.getElementById('edit-title').textContent.trim(),
    title_de: document.getElementById('edit-title-de').textContent.trim(),
    slug: document.getElementById('meta-slug').value.trim(),
    post_type: document.getElementById('meta-post-type').value,
    category_id: catSel.value ? parseInt(catSel.value) : null,
    excerpt: document.getElementById('edit-excerpt').textContent.trim(),
    excerpt_de: document.getElementById('edit-excerpt-de').textContent.trim(),
    body: document.getElementById('edit-body').innerHTML,
    body_de: document.getElementById('edit-body-de').innerHTML,
    meta_title: document.getElementById('meta-title').value,
    meta_description: document.getElementById('meta-desc').value,
    cover_public_id: state.coverPublicId || '',
  };

  try {
    const res = await fetch('/api/publish', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Save failed');
    }
    const data = await res.json();
    document.getElementById('save-admin-link').href = `http://localhost:8000${data.admin_url}`;
    document.getElementById('save-result').classList.remove('hidden');
    btn.textContent = 'Saved ✓';
  } catch (e) {
    alert('Save failed: ' + e.message);
    btn.disabled = false;
    btn.textContent = 'Save as Draft →';
  }
}

function renderRefTable(posts) {
  const tbody = document.getElementById('ref-tbody');
  if (!posts.length) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:24px;">No posts found.</td></tr>';
    return;
  }
  tbody.innerHTML = posts.map(p => `
    <tr>
      <td>${escHtml(p.title)}</td>
      <td>${escHtml(p.category || '—')}</td>
      <td><span class="badge badge-${p.post_type}">${p.post_type.replace('_', ' ')}</span></td>
      <td><span class="badge badge-${p.is_published ? 'published' : 'draft'}">${p.is_published ? 'Published' : 'Draft'}</span></td>
      <td>${p.created_at || ''}</td>
      <td><a href="http://localhost:8000/en/admin/homepage/blogpost/${p.id}/change/" target="_blank">Edit</a></td>
    </tr>
  `).join('');
}

function filterRef(q) {
  const lower = q.toLowerCase();
  renderRefTable(lower ? allPosts.filter(p => p.title.toLowerCase().includes(lower)) : allPosts);
}

function showPanel(n) {
  document.querySelectorAll('.panel').forEach(el => el.classList.remove('active'));
  document.getElementById(`panel-${n}`).classList.add('active');
  ['step-1', 'step-2', 'step-3'].forEach((id, i) => {
    const el = document.getElementById(id);
    el.classList.remove('active', 'done');
    if (i + 1 < n) el.classList.add('done');
    else if (i + 1 === n) el.classList.add('active');
  });
}

function setStatus(text, type) {
  const bar = document.getElementById('status-bar');
  bar.textContent = text;
  bar.className = 'status-bar' + (type ? ` ${type}` : '');
}

function setProgress(pct) {
  document.getElementById('progress-fill').style.width = pct + '%';
}

function setPhaseState(id, state, badgeText) {
  const card = document.getElementById(id);
  card.className = `phase-card ${state}`;
  card.querySelector('.phase-badge').textContent = badgeText;
}

function openPhase(id) { document.getElementById(id).classList.add('open'); }
function togglePhase(id) { document.getElementById(id).classList.toggle('open'); }

function appendStream(id, text) {
  const el = document.getElementById(id);
  el.textContent += text;
  el.scrollTop = el.scrollHeight;
}

function resetPhaseCards() {
  ['phase-seo', 'phase-writing', 'phase-qa', 'phase-translation'].forEach(id => {
    const card = document.getElementById(id);
    card.className = 'phase-card';
    card.classList.remove('open');
    card.querySelector('.phase-badge').textContent = 'Waiting';
    card.querySelector('.phase-stream').textContent = '';
  });
  setProgress(0);
}

function toggleCollapse(id) {
  const body = document.getElementById(id);
  const chevron = document.getElementById('de-chevron');
  body.classList.toggle('open');
  chevron.textContent = body.classList.contains('open') ? '▼' : '▶';
}

function _setCounter(el, counter, max) {
  const len = (el.value !== undefined ? el.value : el.textContent || '').length;
  counter.textContent = `${len} / ${max}`;
  counter.classList.toggle('over', len > max);
}

function updateCounter(inputId, counterId, max) {
  _setCounter(document.getElementById(inputId), document.getElementById(counterId), max);
}

function watchCharCounter(editId, counterId, max) {
  const el = document.getElementById(editId);
  const counter = document.getElementById(counterId);
  el.addEventListener('input', () => _setCounter(el, counter, max));
  _setCounter(el, counter, max);
}

function startOver() {
  state.article = null;
  state.coverFile = null;
  state.coverPublicId = '';
  state.coverSecureUrl = '';
  document.getElementById('btn-generate').disabled = false;
  document.getElementById('save-result').classList.add('hidden');
  document.getElementById('btn-save').disabled = false;
  document.getElementById('btn-save').textContent = 'Save as Draft →';
  document.getElementById('topic').value = '';
  document.getElementById('url-input').value = '';
  state.urls = [];
  renderUrlTags();
  document.getElementById('upload-area').classList.remove('has-file');
  document.getElementById('upload-placeholder').style.display = '';
  document.getElementById('upload-preview').style.display = 'none';
  document.getElementById('cover-input').value = '';
  showPanel(1);
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

init();
