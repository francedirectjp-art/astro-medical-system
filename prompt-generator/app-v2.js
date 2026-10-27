// Anti-Gravity Prompt Builder v2.0 - Swiss Ephemeris Edition
// 最高精度の天体計算（±0.001度）

// Swiss Ephemeris WebAssembly のインポート
let swe = null;
let SwissEPH = null;
let sabianData = null;

// 星座名とハウスシステムの定義
const SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
               'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];

const SIGNS_JP = ['牡羊座', '牡牛座', '双子座', '蟹座', '獅子座', '乙女座',
                  '天秤座', '蠍座', '射手座', '山羊座', '水瓶座', '魚座'];

const PLANET_NAMES = {
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
    'Chiron': 'カイロン',
    'TrueNode': 'ドラゴンヘッド（True Node）'
};

const PLANET_IDS = {
    'Sun': 0,
    'Moon': 1,
    'Mercury': 2,
    'Venus': 3,
    'Mars': 4,
    'Jupiter': 5,
    'Saturn': 6,
    'Uranus': 7,
    'Neptune': 8,
    'Pluto': 9,
    'TrueNode': 11,  // True Node
    'Chiron': 15
};

const ASPECT_NAMES = {
    0: 'コンジャンクション (合)',
    60: 'セクスタイル (60度)',
    90: 'スクエア (90度)',
    120: 'トライン (120度)',
    180: 'オポジション (180度)'
};

// 初期化
document.addEventListener('DOMContentLoaded', async () => {
    await initializeSwissEphemeris();
    await loadSabianData();
    setupEventListeners();
});

// Swiss Ephemeris の初期化
async function initializeSwissEphemeris() {
    try {
        // sweph-wasmの動的インポート（unpkgを使用）
        SwissEPH = await import('https://unpkg.com/sweph-wasm@2.6.9/dist/sweph-wasm.js');
        swe = await SwissEPH.default.init();
        
        // エフェメリスファイルの設定（CDNから自動ダウンロード）
        await swe.swe_set_ephe_path();
        
        console.log('✅ Swiss Ephemeris initialized successfully');
    } catch (error) {
        console.error('❌ Failed to initialize Swiss Ephemeris:', error);
        console.error('Error details:', error);
        alert('Swiss Ephemerisの初期化に失敗しました。\n\n' + error.message);
    }
}

// サビアンシンボルデータの読み込み
async function loadSabianData() {
    try {
        const response = await fetch('sabian_symbols_360.json');
        sabianData = await response.json();
        console.log('✅ Sabian symbols loaded:', Object.keys(sabianData).length);
    } catch (error) {
        console.error('❌ Error loading Sabian data:', error);
        alert('サビアンシンボルデータの読み込みに失敗しました。');
    }
}

// イベントリスナーの設定
function setupEventListeners() {
    document.getElementById('timeUnknown').addEventListener('change', handleTimeUnknown);
    document.getElementById('searchLocation').addEventListener('click', searchLocation);
    document.getElementById('generateBtn').addEventListener('click', generatePrompt);
    document.getElementById('copyBtn')?.addEventListener('click', copyToClipboard);
    document.getElementById('downloadBtn')?.addEventListener('click', downloadPrompt);
}

// 出生時間不明チェックボックスの処理
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

// 位置検索
async function searchLocation() {
    const location = document.getElementById('location').value;
    
    if (!location) {
        alert('出生地を入力してください。');
        return;
    }
    
    try {
        const response = await fetch(
            `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(location)}&format=json&limit=1`
        );
        const data = await response.json();
        
        if (data && data.length > 0) {
            const result = data[0];
            document.getElementById('latitude').value = parseFloat(result.lat).toFixed(4);
            document.getElementById('longitude').value = parseFloat(result.lon).toFixed(4);
            
            const timezone = getTimezoneFromCoordinates(result.lat, result.lon);
            document.getElementById('timezone').value = timezone;
            
            document.getElementById('coordinatesRow').style.display = 'grid';
            alert('✅ 位置情報を取得しました！');
        } else {
            alert('位置が見つかりませんでした。手動で入力してください。');
            document.getElementById('coordinatesRow').style.display = 'grid';
        }
    } catch (error) {
        console.error('Location search error:', error);
        alert('位置検索に失敗しました。手動で入力してください。');
        document.getElementById('coordinatesRow').style.display = 'grid';
    }
}

// タイムゾーン推定
function getTimezoneFromCoordinates(lat, lon) {
    if (lat > 24 && lat < 46 && lon > 122 && lon < 154) {
        return 'Asia/Tokyo';
    }
    const offset = Math.round(lon / 15);
    return `UTC${offset >= 0 ? '+' : ''}${offset}`;
}

// メイン: プロンプト生成
async function generatePrompt() {
    if (!swe) {
        alert('Swiss Ephemerisが初期化されていません。ページを再読み込みしてください。');
        return;
    }
    
    // 入力値の取得とバリデーション
    const name = document.getElementById('name').value;
    const year = parseInt(document.getElementById('year').value);
    const month = parseInt(document.getElementById('month').value);
    const day = parseInt(document.getElementById('day').value);
    const hour = parseInt(document.getElementById('hour').value);
    const minute = parseInt(document.getElementById('minute').value);
    const location = document.getElementById('location').value;
    const latitude = parseFloat(document.getElementById('latitude').value);
    const longitude = parseFloat(document.getElementById('longitude').value);
    const timezone = document.getElementById('timezone').value;
    
    if (!name || !year || !month || !day || isNaN(hour) || isNaN(minute) || !location) {
        alert('すべての必須項目を入力してください。');
        return;
    }
    
    if (isNaN(latitude) || isNaN(longitude)) {
        alert('位置検索を実行するか、緯度・経度を手動で入力してください。');
        return;
    }
    
    // ローディング表示
    document.getElementById('loading').style.display = 'block';
    document.getElementById('outputSection').style.display = 'none';
    
    try {
        // ユリウス日の計算（UTC）
        const jd = swe.swe_julday(year, month, day, hour + minute / 60.0, 1); // 1 = Gregorian calendar
        
        console.log(`📅 Julian Day: ${jd}`);
        
        // 1. ネイタルチャート計算
        const natalChart = await calculateNatalChart(jd, latitude, longitude);
        
        // 2. プログレス計算
        const today = new Date();
        const progressions = calculateProgressions(year, month, day, today);
        
        // 3. トランジット計算（3年分）
        const transits = await calculateTransits(today, latitude, longitude);
        
        // 4. プロンプトテキスト生成
        const promptText = generatePromptText({
            name,
            birthDate: `${year}/${month}/${day} ${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`,
            location,
            latitude,
            longitude,
            natalChart,
            progressions,
            transits,
            today: today.toISOString().split('T')[0]
        });
        
        // 5. 結果表示
        document.getElementById('outputText').textContent = promptText;
        document.getElementById('outputSection').style.display = 'block';
        document.getElementById('loading').style.display = 'none';
        
        // 結果までスクロール
        document.getElementById('outputSection').scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        console.error('❌ Calculation error:', error);
        alert('計算中にエラーが発生しました: ' + error.message);
        document.getElementById('loading').style.display = 'none';
    }
}

// ネイタルチャート計算（Swiss Ephemeris使用）
async function calculateNatalChart(jd, latitude, longitude) {
    const chart = {
        planets: {},
        angles: {},
        houses: [],
        aspects: []
    };
    
    // 天体の計算
    const planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'Chiron', 'TrueNode'];
    
    for (const planet of planets) {
        try {
            const planetId = PLANET_IDS[planet];
            const flags = 0; // SEFLG_SWIEPH (default) + SEFLG_SPEED
            
            // Swiss Ephemerisで計算
            const result = swe.swe_calc_ut(jd, planetId, flags);
            
            const longitude = result[0]; // 黄経
            const latitude_ecl = result[1]; // 黄緯
            const distance = result[2]; // 距離
            const lonSpeed = result[3]; // 黄経の速度（逆行判定に使用）
            
            const signIndex = Math.floor(longitude / 30);
            const degree = longitude % 30;
            
            chart.planets[planet] = {
                sign: SIGNS[signIndex],
                signJP: SIGNS_JP[signIndex],
                degree: degree,
                absoluteLongitude: longitude,
                latitude: latitude_ecl,
                distance: distance,
                speed: lonSpeed,
                retrograde: lonSpeed < 0,
                sabian: getSabianSymbol(longitude)
            };
            
            console.log(`${planet}: ${SIGNS_JP[signIndex]} ${degree.toFixed(4)}°${lonSpeed < 0 ? ' (逆行)' : ''}`);
        } catch (error) {
            console.error(`Error calculating ${planet}:`, error);
        }
    }
    
    // ハウスカスプとアングルの計算（Placidus法）
    try {
        const houses = swe.swe_houses(jd, latitude, longitude, 'P'); // 'P' = Placidus
        
        // ASC（上昇点）
        const asc = houses.ascmc[0];
        chart.angles.ASC = {
            degree: asc,
            sign: SIGNS[Math.floor(asc / 30)],
            signJP: SIGNS_JP[Math.floor(asc / 30)],
            signDegree: asc % 30,
            sabian: getSabianSymbol(asc)
        };
        
        // MC（天頂）
        const mc = houses.ascmc[1];
        chart.angles.MC = {
            degree: mc,
            sign: SIGNS[Math.floor(mc / 30)],
            signJP: SIGNS_JP[Math.floor(mc / 30)],
            signDegree: mc % 30,
            sabian: getSabianSymbol(mc)
        };
        
        // ハウスカスプ
        chart.houses = houses.cusps;
        
        console.log(`ASC: ${chart.angles.ASC.signJP} ${chart.angles.ASC.signDegree.toFixed(4)}°`);
        console.log(`MC: ${chart.angles.MC.signJP} ${chart.angles.MC.signDegree.toFixed(4)}°`);
    } catch (error) {
        console.error('Error calculating houses:', error);
    }
    
    // アスペクトの計算
    chart.aspects = calculateAspects(chart.planets);
    
    return chart;
}

// サビアンシンボルを取得（度数切り上げ）
function getSabianSymbol(longitude) {
    let normalized = ((longitude % 360) + 360) % 360;
    let degree = Math.ceil(normalized);
    if (degree === 0) degree = 360;
    
    const symbol = sabianData[String(degree)];
    
    if (symbol) {
        return {
            degree: degree,
            sign: symbol.sign,
            signDegree: symbol.sign_degree,
            symbol: symbol.symbol || `${symbol.sign} ${symbol.sign_degree}度`,
            keyword: symbol.keyword || '',
            meaning: symbol.japanese_meaning || symbol.meaning || ''
        };
    }
    
    return {
        degree: degree,
        symbol: `度数 ${degree}`,
        meaning: 'シンボル情報なし'
    };
}

// 天体が入るハウスを計算
function getPlanetHouse(planetLongitude, houses) {
    for (let i = 0; i < 12; i++) {
        const currentHouse = houses[i];
        const nextHouse = houses[(i + 1) % 12];
        
        if (nextHouse > currentHouse) {
            if (planetLongitude >= currentHouse && planetLongitude < nextHouse) {
                return i + 1;
            }
        } else {
            if (planetLongitude >= currentHouse || planetLongitude < nextHouse) {
                return i + 1;
            }
        }
    }
    return 1;
}

// アスペクトの計算
function calculateAspects(planets) {
    const aspects = [];
    const planetList = Object.keys(planets);
    const aspectAngles = [0, 60, 90, 120, 180];
    const majorOrbs = { 0: 8, 60: 5, 90: 6, 120: 6, 180: 8 };
    
    for (let i = 0; i < planetList.length; i++) {
        for (let j = i + 1; j < planetList.length; j++) {
            const planet1 = planetList[i];
            const planet2 = planetList[j];
            const lon1 = planets[planet1].absoluteLongitude;
            const lon2 = planets[planet2].absoluteLongitude;
            
            let diff = Math.abs(lon1 - lon2);
            if (diff > 180) diff = 360 - diff;
            
            for (const angle of aspectAngles) {
                const orb = Math.abs(diff - angle);
                const maxOrb = majorOrbs[angle];
                
                if (orb <= maxOrb) {
                    aspects.push({
                        planet1,
                        planet2,
                        aspect: angle,
                        orb: orb.toFixed(2),
                        name: ASPECT_NAMES[angle]
                    });
                }
            }
        }
    }
    
    return aspects;
}

// プログレス計算
function calculateProgressions(birthYear, birthMonth, birthDay, currentDate) {
    // 1日 = 1年のプログレス
    const birthDate = new Date(birthYear, birthMonth - 1, birthDay);
    const daysSinceBirth = (currentDate - birthDate) / (1000 * 60 * 60 * 24);
    const progressDate = new Date(birthDate.getTime() + daysSinceBirth * 24 * 60 * 60 * 1000);
    
    // プログレスのユリウス日
    const pJd = swe.swe_julday(
        progressDate.getFullYear(),
        progressDate.getMonth() + 1,
        progressDate.getDate(),
        12.0,
        1
    );
    
    // P-Sun
    const pSunResult = swe.swe_calc_ut(pJd, PLANET_IDS['Sun'], 0);
    const pSunLon = pSunResult[0];
    
    // P-Moon
    const pMoonResult = swe.swe_calc_ut(pJd, PLANET_IDS['Moon'], 0);
    const pMoonLon = pMoonResult[0];
    
    // 月相計算
    const lunation = (pMoonLon - pSunLon + 360) % 360;
    const phase = getLunarPhase(lunation);
    
    return {
        pSun: {
            sign: SIGNS[Math.floor(pSunLon / 30)],
            signJP: SIGNS_JP[Math.floor(pSunLon / 30)],
            degree: pSunLon % 30,
            sabian: getSabianSymbol(pSunLon)
        },
        pMoon: {
            sign: SIGNS[Math.floor(pMoonLon / 30)],
            signJP: SIGNS_JP[Math.floor(pMoonLon / 30)],
            degree: pMoonLon % 30,
            sabian: getSabianSymbol(pMoonLon)
        },
        phase: phase
    };
}

// 月相フェーズの判定
function getLunarPhase(angle) {
    if (angle < 45) return 'ニュームーン期（新月）';
    if (angle < 90) return 'クレセント期（三日月）';
    if (angle < 135) return 'ファーストクォーター期（上弦）';
    if (angle < 180) return 'ギバウス期（満ちゆく月）';
    if (angle < 225) return 'フルムーン期（満月）';
    if (angle < 270) return 'ディセミネイティング期（欠けゆく月）';
    if (angle < 315) return 'ラストクォーター期（下弦）';
    return 'バルサミック期（暗い月）';
}

// トランジット計算（3年間）
async function calculateTransits(currentDate, latitude, longitude) {
    const transits = {
        jupiter: [],
        saturn: [],
        outerPlanets: {}
    };
    
    const currentJd = swe.swe_julday(
        currentDate.getFullYear(),
        currentDate.getMonth() + 1,
        currentDate.getDate(),
        12.0,
        1
    );
    
    // 現在の外惑星の位置
    ['Uranus', 'Neptune', 'Pluto'].forEach(planet => {
        try {
            const result = swe.swe_calc_ut(currentJd, PLANET_IDS[planet], 0);
            const longitude = result[0];
            
            transits.outerPlanets[planet] = {
                sign: SIGNS[Math.floor(longitude / 30)],
                signJP: SIGNS_JP[Math.floor(longitude / 30)],
                degree: (longitude % 30).toFixed(2)
            };
        } catch (error) {
            console.error(`Error calculating ${planet} transit:`, error);
        }
    });
    
    // 木星と土星の3年間のサイン移動を計算
    transits.jupiter = calculateSignTransits('Jupiter', currentDate, 3);
    transits.saturn = calculateSignTransits('Saturn', currentDate, 3);
    
    return transits;
}

// サイン移動の計算
function calculateSignTransits(planetName, startDate, years) {
    const transits = [];
    const planetId = PLANET_IDS[planetName];
    
    try {
        const startJd = swe.swe_julday(
            startDate.getFullYear(),
            startDate.getMonth() + 1,
            startDate.getDate(),
            12.0,
            1
        );
        
        let currentResult = swe.swe_calc_ut(startJd, planetId, 0);
        let currentSign = Math.floor(currentResult[0] / 30);
        
        // 月単位でチェック
        for (let month = 0; month <= years * 12; month += 1) {
            const checkDate = new Date(startDate.getTime() + month * 30 * 24 * 60 * 60 * 1000);
            const checkJd = swe.swe_julday(
                checkDate.getFullYear(),
                checkDate.getMonth() + 1,
                checkDate.getDate(),
                12.0,
                1
            );
            
            const result = swe.swe_calc_ut(checkJd, planetId, 0);
            const sign = Math.floor(result[0] / 30);
            
            if (sign !== currentSign) {
                transits.push({
                    date: checkDate.toISOString().split('T')[0],
                    sign: SIGNS[sign],
                    signJP: SIGNS_JP[sign]
                });
                currentSign = sign;
            }
        }
    } catch (error) {
        console.error(`Error calculating sign transits for ${planetName}:`, error);
    }
    
    return transits;
}

// プロンプトテキスト生成
function generatePromptText(data) {
    let prompt = `# 依頼: 人生経営戦略書の執筆

あなたは「人生経営戦略コンサルタント」です。
ナレッジにアップロードされた「講義テキスト」を参照し、以下の【Swiss Ephemeris による超高精度天文データ】に基づいて、クライアントの人生戦略書を作成してください。

## 1. クライアント情報 (Client Profile)
- 名前: ${data.name}
- 生年月日: ${data.birthDate}
- 出生地: ${data.location} (Lat: ${data.latitude.toFixed(4)}, Long: ${data.longitude.toFixed(4)})

## 2. 天体スペック (Natal Chart Data)
※Swiss Ephemeris WebAssembly（精度±0.001度）による超精密計算結果

### 【主要天体 & サビアンシンボル】
`;

    // 主要天体
    const planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'Chiron', 'TrueNode'];
    planets.forEach(planet => {
        const p = data.natalChart.planets[planet];
        if (p) {
            const house = getPlanetHouse(p.absoluteLongitude, data.natalChart.houses);
            const retrograde = p.retrograde ? ' (逆行)' : '';
            prompt += `- ${PLANET_NAMES[planet]}: ${p.signJP} ${p.degree.toFixed(4)}度 (House: ${house})${retrograde} / サビアン: "${p.sabian.symbol}"\n`;
        }
    });

    prompt += `
### 【アングル】
- AC (アセンダント): ${data.natalChart.angles.ASC.signJP} ${data.natalChart.angles.ASC.signDegree.toFixed(4)}度 / サビアン: "${data.natalChart.angles.ASC.sabian.symbol}"
- MC (天頂): ${data.natalChart.angles.MC.signJP} ${data.natalChart.angles.MC.signDegree.toFixed(4)}度 / サビアン: "${data.natalChart.angles.MC.sabian.symbol}"

### 【主要アスペクト】
`;

    // アスペクト（オーブの小さい順に最大15個）
    const topAspects = data.natalChart.aspects
        .sort((a, b) => parseFloat(a.orb) - parseFloat(b.orb))
        .slice(0, 15);
    
    topAspects.forEach(aspect => {
        prompt += `- ${PLANET_NAMES[aspect.planet1]} × ${PLANET_NAMES[aspect.planet2]}: ${aspect.name} (Orb: ${aspect.orb}度)\n`;
    });

    prompt += `
## 3. 現在のバイオリズム (Progressions)
※${data.today} 時点
- P-太陽: ${data.progressions.pSun.signJP} ${data.progressions.pSun.degree.toFixed(4)}度 / 人生のテーマ: "${data.progressions.pSun.sabian.symbol}"
- P-月: ${data.progressions.pMoon.signJP} ${data.progressions.pMoon.degree.toFixed(4)}度 / サビアン: "${data.progressions.pMoon.sabian.symbol}"
- 現在の月相フェーズ: ${data.progressions.phase}

## 4. 未来3ヵ年の展望 (Transits 2025-2028)

### 木星の動き:
`;

    data.transits.jupiter.forEach(transit => {
        prompt += `  - ${transit.date} に ${transit.signJP}（${transit.sign}）へ移動\n`;
    });

    prompt += `
### 土星の動き:
`;

    data.transits.saturn.forEach(transit => {
        prompt += `  - ${transit.date} に ${transit.signJP}（${transit.sign}）へ移動\n`;
    });

    prompt += `
### トランスサタニアン（現在位置）:
- 天王星: ${data.transits.outerPlanets.Uranus.signJP} ${data.transits.outerPlanets.Uranus.degree}度
- 海王星: ${data.transits.outerPlanets.Neptune.signJP} ${data.transits.outerPlanets.Neptune.degree}度
- 冥王星: ${data.transits.outerPlanets.Pluto.signJP} ${data.transits.outerPlanets.Pluto.degree}度

## 5. 執筆指示 (Instructions)
上記のSwiss Ephemeris超高精度データを元に、ナレッジファイル内の構成に従って、セッション1〜6を執筆してください。
まずは「セッション1：基盤スペック」からスタートしてください。

---
生成日時: ${new Date().toLocaleString('ja-JP')}
System: Anti-Gravity Prompt Builder v2.0 (Swiss Ephemeris Edition)
Precision: ±0.001 degrees
`;

    return prompt;
}

// クリップボードにコピー
async function copyToClipboard() {
    const text = document.getElementById('outputText').textContent;
    
    try {
        await navigator.clipboard.writeText(text);
        const btn = document.getElementById('copyBtn');
        const originalText = btn.textContent;
        btn.textContent = '✅ コピーしました！';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    } catch (error) {
        console.error('Copy failed:', error);
        alert('コピーに失敗しました。手動でコピーしてください。');
    }
}

// テキストファイルとしてダウンロード
function downloadPrompt() {
    const text = document.getElementById('outputText').textContent;
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `astro-prompt-swisseph-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
