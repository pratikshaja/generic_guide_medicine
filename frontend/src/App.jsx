import { useState } from "react";
import "./App.css";
import { analyzePrescription } from "./api";
import { DEFAULT_DISCLAIMER } from "./constants";
import Notice from "./components/Notice";
import PrescriptionForm from "./components/PrescriptionForm";
import Results from "./components/Results";

export default function App() {
  const [phase, setPhase] = useState("idle"); // idle | loading | done | error
  const [slow, setSlow] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  async function handleSubmit(input) {
    setPhase("loading");
    setError("");
    setSlow(false);
    const timer = setTimeout(() => setSlow(true), 8000); // free hosting can take a while to wake up
    try {
      setData(await analyzePrescription(input));
      setPhase("done");
    } catch (err) {
      setError(err.message);
      setPhase("error");
    } finally {
      clearTimeout(timer);
      setSlow(false);
    }
  }

  const loading = phase === "loading";

  return (
    <div className="page">
      <header className="masthead">
        <span className="mark" aria-hidden="true" />
        <span className="wordmark">GenericGuide</span>
      </header>

      <main>
        <section className="intro">
          <h1>See what your prescription costs as generics</h1>
          <p>
            Paste a prescription or upload a photo. We read the medicines and compare each brand with its generic
            equivalent.
          </p>
        </section>

        <PrescriptionForm loading={loading} onSubmit={handleSubmit} />

        <div className="status-line" aria-live="polite">
          {loading &&
            (slow ? "The server may be waking up. The first request can take up to a minute." : "Reading your prescription…")}
        </div>

        {phase === "error" && <Notice title="Could not check this prescription">{error}</Notice>}
        {phase === "done" && data && <Results data={data} />}
      </main>

      <footer className="foot">
        <p>{data?.disclaimer || DEFAULT_DISCLAIMER}</p>
        <p>Generic prices come from the Jan Aushadhi (PMBJP) product list. Brand prices are approximate sample data.</p>
      </footer>
    </div>
  );
}
