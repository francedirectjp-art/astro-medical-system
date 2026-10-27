// Anti-Gravity Prompt Builder v3.0 - Backend API Edition
// Swiss Ephemeris Backend APIを使用した完全版

// === グローバル変数 ===
let sabianSymbols = [];
const API_BASE_URL = window.location.origin; // Same origin (Flask backend)

// === 定数定義 ===
const SIGNS_JP = ['牡羊座', '牡牛座', '双子座', '蟹座', '獅子座', '乙女座',
                 '天秤座', '蠍座', '射手座', '山羊座', '水瓶座', '魚座'];

const PLANETS_JP = {
    'Sun': '太陽',
    'Moon': '月',
    'Mercury': '水星',
    'Venus': '金星',
    'Mars': '火星',
    'Jupiter': '木星',
    'Saturn': '土星',
    'Uranus': '天王星',
    'Neptune': '海王星',
    'Pluto': '冥王星',
    'TrueNode': 'ドラゴンヘッド',
    'Chiron': 'キローン'
};

const ASPECTS_JP = {
    0: 'コンジャンクション（合）',
    60: 'セクスタイル（60度）',
    90: 'スクエア（90度）',
    120: 'トライン（120度）',
    180: 'オポジション（180度）'
};

// === 初期化 ===
document.addEventListener('DOMContentLoaded', async () => {
    // サビアンシンボルデータの読み込み
    try {
        const response = await fetch('sabian_symbols_360.json');
        sabianSymbols = await response.json();
        console.log('Sabian symbols loaded:', sabianSymbols.length);
    } catch (error) {
        console.error('Failed to load Sabian symbols:', error);
    }

    // イベントリスナー設定
    document.getElementById('timeUnknown').addEventListener('change', handleTimeUnknown);
    document.getElementById('searchLocation').addEventListener('click', searchLocation);
    document.getElementById('generateBtn').addEventListener('click', generatePrompt);
    document.getElementById('copyBtn').addEventListener('click', copyToClipboard);
    document.getElementById('downloadBtn').addEventListener('click', downloadPrompt);
});

// === UI処理 ===
function handleTimeUnknown(e) {
    const hourInput = document.getElementById('hour');
    const minuteInput = document.getElementById('minute');
    
    if (e.target.checked) {
        hourInput.value = 12;
        minuteInput.value = 0;
        hourInput.disabled = true;
        minuteInput.disabled = true;
    } else {
        hourInput.disabled = false;
        minuteInput.disabled = false;
    }
}

async function searchLocation() {
    const location = document.getElementById('location').value;
    if (!location) {
        alert('出生地を入力してください');
        return;
    }

    const button = document.getElementById('searchLocation');
    button.disabled = true;
    button.textContent = '🔍 検索中...';

    try {
        // OpenStreetMap Nominatim API使用
        const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(location)}&accept-language=ja`);
        const data = await response.json();

        if (data && data.length > 0) {
            const result = data[0];
            document.getElementById('latitude').value = parseFloat(result.lat).toFixed(4);
            document.getElementById('longitude').value = parseFloat(result.lon).toFixed(4);
            
            // タイムゾーンを推定（日本の場合はJST、それ以外は経度から推定）
            const timezone = estimateTimezone(parseFloat(result.lon));
            document.getElementById('timezone').value = timezone;
            
            alert(`位置情報が見つかりました:\n${result.display_name}\n緯度: ${result.lat}\n経度: ${result.lon}`);
        } else {
            alert('位置情報が見つかりませんでした。手動で入力してください。');
        }
    } catch (error) {
        console.error('Location search error:', error);
        alert('位置検索エラーが発生しました');
    } finally {
        button.disabled = false;
        button.textContent = '📍 位置検索';
    }
}

function estimateTimezone(longitude) {
    // 経度から簡易的にタイムゾーンを推定
    const offset = Math.round(longitude / 15);
    return offset >= 0 ? `+${offset}` : `${offset}`;
}

async function generatePrompt() {
    // 入力値の検証
    const name = document.getElementById('name').value;
    const year = parseInt(document.getElementById('year').value);
    const month = parseInt(document.getElementById('month').value);
    const day = parseInt(document.getElementById('day').value);
    const hour = parseInt(document.getElementById('hour').value);
    const minute = parseInt(document.getElementById('minute').value);
    const latitude = parseFloat(document.getElementById('latitude').value);
    const longitude = parseFloat(document.getElementById('longitude').value);
    const timezone = document.getElementById('timezone').value;

    if (!name || !year || !month || !day || isNaN(hour) || isNaN(minute) || !latitude || !longitude) {
        alert('すべての必須項目を入力してください');
        return;
    }

    const button = document.getElementById('generateBtn');
    button.disabled = true;
    button.textContent = '⏳ 計算中...';

    try {
        // Backend APIを呼び出し
        const natalChart = await calculateNatalChart(year, month, day, hour, minute, latitude, longitude);
        const progressions = await calculateProgressions(year, month, day);
        const transits = await calculateTransits();

        // プロンプト生成
        const prompt = buildPromptText(name, year, month, day, hour, minute, natalChart, progressions, transits);

        // 結果表示
        document.getElementById('outputText').textContent = prompt;
        document.getElementById('outputSection').style.display = 'block';
        document.getElementById('outputSection').scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
        console.error('Generation error:', error);
        alert(`エラーが発生しました: ${error.message}`);
    } finally {
        button.disabled = false;
        button.textContent = '🚀 プロンプト生成';
    }
}

// === Backend API呼び出し ===
async function calculateNatalChart(year, month, day, hour, minute, latitude, longitude) {
    const response = await fetch(`${API_BASE_URL}/api/calculate-chart`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            year, month, day, hour, minute, latitude, longitude
        })
    });

    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    if (!data.success) {
        throw new Error(data.error || 'Calculation failed');
    }

    return data;
}

async function calculateProgressions(birthYear, birthMonth, birthDay) {
    const currentDate = new Date().toISOString().split('T')[0];
    
    const response = await fetch(`${API_BASE_URL}/api/calculate-progressions`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            birth_year: birthYear,
            birth_month: birthMonth,
            birth_day: birthDay,
            current_date: currentDate
        })
    });

    if (!response.ok) {
        throw new Error(`Progressions API error: ${response.status}`);
    }

    const data = await response.json();
    if (!data.success) {
        throw new Error(data.error || 'Progressions calculation failed');
    }

    return data;
}

async function calculateTransits() {
    const currentDate = new Date().toISOString().split('T')[0];
    
    const response = await fetch(`${API_BASE_URL}/api/calculate-transits`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            start_date: currentDate,
            years: 3 // 3年分のトランジット予測
        })
    });

    if (!response.ok) {
        throw new Error(`Transits API error: ${response.status}`);
    }

    const data = await response.json();
    if (!data.success) {
        throw new Error(data.error || 'Transits calculation failed');
    }

    return data;
}

// === プロンプトテキスト生成 ===
function buildPromptText(name, year, month, day, hour, minute, natalChart, progressions, transits) {
    let prompt = `# 【完全版】${name}さんの占星術データ（超高精度Swiss Ephemeris版）\n\n`;
    prompt += `## 基本情報\n`;
    prompt += `- 生年月日: ${year}年${month}月${day}日 ${hour}時${minute}分\n`;
    prompt += `- 計算エンジン: ${natalChart.calculation_engine}\n`;
    prompt += `- 精度: ${natalChart.precision}\n\n`;

    // ネイタルチャート
    prompt += `## 🌟 ネイタルチャート（出生図）\n\n`;
    prompt += `### 天体の配置\n`;
    
    const planets = natalChart.planets;
    for (const [planetKey, planetData] of Object.entries(planets)) {
        if (planetData.error) {
            prompt += `- **${PLANETS_JP[planetKey]}**: エラー - ${planetData.error}\n`;
            continue;
        }
        
        const sabianDegree = Math.ceil(planetData.degree) + 1;
        const sabianSymbol = getSabianSymbol(planetData.sign, sabianDegree);
        const retrograde = planetData.retrograde ? ' (逆行)' : '';
        
        prompt += `- **${PLANETS_JP[planetKey]}**: ${planetData.signJP} ${planetData.degree.toFixed(2)}°${retrograde} (第${planetData.house}ハウス)\n`;
        prompt += `  - サビアンシンボル: ${sabianSymbol}\n`;
    }

    // アングル
    const houses = natalChart.houses;
    prompt += `\n### アングル（重要な感受点）\n`;
    prompt += `- **ASC（アセンダント）**: ${houses.ascendant.signJP} ${houses.ascendant.degree.toFixed(2)}°\n`;
    prompt += `- **MC（天頂）**: ${houses.midheaven.signJP} ${houses.midheaven.degree.toFixed(2)}°\n`;
    prompt += `- **DESC（ディセンダント）**: ${getOppositeSign(houses.ascendant.signJP)} ${(180 - houses.ascendant.degree).toFixed(2)}°\n`;
    prompt += `- **IC（天底）**: ${getOppositeSign(houses.midheaven.signJP)} ${(180 - houses.midheaven.degree).toFixed(2)}°\n`;

    // ハウスカスプ
    prompt += `\n### ハウスシステム（Placidus式）\n`;
    houses.cusps.forEach((cusp, index) => {
        const signIndex = Math.floor(cusp / 30);
        const degree = cusp % 30;
        prompt += `- 第${index + 1}ハウス: ${SIGNS_JP[signIndex]} ${degree.toFixed(2)}°\n`;
    });

    // プログレス
    if (progressions && progressions.p_sun) {
        prompt += `\n## 📈 プログレス（進行図）\n`;
        prompt += `- 現在日時: ${new Date().toISOString().split('T')[0]}\n`;
        prompt += `- **プログレス太陽**: ${progressions.p_sun.signJP} ${progressions.p_sun.degree.toFixed(2)}°\n`;
        prompt += `- **プログレス月**: ${progressions.p_moon.signJP} ${progressions.p_moon.degree.toFixed(2)}°\n`;
        prompt += `- **月相**: ${progressions.lunar_phase}\n\n`;
    }

    // トランジット
    if (transits && transits.jupiter_ingresses) {
        prompt += `## 🔮 トランジット（経過）\n`;
        prompt += `### 木星イングレス（3年間）\n`;
        transits.jupiter_ingresses.forEach(ing => {
            prompt += `- ${ing.date}: ${ing.sign_jp}入り\n`;
        });
        
        prompt += `\n### 土星イングレス（3年間）\n`;
        transits.saturn_ingresses.forEach(ing => {
            prompt += `- ${ing.date}: ${ing.sign_jp}入り\n`;
        });
    }

    prompt += `\n---\n`;
    prompt += `**生成日時**: ${new Date().toLocaleString('ja-JP')}\n`;
    prompt += `**ツール**: Anti-Gravity Prompt Builder v3.0 (Swiss Ephemeris Backend)\n`;

    return prompt;
}

function getSabianSymbol(sign, degree) {
    // サビアンシンボルを取得
    const symbol = sabianSymbols.find(s => s.sign === sign && s.sign_degree === degree);
    return symbol ? `${symbol.keyword} - ${symbol.meaning}` : '情報なし';
}

function getOppositeSign(signJP) {
    const index = SIGNS_JP.indexOf(signJP);
    return SIGNS_JP[(index + 6) % 12];
}

// === クリップボード・ダウンロード処理 ===
async function copyToClipboard() {
    const text = document.getElementById('outputText').textContent;
    try {
        await navigator.clipboard.writeText(text);
        alert('クリップボードにコピーしました！');
    } catch (error) {
        console.error('Copy error:', error);
        alert('コピーに失敗しました');
    }
}

function downloadPrompt() {
    const text = document.getElementById('outputText').textContent;
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `astrology_prompt_${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
