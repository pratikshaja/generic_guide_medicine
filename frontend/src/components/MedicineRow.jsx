import { STATUS } from "../constants";
import { money, unitWord } from "../format";

/** One medicine from the prescription: what was read, the status badge, and the price comparison. */
export default function MedicineRow({ result }) {
  const status = STATUS[result.status] || STATUS.not_found;
  const { input, match, generic, savings } = result;
  const title = match ? match.brand_name : [input.name, input.strength].filter(Boolean).join(" ");
  const readAs = [input.name, input.strength, input.form, input.frequency].filter(Boolean).join(", ");

  return (
    <li className="row">
      <div className="row-main">
        <div className="row-head">
          <h3 className="row-title">{title}</h3>
          <span className={`badge tone-${status.tone}`}>{status.label}</span>
        </div>

        {match && (
          <p className="composition">
            {match.salt} {match.strength}, {match.form}
          </p>
        )}
        {result.status !== "matched" && result.message && <p className="message">{result.message}</p>}
        {generic && <p className="generic-name">Generic: {generic.generic_name}</p>}

        {result.alternatives?.length > 0 && (
          <ul className="alts" aria-label="Available options">
            {result.alternatives.map((a) => (
              <li key={`${a.brand_name}-${a.strength}-${a.form}`}>
                {a.brand_name}, {a.form}
              </li>
            ))}
          </ul>
        )}

        <details className="how">
          <summary>How this line was read</summary>
          <dl className="facts">
            {input.raw_text && (
              <>
                <dt>You wrote</dt>
                <dd>{input.raw_text}</dd>
              </>
            )}
            <dt>Read as</dt>
            <dd>{readAs || "unclear"}</dd>
            <dt>AI confidence</dt>
            <dd>{Math.round((input.confidence || 0) * 100)}%</dd>
            {input.strength_source === "inferred_from_name" && (
              <>
                <dt>Strength</dt>
                <dd>Taken from the brand name</dd>
              </>
            )}
          </dl>
        </details>
      </div>

      {savings && (
        <div className="row-price">
          <dl className="prices">
            <div>
              <dt>Brand</dt>
              <dd>{money(savings.brand_price)}</dd>
            </div>
            <div>
              <dt>Generic</dt>
              <dd>{money(savings.generic_price_same_quantity)}</dd>
            </div>
            <div className="save">
              <dt>You save</dt>
              <dd>
                {money(savings.saving)}
                <span className="pct">{savings.saving_percent}%</span>
              </dd>
            </div>
          </dl>
          <p className="qty">
            For the same {savings.units_compared} {unitWord(match?.form)}
          </p>
        </div>
      )}
    </li>
  );
}
