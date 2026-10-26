import { money } from "../format";

/** The bill-style summary: total for brands, total for generics, and what you save. */
export default function SavingsReceipt({ summary }) {
  const doctor = summary.status_counts?.ask_doctor || 0;
  return (
    <>
      <div className="receipt-wrap">
        <div className="receipt">
          <dl className="receipt-lines">
            <div>
              <dt>Brands</dt>
              <dd>{money(summary.total_brand_price)}</dd>
            </div>
            <div>
              <dt>Generics, same quantity</dt>
              <dd>{money(summary.total_generic_price)}</dd>
            </div>
          </dl>
          <p className="receipt-save">
            <span className="receipt-save-label">You save</span>
            <span className="receipt-save-amount">{money(summary.total_saving)}</span>
            <span className="receipt-save-pct">{summary.saving_percent}% less</span>
          </p>
          <p className="receipt-foot">
            {summary.with_savings} of {summary.medicines_found} medicines compared
          </p>
        </div>
      </div>
      {doctor > 0 && (
        <p className="receipt-note">
          {doctor === 1 ? "1 medicine was" : `${doctor} medicines were`} left out of the total because your doctor
          should decide on any switch.
        </p>
      )}
    </>
  );
}
