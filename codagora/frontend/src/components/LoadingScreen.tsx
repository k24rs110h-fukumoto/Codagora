import Logo from "./Logo";

type LoadingScreenProps = {
  label?: string;
};

function LoadingScreen({ label = "Codagoraを読み込んでいます" }: LoadingScreenProps) {
  return (
    <main className="loading-screen">
      <Logo />
      <span className="loading-spinner" />
      <p>{label}</p>
    </main>
  );
}

export default LoadingScreen;
