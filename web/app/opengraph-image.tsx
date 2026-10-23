import { ImageResponse } from "next/og";

export const alt = "Imazinthecomics: describe a story, get manga and comics that tell it";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "70px 90px",
          background: "#fcfcfa",
          border: "14px solid #000",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ fontSize: 40, fontWeight: 700, color: "#000" }}>Imazinthecomics</div>
        <div
          style={{
            marginTop: 40,
            padding: "34px 56px",
            border: "6px solid #000",
            borderRadius: 999,
            background: "#fff",
            fontSize: 54,
            color: "#000",
            display: "flex",
          }}
        >
          a detective who can see ghosts
        </div>
        <div style={{ marginTop: 44, fontSize: 32, color: "#2f2f2f", display: "flex" }}>
          Describe a story. Get manga, manhwa and comics that fit.
        </div>
      </div>
    ),
    size,
  );
}
