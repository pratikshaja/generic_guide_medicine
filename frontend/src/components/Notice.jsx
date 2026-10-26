import { useEffect, useRef } from "react";

/** An error message box. Moves keyboard focus to its heading when it appears. */
export default function Notice({ title, children }) {
  const headingRef = useRef(null);
  useEffect(() => {
    headingRef.current?.focus();
  }, []);

  return (
    <section className="notice notice-error" role="alert">
      <h2 className="notice-title" ref={headingRef} tabIndex={-1}>
        {title}
      </h2>
      <p>{children}</p>
    </section>
  );
}
