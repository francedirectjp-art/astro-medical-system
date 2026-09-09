// 2026 未来の航海図 — 体験ページ
// 出生データ → (同アプリの)Swiss Ephemeris APIでチャート計算 → 鑑定プロンプト生成 → Gemで鑑定
// ※AI処理はユーザー自身のGem(Gemini)が行う＝運営のAPIコストは発生しない無料体験。

const API_BASE_URL = window.location.origin;
// Narrative Astrologer GEM (Gemini)
const GEM_URL = 'https://gemini.google.com/gem/1NgB6OizsXJSo8kfeq4suOksYprUgN2io?usp=sharing';

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

let lastPrompt = '';

function formatDeg(d) {
    let deg = Math.floor(d);
    let min = Math.round((d - deg) * 60);
    if (min === 60) { deg += 1; min = 0; }
    return `${deg}°${String(min).padStart(2, '0')}′`;
}

document.addEventListener('DOMContentLoaded', () => {
    const pref = document.getElementById('prefecture');
    Object.keys(PREFECTURES).forEach((p) => {
        const o = document.createElement('option');
        o.value = p; o.textContent = p; pref.appendChild(o);
    });
    document.getElementById('timeUnknown').addEventListener('change', (e) => {
        const h = document.getElementById('hour'), m = document.getElementById('minute');
        if (e.target.checked) { h.value = 12; m.value = 0; h.disabled = true; m.disabled = true; }
        else { h.disabled = false; m.disabled = false; }
    });
    document.getElementById('generateBtn').addEventListener('click', onGenerate);
    document.getElementById('openGemBtn').addEventListener('click', openGem);
    document.getElementById('copyBtn').addEventListener('click', copyPrompt);
    document.getElementById('restartBtn').addEventListener('click', () => {
        document.getElementById('receiveCard').style.display = 'none';
        document.getElementById('formCard').style.display = 'block';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
});

async function onGenerate() {
    const name = document.getElementById('name').value.trim();
    const year = parseInt(document.getElementById('year').value);
    const month = parseInt(document.getElementById('month').value);
    const day = parseInt(document.getElementById('day').value);
    const hour = parseInt(document.getElementById('hour').value);
    const minute = parseInt(document.getElementById('minute').value);
    const prefecture = document.getElementById('prefecture').value;

    if (!name || !year || !month || !day || isNaN(hour) || isNaN(minute) || !prefecture) {
        alert('すべての項目を入力してください');
        return;
    }
    const loc = PREFECTURES[prefecture];
    const btn = document.getElementById('generateBtn');
    btn.disabled = true; btn.textContent = '⏳ 星を計算しています…';
    document.getElementById('loading').style.display = 'block';
    try {
        const natalChart = await calcChart(year, month, day, hour, minute, loc.lat, loc.lon);
        let progressions = null, transits = null;
        try { progressions = await calcProgressions(year, month, day, hour, minute); } catch (e) {}
        try { transits = await calcTransits(); } catch (e) {}
        lastPrompt = buildPromptText(name, year, month, day, hour, minute, prefecture, natalChart, progressions, transits);
        document.getElementById('formCard').style.display = 'none';
        document.getElementById('receiveCard').style.display = 'block';
        document.getElementById('promptPreview').value = lastPrompt;
        document.getElementById('receiveName').textContent = name + ' さん';
        document.getElementById('receiveCard').scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
        alert('計算でエラーが発生しました: ' + err.message);
    } finally {
        document.getElementById('loading').style.display = 'none';
        btn.disabled = false; btn.textContent = '✦ 鑑定書を受け取る';
    }
}

async function calcChart(year, month, day, hour, minute, latitude, longitude) {
    const r = await fetch(`${API_BASE_URL}/api/calculate-chart`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ year, month, day, hour, minute, latitude, longitude })
    });
    if (!r.ok) throw new Error('chart ' + r.status);
    const d = await r.json();
    if (!d.success) throw new Error(d.error || 'chart failed');
    return d;
}
async function calcProgressions(y, mo, d, h, mi) {
    const cur = new Date().toISOString().split('T')[0];
    const r = await fetch(`${API_BASE_URL}/api/calculate-progressions`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ birth_year: y, birth_month: mo, birth_day: d, birth_hour: h, birth_minute: mi, current_date: cur })
    });
    const data = await r.json();
    if (!data.success) throw new Error('prog');
    return data;
}
async function calcTransits() {
    const cur = new Date().toISOString().split('T')[0];
    const r = await fetch(`${API_BASE_URL}/api/calculate-transits`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ start_date: cur, years: 3 })
    });
    const data = await r.json();
    if (!data.success) throw new Error('transit');
    return data;
}

function buildPromptText(name, year, month, day, hour, minute, prefecture, natalChart, progressions, transits) {
    let p = `# 【完全版】${name}さんの占星術データ\n\n`;
    p += `## 基本情報\n- 生年月日: ${year}年${month}月${day}日 ${hour}時${minute}分\n- 出生地: ${prefecture}\n\n`;
    p += `## 🌟 ネイタルチャート（出生図）\n\n### 天体の配置\n`;
    for (const [k, pd] of Object.entries(natalChart.planets)) {
        if (pd.error) continue;
        const r = pd.retrograde ? ' ℞（逆行）' : '';
        p += `- **${PLANETS_JP[k] || k}**: ${pd.signJP} ${formatDeg(pd.degree)}${r} [第${pd.house}ハウス]\n`;
    }
    const h = natalChart.houses;
    p += `\n### アングル（重要な感受点）\n`;
    p += `- **ASC（アセンダント）**: ${h.ascendant.signJP} ${formatDeg(h.ascendant.degree)}\n`;
    p += `- **MC（天頂）**: ${h.midheaven.signJP} ${formatDeg(h.midheaven.degree)}\n`;
    p += `\n### ハウスシステム（Placidus式）\n`;
    h.cusps.forEach((cusp, i) => {
        p += `- 第${i + 1}ハウス: ${SIGNS_JP[Math.floor(cusp / 30)]} ${formatDeg(cusp % 30)}\n`;
    });
    if (progressions && progressions.p_sun) {
        p += `\n## 📈 プログレス（セカンダリー進行図）\n- 基準日: ${new Date().toISOString().split('T')[0]}\n`;
        p += `- **プログレス太陽**: ${progressions.p_sun.signJP} ${formatDeg(progressions.p_sun.degree)}\n`;
        p += `- **プログレス月**: ${progressions.p_moon.signJP} ${formatDeg(progressions.p_moon.degree)}\n\n`;
    }
    if (transits && transits.jupiter_transits) {
        p += `## 🔮 トランジット（今後3年間の主要移動）\n\n### 木星のサイン移動\n`;
        transits.jupiter_transits.forEach((t) => { p += `- ${t.date}: ${t.signJP}入り\n`; });
        p += `\n### 土星のサイン移動\n`;
        transits.saturn_transits.forEach((t) => { p += `- ${t.date}: ${t.signJP}入り\n`; });
        if (transits.outer_planets) {
            const o = transits.outer_planets;
            p += `\n### 外惑星の現在位置\n`;
            if (o.Uranus) p += `- **天王星**: ${o.Uranus.signJP} ${formatDeg(o.Uranus.degree)}${o.Uranus.retrograde ? ' ℞' : ''}\n`;
            if (o.Neptune) p += `- **海王星**: ${o.Neptune.signJP} ${formatDeg(o.Neptune.degree)}${o.Neptune.retrograde ? ' ℞' : ''}\n`;
            if (o.Pluto) p += `- **冥王星**: ${o.Pluto.signJP} ${formatDeg(o.Pluto.degree)}${o.Pluto.retrograde ? ' ℞' : ''}\n`;
        }
    }
    p += `\n---\n**生成日時**: ${new Date().toLocaleString('ja-JP')}\n`;
    return p;
}

async function copyPrompt() {
    try {
        await navigator.clipboard.writeText(lastPrompt);
        flashCopied();
    } catch (e) {
        const ta = document.getElementById('promptPreview');
        ta.style.display = 'block'; ta.select();
        document.execCommand('copy');
        flashCopied();
    }
}
function flashCopied() {
    const s = document.getElementById('copyStatus');
    s.textContent = '✓ コピーしました';
    setTimeout(() => { s.textContent = ''; }, 2500);
}
async function openGem() {
    await copyPrompt();
    document.getElementById('gemSteps').style.display = 'block';
    window.open(GEM_URL, '_blank', 'noopener');
}
