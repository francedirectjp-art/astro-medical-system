// 簡易天体計算ライブラリ
// VSOP87理論に基づく近似計算

class Ephemeris {
    // ユリウス日の計算
    static julianDay(date) {
        const year = date.getUTCFullYear();
        const month = date.getUTCMonth() + 1;
        const day = date.getUTCDate();
        const hour = date.getUTCHours();
        const minute = date.getUTCMinutes();
        const second = date.getUTCSeconds();
        
        let a = Math.floor((14 - month) / 12);
        let y = year + 4800 - a;
        let m = month + 12 * a - 3;
        
        let jdn = day + Math.floor((153 * m + 2) / 5) + 365 * y + 
                  Math.floor(y / 4) - Math.floor(y / 100) + Math.floor(y / 400) - 32045;
        
        let dayFraction = (hour - 12) / 24 + minute / 1440 + second / 86400;
        
        return jdn + dayFraction;
    }
    
    // ユリウス世紀数
    static julianCentury(jd) {
        return (jd - 2451545.0) / 36525.0;
    }
    
    // 角度を0-360に正規化
    static normalize(angle) {
        angle = angle % 360;
        if (angle < 0) angle += 360;
        return angle;
    }
    
    // 太陽の黄経（簡易計算）
    static sunLongitude(date) {
        const jd = this.julianDay(date);
        const T = this.julianCentury(jd);
        
        // 平均黄経
        const L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T;
        
        // 平均近点角
        const M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T;
        const Mrad = M * Math.PI / 180;
        
        // 中心差
        const C = (1.914602 - 0.004817 * T - 0.000014 * T * T) * Math.sin(Mrad) +
                  (0.019993 - 0.000101 * T) * Math.sin(2 * Mrad) +
                  0.000289 * Math.sin(3 * Mrad);
        
        // 真黄経
        const lambda = this.normalize(L0 + C);
        
        return lambda;
    }
    
    // 月の黄経（簡易計算）
    static moonLongitude(date) {
        const jd = this.julianDay(date);
        const T = this.julianCentury(jd);
        
        // 月の平均黄経
        const L = 218.3164477 + 481267.88123421 * T - 
                  0.0015786 * T * T + T * T * T / 538841 - T * T * T * T / 65194000;
        
        // 平均近点角
        const D = 297.8501921 + 445267.1114034 * T - 
                  0.0018819 * T * T + T * T * T / 545868 - T * T * T * T / 113065000;
        
        // 太陽の平均近点角
        const M = 357.5291092 + 35999.0502909 * T - 
                  0.0001536 * T * T + T * T * T / 24490000;
        
        // 月の平均近点角
        const Mprime = 134.9633964 + 477198.8675055 * T + 
                       0.0087414 * T * T + T * T * T / 69699 - T * T * T * T / 14712000;
        
        // 昇交点の平均黄経
        const F = 93.2720950 + 483202.0175233 * T - 
                  0.0036539 * T * T - T * T * T / 3526000 + T * T * T * T / 863310000;
        
        // 主要項の計算（簡易版）
        const Drad = D * Math.PI / 180;
        const Mrad = M * Math.PI / 180;
        const Mprimerad = Mprime * Math.PI / 180;
        const Frad = F * Math.PI / 180;
        
        let correction = 6.288774 * Math.sin(Mprimerad) +
                        1.274027 * Math.sin(2 * Drad - Mprimerad) +
                        0.658314 * Math.sin(2 * Drad) +
                        0.213618 * Math.sin(2 * Mprimerad) -
                        0.185116 * Math.sin(Mrad) -
                        0.114332 * Math.sin(2 * Frad);
        
        return this.normalize(L + correction);
    }
    
    // 惑星の黄経（簡易近似）
    static planetLongitude(planet, date) {
        const jd = this.julianDay(date);
        const T = this.julianCentury(jd);
        
        // 惑星の軌道要素（簡易版）
        const elements = {
            'Mercury': { L0: 252.250906, L1: 149472.6746358, e: 0.20563069, a: 0.38709893 },
            'Venus':   { L0: 181.979801, L1: 58517.8156760, e: 0.00677323, a: 0.72333199 },
            'Mars':    { L0: 355.433000, L1: 19140.299314, e: 0.09341233, a: 1.52366231 },
            'Jupiter': { L0: 34.351519, L1: 3034.90371757, e: 0.04839266, a: 5.20336301 },
            'Saturn':  { L0: 50.077444, L1: 1222.11379404, e: 0.05415060, a: 9.53707032 },
            'Uranus':  { L0: 314.055005, L1: 428.46990410, e: 0.04716771, a: 19.19126393 },
            'Neptune': { L0: 304.348665, L1: 218.48609010, e: 0.00858587, a: 30.06896348 },
            'Pluto':   { L0: 238.928980, L1: 145.18028410, e: 0.24880766, a: 39.48168677 }
        };
        
        if (!elements[planet]) {
            throw new Error(`Unknown planet: ${planet}`);
        }
        
        const elem = elements[planet];
        
        // 平均黄経
        const L = elem.L0 + elem.L1 * T;
        
        // 簡易的な補正（真の近点角を使用）
        const M = L - (elem.L0 + 180);
        const Mrad = M * Math.PI / 180;
        
        // 中心差の近似
        const C = (2 * elem.e - elem.e * elem.e * elem.e / 4) * Math.sin(Mrad) +
                  (5 / 4) * elem.e * elem.e * Math.sin(2 * Mrad) +
                  (13 / 12) * elem.e * elem.e * elem.e * Math.sin(3 * Mrad);
        
        return this.normalize(L + C);
    }
    
    // 天体の黄経を計算（統一インターフェース）
    static eclipticLongitude(body, date) {
        switch (body) {
            case 'Sun':
                return this.sunLongitude(date);
            case 'Moon':
                return this.moonLongitude(date);
            case 'Mercury':
            case 'Venus':
            case 'Mars':
            case 'Jupiter':
            case 'Saturn':
            case 'Uranus':
            case 'Neptune':
            case 'Pluto':
                return this.planetLongitude(body, date);
            default:
                throw new Error(`Unknown body: ${body}`);
        }
    }
    
    // 地方恒星時の計算
    static localSiderealTime(date, longitude) {
        const jd = this.julianDay(date);
        const T = this.julianCentury(jd);
        
        // グリニッジ恒星時
        const theta0 = 280.46061837 + 360.98564736629 * (jd - 2451545.0) +
                       0.000387933 * T * T - T * T * T / 38710000;
        
        // 地方恒星時
        const lst = this.normalize(theta0 + longitude);
        
        return lst;
    }
    
    // アセンダント（上昇点）の計算
    static ascendant(date, latitude, longitude) {
        const lst = this.localSiderealTime(date, longitude);
        const latRad = latitude * Math.PI / 180;
        const lstRad = lst * Math.PI / 180;
        
        // 簡易計算
        const asc = Math.atan2(Math.cos(lstRad), 
                              -Math.sin(lstRad) * Math.cos(latRad));
        let ascDeg = asc * 180 / Math.PI;
        
        return this.normalize(ascDeg);
    }
    
    // MC（天頂）の計算
    static midheaven(date, longitude) {
        const lst = this.localSiderealTime(date, longitude);
        return this.normalize(lst);
    }
}

// グローバルに公開
window.Ephemeris = Ephemeris;
