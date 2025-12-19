// 占星術プロンプト・ジェネレーター（都道府県選択式）

// === グローバル変数 ===
let sabianSymbols = [];
const API_BASE_URL = window.location.origin;

// === 都道府県座標データ ===
const PREFECTURES = {
    '北海道': { lat: 43.0642, lon: 141.3469 },
    '青森県': { lat: 40.8244, lon: 140.7400 },
    '岩手県': { lat: 39.7036, lon: 141.1527 },
    '宮城県': { lat: 38.2682, lon: 140.8721 },
    '秋田県': { lat: 39.7186, lon: 140.1022 },
    '山形県': { lat: 38.2404, lon: 140.3633 },
    '福島県': { lat: 37.7503, lon: 140.4677 },
    '茨城県': { lat: 36.3418, lon: 140.4468 },
    '栃木県': { lat: 36.5658, lon: 139.8836 },
    '群馬県': { lat: 36.3906, lon: 139.0608 },
    '埼玉県': { lat: 35.8617, lon: 139.6455 },
    '千葉県': { lat: 35.6074, lon: 140.1065 },
    '東京都': { lat: 35.6762, lon: 139.6503 },
    '神奈川県': { lat: 35.4478, lon: 139.6425 },
    '新潟県': { lat: 37.9026, lon: 139.0232 },
    '富山県': { lat: 36.6959, lon: 137.2137 },
    '石川県': { lat: 36.5946, lon: 136.6256 },
    '福井県': { lat: 36.0652, lon: 136.2216 },
    '山梨県': { lat: 35.6642, lon: 138.5681 },
    '長野県': { lat: 36.6513, lon: 138.1809 },
    '岐阜県': { lat: 35.3912, lon: 136.7223 },
    '静岡県': { lat: 34.9756, lon: 138.3827 },
    '愛知県': { lat: 35.1802, lon: 136.9066 },
    '三重県': { lat: 34.7302, lon: 136.5086 },
    '滋賀県': { lat: 35.0045, lon: 135.8686 },
    '京都府': { lat: 35.0211, lon: 135.7556 },
    '大阪府': { lat: 34.6937, lon: 135.5023 },
    '兵庫県': { lat: 34.6913, lon: 135.1830 },
    '奈良県': { lat: 34.6851, lon: 135.8048 },
    '和歌山県': { lat: 34.2261, lon: 135.1675 },
    '鳥取県': { lat: 35.5038, lon: 134.2378 },
    '島根県': { lat: 35.4723, lon: 133.0505 },
    '岡山県': { lat: 34.6618, lon: 133.9346 },
    '広島県': { lat: 34.3963, lon: 132.4596 },
    '山口県': { lat: 34.1861, lon: 131.4707 },
    '徳島県': { lat: 34.0658, lon: 134.5593 },
    '香川県': { lat: 34.3401, lon: 134.0430 },
    '愛媛県': { lat: 33.8416, lon: 132.7658 },
    '高知県': { lat: 33.5597, lon: 133.5311 },
    '福岡県': { lat: 33.6064, lon: 130.4181 },
    '佐賀県': { lat: 33.2494, lon: 130.2989 },
    '長崎県': { lat: 32.7503, lon: 129.8779 },
    '熊本県': { lat: 32.7898, lon: 130.7417 },
    '大分県': { lat: 33.2382, lon: 131.6126 },
    '宮崎県': { lat: 31.9077, lon: 131.4202 },
    '鹿児島県': { lat: 31.5602, lon: 130.5581 },
    '沖縄県': { lat: 26.2124, lon: 127.6792 }
};

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

// === 初期化 ===
document.addEventListener('DOMContentLoaded', async () => {
    // サビアンシンボルデータの読み込み
    try {
        const response = await fetch('sabian_symbols_360.json');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        
        if (Array.isArray(data)) {
            sabianSymbols = data;
        } else {
            console.warn('⚠️ Sabian symbols is not an array, trying to extract array from object');
            sabianSymbols = [];
        }
        
        console.log('✅ Sabian symbols loaded:', sabianSymbols.length, 'symbols');
    } catch (error) {
        console.error('❌ Failed to load Sabian symbols:', error);
        sabianSymbols = [];
    }

    // イベントリスナー設定
    document.getElementById('timeUnknown').addEventListener('change', handleTimeUnknown);
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

async function generatePrompt() {
    // 入力値の検証
    const name = document.getElementById('name').value;
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

    // 都道府県から緯度経度を取得
    const location = PREFECTURES[prefecture];
    if (!location) {
        alert('都道府県の座標データが見つかりません');
        return;
    }

    const button = document.getElementById('generateBtn');
    const loading = document.getElementById('loading');
    
    button.disabled = true;
    button.textContent = '⏳ 計算中...';
    loading.style.display = 'block';

    try {
        console.log(`📍 計算開始: ${prefecture} (緯度: ${location.lat}, 経度: ${location.lon})`);
        
        // Backend APIを呼び出し
        const natalChart = await calculateNatalChart(
            year, month, day, hour, minute, 
            location.lat, location.lon
        );
        
        const progressions = await calculateProgressions(year, month, day, hour, minute);
        const transits = await calculateTransits();

        // プロンプト生成
        const prompt = buildPromptText(
            name, year, month, day, hour, minute, 
            prefecture, natalChart, progressions, transits
        );

        // 結果表示
        document.getElementById('outputText').textContent = prompt;
        document.getElementById('outputSection').style.display = 'block';
        loading.style.display = 'none';
        document.getElementById('outputSection').scrollIntoView({ behavior: 'smooth' });

        console.log('✅ プロンプト生成完了');

    } catch (error) {
        console.error('❌ エラー発生:', error);
        alert(`エラーが発生しました: ${error.message}`);
        loading.style.display = 'none';
    } finally {
        button.disabled = false;
        button.textContent = '🚀 プロンプト生成';
    }
}

// === Backend API呼び出し ===
async function calculateNatalChart(year, month, day, hour, minute, latitude, longitude) {
    console.log('📡 ネイタルチャート計算API呼び出し...');
    
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

    console.log('✅ ネイタルチャート計算成功');
    return data;
}

async function calculateProgressions(birthYear, birthMonth, birthDay, birthHour, birthMinute) {
    console.log('📡 プログレス計算API呼び出し...');
    
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
            birth_hour: birthHour,
            birth_minute: birthMinute,
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

    console.log('✅ プログレス計算成功');
    return data;
}

async function calculateTransits() {
    console.log('📡 トランジット計算API呼び出し...');
    
    const currentDate = new Date().toISOString().split('T')[0];
    
    const response = await fetch(`${API_BASE_URL}/api/calculate-transits`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            start_date: currentDate,
            years: 3
        })
    });

    if (!response.ok) {
        throw new Error(`Transits API error: ${response.status}`);
    }

    const data = await response.json();
    if (!data.success) {
        throw new Error(data.error || 'Transits calculation failed');
    }

    console.log('✅ トランジット計算成功');
    return data;
}

// === プロンプトテキスト生成 ===
function buildPromptText(name, year, month, day, hour, minute, prefecture, natalChart, progressions, transits) {
    let prompt = `# 【完全版】${name}さんの占星術データ\n\n`;
    prompt += `## 基本情報\n`;
    prompt += `- 生年月日: ${year}年${month}月${day}日 ${hour}時${minute}分\n`;
    prompt += `- 出生地: ${prefecture}\n\n`;

    // ネイタルチャート
    prompt += `## 🌟 ネイタルチャート（出生図）\n\n`;
    prompt += `### 天体の配置\n`;
    
    const planets = natalChart.planets;
    for (const [planetKey, planetData] of Object.entries(planets)) {
        if (planetData.error) {
            prompt += `- **${PLANETS_JP[planetKey]}**: エラー - ${planetData.error}\n`;
            continue;
        }
        
        const sabianDegree = Math.ceil(planetData.degree);
        const retrograde = planetData.retrograde ? ' ℞（逆行）' : '';
        
        prompt += `- **${PLANETS_JP[planetKey]}**: ${planetData.signJP} ${planetData.degree.toFixed(2)}°${retrograde} [第${planetData.house}ハウス]\n`;
    }

    // アングル
    const houses = natalChart.houses;
    prompt += `\n### アングル（重要な感受点）\n`;
    prompt += `- **ASC（アセンダント）**: ${houses.ascendant.signJP} ${houses.ascendant.degree.toFixed(2)}°\n`;
    prompt += `- **MC（天頂）**: ${houses.midheaven.signJP} ${houses.midheaven.degree.toFixed(2)}°\n`;

    // ハウスカスプ
    prompt += `\n### ハウスシステム（Placidus式）\n`;
    houses.cusps.forEach((cusp, index) => {
        const signIndex = Math.floor(cusp / 30);
        const degree = cusp % 30;
        prompt += `- 第${index + 1}ハウス: ${SIGNS_JP[signIndex]} ${degree.toFixed(2)}°\n`;
    });

    // プログレス
    if (progressions && progressions.p_sun) {
        prompt += `\n## 📈 プログレス（セカンダリー進行図）\n`;
        prompt += `- 基準日: ${new Date().toISOString().split('T')[0]}\n`;
        prompt += `- **プログレス太陽**: ${progressions.p_sun.signJP} ${progressions.p_sun.degree.toFixed(2)}°\n`;
        prompt += `- **プログレス月**: ${progressions.p_moon.signJP} ${progressions.p_moon.degree.toFixed(2)}°\n\n`;
    }

    // トランジット
    if (transits && transits.jupiter_transits) {
        prompt += `## 🔮 トランジット（今後3年間の主要移動）\n\n`;
        
        prompt += `### 木星のサイン移動\n`;
        transits.jupiter_transits.forEach(transit => {
            prompt += `- ${transit.date}: ${transit.signJP}入り\n`;
        });
        
        prompt += `\n### 土星のサイン移動\n`;
        transits.saturn_transits.forEach(transit => {
            prompt += `- ${transit.date}: ${transit.signJP}入り\n`;
        });
        
        if (transits.outer_planets) {
            prompt += `\n### 外惑星の現在位置\n`;
            const outer = transits.outer_planets;
            if (outer.Uranus) {
                prompt += `- **天王星**: ${outer.Uranus.signJP} ${outer.Uranus.degree.toFixed(2)}°${outer.Uranus.retrograde ? ' ℞' : ''}\n`;
            }
            if (outer.Neptune) {
                prompt += `- **海王星**: ${outer.Neptune.signJP} ${outer.Neptune.degree.toFixed(2)}°${outer.Neptune.retrograde ? ' ℞' : ''}\n`;
            }
            if (outer.Pluto) {
                prompt += `- **冥王星**: ${outer.Pluto.signJP} ${outer.Pluto.degree.toFixed(2)}°${outer.Pluto.retrograde ? ' ℞' : ''}\n`;
            }
        }
    }

    prompt += `\n---\n`;
    prompt += `**生成日時**: ${new Date().toLocaleString('ja-JP')}\n`;

    return prompt;
}

function getSabianSymbol(sign, degree) {
    // サビアンシンボルを取得（度数は1-30の範囲）
    if (!Array.isArray(sabianSymbols) || sabianSymbols.length === 0) {
        return null;
    }
    
    const adjustedDegree = degree === 0 ? 30 : Math.ceil(degree);
    const symbol = sabianSymbols.find(s => s.sign === sign && s.sign_degree === adjustedDegree);
    return symbol ? `${symbol.keyword} - ${symbol.meaning}` : null;
}

// === クリップボード・ダウンロード処理 ===
async function copyToClipboard() {
    const text = document.getElementById('outputText').textContent;
    try {
        await navigator.clipboard.writeText(text);
        alert('✅ クリップボードにコピーしました！');
    } catch (error) {
        console.error('❌ Copy error:', error);
        alert('コピーに失敗しました');
    }
}

function downloadPrompt() {
    const text = document.getElementById('outputText').textContent;
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const timestamp = new Date().toISOString().split('T')[0];
    a.download = `占星術プロンプト_${timestamp}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
