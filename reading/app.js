// ナラティブ・アストロロジー鑑定書（第2版）
// 入力 → Swiss Ephemeris API → チャートテキスト → /api/reading/stream (gem v2)
// → 6ブロックを自動進行で受信 → 鑑定書として表示 → 印刷/PDF

const API_BASE_URL = window.location.origin;
const TOTAL_BLOCKS = 6;
const CONTINUE_MARKER = /（『はい』または『続けて』と入力すると、次へ進みます）/g;

const PREFECTURES = {
    '北海道': { lat: 43.0642, lon: 141.3469 }, '青森県': { lat: 40.8244, lon: 140.7400 },
    '岩手県': { lat: 39.7036, lon: 141.1527 }, '宮城県': { lat: 38.2682, lon: 140.8721 },
    '秋田県': { lat: 39.7186, lon: 140.1022 }, '山形県': { lat: 38.2404, lon: 140.3633 },
    '福島県': { lat: 37.7503, lon: 140.4677 }, '茨城県': { lat: 36.3418, lon: 140.4468 },
    '栃木県': { lat: 36.5658, lon: 139.8836 }, '群馬県': { lat: 36.3906, lon: 139.0608 },
    '埼玉県': { lat: 35.8617, lon: 139.6455 }, '千葉県': { lat: 35.6074, lon: 140.1065 },
    '東京都': { lat: 35.6762, lon: 139.6503 }, '神奈川県': { lat: 35.4478, lon: 139.6425 },
    '新潟県': { lat: 37.9026, lon: 139.0232 }, '富山県': { lat: 36.6959, lon: 137.2137 },
    '石川県': { lat: 36.5946, lon: 136.6256 }, '福井県': { lat: 36.0652, lon: 136.2216 },
    '山梨県': { lat: 35.6642, lon: 138.5681 }, '長野県': { lat: 36.6513, lon: 138.1809 },
    '岐阜県': { lat: 35.3912, lon: 136.7223 }, '静岡県': { lat: 34.9756, lon: 138.3827 },
    '愛知県': { lat: 35.1802, lon: 136.9066 }, '三重県': { lat: 34.7302, lon: 136.5086 },
    '滋賀県': { lat: 35.0045, lon: 135.8686 }, '京都府': { lat: 35.0211, lon: 135.7556 },
    '大阪府': { lat: 34.6937, lon: 135.5023 }, '兵庫県': { lat: 34.6913, lon: 135.1830 },
    '奈良県': { lat: 34.6851, lon: 135.8048 }, '和歌山県': { lat: 34.2261, lon: 135.1675 },
    '鳥取県': { lat: 35.5038, lon: 134.2378 }, '島根県': { lat: 35.4723, lon: 133.0505 },
    '岡山県': { lat: 34.6618, lon: 133.9346 }, '広島県': { lat: 34.3963, lon: 132.4596 },
    '山口県': { lat: 34.1861, lon: 131.4707 }, '徳島県': { lat: 34.0658, lon: 134.5593 },
    '香川県': { lat: 34.3401, lon: 134.0430 }, '愛媛県': { lat: 33.8416, lon: 132.7658 },
    '高知県': { lat: 33.5597, lon: 133.5311 }, '福岡県': { lat: 33.6064, lon: 130.4181 },
    '佐賀県': { lat: 33.2494, lon: 130.2989 }, '長崎県': { lat: 32.7503, lon: 129.8779 },
    '熊本県': { lat: 32.7898, lon: 130.7417 }, '大分県': { lat: 33.2382, lon: 131.6126 },
    '宮崎県': { lat: 31.9077, lon: 131.4202 }, '鹿児島県': { lat: 31.5602, lon: 130.5581 },
    '沖縄県': { lat: 26.2124, lon: 127.6792 }
};

const SIGNS_JP = ['牡羊座', '牡牛座', '双子座', '蟹座', '獅子座', '乙女座',
                  '天秤座', '蠍座', '射手座', '山羊座', '水瓶座', '魚座'];

const PLANETS_JP = {
    'Sun': '太陽', 'Moon': '月', 'Mercury': '水星', 'Venus': '金星', 'Mars': '火星',
    'Jupiter': '木星', 'Saturn': '土星', 'Uranus': '天王星', 'Neptune': '海王星',
    'Pluto': '冥王星', 'TrueNode': 'ドラゴンヘッド', 'Chiron': 'キローン'
};

// === 実行状態（エラー時の再開用） ===
const state = {
    messages: [],       // 会話履歴（user/assistant交互）
    blockIndex: 0,      // 完了したブロック数
    running: false,
    reportChunks: [],   // 表示済みブロックの整形前テキスト
};

// === 初期化 ===
document.addEventListener('DOMContentLoaded', () => {
    const sel = document.getElementById('prefecture');
    Object.keys(PREFECTURES).forEach(p => {
        const opt = document.createElement('option');
        opt.value = p;
        opt.textContent = p;
        sel.appendChild(opt);
    });

    document.getElementById('timeUnknown').addEventListener('change', (e) => {
        const h = document.getElementById('hour');
        const m = document.getElementById('minute');
        if (e.target.checked) {
            h.value = 12; m.value = 0; h.disabled = true; m.disabled = true;
        } else {
            h.disabled = false; m.disabled = false;
        }
    });

    document.getElementById('generateBtn').addEventListener('click', startReading);
    document.getElementById('retryBtn').addEventListener('click', resumeReading);
    document.getElementById('printBtn').addEventListener('click', () => window.print());
});

// === メインフロー ===
async function startReading() {
    const name = document.getElementById('name').value.trim();
    const year = parseInt(document.getElementById('year').value);
    const month = parseInt(document.getElementById('month').value);
    const day = parseInt(document.getElementById('day').value);
    const hour = parseInt(document.getElementById('hour').value);
    const minute = parseInt(document.getElementById('minute').value);
    const prefecture = document.getElementById('prefecture').value;
    const consultation = document.getElementById('consultation').value.trim();

    if (!name || !year || !month || !day || isNaN(hour) || isNaN(minute) || !prefecture) {
        alert('お名前・生年月日・出生時間・出生地をすべて入力してください');
        return;
    }

    const btn = document.getElementById('generateBtn');
    btn.disabled = true;
    hideError();
    setStatus('天体位置を計算しています…', 2);

    try {
        const loc = PREFECTURES[prefecture];
        const natal = await postJson('/api/calculate-chart',
            { year, month, day, hour, minute, latitude: loc.lat, longitude: loc.lon });

        const currentDate = new Date().toISOString().split('T')[0];
        const [progressions, transits, solarReturn] = await Promise.all([
            postJson('/api/calculate-progressions', {
                birth_year: year, birth_month: month, birth_day: day,
                birth_hour: hour, birth_minute: minute, current_date: currentDate
            }),
            postJson('/api/calculate-transits', { start_date: currentDate, years: 3 }),
            postJson('/api/calculate-solar-return', {
                birth_year: year, birth_month: month, birth_day: day,
                birth_hour: hour, birth_minute: minute,
                latitude: loc.lat, longitude: loc.lon, tz_name: 'Asia/Tokyo',
                current_date: currentDate,
                sr_latitude: loc.lat, sr_longitude: loc.lon, sr_tz_name: 'Asia/Tokyo'
            })
        ]);

        const chartText = buildChartText(
            name, year, month, day, hour, minute, prefecture,
            natal, progressions, transits, solarReturn, consultation, currentDate
        );

        // 鑑定書ヘッダー
        document.getElementById('reportTitle').textContent = `${name} 様`;
        document.getElementById('reportMeta').textContent =
            `${year}年${month}月${day}日 ${hour}時${String(minute).padStart(2, '0')}分 ${prefecture}生まれ ／ 鑑定日 ${currentDate}`;
        document.getElementById('reportBody').innerHTML = '';
        document.getElementById('reportSection').style.display = 'block';

        // 会話を初期化して6ブロック自動進行
        state.messages = [{ role: 'user', content: chartText }];
        state.blockIndex = 0;
        state.reportChunks = [];
        await runAllBlocks();

    } catch (err) {
        console.error(err);
        showError(`エラーが発生しました: ${err.message}`);
        btn.disabled = false;
    }
}

async function runAllBlocks() {
    state.running = true;
    hideError();
    try {
        while (state.blockIndex < TOTAL_BLOCKS) {
            setStatus(
                `鑑定書を執筆しています… （${state.blockIndex + 1} / ${TOTAL_BLOCKS} ブロック）`,
                5 + Math.round(90 * state.blockIndex / TOTAL_BLOCKS)
            );
            const blockText = await streamOneBlock();
            state.messages.push({ role: 'assistant', content: blockText });
            state.messages.push({ role: 'user', content: '続けて' });
            state.blockIndex += 1;
        }
        // 最後に積んだ「続けて」は不要
        state.messages.pop();
        setStatus('鑑定書が完成しました', 100);
        document.getElementById('generateBtn').disabled = false;
        document.getElementById('generateBtn').textContent = 'もう一度作成する';
    } catch (err) {
        console.error(err);
        showError(`執筆中にエラーが発生しました: ${err.message}`);
    } finally {
        state.running = false;
    }
}

// エラー後、完了済みブロックを保持したまま続きから再開
async function resumeReading() {
    if (state.running || state.messages.length === 0) return;
    // 直前の未完ブロックの表示を消してから再実行
    const body = document.getElementById('reportBody');
    const partial = body.querySelector('.block-partial');
    if (partial) partial.remove();
    await runAllBlocks();
}

// === 1ブロック分のストリーミング受信 ===
async function streamOneBlock() {
    const body = document.getElementById('reportBody');
    const blockDiv = document.createElement('div');
    blockDiv.className = 'block-partial';
    body.appendChild(blockDiv);

    const resp = await fetch(`${API_BASE_URL}/api/reading/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: state.messages, gem: 'v2' })
    });
    if (!resp.ok) {
        blockDiv.remove();
        let msg = `HTTP ${resp.status}`;
        try { msg = (await resp.json()).error || msg; } catch (_) { /* noop */ }
        throw new Error(msg);
    }

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let blockText = '';
    let renderTimer = null;

    const render = () => {
        blockDiv.innerHTML = formatBlock(blockText);
    };

    try {
        for (;;) {
            const { value, done } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const events = buffer.split('\n\n');
            buffer = events.pop();
            for (const ev of events) {
                const line = ev.trim();
                if (!line.startsWith('data:')) continue;
                let obj;
                try { obj = JSON.parse(line.slice(5)); } catch (_) { continue; }
                if (obj.error) throw new Error(obj.error);
                if (obj.t) {
                    blockText += obj.t;
                    if (!renderTimer) {
                        renderTimer = setTimeout(() => { renderTimer = null; render(); }, 150);
                    }
                }
            }
        }
    } catch (err) {
        // 途中まで表示されたブロックは resumeReading が破棄する
        throw err;
    }
    if (renderTimer) clearTimeout(renderTimer);
    if (!blockText.trim()) throw new Error('応答が空でした');
    render();
    blockDiv.className = 'block-done';
    state.reportChunks.push(blockText);
    return blockText;
}

// === チャートテキスト生成（第2版の入力仕様に合わせる） ===
function buildChartText(name, year, month, day, hour, minute, prefecture,
                        natalChart, progressions, transits, solarReturn,
                        consultation, currentDate) {
    let t = `# ${name}さんの占星術データ（鑑定用）\n\n`;
    t += `## 基本情報\n`;
    t += `- 生年月日: ${year}年${month}月${day}日 ${hour}時${minute}分\n`;
    t += `- 出生地: ${prefecture}\n`;
    t += `- 鑑定日: ${currentDate}\n`;
    if (solarReturn && typeof solarReturn.age === 'number') {
        t += `- 現在の年齢: ${solarReturn.age}歳\n`;
    }
    t += `\n## ネイタルチャート（出生図）\n\n### 天体の配置\n`;

    for (const [key, p] of Object.entries(natalChart.planets)) {
        if (p.error) continue;
        const rx = p.retrograde ? ' ℞（逆行）' : '';
        t += `- ${PLANETS_JP[key] || key}: ${p.signJP} ${formatDeg(p.degree)}${rx} [第${p.house}ハウス]\n`;
    }

    const houses = natalChart.houses;
    t += `\n### アングル\n`;
    t += `- ASC（アセンダント）: ${houses.ascendant.signJP} ${formatDeg(houses.ascendant.degree)}\n`;
    t += `- MC（天頂）: ${houses.midheaven.signJP} ${formatDeg(houses.midheaven.degree)}\n`;

    t += `\n### ハウスカスプ（Placidus式）\n`;
    houses.cusps.forEach((cusp, i) => {
        const si = Math.floor(cusp / 30);
        t += `- 第${i + 1}ハウス: ${SIGNS_JP[si]} ${formatDeg(cusp % 30)}\n`;
    });

    if (progressions && progressions.p_sun) {
        t += `\n## プログレス（セカンダリー進行図）\n`;
        t += `- 基準日: ${currentDate}\n`;
        t += `- プログレス太陽: ${progressions.p_sun.signJP} ${formatDeg(progressions.p_sun.degree)}\n`;
        t += `- プログレス月: ${progressions.p_moon.signJP} ${formatDeg(progressions.p_moon.degree)}\n`;
    }

    if (transits) {
        t += `\n## トランジット\n`;
        if (transits.outer_planets) {
            t += `\n### 外惑星の現在位置（${currentDate}時点）\n`;
            for (const key of ['Uranus', 'Neptune', 'Pluto']) {
                const p = transits.outer_planets[key];
                if (!p) continue;
                t += `- ${PLANETS_JP[key]}: ${p.signJP} ${formatDeg(p.degree)}${p.retrograde ? ' ℞' : ''}\n`;
            }
        }
        if (transits.jupiter_transits && transits.jupiter_transits.length) {
            t += `\n### 木星のサイン移動（今後3年）\n`;
            transits.jupiter_transits.forEach(tr => { t += `- ${tr.date}: ${tr.signJP}入り\n`; });
        }
        if (transits.saturn_transits && transits.saturn_transits.length) {
            t += `\n### 土星のサイン移動（今後3年）\n`;
            transits.saturn_transits.forEach(tr => { t += `- ${tr.date}: ${tr.signJP}入り\n`; });
        }
        t += `\n### 日食・月食\n- データ提供なし（日食・月食には言及しないでください）\n`;
    }

    if (solarReturn && solarReturn.planets) {
        const sr = solarReturn;
        t += `\n## ソーラーリターン図（太陽回帰図）\n`;
        t += `- 対象年齢: ${sr.age}歳\n`;
        t += `- リターン成立日時: ${sr.return_datetime_local}（${sr.tz_name}, ${sr.utc_offset}）\n`;
        t += `- 有効期間: ${sr.valid_from} 〜 ${sr.valid_until}（現在進行中の一年）\n`;
        t += `- 作成場所: 出生地（${prefecture}）\n`;
        t += `- SR-ASC: ${sr.houses.ascendant.signJP} ${formatDeg(sr.houses.ascendant.degree)}\n`;
        t += `- SR-MC: ${sr.houses.midheaven.signJP} ${formatDeg(sr.houses.midheaven.degree)}\n`;
        for (const key of ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
                           'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']) {
            const p = sr.planets[key];
            if (!p || p.error) continue;
            const rx = p.retrograde ? ' ℞（逆行）' : '';
            const house = p.house ? ` [第${p.house}ハウス]` : '';
            t += `- ${PLANETS_JP[key]}: ${p.signJP} ${formatDeg(p.degree)}${rx}${house}\n`;
        }
    }

    if (consultation) {
        t += `\n## ご本人からの近況とご相談（参考）\n${consultation}\n`;
    }

    t += `\n---\n以上のデータで鑑定書の執筆を開始してください。\n`;
    return t;
}

// === ブロックテキスト → HTML 整形 ===
function formatBlock(text) {
    const cleaned = text.replace(CONTINUE_MARKER, '').trim();
    const lines = cleaned.split('\n');
    let html = '';
    let para = [];
    const flush = () => {
        if (para.length) {
            html += `<p>${escapeHtml(para.join(''))}</p>`;
            para = [];
        }
    };
    for (const raw of lines) {
        const line = raw.trim();
        if (!line) { flush(); continue; }
        // 章題（「序章｜」「第N章｜」「終章｜」または #/## 見出し）
        const heading = line.replace(/^#+\s*/, '');
        if (/^(序章|第[0-9１-９十]+章|終章)[｜|]/.test(heading)) {
            flush();
            html += `<h2 class="chapter-title">${escapeHtml(heading)}</h2>`;
            continue;
        }
        if (/^#+\s/.test(line)) {
            flush();
            html += `<h3 class="minor-title">${escapeHtml(heading)}</h3>`;
            continue;
        }
        // レシピ等の箇条書き（第9章のみ許可されている）
        if (/^[-*・]\s/.test(line)) {
            flush();
            html += `<p class="recipe-line">${escapeHtml(line.replace(/^[-*]\s/, '・'))}</p>`;
            continue;
        }
        para.push(line);
    }
    flush();
    return html;
}

function escapeHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
}

// === ユーティリティ ===
async function postJson(path, body) {
    const resp = await fetch(`${API_BASE_URL}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    if (!resp.ok) throw new Error(`${path} → HTTP ${resp.status}`);
    const data = await resp.json();
    if (!data.success) throw new Error(data.error || `${path} failed`);
    return data;
}

function setStatus(text, percent) {
    const box = document.getElementById('statusBox');
    box.style.display = 'block';
    document.getElementById('statusText').textContent = text;
    document.getElementById('progressFill').style.width = `${percent}%`;
}

function showError(msg) {
    const box = document.getElementById('errorBox');
    box.style.display = 'block';
    document.getElementById('errorText').textContent = msg;
}

function hideError() {
    document.getElementById('errorBox').style.display = 'none';
}

function formatDeg(d) {
    let deg = Math.floor(d);
    let min = Math.round((d - deg) * 60);
    if (min === 60) { deg += 1; min = 0; }
    return `${deg}°${String(min).padStart(2, '0')}′`;
}
