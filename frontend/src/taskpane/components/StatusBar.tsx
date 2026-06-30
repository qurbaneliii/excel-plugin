export function StatusBar({ backendOk, message }: { backendOk: boolean; message: string }) {
  return (
    <div className={`status ${backendOk ? "ok" : "error"}`}>
      <strong>Backend:</strong> {backendOk ? "Connected" : "Disconnected"} | {message}
    </div>
  );
}
