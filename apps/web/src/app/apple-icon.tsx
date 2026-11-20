import { ImageResponse } from "next/og";

export const size = {
  width: 180,
  height: 180,
};

export const contentType = "image/png";

/**
 * Generate the 180x180 PNG Apple Touch Icon matching the VoiceBridge AI brand mark.
 */
export default function AppleIcon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background:
            "linear-gradient(135deg, #6366F1 0%, #4F46E5 55%, #3730A3 100%)",
          borderRadius: 40,
        }}
      >
        <svg
          width="132"
          height="132"
          viewBox="0 0 64 64"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M10 32H17L22 18L29 46L36 15L42 41L47 32H54"
            stroke="#FFFFFF"
            strokeWidth="4.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <circle cx="52" cy="12" r="4.5" fill="#34D399" />
        </svg>
      </div>
    ),
    {
      ...size,
    }
  );
}
