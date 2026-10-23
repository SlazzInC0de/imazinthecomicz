"use client";

export default function Error({ reset }: { error: Error; reset: () => void }) {
  return (
    <div className="notice" role="alert" style={{ marginTop: 56 }}>
      <h2>This page did not load</h2>
      <p>
        Something went wrong while building it.{" "}
        <button type="button" className="btn quiet" onClick={reset} style={{ marginLeft: 8, padding: "6px 14px" }}>
          Try again
        </button>
      </p>
    </div>
  );
}
