// 円形ホロスコープ図(SVG)とデータ表・プロフェクション計算
// app.js から window.HoroscopeChart 経由で利用する

(function () {
    const SIGN_GLYPHS = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓']
        .map(g => g + '︎');
    const SIGNS_JP = ['牡羊座', '牡牛座', '双子座', '蟹座', '獅子座', '乙女座',
                      '天秤座', '蠍座', '射手座', '山羊座', '水瓶座', '魚座'];
    const SIGN_COLORS = ['#c0392b', '#7d6608', '#2471a3', '#1e8449',
                         '#c0392b', '#7d6608', '#2471a3', '#1e8449',
                         '#c0392b', '#7d6608', '#2471a3', '#1e8449'];
    const GLYPHS = {
        Sun: '☉', Moon: '☽', Mercury: '☿', Venus: '♀', Mars: '♂',
        Jupiter: '♃', Saturn: '♄', Uranus: '♅', Neptune: '♆', Pluto: '♇',
        TrueNode: '☊', Chiron: '⚷'
    };
    Object.keys(GLYPHS).forEach(k => { GLYPHS[k] += '︎'; });
    const ORDER = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn',
                   'Uranus', 'Neptune', 'Pluto', 'TrueNode', 'Chiron'];
    const NAMES_JP = {
        Sun: '太陽', Moon: '月', Mercury: '水星', Venus: '金星', Mars: '火星',
        Jupiter: '木星', Saturn: '土星', Uranus: '天王星', Neptune: '海王星',
        Pluto: '冥王星', TrueNode: 'ドラゴンヘッド', Chiron: 'キローン'
    };
    // 伝統ルーラー(年主星の判定に使用)
    const RULERS_JP = ['火星', '金星', '水星', '月', '太陽', '水星',
                      '金星', '火星', '木星', '土星', '土星', '木星'];

    const CX = 540, CY = 540;
    const R_OUT = 400, R_IN = 340, R_PLANET = 265, R_HOUSE = 165, R_ASPECT = 195;
    const R_TRANS = 428;          // 外周リング(トランジット/プログレス)の基準半径
    const R_TRANS_OUT = 466;      // 外周リングの外側境界
    const INK = '#2b2a26', ACCENT = '#7a5c2e', LINE = '#cbc2ae';
    const C_TRANS = '#2471a3';    // トランジット=青
    const C_PROG = '#1e8449';     // プログレス=緑

    function fmtDeg(d) {
        let deg = Math.floor(d);
        let min = Math.round((d - deg) * 60);
        if (min === 60) { deg += 1; min = 0; }
        return `${deg}°${String(min).padStart(2, '0')}′`;
    }

    // extras: {transit: {Sun:{longitude,...},...}, progressed: [{label:'P☉', pd:{longitude,...}}, ...]}
    function wheelSVG(natal, extras) {
        const asc = natal.houses.ascendant.longitude;
        const mc = natal.houses.midheaven.longitude;
        const cusps = natal.houses.cusps;
        const hasOuter = !!(extras && (extras.transit || extras.progressed));
        const viewH = hasOuter ? 1148 : 1080;
        const pt = (deg, r) => {
            const th = (180 + (deg - asc)) * Math.PI / 180;
            return [CX + r * Math.cos(th), CY - r * Math.sin(th)];
        };
        const s = [];
        s.push(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 ${viewH}" ` +
               `font-family="Hiragino Mincho ProN, Yu Mincho, serif">`);
        for (const r of [R_OUT, R_IN, R_ASPECT]) {
            s.push(`<circle cx="${CX}" cy="${CY}" r="${r}" fill="none" stroke="${LINE}" stroke-width="1.5"/>`);
        }
        s.push(`<circle cx="${CX}" cy="${CY}" r="${R_OUT}" fill="none" stroke="${ACCENT}" stroke-width="2.5"/>`);
        if (hasOuter) {
            s.push(`<circle cx="${CX}" cy="${CY}" r="${R_TRANS_OUT}" fill="none" stroke="${LINE}" stroke-width="1.2"/>`);
        }

        for (let i = 0; i < 12; i++) {
            const [x1, y1] = pt(i * 30, R_IN);
            const [x2, y2] = pt(i * 30, R_OUT);
            s.push(`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${ACCENT}" stroke-width="1.2"/>`);
            const [gx, gy] = pt(i * 30 + 15, (R_OUT + R_IN) / 2);
            s.push(`<text x="${gx}" y="${gy + 12}" text-anchor="middle" font-size="34" ` +
                   `fill="${SIGN_COLORS[i]}">${SIGN_GLYPHS[i]}</text>`);
            for (let d = 0; d < 30; d += 5) {
                const [ax, ay] = pt(i * 30 + d, R_IN);
                const [bx, by] = pt(i * 30 + d, R_IN + (d % 10 === 0 ? 14 : 8));
                s.push(`<line x1="${ax}" y1="${ay}" x2="${bx}" y2="${by}" stroke="${LINE}" stroke-width="1"/>`);
            }
        }

        cusps.forEach((c, i) => {
            const bold = [0, 3, 6, 9].includes(i);
            const [x1, y1] = pt(c, R_ASPECT);
            const [x2, y2] = pt(c, R_IN);
            s.push(`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" ` +
                   `stroke="${bold ? ACCENT : LINE}" stroke-width="${bold ? 2.5 : 1}"/>`);
            const span = ((cusps[(i + 1) % 12] - c) % 360 + 360) % 360;
            const [hx, hy] = pt(c + span / 2, R_HOUSE);
            s.push(`<text x="${hx}" y="${hy + 6}" text-anchor="middle" font-size="17" fill="#9b9483">${i + 1}</text>`);
        });

        for (const [ang, name] of [[asc, 'ASC'], [mc, 'MC']]) {
            const [lx, ly] = pt(ang, (hasOuter ? R_TRANS_OUT : R_OUT) + 24);
            s.push(`<text x="${lx}" y="${ly + 6}" text-anchor="middle" font-size="19" ` +
                   `font-weight="bold" fill="${ACCENT}">${name}</text>`);
        }

        // 天体(近接時は内側へずらす)
        const entries = ORDER
            .filter(k => natal.planets[k] && natal.planets[k].longitude !== undefined)
            .map(k => [natal.planets[k].longitude, k, natal.planets[k]])
            .sort((a, b) => a[0] - b[0]);
        const placed = [];
        for (const [deg, name, pd] of entries) {
            let r = R_PLANET;
            let moved = true;
            while (moved) {
                moved = false;
                for (const [pdeg, pr] of placed) {
                    const gap = Math.abs(((deg - pdeg + 180) % 360 + 360) % 360 - 180);
                    if (gap < 8 && Math.abs(r - pr) < 36) { r -= 42; moved = true; }
                }
            }
            placed.push([deg, r]);
            const [tx, ty] = pt(deg, R_IN);
            const [ix, iy] = pt(deg, R_IN - 10);
            s.push(`<line x1="${tx}" y1="${ty}" x2="${ix}" y2="${iy}" stroke="${INK}" stroke-width="2"/>`);
            const [gx, gy] = pt(deg, r);
            s.push(`<text x="${gx}" y="${gy + 11}" text-anchor="middle" font-size="30" fill="${INK}">${GLYPHS[name]}</text>`);
            const [rx, ry] = pt(deg, r - 34);
            const retro = pd.retrograde ? 'R' : '';
            s.push(`<text x="${rx}" y="${ry + 5}" text-anchor="middle" font-size="13" ` +
                   `fill="#6b675e">${Math.floor(pd.degree)}°${String(Math.round((pd.degree % 1) * 60)).padStart(2, '0')}${retro}</text>`);
        }

        // メジャーアスペクト
        const ASPECTS = [[60, 5, '#1e8449', 1.4], [90, 6, '#c0392b', 1.6],
                         [120, 6, '#2471a3', 1.6], [180, 7, '#c0392b', 2]];
        const majors = entries.filter(e => e[1] !== 'TrueNode' && e[1] !== 'Chiron');
        for (let i = 0; i < majors.length; i++) {
            for (let j = i + 1; j < majors.length; j++) {
                const diff = Math.abs(((majors[i][0] - majors[j][0] + 180) % 360 + 360) % 360 - 180);
                for (const [ang, orb, color, w] of ASPECTS) {
                    if (Math.abs(diff - ang) <= orb) {
                        const [x1, y1] = pt(majors[i][0], R_ASPECT);
                        const [x2, y2] = pt(majors[j][0], R_ASPECT);
                        s.push(`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" ` +
                               `stroke="${color}" stroke-width="${w}" opacity="0.55"/>`);
                        break;
                    }
                }
            }
        }
        // 外周リング: トランジット(青)とプログレス(緑)
        if (hasOuter) {
            const outer = [];
            if (extras.transit) {
                for (const k of ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
                                 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']) {
                    const p = extras.transit[k];
                    if (p && p.longitude !== undefined) {
                        outer.push({ deg: p.longitude, glyph: GLYPHS[k], pd: p, color: C_TRANS });
                    }
                }
            }
            (extras.progressed || []).forEach(e => {
                if (e.pd && e.pd.longitude !== undefined) {
                    outer.push({ deg: e.pd.longitude, glyph: e.label, pd: e.pd, color: C_PROG, small: true });
                }
            });
            outer.sort((a, b) => a.deg - b.deg);
            const placedOuter = [];
            for (const o of outer) {
                let r = R_TRANS;
                let moved = true;
                while (moved) {
                    moved = false;
                    for (const [pdeg, pr] of placedOuter) {
                        const gap = Math.abs(((o.deg - pdeg + 180) % 360 + 360) % 360 - 180);
                        if (gap < 6 && Math.abs(r - pr) < 30) { r += 32; moved = true; }
                    }
                }
                placedOuter.push([o.deg, r]);
                const [tx, ty] = pt(o.deg, R_OUT);
                const [ix, iy] = pt(o.deg, R_OUT + 9);
                s.push(`<line x1="${tx}" y1="${ty}" x2="${ix}" y2="${iy}" stroke="${o.color}" stroke-width="2"/>`);
                const [gx, gy] = pt(o.deg, r);
                s.push(`<text x="${gx}" y="${gy + 8}" text-anchor="middle" ` +
                       `font-size="${o.small ? 17 : 22}" fill="${o.color}">${o.glyph}</text>`);
                const [rx, ry] = pt(o.deg, r + 22);
                const retro = o.pd.retrograde ? 'R' : '';
                s.push(`<text x="${rx}" y="${ry + 4}" text-anchor="middle" font-size="11" ` +
                       `fill="${o.color}" opacity="0.8">${Math.floor(o.pd.degree)}°${retro}</text>`);
            }
            // 凡例
            s.push(`<text x="${CX}" y="1112" text-anchor="middle" font-size="19" fill="#6b675e">` +
                   `<tspan fill="${INK}">● 内円=ネイタル</tspan>` +
                   `<tspan dx="26" fill="${C_TRANS}">● 外周=トランジット(現在)</tspan>` +
                   `<tspan dx="26" fill="${C_PROG}">● P=プログレス</tspan></text>`);
        }
        s.push('</svg>');
        return s.join('');
    }

    // 黄経→在室ハウス(ネイタルカスプ基準)
    function houseOf(lon, cusps) {
        for (let i = 0; i < 12; i++) {
            const a = cusps[i], b = cusps[(i + 1) % 12];
            if (((lon - a) % 360 + 360) % 360 < ((b - a) % 360 + 360) % 360) return i + 1;
        }
        return 12;
    }

    // プロフェクション: 年齢→起動ハウス(余り0=1ハウス)→起動サイン→年主星
    function profection(age, cusps) {
        const houseNum = (age % 12) + 1;
        const signIdx = Math.floor(cusps[houseNum - 1] / 30);
        return {
            age,
            house: houseNum,
            signJP: SIGNS_JP[signIdx],
            lordJP: RULERS_JP[signIdx],
            prevAge: age - 12,
        };
    }

    function esc(x) { return String(x).replace(/</g, '&lt;'); }

    function tablesHTML(natal, prog, trans, sr, prof, currentDate) {
        const h = [];
        h.push('<div class="data-grid">');

        // 天体配置
        h.push('<div class="data-card"><h4>ネイタル天体</h4><table>');
        for (const k of ORDER) {
            const p = natal.planets[k];
            if (!p || p.longitude === undefined) continue;
            h.push(`<tr><td>${GLYPHS[k]} ${NAMES_JP[k]}</td>` +
                   `<td>${p.signJP} ${fmtDeg(p.degree)}${p.retrograde ? ' ℞' : ''}</td>` +
                   `<td>第${p.house}ハウス</td></tr>`);
        }
        h.push(`<tr><td>ASC</td><td>${natal.houses.ascendant.signJP} ${fmtDeg(natal.houses.ascendant.degree)}</td><td>—</td></tr>`);
        h.push(`<tr><td>MC</td><td>${natal.houses.midheaven.signJP} ${fmtDeg(natal.houses.midheaven.degree)}</td><td>—</td></tr>`);
        h.push('</table></div>');

        // プロフェクション
        h.push('<div class="data-card"><h4>プロフェクション（今年の部屋）</h4><table>');
        h.push(`<tr><td>現在の年齢</td><td>${prof.age}歳</td></tr>`);
        h.push(`<tr><td>起動ハウス</td><td>第${prof.house}ハウス（${esc(prof.signJP)}）</td></tr>`);
        h.push(`<tr><td>年主星（鍵を預かる星）</td><td><strong>${esc(prof.lordJP)}</strong></td></tr>`);
        if (prof.prevAge >= 0) {
            h.push(`<tr><td>同じ部屋が前回起動した年齢</td><td>${prof.prevAge}歳</td></tr>`);
        }
        h.push('</table></div>');

        // プログレス(ハウスは出生図に重ねた在室)
        if (prog && prog.p_sun) {
            const cusps = natal.houses.cusps;
            const psH = houseOf(prog.p_sun.longitude, cusps);
            const pmH = houseOf(prog.p_moon.longitude, cusps);
            h.push('<div class="data-card"><h4>プログレス（進行図）</h4><table>');
            h.push(`<tr><td>進行の太陽</td><td>${prog.p_sun.signJP} ${fmtDeg(prog.p_sun.degree)}（ネイタル第${psH}ハウス）</td></tr>`);
            h.push(`<tr><td>進行の月</td><td>${prog.p_moon.signJP} ${fmtDeg(prog.p_moon.degree)}（ネイタル第${pmH}ハウス）</td></tr>`);
            h.push(`<tr><td>基準日</td><td>${esc(currentDate)}</td></tr>`);
            h.push('</table></div>');
        }

        // トランジット
        if (trans) {
            h.push('<div class="data-card"><h4>トランジット</h4><table>');
            if (trans.outer_planets) {
                for (const k of ['Uranus', 'Neptune', 'Pluto']) {
                    const p = trans.outer_planets[k];
                    if (!p) continue;
                    h.push(`<tr><td>${GLYPHS[k]} ${NAMES_JP[k]}（現在）</td>` +
                           `<td>${p.signJP} ${fmtDeg(p.degree)}${p.retrograde ? ' ℞' : ''}</td></tr>`);
                }
            }
            (trans.jupiter_transits || []).forEach(t => {
                h.push(`<tr><td>♃︎ 木星イングレス</td><td>${esc(t.date)} ${t.signJP}入り</td></tr>`);
            });
            (trans.saturn_transits || []).forEach(t => {
                h.push(`<tr><td>♄︎ 土星イングレス</td><td>${esc(t.date)} ${t.signJP}入り</td></tr>`);
            });
            h.push('</table></div>');
        }

        // ソーラーリターン
        if (sr && sr.houses) {
            h.push('<div class="data-card"><h4>ソーラーリターン（今年の図）</h4><table>');
            h.push(`<tr><td>有効期間</td><td>${esc(sr.valid_from)} 〜 ${esc(sr.valid_until)}</td></tr>`);
            h.push(`<tr><td>SR-ASC</td><td>${sr.houses.ascendant.signJP} ${fmtDeg(sr.houses.ascendant.degree)}</td></tr>`);
            h.push(`<tr><td>SR-MC</td><td>${sr.houses.midheaven.signJP} ${fmtDeg(sr.houses.midheaven.degree)}</td></tr>`);
            const su = sr.planets && sr.planets.Sun;
            if (su && su.house) h.push(`<tr><td>SR太陽の部屋</td><td>第${su.house}ハウス</td></tr>`);
            const mo = sr.planets && sr.planets.Moon;
            if (mo) h.push(`<tr><td>SR月</td><td>${mo.signJP} ${fmtDeg(mo.degree)}${mo.house ? `（第${mo.house}ハウス）` : ''}</td></tr>`);
            h.push('</table></div>');
        }

        h.push('</div>');
        return h.join('');
    }

    window.HoroscopeChart = { wheelSVG, profection, tablesHTML, houseOf };
})();
