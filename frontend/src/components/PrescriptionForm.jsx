import { useEffect, useRef, useState } from "react";
import { EXAMPLES, IMAGE_TYPES, MAX_IMAGE_BYTES } from "../constants";

/** The input card: choose text or photo, fill it in, and submit. Reports the input up via onSubmit. */
export default function PrescriptionForm({ loading, onSubmit }) {
  const [mode, setMode] = useState("text"); // text | image
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [fileError, setFileError] = useState("");
  const [previewUrl, setPreviewUrl] = useState("");
  const fileInput = useRef(null);

  useEffect(() => {
    if (!file) {
      setPreviewUrl("");
      return undefined;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  function pickFile(event) {
    const chosen = event.target.files?.[0];
    setFileError("");
    if (!chosen) return;
    if (!IMAGE_TYPES.includes(chosen.type)) {
      setFile(null);
      setFileError("Use a JPEG, PNG or WebP image.");
    } else if (chosen.size > MAX_IMAGE_BYTES) {
      setFile(null);
      setFileError("This image is larger than 5 MB. Choose a smaller one.");
    } else {
      setFile(chosen);
    }
    event.target.value = "";
  }

  function removeFile() {
    setFile(null);
    setFileError("");
  }

  function handleSubmit(event) {
    event.preventDefault();
    onSubmit({ mode, text, file });
  }

  const canSubmit = !loading && (mode === "text" ? text.trim().length > 0 : Boolean(file));

  return (
    <form className="intake" onSubmit={handleSubmit}>
      <div className="modes" role="group" aria-label="How to add the prescription">
        <button type="button" aria-pressed={mode === "text"} onClick={() => setMode("text")}>
          Paste text
        </button>
        <button type="button" aria-pressed={mode === "image"} onClick={() => setMode("image")}>
          Upload photo
        </button>
      </div>

      {mode === "text" ? (
        <>
          <label className="field-label" htmlFor="rx">
            Prescription text
          </label>
          <textarea
            id="rx"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={"Tab Dolo 650 1 tab TDS x 3 days\nTab Pan 40 1 tab OD before breakfast"}
            rows={9}
          />
          <div className="examples">
            <span>Try an example:</span>
            {EXAMPLES.map((ex) => (
              <button type="button" className="example" key={ex.label} onClick={() => setText(ex.text)}>
                {ex.label}
              </button>
            ))}
          </div>
        </>
      ) : (
        <>
          <input
            ref={fileInput}
            className="file-input"
            type="file"
            accept={IMAGE_TYPES.join(",")}
            onChange={pickFile}
            aria-label="Choose a prescription photo"
          />
          {previewUrl ? (
            <div className="drop has-photo">
              <img src={previewUrl} alt="Selected prescription" />
            </div>
          ) : (
            <button type="button" className="drop" onClick={() => fileInput.current?.click()}>
              <span className="drop-text">
                <strong>Choose a photo of the prescription</strong>
                <span>JPEG, PNG or WebP, up to 5 MB</span>
              </span>
            </button>
          )}
          {file && (
            <div className="photo-bar">
              <span className="file-name">{file.name}</span>
              <span className="photo-actions">
                <button type="button" className="secondary" onClick={() => fileInput.current?.click()}>
                  Replace photo
                </button>
                <button type="button" className="secondary danger" onClick={removeFile}>
                  Remove photo
                </button>
              </span>
            </div>
          )}
          {fileError && (
            <p className="field-error" role="alert">
              {fileError}
            </p>
          )}
        </>
      )}

      <div className="actions">
        <button type="submit" className="primary" disabled={!canSubmit}>
          {loading ? "Reading prescription…" : "Find generics"}
        </button>
         {text && (
              <button type="button" className="secondary" onClick={() => setText("")}>
                Clear Text
              </button>
            )}
        <p className="fine">Sample prices. Not medical advice.</p>
      </div>
    </form>
  );
}
