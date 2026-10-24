import { number, percent } from '@/lib/format';
import { names, sentiments, splitNames } from '@/lib/sentiment';
import type { Counts, Split, Summary } from '@/lib/types';

const splits: Split[] = ['train', 'val', 'test'];

export function SentimentDonut({ counts }: { counts: Counts }) {
  const total = sentiments.reduce((sum, label) => sum + counts[label], 0);
  if (!total) return <p className="chart-empty">Belum ada opini berlabel untuk ditampilkan.</p>;
  let offset = 0;
  const segments = sentiments.map(label => {
    const segment = { label, share: counts[label] / total * 100, offset };
    offset += segment.share;
    return segment;
  });
  const description = sentiments.map(label => `${names[label]}: ${number(counts[label])} opini (${percent(counts[label] / total)})`).join(', ');

  return (
    <div className="donut-layout">
      <div className="donut-figure">
        <svg className="sentiment-donut" viewBox="0 0 220 220" role="img" aria-label={`Proporsi sentimen. ${description}`}>
          {segments.filter(segment => segment.share > 0).map(segment => (
            <circle key={segment.label} cx="110" cy="110" r="83" pathLength="100" fill="none" stroke={`var(--${segment.label})`} strokeWidth="25" strokeDasharray={`${segment.share} ${100 - segment.share}`} strokeDashoffset={-segment.offset} transform="rotate(-90 110 110)" />
          ))}
          {segments.filter(segment => segment.share > 0 && segment.share < 100).map(segment => {
            const angle = (segment.offset / 100 * 360 - 90) * Math.PI / 180;
            return <line key={segment.label} x1={110 + 69 * Math.cos(angle)} y1={110 + 69 * Math.sin(angle)} x2={110 + 97 * Math.cos(angle)} y2={110 + 97 * Math.sin(angle)} stroke="var(--surface)" strokeWidth="3" />;
          })}
        </svg>
        <div className="donut-total" aria-hidden="true"><strong>{number(total)}</strong><span>opini berlabel</span></div>
      </div>
      <dl className="donut-legend">
        {sentiments.map(label => (
          <div key={label}>
            <dt><span className={`legend-swatch ${label}`} aria-hidden="true" />{names[label]}</dt>
            <dd><strong>{number(counts[label])}</strong><span>{percent(counts[label] / total)}</span></dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

export function SplitDistribution({ data }: { data: Summary['splits'] }) {
  const maximum = Math.max(...splits.flatMap(split => sentiments.map(label => data[split].counts[label])));
  if (!maximum) return <p className="chart-empty">Bagian dataset belum memiliki opini berlabel.</p>;
  const magnitude = 10 ** Math.floor(Math.log10(maximum));
  const ceiling = Math.ceil(maximum / magnitude) * magnitude;
  const description = splits.map(split => `${splitNames[split]}: ${sentiments.map(label => `${names[label]} ${number(data[split].counts[label])}`).join(', ')}`).join('. ');

  return (
    <div className="split-chart-content">
      <ul className="chart-legend" aria-label="Kategori sentimen">{sentiments.map(label => <li key={label}><span className={`legend-swatch ${label}`} aria-hidden="true" />{names[label]}</li>)}</ul>
      <div className="grouped-plot" role="img" aria-label={`Jumlah opini menurut bagian dataset. ${description}`}>
        <div className="plot-scale" aria-hidden="true">{[1, .75, .5, .25, 0].map(tick => <span key={tick}>{number(ceiling * tick)}</span>)}</div>
        <div className="plot-area" aria-hidden="true">
          <div className="plot-grid">{[0, 1, 2, 3, 4].map(tick => <span key={tick} />)}</div>
          <div className="plot-groups">
            {splits.map(split => (
              <div className="plot-group" key={split}>
                <div className="plot-bars">{sentiments.map(label => <span key={label} className={`plot-bar ${label}`} style={{ height: `${data[split].counts[label] / ceiling * 100}%` }} title={`${splitNames[split]} · ${names[label]}: ${number(data[split].counts[label])}`} />)}</div>
                <span className="plot-group-label">{splitNames[split]}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
      <details className="chart-data-details">
        <summary>Lihat angka pada grafik</summary>
        <div className="table-scroll" tabIndex={0} role="region" aria-label="Jumlah sentimen per bagian dataset">
          <table><caption className="sr-only">Jumlah opini untuk setiap sentimen dan bagian dataset</caption><thead><tr><th scope="col">Bagian</th>{sentiments.map(label => <th scope="col" key={label}>{names[label]}</th>)}</tr></thead><tbody>{splits.map(split => <tr key={split}><th scope="row">{splitNames[split]}</th>{sentiments.map(label => <td key={label}>{number(data[split].counts[label])}</td>)}</tr>)}</tbody></table>
        </div>
      </details>
    </div>
  );
}
