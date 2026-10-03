/* Small deterministic search index for the current evidence snapshot. */
window.PPRSearch = (() => {
  const aliases = {
    'Arabidopsis thaliana': ['arabidopsis', 'thale cress', '拟南芥'],
    'Brassica napus': ['rapeseed', 'canola', '油菜'],
    'Brassica rapa': ['field mustard', '白菜', '芜菁'],
    'Daucus carota': ['carrot', '胡萝卜'],
    'Glycine max': ['soybean', 'soya', '大豆'],
    'Lotus japonicus': ['lotus', '百脉根'],
    'Medicago truncatula': ['medicago', 'barrel medic', '苜蓿'],
    'Oryza sativa': ['rice', '水稻', '稻'],
    'Solanum lycopersicum': ['tomato', '番茄'],
    'Triticum aestivum': ['wheat', 'bread wheat', '小麦'],
    'Zea mays': ['maize', 'corn', '玉米']
  };
  const normalize = value => String(value || '').normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
  const geneTokens = value => String(value || '').match(/\b(?:[A-Z]{2,}[A-Za-z0-9.-]*|[A-Z][a-z]+[A-Z][A-Za-z0-9.-]*|[A-Z][a-z]*[A-Z]{2,}[A-Za-z0-9.-]*)\b/g) || [];

  function distance(a, b, limit) {
    if (Math.abs(a.length - b.length) > limit) return limit + 1;
    let previous = Array.from({length:b.length + 1}, (_, i) => i);
    for (let i = 1; i <= a.length; i++) {
      const next = [i];
      let minimum = next[0];
      for (let j = 1; j <= b.length; j++) {
        next[j] = Math.min(next[j - 1] + 1, previous[j] + 1, previous[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
        minimum = Math.min(minimum, next[j]);
      }
      if (minimum > limit) return limit + 1;
      previous = next;
    }
    return previous[b.length];
  }

  function matchScore(query, term, weight, allowFuzzy = true) {
    const q = normalize(query), t = normalize(term);
    if (!q || !t) return 0;
    if (q === t) return 130 + weight;
    if (t.startsWith(q)) return 106 + weight - Math.min(18, t.length - q.length);
    if (t.includes(q)) return 84 + weight;
    if (q.length >= 4 && q.includes(t)) return 72 + weight;
    if (!allowFuzzy || q.length < 3) return 0;
    const stem = t.replace(/[0-9]+$/, '');
    const candidates = stem.length >= 3 && stem !== t ? [t, stem] : [t];
    const max = q.length >= 5 ? 2 : 1;
    const best = Math.min(...candidates.map(candidate => distance(q, candidate, max)));
    return best <= max ? 52 + weight - (best - 1) * 18 : 0;
  }

  function termsFor(record) {
    const out = [];
    const add = (value, type, weight, suggest = false) => {
      if (value && normalize(value).length >= 2) out.push({value, type, weight, suggest});
    };
    add(record.pair_id, 'Record ID', 65, true);
    add(record.species, 'Species', 52, true);
    for (const alias of aliases[record.species] || []) add(alias, 'Common name', 54, true);
    add(record.ligand_tested, 'Ligand', 29, false);
    add(record.receptor_or_complex_tested, 'Receptor', 25, false);
    for (const token of geneTokens(record.ligand_tested)) add(token, 'Ligand', 48, true);
    for (const token of geneTokens(record.receptor_or_complex_tested)) add(token, 'Receptor', 43, true);
    add(record.primary_doi, 'DOI', 16, false);
    add(record.binding_assay, 'Assay', -8, false);
    return out;
  }

  function create(records) {
    const indexed = records.map(record => ({record, terms:termsFor(record)}));
    const catalog = new Map();
    for (const {record, terms} of indexed) for (const term of terms) {
      if (!term.suggest) continue;
      const key = `${normalize(term.value)}|${term.type}`;
      const found = catalog.get(key);
      if (found) found.ids.add(record.pair_id);
      else catalog.set(key, {...term, ids:new Set([record.pair_id])});
    }
    function search(query) {
      if (!normalize(query)) return records.map(record => ({record, score:0}));
      const exactId = indexed.find(({record}) => normalize(record.pair_id) === normalize(query));
      if (exactId) return [{record:exactId.record, score:999}];
      const rank = allowFuzzy => indexed.map(({record, terms}) => ({record, score:Math.max(0, ...terms.map(t => matchScore(query, t.value, t.weight, allowFuzzy)))}))
        .filter(hit => hit.score > 0)
        .sort((a,b) => b.score - a.score || Number(a.record.pair_id.slice(4)) - Number(b.record.pair_id.slice(4)));
      const direct = rank(false);
      return direct.length ? direct : rank(true);
    }
    function suggest(query) {
      if (normalize(query).length < 2) return [];
      const all = [...catalog.values()];
      const exact = all.filter(item => normalize(item.value) === normalize(query));
      return (exact.length ? exact : all)
        .map(item => ({...item, score:matchScore(query, item.value, item.weight)}))
        .filter(item => item.score > 0)
        .sort((a,b) => b.score - a.score || b.ids.size - a.ids.size || a.value.localeCompare(b.value))
        .slice(0, 7);
    }
    return {search, suggest};
  }
  return {create};
})();

