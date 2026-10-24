import Link from "next/link";

export default function NotFound() {
  return (
    <div className="wrap missing">
      <h1>KRAKA-404!</h1>
      <p>This page wandered off into another universe.</p>
      <Link href="/" className="btn btn-primary">
        Back to search
      </Link>
    </div>
  );
}
