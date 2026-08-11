import { Link } from "react-router-dom";

type LogoProps = {
  to?: string;
  compact?: boolean;
};

function Logo({ to = "/", compact = false }: LogoProps) {
  return (
    <Link to={to} className={`brand${compact ? " brand--compact" : ""}`}>
      <span className="brand-mark" aria-hidden="true">
        <span />
        <span />
        <span />
      </span>

      {!compact && <span>Codagora</span>}
    </Link>
  );
}

export default Logo;
