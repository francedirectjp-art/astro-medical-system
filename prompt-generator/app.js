// Anti-Gravity Prompt Builder - Main Application
// Version: 1.0 MVP

// グローバル変数
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
    'Pluto': '冥王星'
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
    await loadSabianData();
    setupEventListeners();
});

// サビアンシンボルデータの読み込み
async function loadSabianData() {
    try {
        const response = await fetch('sabian_symbols_360.json');
        sabianData = await response.json();
        console.log('Sabian symbols loaded:', Object.keys(sabianData).length);
    } catch (error) {
        console.error('Error loading Sabian data:', error);
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

// 位置検索（簡易実装 - Google Maps API統合は後で追加可能）
async function searchLocation() {
    const location = document.getElementById('location').value;
    
    if (!location) {
        alert('出生地を入力してください。');
        return;
    }
    
    // Nominatim API (OpenStreetMap) を使用した無料のジオコーディング
    try {
        const response = await fetch(
            `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(location)}&format=json&limit=1`
        );
        const data = await response.json();
        
        if (data && data.length > 0) {
            const result = data[0];
            document.getElementById('latitude').value = parseFloat(result.lat).toFixed(4);
            document.getElementById('longitude').value = parseFloat(result.lon).toFixed(4);
            
            // タイムゾーンの推定（簡易版）
            const timezone = getTimezoneFromCoordinates(result.lat, result.lon);
            document.getElementById('timezone').value = timezone;
            
            document.getElementById('coordinatesRow').style.display = 'grid';
            alert('位置情報を取得しました！');
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

// 緯度経度からタイムゾーンを推定（簡易版）
function getTimezoneFromCoordinates(lat, lon) {
    // 日本の座標範囲
    if (lat > 24 && lat < 46 && lon > 122 && lon < 154) {
        return 'Asia/Tokyo';
    }
    // その他の主要タイムゾーン（簡易的）
    const offset = Math.round(lon / 15);
    return `UTC${offset >= 0 ? '+' : ''}${offset}`;
}

// メイン: プロンプト生成
async function generatePrompt() {
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
        // 1. ネイタルチャート計算
        const birthDate = new Date(Date.UTC(year, month - 1, day, hour, minute));
        const natalChart = await calculateNatalChart(birthDate, latitude, longitude);
        
        // 2. プログレス計算
        const today = new Date();
        const progressions = calculateProgressions(birthDate, today);
        
        // 3. トランジット計算（3年分）
        const transits = calculateTransits(today, latitude, longitude);
        
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
        console.error('Calculation error:', error);
        alert('計算中にエラーが発生しました: ' + error.message);
        document.getElementById('loading').style.display = 'none';
    }
}

// ネイタルチャート計算
async function calculateNatalChart(birthDate, latitude, longitude) {
    const observer = Astronomy.MakeObserver(latitude, longitude, 0);
    
    const chart = {
        planets: {},
        angles: {},
        houses: [],
        aspects: []
    };
    
    // 10天体の計算
    const planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto'];
    
    for (const planet of planets) {
        const body = Astronomy.Body[planet];
        const equator = Astronomy.Equator(body, birthDate, observer, true, true);
        const ecliptic = Astronomy.Ecliptic(equator);
        
        const longitude = ecliptic.elon;
        const signIndex = Math.floor(longitude / 30);
        const degree = longitude % 30;
        
        chart.planets[planet] = {
            sign: SIGNS[signIndex],
            signJP: SIGNS_JP[signIndex],
            degree: degree,
            absoluteLongitude: longitude,
            sabian: getSabianSymbol(longitude)
        };
    }
    
    // ASC, MC の計算（簡易版）
    const siderealTime = calculateLocalSiderealTime(birthDate, longitude);
    const mc = calculateMC(siderealTime);
    const asc = calculateASC(siderealTime, latitude);
    
    chart.angles.ASC = {
        degree: asc,
        sign: SIGNS[Math.floor(asc / 30)],
        signJP: SIGNS_JP[Math.floor(asc / 30)],
        signDegree: asc % 30,
        sabian: getSabianSymbol(asc)
    };
    
    chart.angles.MC = {
        degree: mc,
        sign: SIGNS[Math.floor(mc / 30)],
        signJP: SIGNS_JP[Math.floor(mc / 30)],
        signDegree: mc % 30,
        sabian: getSabianSymbol(mc)
    };
    
    // ハウスカスプの計算（Placidus法の簡易実装）
    chart.houses = calculateHousesPlacidus(asc, mc, latitude);
    
    // アスペクトの計算
    chart.aspects = calculateAspects(chart.planets);
    
    return chart;
}

// サビアンシンボルを取得（度数切り上げ）
function getSabianSymbol(longitude) {
    // 0-360度の範囲に正規化
    let normalized = ((longitude % 360) + 360) % 360;
    
    // サビアンシンボルは度数を切り上げ
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

// 地方恒星時の計算
function calculateLocalSiderealTime(date, longitude) {
    const jd = dateToJulianDay(date);
    const T = (jd - 2451545.0) / 36525.0;
    
    // グリニッジ平均恒星時
    let gmst = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 
               0.000387933 * T * T - T * T * T / 38710000.0;
    
    // 地方恒星時
    let lst = gmst + longitude;
    lst = ((lst % 360) + 360) % 360;
    
    return lst;
}

// ユリウス日の計算
function dateToJulianDay(date) {
    const a = Math.floor((14 - (date.getUTCMonth() + 1)) / 12);
    const y = date.getUTCFullYear() + 4800 - a;
    const m = (date.getUTCMonth() + 1) + 12 * a - 3;
    
    let jd = date.getUTCDate() + Math.floor((153 * m + 2) / 5) + 365 * y + 
             Math.floor(y / 4) - Math.floor(y / 100) + Math.floor(y / 400) - 32045;
    
    const dayFraction = (date.getUTCHours() + date.getUTCMinutes() / 60.0 + 
                        date.getUTCSeconds() / 3600.0) / 24.0;
    
    return jd + dayFraction;
}

// MC（天頂）の計算
function calculateMC(siderealTime) {
    return siderealTime;
}

// ASC（上昇点）の計算
function calculateASC(siderealTime, latitude) {
    const latRad = latitude * Math.PI / 180;
    const stRad = siderealTime * Math.PI / 180;
    
    // 簡易計算
    const asc = Math.atan2(Math.cos(stRad), -Math.sin(stRad) * Math.cos(latRad));
    let ascDeg = asc * 180 / Math.PI;
    ascDeg = ((ascDeg % 360) + 360) % 360;
    
    return ascDeg;
}

// Placidusハウスシステムの計算（簡易版）
function calculateHousesPlacidus(asc, mc, latitude) {
    const houses = [];
    
    // 1室（ASC）から12室まで
    houses[1] = asc;
    houses[10] = mc;
    houses[4] = (mc + 180) % 360; // IC
    houses[7] = (asc + 180) % 360; // DSC
    
    // 他のハウスカスプ（等分法で簡易計算）
    for (let i = 2; i <= 3; i++) {
        houses[i] = (asc + (i - 1) * 30) % 360;
    }
    for (let i = 5; i <= 6; i++) {
        houses[i] = (houses[4] + (i - 4) * 30) % 360;
    }
    for (let i = 8; i <= 9; i++) {
        houses[i] = (houses[7] + (i - 7) * 30) % 360;
    }
    for (let i = 11; i <= 12; i++) {
        houses[i] = (mc + (i - 10) * 30) % 360;
    }
    
    return houses;
}

// 天体が入るハウスを計算
function getPlanetHouse(planetLongitude, houses) {
    for (let i = 1; i <= 12; i++) {
        const currentHouse = houses[i];
        const nextHouse = houses[i === 12 ? 1 : i + 1];
        
        if (nextHouse > currentHouse) {
            if (planetLongitude >= currentHouse && planetLongitude < nextHouse) {
                return i;
            }
        } else {
            if (planetLongitude >= currentHouse || planetLongitude < nextHouse) {
                return i;
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
function calculateProgressions(birthDate, currentDate) {
    // 1日 = 1年のプログレス
    const daysSinceBirth = (currentDate - birthDate) / (1000 * 60 * 60 * 24);
    const progressDate = new Date(birthDate.getTime() + daysSinceBirth * 24 * 60 * 60 * 1000);
    
    const observer = Astronomy.MakeObserver(0, 0, 0);
    
    // P-Sun
    const pSunEq = Astronomy.Equator('Sun', progressDate, observer, true, true);
    const pSunEcl = Astronomy.Ecliptic(pSunEq);
    const pSunLon = pSunEcl.elon;
    
    // P-Moon
    const pMoonEq = Astronomy.Equator('Moon', progressDate, observer, true, true);
    const pMoonEcl = Astronomy.Ecliptic(pMoonEq);
    const pMoonLon = pMoonEcl.elon;
    
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
function calculateTransits(currentDate, latitude, longitude) {
    const observer = Astronomy.MakeObserver(latitude, longitude, 0);
    const transits = {
        jupiter: [],
        saturn: [],
        outerPlanets: {}
    };
    
    // 現在の外惑星の位置
    ['Uranus', 'Neptune', 'Pluto'].forEach(planet => {
        const body = Astronomy.Body[planet];
        const equator = Astronomy.Equator(body, currentDate, observer, true, true);
        const ecliptic = Astronomy.Ecliptic(equator);
        const longitude = ecliptic.elon;
        
        transits.outerPlanets[planet] = {
            sign: SIGNS[Math.floor(longitude / 30)],
            signJP: SIGNS_JP[Math.floor(longitude / 30)],
            degree: (longitude % 30).toFixed(2)
        };
    });
    
    // 木星と土星の3年間のサイン移動を計算
    // （簡易実装: 現在の位置から推定）
    const jupiterTransit = calculateSignTransits('Jupiter', currentDate, 3);
    const saturnTransit = calculateSignTransits('Saturn', currentDate, 3);
    
    transits.jupiter = jupiterTransit;
    transits.saturn = saturnTransit;
    
    return transits;
}

// サイン移動の計算（簡易版）
function calculateSignTransits(planetName, startDate, years) {
    const transits = [];
    const body = Astronomy.Body[planetName];
    const observer = Astronomy.MakeObserver(0, 0, 0);
    
    // 現在の位置
    let currentEq = Astronomy.Equator(body, startDate, observer, true, true);
    let currentEcl = Astronomy.Ecliptic(currentEq);
    let currentSign = Math.floor(currentEcl.elon / 30);
    
    // 月単位でチェック
    for (let month = 0; month <= years * 12; month += 1) {
        const checkDate = new Date(startDate.getTime() + month * 30 * 24 * 60 * 60 * 1000);
        const eq = Astronomy.Equator(body, checkDate, observer, true, true);
        const ecl = Astronomy.Ecliptic(eq);
        const sign = Math.floor(ecl.elon / 30);
        
        if (sign !== currentSign) {
            transits.push({
                date: checkDate.toISOString().split('T')[0],
                sign: SIGNS[sign],
                signJP: SIGNS_JP[sign]
            });
            currentSign = sign;
        }
    }
    
    return transits;
}

// プロンプトテキスト生成
function generatePromptText(data) {
    let prompt = `# 依頼: 人生経営戦略書の執筆

あなたは「人生経営戦略コンサルタント」です。
ナレッジにアップロードされた「講義テキスト」を参照し、以下の【高精度な天文データ】に基づいて、クライアントの人生戦略書を作成してください。

## 1. クライアント情報 (Client Profile)
- 名前: ${data.name}
- 生年月日: ${data.birthDate}
- 出生地: ${data.location} (Lat: ${data.latitude.toFixed(4)}, Long: ${data.longitude.toFixed(4)})

## 2. 天体スペック (Natal Chart Data)
※Astronomy Engine（Swiss Ephemeris級精度）による精密計算結果

### 【主要天体 & サビアンシンボル】
`;

    // 主要天体
    const planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto'];
    planets.forEach(planet => {
        const p = data.natalChart.planets[planet];
        const house = getPlanetHouse(p.absoluteLongitude, data.natalChart.houses);
        prompt += `- ${PLANET_NAMES[planet]}: ${p.signJP} ${p.degree.toFixed(2)}度 (House: ${house}) / サビアン: "${p.sabian.symbol}"\n`;
    });

    prompt += `
### 【アングル】
- AC (アセンダント): ${data.natalChart.angles.ASC.signJP} ${data.natalChart.angles.ASC.signDegree.toFixed(2)}度 / サビアン: "${data.natalChart.angles.ASC.sabian.symbol}"
- MC (天頂): ${data.natalChart.angles.MC.signJP} ${data.natalChart.angles.MC.signDegree.toFixed(2)}度 / サビアン: "${data.natalChart.angles.MC.sabian.symbol}"

### 【主要アスペクト】
`;

    // アスペクト（オーブの小さい順に最大10個）
    const topAspects = data.natalChart.aspects
        .sort((a, b) => parseFloat(a.orb) - parseFloat(b.orb))
        .slice(0, 10);
    
    topAspects.forEach(aspect => {
        prompt += `- ${PLANET_NAMES[aspect.planet1]} × ${PLANET_NAMES[aspect.planet2]}: ${aspect.name} (Orb: ${aspect.orb}度)\n`;
    });

    prompt += `
## 3. 現在のバイオリズム (Progressions)
※${data.today} 時点
- P-太陽: ${data.progressions.pSun.signJP} ${data.progressions.pSun.degree.toFixed(2)}度 / 人生のテーマ: "${data.progressions.pSun.sabian.symbol}"
- P-月: ${data.progressions.pMoon.signJP} ${data.progressions.pMoon.degree.toFixed(2)}度 / サビアン: "${data.progressions.pMoon.sabian.symbol}"
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
上記のデータを元に、ナレッジファイル内の構成に従って、セッション1〜6を執筆してください。
まずは「セッション1：基盤スペック」からスタートしてください。

---
生成日時: ${new Date().toLocaleString('ja-JP')}
System: Anti-Gravity Prompt Builder v1.0
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
    a.download = `astro-prompt-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
