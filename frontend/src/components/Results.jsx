import { useEffect, useRef } from "react";
import MedicineRow from "./MedicineRow";
import SavingsReceipt from "./SavingsReceipt";

/** Everything shown after a successful check: heading, savings bill and one row per medicine. */
export default function Results({ data }) {
  const headingRef = useRef(null);
  useEffect(() => {
    headingRef.current?.focus();
  }, []);

  const results = data.results || [];

  return (
    <section className="results" aria-labelledby="results-title">
      <h2 id="results-title" className="results-title" ref={headingRef} tabIndex={-1}>
        {results.length === 0
          ? "No medicines found"
          : `${results.length} ${results.length === 1 ? "medicine" : "medicines"} found`}
      </h2>

      {results.length === 0 ? (
        <p className="empty">Try pasting just the medicine lines as text, or upload a sharper, well-lit photo.</p>
      ) : (
        <>
          {data.summary.with_savings > 0 && <SavingsReceipt summary={data.summary} />}
          <ul className="ledger">
            {results.map((result, i) => (
              <MedicineRow result={result} key={`${result.input.name}-${i}`} />
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
